import streamlit as st 
import pandas as pd 
import numpy as np
import yfinance as yf # For real stock data (optional, requires internet access)
import google.generativeai as genai # For generative AI features (optional, requires API key)

# ----------------------------------------------------------
# Hide the streamlit menu and toolbar
# ----------------------------------------------------------
hide_streamlit_style = """
<style>
/* Target specifically the action items on the right side of the header */
[data-testid="stToolbarActions"] {visibility: hidden !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# ----------------------------------------------------------
# 1. PAGE CONFIGURATION  (must be the very first st command)
# ----------------------------------------------------------

st.set_page_config(page_title=" My Time Series Chart",
                   page_icon="📈",
                   layout ="wide",)

@st.cache_data(ttl = 3600,show_spinner=False) #Cache the data for 1 hour to avoid hitting API limits and speed up the app
def fecth_stock_data(ticker_symbol,days):
    ticker = yf.Ticker(ticker_symbol)

    end_date = pd.Timestamp.today()#Specify the end date as today
    start_date = end_date - pd.Timedelta(days=days) #Calculate the start date
    hist = ticker.history(start=start_date, end=end_date)
    return hist

# ----------------------------------------------------------
# 2. TITLE & DESCRIPTION
# ----------------------------------------------------------
st.title("📈 Time Series Chart -Beginner Tutorial")
st.write("This app shows how to build a simple interactive time series chart in Streamlit.")

# ----------------------------------------------------------
# 3. SIDEBAR CONTROLS  (interactive widgets for the user)
# ----------------------------------------------------------
st.sidebar.header("⚙️ Settings")

#Germini API Key input (optional, only needed if you want to use generative AI features later)
api_key = st.sidebar.text_input("Enter your Germini API Key", type="password")
st.sidebar.markdown("[Get an API key here](https://aistudio.google.com/app/apikey)")
st.sidebar.divider()

#Dropdown to choose a dataset 
dataset = st.sidebar.selectbox(
    "Choose a dataset",
    options = ["Stock Price","Temperature","Website Traffic"],
)

if dataset == "Stock Price":
    ticker_symbol = st.sidebar.text_input("Enter Stock Ticker( e.g. AAPL,TSLA,MFST)",value="AAPL").upper()
#Slider to choose the number of days to show 

num_days = st.sidebar.slider(
    "Number of days ",
    min_value = 30,
    max_value = 365,
    value = 90,#Default value 
    step = 10
)

#Checkbox to toggle a 7 days rolling averagel line 
show_average = st.sidebar.checkbox("Show 7-day rolling average",value=True)

# ----------------------------------------------------------
# 4. GENERATE SAMPLE DATA  (replace this with your real data)
# ----------------------------------------------------------
np.random.seed(42)

# Build a date range ending today
dates = pd.date_range(end=pd.Timestamp.today(), periods=num_days, freq="D")

# Create different fake data depending on the selected dataset
if dataset == "Stock Price":
    with st.spinner(f"Fetching {ticker_symbol} data..."):
        hist = fecth_stock_data(ticker_symbol,num_days)

    #Safety check on the input provided. 
    if hist.empty:
        st.error(f"Could not find any data for ticker {ticker_symbol}.Please check the spelling and try again.")
        st.stop() #Stop the app if no data is found  
    #We only need the 'close' price for a simple line chart 
    df = hist[['Close']].copy()
    ylabel = f"{ticker_symbol} Close Price (USD)"

    df.columns = [ylabel] #Rename the column to match the ylabel for consistency
    #Ensure the index is formatted nicely as just the date 
    df.index = df.index.tz_localize(None).normalize() #Remove timezone and time component for cleaner x-axis labels
    df.index.name = "Date" #Name the index for better display in the raw data table

elif dataset == "Temperature":
    # Seasonal sine wave + noise
    values = 20 + 10 * np.sin(np.linspace(0, 2 * np.pi, num_days)) + np.random.randn(num_days)
    ylabel = "Temperature (°C)"
    df = pd.DataFrame({"Date": dates, ylabel: values}).set_index("Date")
else:  # Website Traffic
    values = np.abs(500 + np.cumsum(np.random.randn(num_days) * 20))
    ylabel = "Daily Visitors"
    df = pd.DataFrame({"Date": dates, ylabel: values}).set_index("Date")



# Optionally add a rolling average column
if show_average:
    df["7-Day Average"] = df[ylabel].rolling(7).mean()

# ----------------------------------------------------------
# 5. DISPLAY THE CHART
# ----------------------------------------------------------
st.subheader(f"{dataset} – Last {num_days} Days")

#Line chart which is them most simplest way to draw a time series 
st.line_chart(df)

# ----------------------------------------------------------
# 6. SHOW THE RAW DATA  (optional, great for debugging)
# ----------------------------------------------------------
with st.expander("🔍 See raw data"):
    st.dataframe(df.tail(20))  # Show the last 20 rows of the data

# ----------------------------------------------------------
# 7. KEY METRICS  (a nice summary at the bottom)
# ----------------------------------------------------------

st.divider()
col1, col2, col3 , col4= st.columns(4)
col1.metric("Latest Value",  f"{df.iloc[-1, 0]:.2f}")
col2.metric("Average",       f"{df.iloc[:, 0].mean():.2f}")
col3.metric("Max Value",     f"{df.iloc[:, 0].max():.2f}")
col4.metric("Min Value",     f"{df.iloc[:, 0].min():.2f}")
# ----------------------------------------------------------
# TIP: Replace the generated data above with your own CSV:
#
#   df = pd.read_csv("mydata.csv", parse_dates=["Date"])
#   df = df.set_index("Date")
#   st.line_chart(df)
# ----------------------------------------------------------

# ----------------------------------------------------------
# 8. AI TIME SERIES ANALYSIS (optional, only if API key is provided)
# ----------------------------------------------------------
st.divider()
st.subheader("AI Insights")
st.write("Ask Gemini to analyze the trends, volatility, and anomalies in your current dataset.")

if st.button("Generate Analysis with Germini"):
    if not api_key:
        st.error("PAsk Germini to analyze the trends ,volatility, and anomalies in your current dataset.")
    else:
        with st.spinner("Gemini is analyzing the data..."):
            try:
                genai.configure(api_key=api_key)

                model = genai.GenerativeModel('gemini-2.5-flash')

                #Convert the dataframe to CSV format for easier input to the model
                csv_data = df.to_csv()

                #Construct a prompt for the model
                prompt = f"""
                You are an expert data analyst. I am providing you with a time series dataset representing {dataset} over the last {num_days} days.
                
                Please provide a brief, well-structured analysis including:
                1. The overall trend (upward, downward, stagnant).
                2. Any noticeable volatility or patterns (like seasonality).
                3. A brief summary of what this data might indicate for the future.
                4. Provide required recommendations.
                
                Here is the raw CSV data:
                {csv_data}
                """

                #Call the API to generate the analysis
                response = model.generate_content(prompt)

                #Display the response 
                st.success("Analysis Complete!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"An error occured : {e}")
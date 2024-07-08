#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)
def fetch_stock_data(tickers, start_date, end_date):
    try:
        data = yf.download(tickers, start=start_date, end=end_date)
        if isinstance(data.columns, pd.MultiIndex):
            return data
        else:
            return pd.DataFrame({tickers: data})
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def calculate_vwap(data):
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    return (tp * data['Volume']).cumsum() / data['Volume'].cumsum()

def check_vwap_breakouts(data):
    results = []
    for ticker in data.columns.levels[1] if isinstance(data.columns, pd.MultiIndex) else [data.columns[0]]:
        ticker_data = data.xs(ticker, axis=1, level=1) if isinstance(data.columns, pd.MultiIndex) else data
        vwap = calculate_vwap(ticker_data)
        
        last_3_days = ticker_data.tail(3)
        latest_close = last_3_days['Close'].iloc[-1]
        latest_vwap = vwap.iloc[-1]
        
        if (last_3_days['Close'].iloc[1:] > vwap.iloc[-2:]).any() and not (last_3_days['Close'].iloc[0] > vwap.iloc[-3]):
            results.append({
                "Ticker": ticker,
                "Closing Price": f"${latest_close:.2f}",
                "Latest VWAP": f"${latest_vwap:.2f}"
            })
    return results

st.title("Stock VWAP Breakout Checker")

tickers_input = st.text_area("Enter stock tickers (comma-separated)", "AAPL,MSFT,GOOGL,AMZN,FB,TSLA,NVDA,JPM,V,JNJ")
tickers = [ticker.strip() for ticker in tickers_input.split(',')]

BATCH_SIZE = 100

if st.button("Check VWAP Breakout"):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # Using 1 year of data
    
    results = []
    progress_bar = st.progress(0)
    
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i+BATCH_SIZE]
        data = fetch_stock_data(batch, start_date, end_date)
        
        if data is not None:
            batch_results = check_vwap_breakouts(data)
            results.extend(batch_results)
        
        progress_bar.progress((i + len(batch)) / len(tickers))
    
    if results:
        st.subheader("Stocks that passed VWAP in the last 2 days")
        df_results = pd.DataFrame(results)
        st.table(df_results)
    else:
        st.info("No stocks passed their VWAP in the last 2 days")


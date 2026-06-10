import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=60)
def get_realtime_price(ticker: str):
    """
    Fetch realtime price using yfinance.
    Ticker should be without .JK, we will append it.
    """
    try:
        ticker_symbol = ticker.upper()
        if not ticker_symbol.endswith('.JK'):
            ticker_symbol = f"{ticker_symbol}.JK"
            
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="1d")
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[-1]
        
        # Calculate change and percent change relative to previous close if available
        # yfinance history for 1d might not have previous close easily accessible without fetching more data
        # So we fetch 5d to calculate accurate daily change
        hist_5d = stock.history(period="5d")
        if len(hist_5d) > 1:
            prev_close = hist_5d['Close'].iloc[-2]
            change = current_price - prev_close
            pct_change = (change / prev_close) * 100
        else:
            change = current_price - open_price
            pct_change = (change / open_price) * 100 if open_price > 0 else 0

        return {
            "price": current_price,
            "open": open_price,
            "high": hist['High'].iloc[-1],
            "low": hist['Low'].iloc[-1],
            "volume": hist['Volume'].iloc[-1],
            "change": change,
            "pct_change": pct_change
        }
    except Exception as e:
        return None

import streamlit as st
import yfinance as yf
import pandas as pd
from utils.db import query_db
from utils.styles import apply_custom_css

st.set_page_config(page_title="Fundamental Analysis", page_icon="📑", layout="wide")
apply_custom_css()

st.title("📑 Fundamental Analysis")

# Ambil daftar saham dari database
query = """
SELECT code, name 
FROM stock_summary 
WHERE date = (SELECT MAX(date) FROM stock_summary)
ORDER BY code ASC
"""
df_stocks = query_db(query)

with st.container():
    st.markdown("### 🔍 Pencarian Saham")
    if not df_stocks.empty:
        options = df_stocks.apply(lambda x: f"{x['code']} - {x['name']}", axis=1).tolist()
        default_index = next((i for i, opt in enumerate(options) if opt.startswith("BBCA")), 0)
        selected_option = st.selectbox("Ketik atau Pilih Kode Saham", options, index=default_index)
        ticker = selected_option.split(" - ")[0]
    else:
        ticker = st.text_input("Masukkan Kode Saham (Contoh: BBCA)", value="BBCA").upper()

st.markdown("<hr>", unsafe_allow_html=True)

if ticker:
    st.subheader(f"Valuasi & Fundamental: {ticker}")
    ticker_symbol = f"{ticker}.JK" if not ticker.endswith('.JK') else ticker
    
    with st.spinner("Memuat data fundamental premium..."):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            if 'regularMarketPrice' not in info and 'previousClose' not in info and 'marketCap' not in info:
                st.warning("Data fundamental tidak tersedia atau gagal dimuat dari yfinance.")
            else:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Market Cap", f"Rp {info.get('marketCap', 0)/1e12:,.2f} T")
                    st.metric("PE Ratio (TTM)", f"{info.get('trailingPE', 'N/A')}")
                
                with col2:
                    st.metric("PB Ratio", f"{info.get('priceToBook', 'N/A')}")
                    st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A")
                    
                with col3:
                    st.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/A")
                    st.metric("ROA", f"{info.get('returnOnAssets', 0)*100:.2f}%" if info.get('returnOnAssets') else "N/A")
                    
                with col4:
                    st.metric("Debt to Equity", f"{info.get('debtToEquity', 'N/A')}")
                    st.metric("EPS (TTM)", f"Rp {info.get('trailingEps', 'N/A')}")
            
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.subheader("Laporan Keuangan (Annual Financial Statements)")
                
                tab1, tab2, tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
                
                with tab1:
                    inc = stock.financials
                    if not inc.empty:
                        st.dataframe(inc, use_container_width=True)
                    else:
                        st.info("Data Income Statement tidak tersedia")
                        
                with tab2:
                    bs = stock.balance_sheet
                    if not bs.empty:
                        st.dataframe(bs, use_container_width=True)
                    else:
                        st.info("Data Balance Sheet tidak tersedia")
                        
                with tab3:
                    cf = stock.cashflow
                    if not cf.empty:
                        st.dataframe(cf, use_container_width=True)
                    else:
                        st.info("Data Cash Flow tidak tersedia")
                        
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memuat data: {e}")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from utils.idx_helpers import get_realtime_price
from utils.db import query_db
from utils.styles import apply_custom_css

st.set_page_config(page_title="Realtime & Price", page_icon="📈", layout="wide")
apply_custom_css()

st.title("📈 Realtime Price & Chart")

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
    # --- Realtime Price ---
    st.subheader(f"Ringkasan Harga: {ticker}")
    price_data = get_realtime_price(ticker)
    
    if price_data:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Harga Terkini", f"Rp {price_data['price']:,.0f}", f"{price_data['change']:,.0f} ({price_data['pct_change']:.2f}%)")
        with col2:
            st.metric("Open", f"Rp {price_data['open']:,.0f}")
        with col3:
            st.metric("High / Low", f"Rp {price_data['high']:,.0f} / Rp {price_data['low']:,.0f}")
        with col4:
            st.metric("Volume (Shares)", f"{price_data['volume']:,.0f}")
    else:
        st.warning(f"Data realtime untuk {ticker} tidak ditemukan.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Historical Chart ---
    col_chart, col_period = st.columns([3, 1])
    with col_chart:
        st.subheader("Interactive Candlestick Chart")
    with col_period:
        period = st.selectbox("Periode Waktu", ["1mo", "3mo", "6mo", "1y", "5y"], index=2)
    
    with st.spinner("Memuat grafik premium..."):
        try:
            ticker_symbol = f"{ticker}.JK" if not ticker.endswith('.JK') else ticker
            stock = yf.Ticker(ticker_symbol)
            hist = stock.history(period=period)
            
            if not hist.empty:
                fig = go.Figure(data=[go.Candlestick(x=hist.index,
                                open=hist['Open'],
                                high=hist['High'],
                                low=hist['Low'],
                                close=hist['Close'],
                                name=ticker)])
                
                fig.update_layout(
                    xaxis_title="Tanggal",
                    yaxis_title="Harga (Rp)",
                    template="plotly_dark",
                    height=600,
                    margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data historis tidak tersedia untuk periode ini.")
        except Exception as e:
            st.error(f"Gagal memuat grafik: {e}")

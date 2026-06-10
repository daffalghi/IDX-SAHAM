import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import query_db
from utils.styles import apply_custom_css
from utils.formatters import format_date, format_number, format_currency

st.set_page_config(page_title="Foreign Flow", page_icon="💸", layout="wide")
apply_custom_css()

st.title("💸 Foreign Flow Analysis")

st.markdown("""
Pantau akumulasi atau distribusi dana dari investor asing (Foreign Flow) di Bursa Efek Indonesia.
""")

query_dates = "SELECT DISTINCT date FROM stock_summary ORDER BY date DESC LIMIT 30"
dates_df = query_db(query_dates)

if dates_df.empty:
    st.warning("Data belum tersedia. Silakan jalankan sinkronisasi data IDX-API.")
else:
    dates_raw = dates_df['date'].tolist()
    date_options = {raw: format_date(raw) for raw in dates_raw}
    
    with st.container():
        st.markdown("### 📅 Market-Wide Foreign Flow")
        selected_raw_date = st.selectbox("Pilih Tanggal Transaksi", dates_raw, format_func=lambda x: date_options[x])
        
        query = "SELECT code, name, foreign_buy, foreign_sell, foreign_net FROM stock_summary WHERE date = ? ORDER BY foreign_net DESC"
        df = query_db(query, [selected_raw_date])
        
        if not df.empty:
            col1, col2 = st.columns(2)
            
            df['foreign_net'] = pd.to_numeric(df['foreign_net'], errors='coerce').fillna(0)
            df = df.sort_values(by='foreign_net', ascending=False)
            
            top_foreign_buy = df.head(10).copy()
            top_foreign_sell = df.tail(10).sort_values(by='foreign_net', ascending=True).copy()
            
            with col1:
                st.markdown("**Top 10 Net Foreign Buy (Volume)**")
                fig1 = px.bar(top_foreign_buy, x='code', y='foreign_net', hover_data=['name'], color_discrete_sequence=['#10b981'])
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=0, l=0, r=0))
                st.plotly_chart(fig1, use_container_width=True)
                
            with col2:
                st.markdown("**Top 10 Net Foreign Sell (Volume)**")
                fig2 = px.bar(top_foreign_sell, x='code', y='foreign_net', hover_data=['name'], color_discrete_sequence=['#ef4444'])
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=0, l=0, r=0))
                st.plotly_chart(fig2, use_container_width=True)
                
    st.markdown("<hr>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("### 🔎 Analisis Spesifik Saham")
        
        options = df.apply(lambda x: f"{x['code']} - {x['name']}", axis=1).tolist()
        default_index = next((i for i, opt in enumerate(options) if opt.startswith("BBCA")), 0)
        selected_option = st.selectbox("Ketik atau Pilih Kode Saham", options, index=default_index)
        ticker = selected_option.split(" - ")[0]
        
        if ticker:
            query_stock = "SELECT date, foreign_buy, foreign_sell, foreign_net FROM stock_summary WHERE code = ? ORDER BY date ASC"
            df_stock = query_db(query_stock, [ticker])
            
            if not df_stock.empty:
                df_stock['foreign_net'] = pd.to_numeric(df_stock['foreign_net'], errors='coerce').fillna(0)
                df_stock['date_str'] = df_stock['date'].apply(format_date)
                df_stock['cumulative_net'] = df_stock['foreign_net'].cumsum()
                
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(x=df_stock['date_str'], y=df_stock['foreign_net'], name='Daily Net', marker_color='#3b82f6'))
                fig3.add_trace(go.Scatter(x=df_stock['date_str'], y=df_stock['cumulative_net'], mode='lines', name='Cumulative Net', yaxis='y2', line=dict(color='#f59e0b', width=3)))
                
                fig3.update_layout(
                    title=f"Net Foreign Flow: {ticker}",
                    xaxis_title="Tanggal",
                    yaxis_title="Volume Net Harian",
                    yaxis2=dict(
                        title="Cumulative Volume",
                        overlaying='y',
                        side='right'
                    ),
                    template="plotly_dark",
                    height=500,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info(f"Tidak ada data Foreign Flow historis untuk saham {ticker}.")

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import query_db
from utils.styles import apply_custom_css
from utils.formatters import format_date, format_currency, format_number

st.set_page_config(page_title="Broker Analysis", page_icon="🏢", layout="wide")
apply_custom_css()

st.title("🏢 Broker Analysis (Market Wide)")

st.markdown("""
Halaman ini menampilkan ringkasan total aktivitas transaksi broker secara keseluruhan di Bursa Efek Indonesia berdasarkan data harian dari **IDX-API**.
""")

query = "SELECT DISTINCT date FROM broker_summary ORDER BY date DESC"
dates_df = query_db(query)

if dates_df.empty:
    st.warning("Belum ada data Broker Summary. Silakan jalankan sinkronisasi data.")
else:
    dates_raw = dates_df['date'].tolist()
    date_options = {raw: format_date(raw) for raw in dates_raw}
    
    with st.container():
        st.markdown("### 📅 Pilih Tanggal Transaksi")
        selected_raw_date = st.selectbox("Pilih Tanggal", dates_raw, format_func=lambda x: date_options[x])
        
    query = "SELECT broker_code, broker_name, total_value, volume, frequency FROM broker_summary WHERE date = ?"
    params = [selected_raw_date]
        
    df = query_db(query, params)
    
    if df.empty:
        st.info("Tidak ada data untuk tanggal tersebut.")
    else:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader(f"Top Broker Activity - {date_options[selected_raw_date]}")
        
        for col in ['total_value', 'volume', 'frequency']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        top_by_value = df.sort_values(by='total_value', ascending=False).head(20)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top 20 Broker (by Transaction Value)**")
            fig1 = px.bar(top_by_value, x='broker_code', y='total_value', hover_data=['broker_name'], color_discrete_sequence=['#3b82f6'])
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=0, l=0, r=0))
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            st.markdown("**Top 20 Broker (by Volume)**")
            top_by_volume = df.sort_values(by='volume', ascending=False).head(20)
            fig2 = px.bar(top_by_volume, x='broker_code', y='volume', hover_data=['broker_name'], color_discrete_sequence=['#f59e0b'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=0, l=0, r=0))
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("---")
        st.markdown("**Data Lengkap Transaksi**")
        
        # Display DataFrame with formatted values
        df_display = df.sort_values(by='total_value', ascending=False).copy()
        df_display['Value (Rp)'] = df_display['total_value'].apply(format_currency)
        df_display['Volume'] = df_display['volume'].apply(format_number)
        
        st.dataframe(df_display[['broker_code', 'broker_name', 'Value (Rp)', 'Volume', 'frequency']], use_container_width=True)

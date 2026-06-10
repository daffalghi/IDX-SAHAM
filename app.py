import streamlit as st
from utils.styles import apply_custom_css

st.set_page_config(
    page_title="IDX Stock AI Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()

st.title("📈 IDX Stock AI Agent")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ### Selamat datang di Platform Analisis Saham Modern!
    Aplikasi ini dirancang dengan antarmuka premium untuk memberikan pengalaman terbaik bagi trader retail di Bursa Efek Indonesia (IDX).
    
    #### 🚀 Fitur Unggulan
    - **Realtime Price & Chart**: Pantau pergerakan harga saham secara terkini dengan candlestick interaktif.
    - **Fundamental Analysis**: Analisis rasio keuangan dan ringkasan laporan keuangan secara mendalam.
    - **Broker Analysis**: Lacak aktivitas broker dan broker summary (Market Wide).
    - **Foreign Flow**: Pantau aliran dana asing untuk melihat akumulasi institusi asing.
    - **AI Recommendation & Signals**: Engine cerdas perpaduan teknikal dan fundamental yang menghasilkan sinyal *Buy/Sell/Hold* otomatis ke Telegram Anda.
    """)

with col2:
    st.info("💡 **Tips Penggunaan**\nGunakan navigasi di sebelah kiri (Sidebar) untuk berpindah antar fitur analisis.")
    st.success("🤖 **AI Signals Active**\nPastikan Anda telah mengatur konfigurasi Telegram di file `.env` untuk menerima push notifications.")

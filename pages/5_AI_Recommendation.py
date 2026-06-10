import streamlit as st
import pandas as pd
from utils.ai_signals import get_stock_recommendation
from utils.telegram_bot import send_telegram_message
from utils.db import query_db
from utils.styles import apply_custom_css

st.set_page_config(page_title="AI Stock Recommendation", page_icon="🤖", layout="wide")
apply_custom_css()

st.title("🤖 AI Stock Recommendation & Signals")

st.markdown("""
Sistem ini menggunakan kombinasi **Analisis Teknikal (RSI, MACD, EMA)** dan **Fundamental Dasar (P/E, PBV)** untuk menghasilkan sinyal *Buy/Hold/Sell* otomatis beserta strategi *trading*.
""")
st.markdown("<br>", unsafe_allow_html=True)

# Mengambil seluruh data saham beserta harga penutupan terakhir dari DB
query = """
SELECT code, name, close 
FROM stock_summary 
WHERE date = (SELECT MAX(date) FROM stock_summary)
ORDER BY code ASC
"""
df_stocks = query_db(query)

if df_stocks.empty:
    st.warning("Data saham tidak tersedia di database. Pastikan Anda telah menjalankan sinkronisasi awal IDX-API.")
else:
    with st.container():
        st.markdown("### ⚙️ Filter & Pemilihan Saham")
        
        # --- 1. Filter Berdasarkan Harga (Number Inputs) ---
        col1, col2 = st.columns(2)
        min_price_db = int(df_stocks['close'].min())
        max_price_db = int(df_stocks['close'].max())
        
        with col1:
            min_price = st.number_input("Harga Minimum (Rp)", min_value=min_price_db, max_value=max_price_db, value=min_price_db, step=50)
        with col2:
            max_price = st.number_input("Harga Maksimum (Rp)", min_value=min_price_db, max_value=max_price_db, value=max_price_db, step=50)
        
        # Terapkan filter harga ke DataFrame
        filtered_df = df_stocks[(df_stocks['close'] >= min_price) & (df_stocks['close'] <= max_price)]
        st.caption(f"✨ Ditemukan **{len(filtered_df)}** saham dalam rentang harga ini.")
        
        # --- 2. Multiselect Saham ---
        options = filtered_df.apply(lambda x: f"{x['code']} - {x['name']} (Rp {x['close']:,.0f})", axis=1).tolist()
        
        lq45_samples = ["BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "GOTO"]
        default_selections = [opt for opt in options if any(opt.startswith(t) for t in lq45_samples)]
        
        st.markdown("<br>", unsafe_allow_html=True)
        selected_options = st.multiselect(
            "Pilih Saham untuk Dianalisis (Bisa lebih dari 1):",
            options=options,
            default=default_selections
        )
        
        tickers = [opt.split(" - ")[0] for opt in selected_options]
        
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_clicked = st.button("🚀 Generate Rekomendasi & Sinyal AI")

    if analyze_clicked:
        if not tickers:
            st.warning("Silakan pilih minimal 1 saham terlebih dahulu.")
        else:
            with st.spinner(f"Menganalisis {len(tickers)} saham dengan AI Engine..."):
                results = []
                for ticker in tickers:
                    res = get_stock_recommendation(ticker)
                    if res:
                        results.append(res)
                
                if results:
                    st.session_state['ai_results'] = results
                    st.success("Analisis berhasil diselesaikan!")
                else:
                    st.error("Gagal mendapatkan data teknikal dari yfinance.")

    # Tampilkan Hasil Analisis
    if 'ai_results' in st.session_state:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 📊 Hasil Analisis AI")
        results = st.session_state['ai_results']
        
        for res in results:
            signal_color = "🟢" if "Buy" in res['signal'] else ("🔴" if "Sell" in res['signal'] else "🟡")
            
            with st.expander(f"{signal_color} {res['ticker']} - {res['signal']} (Score: {res['score']})", expanded=True):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("Harga Terkini", f"Rp {res['close']:,.0f}")
                    st.markdown(f"**RSI (14)**: {res['rsi']:.2f}<br>**MACD Trend**: {res['macd']}<br>**P/E Ratio**: {res['pe']}<br>**PBV**: {res['pbv']}", unsafe_allow_html=True)
                    
                with c2:
                    st.markdown("#### 💡 Strategi Trading Direkomendasikan")
                    st.info(res['strategy'])
                    
        st.markdown("---")
        st.subheader("📲 Notifikasi Telegram")
        if st.button("Kirim Sinyal Rekomendasi ke Telegram"):
            with st.spinner("Mengirim pesan ke Telegram..."):
                msg = "🤖 *IDX Stock AI Agent - Rekomendasi Hari Ini*\n\n"
                for res in results:
                    msg += f"*{res['ticker']}* - {res['signal']}\n"
                    msg += f"Harga: Rp {res['close']:,.0f} | RSI: {res['rsi']:.2f}\n"
                    msg += f"Strategi: {res['strategy']}\n\n"
                
                success, info = send_telegram_message(msg)
                if success:
                    st.success(info)
                else:
                    st.error(info)
                    
    # --- Tambahan: Manual Trigger Market-Wide Auto Scanner dari Website ---
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🌐 Market-Wide Auto Scanner")
    st.markdown("Pindai 50 saham paling aktif di bursa secara massal dan temukan yang memiliki sinyal Buy terbaik, lalu kirim rekomendasinya otomatis ke Telegram Anda.")
    
    if st.button("⚡ Jalankan Auto-Scanner Keseluruhan Pasar (Kirim ke Telegram)"):
        with st.spinner("Memindai puluhan saham teraktif... Mohon tunggu beberapa saat."):
            from auto_scanner import run_auto_scan
            import sys
            import io
            
            # Alihkan output print dari run_auto_scan agar tidak tumpah di console saja
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout
            
            try:
                run_auto_scan()
                output = new_stdout.getvalue()
                st.success("Auto-Scan selesai! Silakan cek Telegram Anda untuk melihat hasilnya (jika ada sinyal Buy).")
                with st.expander("Lihat Log Pemindaian"):
                    st.code(output)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memindai: {e}")
            finally:
                sys.stdout = old_stdout

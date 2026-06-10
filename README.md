# IDX Stock AI Agent

Web application sederhana untuk analisis saham Bursa Efek Indonesia (IDX) yang dibangun menggunakan Streamlit, yfinance, dan terintegrasi dengan IDX-API lokal.

## Fitur Utama
1. **Realtime Price & Chart**: Data harga harian beserta candlestick chart interaktif.
2. **Fundamental Analysis**: Analisis rasio keuangan, valuasi, dan ringkasan laporan keuangan.
3. **Broker Analysis**: Ringkasan aktivitas broker (Top Net Buyers & Sellers).
4. **Foreign Flow**: Analisis aliran dana asing (Net Foreign Buy/Sell harian dan kumulatif).

## Instalasi & Cara Menjalankan

1. Pastikan Anda memiliki **Python 3.10+** dan **Deno** terinstall.
2. Clone repository ini.
3. Setup Python Virtual Environment:
   ```bash
   python -m venv venv
   # Untuk Windows:
   venv\Scripts\activate
   # Untuk Mac/Linux:
   source venv/bin/activate
   ```
4. Install dependencies Python:
   ```bash
   pip install -r requirements.txt
   ```
5. Inisialisasi Database dan Sync Data Awal (Deno):
   ```bash
   cd IDX-API
   deno task db:sync
   deno run -A sync_init.ts
   cd ..
   ```
6. Jalankan aplikasi Streamlit:
   ```bash
   streamlit run app.py
   ```
7. Buka browser pada alamat `http://localhost:8501`.

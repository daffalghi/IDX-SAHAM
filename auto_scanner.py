import os
import sqlite3
import pandas as pd
from utils.ai_signals import get_stock_recommendation
from utils.telegram_bot import send_telegram_message
from dotenv import load_dotenv

# Load environment variables untuk memastikan token Telegram terbaca
load_dotenv()

def run_auto_scan():
    print("Memulai proses Auto-Scan Saham menggunakan AI...")
    
    try:
        print("Sinkronisasi database terbaru dari IDX-API...")
        import subprocess
        subprocess.run(["deno", "run", "-A", "sync_init.ts"], cwd="IDX-API", check=True)
        print("Sinkronisasi database berhasil!")
        
        # Menghubungkan ke database lokal IDX-API
        conn = sqlite3.connect('IDX-API/data/database.sqlite')
        
        # Mengambil 50 saham paling likuid (berdasarkan volume tertinggi) di hari terakhir perdagangan
        query = """
        SELECT code, name, close 
        FROM stock_summary 
        WHERE date = (SELECT MAX(date) FROM stock_summary)
        ORDER BY volume DESC
        LIMIT 50
        """
        df_stocks = pd.read_sql_query(query, conn)
        conn.close()
    except Exception as e:
        print(f"Error saat mengakses database: {e}")
        return

    if df_stocks.empty:
        print("Tidak ada data saham yang ditemukan di database.")
        return
        
    print(f"Menganalisis {len(df_stocks)} saham paling aktif...")
    
    buy_signals = []
    
    for index, row in df_stocks.iterrows():
        ticker = row['code']
        # Panggil AI engine untuk mendapatkan sinyal teknikal & fundamental
        res = get_stock_recommendation(ticker)
        
        if res:
            # Hanya filter yang memiliki sinyal "Strong Buy" atau "Buy"
            if "Buy" in res['signal']:
                buy_signals.append(res)
                print(f"[+] {ticker} | Signal: {res['signal']} (Score: {res['score']})")
            else:
                print(f"[-] {ticker} | Diabaikan ({res['signal']})")
        else:
            print(f"[!] {ticker} | Gagal mendapatkan data teknikal.")
            
    # Jika ditemukan saham dengan sinyal Buy
    if buy_signals:
        print("\nMenyusun pesan untuk Telegram...")
        # Urutkan berdasarkan score indikator teknikal/fundamental tertinggi
        buy_signals.sort(key=lambda x: x['score'], reverse=True)
        
        # Batasi hanya Top 5 saham terbaik agar pesan tidak terlalu panjang
        top_recommendations = buy_signals[:5]
        
        msg = "🤖 *AUTO SCAN: REKOMENDASI SAHAM HARI INI*\n"
        msg += f"Dari 50 saham teraktif, berikut adalah {len(top_recommendations)} saham dengan momentum terbaik:\n\n"
        
        for res in top_recommendations:
            signal_emoji = "🔥" if res['signal'] == "Strong Buy" else "🟢"
            msg += f"*{res['ticker']}* {signal_emoji} *{res['signal']}*\n"
            msg += f"💰 Harga: Rp {res['close']:,.0f}\n"
            msg += f"📊 RSI: {res['rsi']:.2f} | MACD: {res['macd']}\n"
            msg += f"💡 *Strategi*: {res['strategy']}\n\n"
            
        success, info = send_telegram_message(msg)
        if success:
            print("[SUCCESS] Berhasil mengirim notifikasi rekomendasi saham ke Telegram!")
        else:
            print(f"[ERROR] Gagal mengirim pesan ke Telegram: {info}")
    else:
        print("Tidak ada saham dengan sinyal Buy yang cukup kuat hari ini.")
        msg = "🤖 *AUTO SCAN: REKOMENDASI SAHAM HARI INI*\n\n"
        msg += "Hari ini *TIDAK ADA* saham yang lolos filter ketat algoritma 100-Poin (Level Institusi) kita.\n\n"
        msg += "Kondisi pasar saat ini kemungkinan sedang tidak kondusif (sideways/downtrend) atau saham-saham likuid sedang berada di area risiko tinggi (Overbought/Dekat Resistance). Lebih baik bersabar (Wait & See) untuk melindungi modal Anda hari ini. 🛡️"
        
        success, info = send_telegram_message(msg)
        if success:
            print("[SUCCESS] Berhasil mengirim notifikasi perlindungan modal ke Telegram!")
        else:
            print(f"[ERROR] Gagal mengirim pesan ke Telegram: {info}")
        
import schedule
import time

def job():
    run_auto_scan()

if __name__ == "__main__":
    print("[INFO] Menjalankan AI Auto-Scanner di Background...")
    print("Sinyal akan dianalisis dan dikirim otomatis setiap Senin - Jumat pukul 16:30 WIB (Setelah bursa tutup).")
    print("Biarkan terminal ini tetap terbuka.")
    
    # Jadwalkan eksekusi setiap hari kerja jam 16:30
    schedule.every().monday.at("16:30").do(job)
    schedule.every().tuesday.at("16:30").do(job)
    schedule.every().wednesday.at("16:30").do(job)
    schedule.every().thursday.at("16:30").do(job)
    schedule.every().friday.at("16:30").do(job)
    
    # Loop tak terbatas untuk menjaga script tetap hidup
    while True:
        schedule.run_pending()
        time.sleep(60) # Cek jadwal setiap 1 menit

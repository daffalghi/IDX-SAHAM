import os
import sqlite3
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.ai_signals import get_stock_recommendation
from utils.telegram_bot import send_telegram_message
from dotenv import load_dotenv

# Load environment variables untuk memastikan token Telegram terbaca
load_dotenv()

WIB = timezone(timedelta(hours=7))

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
        
    total = len(df_stocks)
    print(f"Menganalisis {total} saham paling aktif secara paralel...")
    
    scan_time = datetime.now(WIB).strftime("%H:%M WIB")
    tickers = df_stocks['code'].tolist()
    buy_signals = []
    
    # ── Scan paralel: hemat 60-70% waktu dibanding loop serial ──
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(get_stock_recommendation, ticker): ticker
                   for ticker in tickers}
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                res = future.result()
                if res:
                    if "Buy" in res['signal']:
                        buy_signals.append(res)
                        print(f"[+] {ticker} | Signal: {res['signal']} (Score: {res['score']})")
                    else:
                        print(f"[-] {ticker} | Diabaikan ({res['signal']})")
                else:
                    print(f"[!] {ticker} | Gagal mendapatkan data teknikal.")
            except Exception as e:
                print(f"[!] {ticker} | Exception: {e}")
            
    # Jika ditemukan saham dengan sinyal Buy
    if buy_signals:
        print("\nMenyusun pesan untuk Telegram...")
        # Urutkan berdasarkan score indikator teknikal/fundamental tertinggi
        buy_signals.sort(key=lambda x: x['score'], reverse=True)
        
        # Batasi hanya Top 5 saham terbaik agar pesan tidak terlalu panjang
        top_recommendations = buy_signals[:5]
        
        separator = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        msg  = f"🤖 *AUTO SCAN — IDX TOP PICKS*\n"
        msg += f"🕐 Waktu Analisis: {scan_time}\n"
        msg += f"📋 {len(top_recommendations)} dari {total} saham lolos filter ketat\n\n"
        
        for i, res in enumerate(top_recommendations, 1):
            signal_emoji = "🔥" if res['signal'] == "Strong Buy" else "🟢"
            msg += f"{separator}\n"
            msg += f"{signal_emoji} *[{i}] {res['ticker']}* — *{res['signal']}*  `{res['score']}/100`\n\n"
            msg += f"💰 Harga Tutup  : Rp {res['close']:>10,.0f}\n"
            msg += f"📊 RSI: {res['rsi']:.1f}  |  MACD: {res['macd']}\n"
            msg += f"📰 Sentimen     : {res.get('news', 'Netral')}\n\n"
            # ── Level Harga Kunci ──
            msg += f"🎯 *Entry Zone*   : Rp {res['close']:,.0f} – {int(res['close'] * 1.005):,}\n"
            msg += f"✅ *TP1* (Konservatif): Rp {res['tp1']:,}  _(+{res['tp1_pct']}%)_\n"
            msg += f"🚀 *TP2* (Agresif)   : Rp {res['tp2']:,}  _(+{res['tp2_pct']}%)_\n"
            msg += f"🛑 *Stop Loss*       : Rp {res['sl']:,}   _(-{res['sl_pct']}%)_\n"
            msg += f"⚖️ *Risk/Reward*     : 1 : {res['rr']}\n\n"
            msg += f"💡 _{res['strategy'].split(chr(10))[0]}_\n\n"
            
        msg += separator
        msg += "\n⚠️ _Bukan rekomendasi finansial. DYOR & kelola risiko Anda sendiri._"
            
        success, info = send_telegram_message(msg)
        if success:
            print("[SUCCESS] Berhasil mengirim notifikasi rekomendasi saham ke Telegram!")
        else:
            print(f"[ERROR] Gagal mengirim pesan ke Telegram: {info}")
    else:
        print("Tidak ada saham dengan sinyal Buy yang cukup kuat hari ini.")
        msg  = f"🤖 *AUTO SCAN — IDX TOP PICKS*\n"
        msg += f"🕐 Waktu Analisis: {scan_time}\n\n"
        msg += "❌ Hari ini *TIDAK ADA* saham yang lolos filter ketat algoritma (Level Institusi).\n\n"
        msg += "Kondisi pasar saat ini kemungkinan sedang tidak kondusif (sideways/downtrend) atau saham-saham likuid sedang berada di area risiko tinggi. Lebih baik *Wait & See* untuk melindungi modal Anda hari ini. 🛡️"
        
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

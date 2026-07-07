import os
import schedule
import time
from utils.crypto_signals import get_crypto_recommendation
from utils.telegram_bot import send_telegram_message
from dotenv import load_dotenv

load_dotenv()

# Top 10 Liquid Coins to Scan on Binance USDT Futures
COINS_TO_SCAN = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", 
    "XRP/USDT", "DOGE/USDT", "ADA/USDT", "AVAX/USDT", 
    "LINK/USDT", "DOT/USDT"
]

def run_binance_scan():
    print("Memulai proses Auto-Scan Binance Futures...")
    
    signals = []
    
    for coin in COINS_TO_SCAN:
        print(f"Menganalisis {coin}...")
        res = get_crypto_recommendation(coin, timeframe="4h")
        if res:
            signals.append(res)
            print(f"[+] {coin} | Signal: {res['signal']}")
        else:
            print(f"[-] {coin} | Neutral / Skip")
            
    print("\nMenyusun pesan untuk Telegram...")
    
    if signals:
        msg = "🤖 *BINANCE FUTURES 4H SCANNER*\n\n"
        for res in signals:
            msg += f"*{res['ticker']}* {res['signal']}\n"
            msg += f"💰 Entry Harga: {res['close']:.4f}\n"
            msg += f"🎯 Target (TP): {res['target']}\n"
            msg += f"🛑 Stop Loss: {res['stop_loss']}\n"
            msg += f"💡 Aksi: *{res['action']}*\n\n"
            
        success, info = send_telegram_message(msg)
        if success:
            print("[SUCCESS] Berhasil mengirim notifikasi Binance Futures ke Telegram!")
        else:
            print(f"[ERROR] Gagal mengirim pesan ke Telegram: {info}")
    else:
        print("Tidak ada sinyal kripto saat ini.")
        # Optional: Send a heartbeat message to Telegram
        msg = "🤖 *BINANCE FUTURES 4H SCANNER*\n\nSaat ini tidak ada sinyal LONG/SHORT yang valid di Top 10 Coins. Wait & See. ☕"
        send_telegram_message(msg)

def job():
    run_binance_scan()

if __name__ == "__main__":
    print("[INFO] Menjalankan Binance Futures Auto-Scanner di Background...")
    print("Pemindaian akan dilakukan setiap 4 Jam.")
    
    # Jadwalkan eksekusi setiap 4 jam
    schedule.every(4).hours.do(job)
    
    # Langsung jalankan sekali saat script dinyalakan
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

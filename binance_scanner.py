import os
import schedule
import time
import ccxt
from utils.crypto_signals import get_crypto_recommendation
from utils.telegram_bot import send_telegram_message
from dotenv import load_dotenv

load_dotenv()

def run_binance_scan():
    print("Memulai proses Auto-Scan Binance (Spot & Futures All-Coins)...")
    
    # 1. Inisialisasi CCXT Spot & Futures
    try:
        spot_exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        futures_exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        
        print("Menarik daftar seluruh koin USDT dari Binance...")
        spot_markets = spot_exchange.load_markets()
        futures_markets = futures_exchange.load_markets()
        
        # Ambil semua simbol USDT yang aktif
        spot_symbols = [s for s in spot_markets if s.endswith('/USDT') and spot_markets[s]['active']]
        futures_symbols = [s for s in futures_markets if s.endswith('/USDT') and futures_markets[s]['active']]
        
        print(f"Ditemukan {len(spot_symbols)} koin Spot dan {len(futures_symbols)} koin Futures.")
        
    except Exception as e:
        print(f"Gagal terhubung ke Binance: {e}")
        return
        
    spot_signals = []
    futures_signals = []
    
    # 2. Pindai Koin Futures (Prioritas)
    print("\n[+] Memindai Pasar Futures...")
    for sym in futures_symbols:
        res = get_crypto_recommendation(futures_exchange, sym, market_type="future", timeframe="1h")
        if res:
            futures_signals.append(res)
            print(f"   -> [FUTURES] {sym}: {res['signal']} (Score: {res['score']})")
        time.sleep(0.1) # Hindari Rate Limit
            
    # 3. Pindai Koin Spot (Termasuk Micin)
    print("\n[+] Memindai Pasar Spot...")
    # Batasi spot max 300 koin teratas berdasarkan volume agar tidak terlalu lama (opsional)
    # Di sini kita scan semua untuk menangkap micin
    for sym in spot_symbols:
        res = get_crypto_recommendation(spot_exchange, sym, market_type="spot", timeframe="1h")
        if res:
            spot_signals.append(res)
            print(f"   -> [SPOT] {sym}: {res['signal']} (Score: {res['score']})")
        time.sleep(0.1) # Hindari Rate Limit
            
    print("\nMenyusun pesan untuk Telegram...")
    
    # Urutkan berdasarkan skor tertinggi (yang volumenya melonjak)
    spot_signals.sort(key=lambda x: x['score'], reverse=True)
    futures_signals.sort(key=lambda x: x['score'], reverse=True)
    
    # Ambil Top 5 untuk masing-masing agar tidak SPAM
    top_spot = spot_signals[:5]
    top_futures = futures_signals[:5]
    
    msg = "🤖 *BINANCE 1H ALL-COIN SCANNER*\n\n"
    
    if top_futures:
        msg += "📈 *TOP 5 FUTURES SIGNALS*\n"
        for res in top_futures:
            msg += f"*{res['ticker']}* {res['signal']}\n"
            msg += f"Entry: {res['close']:.6f} | TP: {res['target']} | SL: {res['stop_loss']}\n\n"
            
    if top_spot:
        msg += "💎 *TOP 5 SPOT (MICIN) SIGNALS*\n"
        for res in top_spot:
            msg += f"*{res['ticker']}* {res['signal']}\n"
            msg += f"Harga: {res['close']:.6f} | TP: {res['target']} | SL: {res['stop_loss']}\n\n"
            
    if not top_futures and not top_spot:
        msg += "Saat ini tidak ada koin (Spot maupun Futures) yang menembus filter momentum & volume. Wait & See. ☕"
        
    success, info = send_telegram_message(msg)
    if success:
        print("[SUCCESS] Berhasil mengirim notifikasi Binance ke Telegram!")
    else:
        print(f"[ERROR] Gagal mengirim pesan ke Telegram: {info}")

def job():
    run_binance_scan()

if __name__ == "__main__":
    import sys
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("[INFO] Berjalan di GitHub Actions. Mengeksekusi 1 kali pemindaian...")
        run_binance_scan()
        sys.exit(0)
        
    print("[INFO] Menjalankan Binance Scanner di Background (Local)...")
    schedule.every(1).hours.do(job)
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

import os
import time
import ccxt
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.crypto_signals import get_crypto_recommendation, get_btc_context
from utils.telegram_bot import send_telegram_message
from dotenv import load_dotenv

load_dotenv()

WIB = timezone(timedelta(hours=7))


def _scan_worker(exchange, sym, market_type, btc_context):
    """Worker function untuk ThreadPoolExecutor."""
    try:
        res = get_crypto_recommendation(
            exchange, sym,
            market_type=market_type,
            timeframe="1h",
            btc_context=btc_context
        )
        time.sleep(0.15)  # Jeda kecil per worker untuk hindari rate limit
        return res
    except Exception:
        return None


def run_binance_scan():
    print("Memulai proses Auto-Scan Binance (Spot & Futures All-Coins)...")

    # ── 1. Koneksi ke Exchange ────────────────────────────────────────────────
    try:
        exchange = ccxt.mexc({'enableRateLimit': True})

        print("Menarik daftar seluruh koin USDT dari MEXC...")
        markets = exchange.load_markets()

        spot_symbols    = [s for s in markets
                           if markets[s].get('spot') and s.endswith('/USDT')
                           and markets[s].get('active')]
        futures_symbols = [s for s in markets
                           if markets[s].get('swap') and s.endswith('/USDT:USDT')
                           and markets[s].get('active')]

        print(f"Ditemukan {len(spot_symbols)} koin Spot dan {len(futures_symbols)} koin Futures.")

    except Exception as e:
        err_msg = f"Gagal terhubung ke MEXC: {e}"
        print(err_msg)
        send_telegram_message(f"⚠️ *ERROR SISTEM Kripto:*\n\n{err_msg}")
        return

    scan_time = datetime.now(WIB).strftime("%H:%M WIB")

    # ── 2. Ambil BTC Context SEKALI (Barometer Pasar) ─────────────────────────
    print("\n[INFO] Mengambil konteks BTC sebagai barometer pasar...")
    btc_context = get_btc_context(exchange)
    if btc_context['strong']:
        btc_status = "🔥 Strong Bull"
    elif btc_context['bullish']:
        btc_status = "🟢 Bullish"
    else:
        btc_status = "🔴 Bearish"

    futures_signals = []
    spot_signals    = []

    # ── 3. Scan Futures secara Paralel ───────────────────────────────────────
    print(f"\n[+] Memindai {len(futures_symbols)} Futures secara paralel (max_workers=5)...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures_map = {
            executor.submit(_scan_worker, exchange, sym, "future", btc_context): sym
            for sym in futures_symbols
        }
        for future in as_completed(futures_map):
            sym = futures_map[future]
            try:
                res = future.result()
                if res:
                    futures_signals.append(res)
                    print(f"   -> [FUTURES] {sym}: {res['signal']} (Score: {res['score']})")
            except Exception:
                pass

    # ── 4. Scan Spot secara Paralel ──────────────────────────────────────────
    print(f"\n[+] Memindai {len(spot_symbols)} Spot secara paralel (max_workers=5)...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        spot_map = {
            executor.submit(_scan_worker, exchange, sym, "spot", btc_context): sym
            for sym in spot_symbols
        }
        for future in as_completed(spot_map):
            sym = spot_map[future]
            try:
                res = future.result()
                if res:
                    spot_signals.append(res)
                    print(f"   -> [SPOT] {sym}: {res['signal']} (Score: {res['score']})")
            except Exception:
                pass

    # ── 5. Sortir & Ambil Top 5 ──────────────────────────────────────────────
    print("\nMenyusun pesan untuk Telegram...")
    futures_signals.sort(key=lambda x: x['score'], reverse=True)
    spot_signals.sort(key=lambda x: x['score'], reverse=True)

    top_futures = futures_signals[:5]
    top_spot    = spot_signals[:5]

    # ── 6. Format Pesan Telegram ─────────────────────────────────────────────
    separator = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    msg  = f"🤖 *CRYPTO SCANNER — MEXC*\n"
    msg += f"🕐 Waktu: {scan_time}  |  TF: 1H\n"
    msg += f"₿ BTC Status: {btc_status}  |  RSI BTC: {btc_context['rsi']}\n\n"

    if top_futures:
        msg += f"📈 *TOP FUTURES* ({len(futures_signals)} lolos filter)\n\n"
        for i, res in enumerate(top_futures, 1):
            msg += f"{separator}\n"
            msg += f"{res['signal']} *[{i}] {res['ticker']}*  `{res['score']}/100`\n\n"
            msg += f"💰 Harga      : `{res['close']:.6f}` USDT\n"
            msg += f"📊 RSI: {res['rsi']}  |  MACD: {res['macd']}  |  ADX: {res['adx']}\n"
            msg += f"📦 Volume     : {res['vol_ratio']}× avg {'✅ SURGE' if res['volume_surge'] else '—'}\n"
            msg += f"💸 Funding    : {res['funding_rate']}\n\n"
            msg += f"🎯 *Entry*    : `{res['close']:.6f}`\n"
            msg += f"✅ *TP1*       : `{res['tp1']:.6f}`  _(+{res['tp1_pct']}%)_\n"
            msg += f"🚀 *TP2*       : `{res['tp2']:.6f}`  _(+{res['tp2_pct']}%)_\n"
            msg += f"🛑 *Stop Loss* : `{res['sl']:.6f}`   _(-{res['sl_pct']}%)_\n"
            msg += f"⚖️ *R:R*       : 1 : {res['rr']}\n"
            msg += f"⚙️ {res['margin_mode']}  |  🎚 {res['leverage']}\n\n"

    if top_spot:
        msg += f"\n💎 *TOP SPOT* ({len(spot_signals)} lolos filter)\n\n"
        for i, res in enumerate(top_spot, 1):
            msg += f"{separator}\n"
            msg += f"{res['signal']} *[{i}] {res['ticker']}*  `{res['score']}/100`\n\n"
            msg += f"💰 Harga      : `{res['close']:.6f}` USDT\n"
            msg += f"📊 RSI: {res['rsi']}  |  MACD: {res['macd']}  |  ADX: {res['adx']}\n"
            msg += f"📦 Volume     : {res['vol_ratio']}× avg {'✅ SURGE' if res['volume_surge'] else '—'}\n\n"
            msg += f"✅ *TP1*       : `{res['tp1']:.6f}`  _(+{res['tp1_pct']}%)_\n"
            msg += f"🚀 *TP2*       : `{res['tp2']:.6f}`  _(+{res['tp2_pct']}%)_\n"
            msg += f"🛑 *Stop Loss* : `{res['sl']:.6f}`   _(-{res['sl_pct']}%)_\n"
            msg += f"⚖️ *R:R*       : 1 : {res['rr']}\n\n"

    if not top_futures and not top_spot:
        msg += "Saat ini tidak ada koin (Spot maupun Futures) yang menembus filter momentum & volume. Wait & See. ☕"

    msg += separator
    msg += "\n⚠️ _Bukan rekomendasi finansial. DYOR & kelola risiko Anda sendiri._"

    success, info = send_telegram_message(msg)
    if success:
        print("[SUCCESS] Berhasil mengirim notifikasi Crypto ke Telegram!")
    else:
        print(f"[ERROR] Gagal mengirim pesan ke Telegram: {info}")


def job():
    run_binance_scan()


if __name__ == "__main__":
    import sys
    import schedule

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


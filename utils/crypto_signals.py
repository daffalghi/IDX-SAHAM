import math
import pandas as pd
import pandas_ta as ta


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: NaN-safe float extractor
# ─────────────────────────────────────────────────────────────────────────────

def _safe(val, fallback):
    """Return float(val) jika valid, else fallback."""
    try:
        v = float(val)
        return fallback if math.isnan(v) or math.isinf(v) else v
    except Exception:
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: BTC Context  (diambil sekali sebelum loop scan)
# ─────────────────────────────────────────────────────────────────────────────

def get_btc_context(exchange):
    """
    Ambil kondisi BTC sebagai barometer pasar kripto.
    Hasilnya di-pass ke get_crypto_recommendation() agar tidak refetch.
    """
    try:
        try:
            ohlcv = exchange.fetch_ohlcv('BTC/USDT:USDT', '1h', limit=60)
        except Exception:
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=60)

        if not ohlcv or len(ohlcv) < 50:
            raise ValueError("Data BTC tidak cukup")

        df    = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        close = float(df['close'].iloc[-1])
        ema50 = _safe(ta.ema(df['close'], length=50).iloc[-1], close)
        ema21 = _safe(ta.ema(df['close'], length=21).iloc[-1], close)
        rsi   = _safe(ta.rsi(df['close'], length=14).iloc[-1], 50.0)

        btc_bullish = close > ema50
        btc_strong  = close > ema50 and ema21 > ema50

        status = '🔥 Strong Bull' if btc_strong else ('🟢 Bullish' if btc_bullish else '🔴 Bearish')
        print(f"[BTC] Close: {close:.2f} | EMA50: {ema50:.2f} | RSI: {rsi:.1f} | {status}")

        return {
            'bullish': btc_bullish,
            'strong':  btc_strong,
            'rsi':     round(rsi, 1),
            'close':   close,
        }
    except Exception as e:
        print(f"[WARN] Gagal ambil BTC context: {e} — default Netral.")
        return {'bullish': True, 'strong': False, 'rsi': 50.0, 'close': 0}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Funding Rate  (khusus futures)
# ─────────────────────────────────────────────────────────────────────────────

def get_funding_rate(exchange, symbol):
    try:
        data = exchange.fetch_funding_rate(symbol)
        return data.get('fundingRate') if data else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def get_crypto_recommendation(exchange, symbol: str, market_type: str = "future",
                               timeframe: str = "1h", btc_context: dict = None):
    """
    Analisis koin dengan deteksi binary yang terbukti bekerja + output kaya.

    Syarat LONG  : (close > EMA21 ATAU EMA9 > EMA21) DAN MACD bullish DAN RSI > 40
    Syarat SHORT : (close < EMA21 ATAU EMA9 < EMA21) DAN MACD bearish DAN RSI < 60
    Spot         : tambah wajib volume surge (1.5×)

    Skor mulai 60 (base). Semua kondisi tambahan hanya BONUS — tidak ada penalti.
    """
    try:
        # ── Data ─────────────────────────────────────────────────────────────
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        if not ohlcv or len(ohlcv) < 50:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # ── Indikator ────────────────────────────────────────────────────────
        df['EMA_9']  = ta.ema(df['close'], length=9)
        df['EMA_21'] = ta.ema(df['close'], length=21)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        df['RSI']    = ta.rsi(df['close'], length=14)
        df['ATR']    = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['OBV']    = ta.obv(df['close'], df['volume'])

        macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            df = pd.concat([df, macd_df], axis=1)

        stoch_df = ta.stoch(df['high'], df['low'], df['close'])
        if stoch_df is not None and not stoch_df.empty:
            df = pd.concat([df, stoch_df], axis=1)

        adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx_df is not None and not adx_df.empty:
            df = pd.concat([df, adx_df], axis=1)

        # ── Ekstrak nilai terakhir (NaN-safe) ────────────────────────────────
        last = df.iloc[-1]

        close   = float(last['close'])
        open_c  = float(last['open'])
        ema9    = _safe(last.get('EMA_9'),  close)
        ema21   = _safe(last.get('EMA_21'), close)
        ema50   = _safe(last.get('EMA_50'), close)
        rsi     = _safe(last.get('RSI'),    50.0)
        atr     = _safe(last.get('ATRr_14'), close * 0.02)
        macd_l  = _safe(last.get('MACD_12_26_9'),  0.0)
        macd_s  = _safe(last.get('MACDs_12_26_9'), 0.0)
        stoch_k = _safe(last.get('STOCHk_14_3_3'), 50.0)
        stoch_d = _safe(last.get('STOCHd_14_3_3'), 50.0)
        adx_val = _safe(last.get('ADX_14'), 0.0)
        obv_now = _safe(last.get('OBV'), 0.0)
        obv_old = _safe(df['OBV'].iloc[-5] if len(df) > 5 else 0.0, 0.0)

        avg_vol      = df['volume'].rolling(20).mean().iloc[-2]
        curr_vol     = float(df['volume'].iloc[-1])
        avg_vol_f    = float(avg_vol) if avg_vol and not math.isnan(float(avg_vol)) else 1.0
        vol_ratio    = round(curr_vol / avg_vol_f, 2) if avg_vol_f > 0 else 1.0
        volume_surge = vol_ratio > 1.5
        macd_bull    = macd_l > macd_s

        # ── Deteksi arah (binary — terbukti bekerja) ─────────────────────────
        long_cond  = (close > ema21 or ema9 > ema21) and macd_bull     and rsi > 40
        short_cond = (close < ema21 or ema9 < ema21) and (not macd_bull) and rsi < 60

        # Spot: wajib volume surge untuk filter pump-dump
        if market_type == "spot":
            long_cond  = long_cond  and volume_surge
            short_cond = short_cond and volume_surge

        if not long_cond and not short_cond:
            return None

        direction = "LONG" if long_cond else "SHORT"

        # ── Scoring (Base 60, hanya bonus) ───────────────────────────────────
        score = 60

        if volume_surge:   score += 15   # Ledakan volume — sinyal kuat

        if direction == "LONG":
            if close > ema50:                    score += 8   # Di atas MA jangka menengah
            if ema9  > ema21:                    score += 5   # EMA cross bullish
            if 50 <= rsi <= 70:                  score += 5   # RSI sweet spot
            if stoch_k > stoch_d and stoch_k > 30: score += 4
            if obv_now > obv_old:                score += 3   # Smart money masuk
            if adx_val > 25:                     score += 5   # Tren kuat
        else:
            if close < ema50:                    score += 8
            if ema9  < ema21:                    score += 5
            if 30 <= rsi <= 50:                  score += 5
            if stoch_k < stoch_d and stoch_k < 70: score += 4
            if obv_now < obv_old:                score += 3
            if adx_val > 25:                     score += 5

        # BTC context bonus
        btc = btc_context or {'bullish': True, 'strong': False}
        if direction == "LONG"  and btc.get('bullish'):       score += 3
        if direction == "LONG"  and btc.get('strong'):        score += 2
        if direction == "SHORT" and not btc.get('bullish'):   score += 3

        # ── Label sinyal ─────────────────────────────────────────────────────
        if score >= 85:
            signal = f"💥 STRONG {'LONG' if direction == 'LONG' else 'SHORT'}"
        else:
            signal = f"{'🚀 LONG' if direction == 'LONG' else '🩸 SHORT'}"

        # ── TP / SL / RR (ATR-based) ─────────────────────────────────────────
        atr_pct = (atr / close) * 100 if close > 0 else 2.0

        if direction == "LONG":
            sl_price  = close - 1.5 * atr
            tp1_price = close + 1.5 * atr
            tp2_price = close + 3.0 * atr
        else:
            sl_price  = close + 1.5 * atr
            tp1_price = close - 1.5 * atr
            tp2_price = close - 3.0 * atr

        risk    = abs(close - sl_price)
        rr      = round(abs(tp1_price - close) / risk, 2) if risk > 0 else 1.0
        tp1_pct = round(abs(tp1_price - close) / close * 100, 2)
        tp2_pct = round(abs(tp2_price - close) / close * 100, 2)
        sl_pct  = round(abs(close - sl_price)  / close * 100, 2)

        # ── Leverage (berbasis volatilitas ATR) ──────────────────────────────
        margin_mode = "-"
        leverage    = "-"
        if market_type == "future":
            if atr_pct > 3.0:
                margin_mode, leverage = "Isolated",       "3x – 5x"
            elif atr_pct > 1.5:
                margin_mode, leverage = "Isolated",       "5x – 10x"
            elif atr_pct > 0.8:
                margin_mode, leverage = "Cross/Isolated", "10x – 15x"
            else:
                margin_mode, leverage = "Cross",          "20x – 50x"

        # ── Funding rate ─────────────────────────────────────────────────────
        funding_desc = "N/A"
        if market_type == "future":
            try:
                fr_data = exchange.fetch_funding_rate(symbol)
                fr = fr_data.get('fundingRate') if fr_data else None
                if fr is not None:
                    fr = float(fr)
                    fr_pct = fr * 100
                    if direction == "LONG" and fr < -0.005:
                        score += 5
                        funding_desc = f"{fr_pct:.4f}% 🟢 Short crowded"
                    elif direction == "SHORT" and fr > 0.05:
                        score += 5
                        funding_desc = f"{fr_pct:.4f}% 🟢 Long crowded"
                    else:
                        funding_desc = f"{fr_pct:.4f}%"
            except Exception:
                pass

        return {
            "ticker":       symbol,
            "signal":       signal,
            "direction":    direction,
            "score":        score,
            "close":        close,
            "rsi":          round(rsi, 1),
            "adx":          round(adx_val, 1),
            "macd":         "Bullish" if macd_bull else "Bearish",
            "vol_ratio":    vol_ratio,
            "volume_surge": volume_surge,
            "funding_rate": funding_desc,
            "tp1":          round(tp1_price, 6),
            "tp2":          round(tp2_price, 6),
            "sl":           round(sl_price,  6),
            "tp1_pct":      tp1_pct,
            "tp2_pct":      tp2_pct,
            "sl_pct":       sl_pct,
            "rr":           rr,
            "atr_pct":      round(atr_pct, 2),
            "market":       market_type.upper(),
            "margin_mode":  margin_mode,
            "leverage":     leverage,
        }

    except Exception:
        return None   # Silenced — hindari spam saat scan ratusan koin

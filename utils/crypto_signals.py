import pandas as pd
import pandas_ta as ta

# ──────────────────────────────────────────────────────────────────────────────
# HELPER: BTC Context (Barometer Pasar Kripto)
# Dijalankan SEKALI sebelum loop scan, bukan per koin — efisien & tidak delay
# ──────────────────────────────────────────────────────────────────────────────

def get_btc_context(exchange):
    """
    Ambil kondisi BTC sebagai 'IHSG'-nya pasar kripto.
    Hasilnya dipass ke setiap get_crypto_recommendation() agar tidak refetch.
    """
    try:
        # Coba ambil dari futures dulu, fallback ke spot
        try:
            ohlcv = exchange.fetch_ohlcv('BTC/USDT:USDT', '1h', limit=60)
        except Exception:
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=60)

        if not ohlcv or len(ohlcv) < 50:
            raise ValueError("Data BTC tidak cukup")

        df    = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        close = df['close'].iloc[-1]
        ema21 = ta.ema(df['close'], length=21).iloc[-1]
        ema50 = ta.ema(df['close'], length=50).iloc[-1]
        rsi   = ta.rsi(df['close'], length=14).iloc[-1]

        btc_bullish = close > ema50
        btc_strong  = close > ema50 and ema21 > ema50  # Bull market kuat

        status = '🔥 Strong Bull' if btc_strong else ('🟢 Bullish' if btc_bullish else '🔴 Bearish')
        print(f"[BTC] Close: {close:.2f} | EMA50: {ema50:.2f} | RSI: {rsi:.1f} | {status}")

        return {
            'bullish': btc_bullish,
            'strong':  btc_strong,
            'rsi':     round(rsi, 1),
            'close':   close,
        }
    except Exception as e:
        print(f"[WARN] Gagal ambil BTC context: {e} — menggunakan default Netral.")
        return {'bullish': True, 'strong': False, 'rsi': 50.0, 'close': 0}


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: Funding Rate (Eksklusif Futures)
# ──────────────────────────────────────────────────────────────────────────────

def get_funding_rate(exchange, symbol):
    """
    Ambil funding rate untuk futures.
    - Negatif      → short crowded  → kondusif untuk LONG
    - Positif tinggi → long crowded → bahaya untuk LONG
    Returns float atau None jika tidak tersedia.
    """
    try:
        fr_data = exchange.fetch_funding_rate(symbol)
        return fr_data.get('fundingRate', None)
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE: Sistem Scoring 100 Poin
# ──────────────────────────────────────────────────────────────────────────────

def get_crypto_recommendation(exchange, symbol: str, market_type: str = "future",
                               timeframe: str = "1h", btc_context: dict = None):
    """
    Analisis koin dengan sistem scoring berlapis 100 poin.

    Kategori Scoring:
      A. Trend Alignment         (25 poin)
      B. Momentum Konfirmasi     (25 poin)
      C. Volume & Smart Money    (20 poin)
      D. Kekuatan Tren / ADX     (15 poin)
      E. Price Action & Struktur (15 poin)
      + Bonus Makro BTC Context & Funding Rate
      - Penalti volatilitas, divergence, extreme RSI

    market_type : "future" | "spot"
    btc_context : dict dari get_btc_context() — dipass dari luar agar efisien
    """
    try:
        # Ambil 100 candle terakhir
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        if not ohlcv or len(ohlcv) < 60:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # ── FEATURE ENGINEERING ─────────────────────────────────────────────
        df['EMA_9']  = ta.ema(df['close'], length=9)
        df['EMA_21'] = ta.ema(df['close'], length=21)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        df['VWAP']   = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
        df['RSI']    = ta.rsi(df['close'], length=14)
        df['OBV']    = ta.obv(df['close'], df['volume'])
        df['ATR']    = ta.atr(df['high'], df['low'], df['close'], length=14)

        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            df = pd.concat([df, macd], axis=1)

        stoch = ta.stoch(df['high'], df['low'], df['close'])
        if stoch is not None and not stoch.empty:
            df = pd.concat([df, stoch], axis=1)

        adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx_df is not None and not adx_df.empty:
            df = pd.concat([df, adx_df], axis=1)

        bbands = ta.bbands(df['close'], length=20, std=2)
        if bbands is not None and not bbands.empty:
            df = pd.concat([df, bbands], axis=1)

        # ── EKSTRAKSI NILAI ──────────────────────────────────────────────────
        last = df.iloc[-1]

        close    = last['close']
        open_c   = last['open']
        ema9     = last.get('EMA_9',  close)
        ema21    = last.get('EMA_21', close)
        ema50    = last.get('EMA_50', close)
        vwap     = last.get('VWAP',   close)
        rsi      = last.get('RSI',    50)
        macd_l   = last.get('MACD_12_26_9',  0)
        macd_s   = last.get('MACDs_12_26_9', 0)
        stoch_k  = last.get('STOCHk_14_3_3', 50)
        stoch_d  = last.get('STOCHd_14_3_3', 50)
        atr      = last.get('ATRr_14', close * 0.02)
        adx_val  = last.get('ADX_14', 0)
        bb_upper = last.get('BBU_20_2.0', close * 1.1)
        bb_lower = last.get('BBL_20_2.0', close * 0.9)
        obv_curr = last.get('OBV', 0)
        obv_prev = df['OBV'].iloc[-5] if len(df) > 5 else obv_curr

        avg_vol      = df['volume'].rolling(20).mean().iloc[-2]
        curr_vol     = df['volume'].iloc[-1]
        vol_ratio    = round(curr_vol / avg_vol, 2) if avg_vol > 0 else 1.0
        volume_surge = vol_ratio > 1.5

        # Deteksi arah tren — cukup satu kondisi EMA, MACD hanya di scoring
        long_bias  = close > ema21 or ema9 > ema21
        short_bias = close < ema21 or ema9 < ema21

        # ── 1. MANDATORY FILTER (minimal, keputusan diserahkan ke scoring) ──
        if adx_val < 12:                       return None  # Benar-benar flat/choppy
        if not long_bias and not short_bias:   return None  # Tidak ada tren sama sekali
        if long_bias  and rsi > 85:            return None  # Extreme overbought parah
        if short_bias and rsi < 15:            return None  # Extreme oversold parah

        # Prioritaskan arah: jika keduanya True, ambil yang lebih kuat
        if long_bias and short_bias:
            long_bias  = macd_l >= macd_s   # MACD sebagai tiebreaker
            short_bias = not long_bias


        direction = "LONG" if long_bias else "SHORT"
        score = 0

        # ── 2. A: TREND ALIGNMENT (25 poin) ─────────────────────────────────
        if direction == "LONG":
            if close > ema50:  score += 10
            if ema9  > ema21:  score += 8
            if ema21 > ema50:  score += 7
        else:
            if close < ema50:  score += 10
            if ema9  < ema21:  score += 8
            if ema21 < ema50:  score += 7

        # ── 2. B: MOMENTUM KONFIRMASI (25 poin) ─────────────────────────────
        if direction == "LONG":
            if 50 <= rsi <= 70:                             score += 10
            elif rsi > 70:                                  score += 5   # Bullish tapi memanas
            if macd_l > macd_s:                             score += 8
            if stoch_k > stoch_d and stoch_k > 30:          score += 7
        else:
            if 30 <= rsi <= 50:                             score += 10
            elif rsi < 30:                                  score += 5
            if macd_l < macd_s:                             score += 8
            if stoch_k < stoch_d and stoch_k < 70:          score += 7

        # ── 2. C: VOLUME & SMART MONEY (20 poin) ────────────────────────────
        if volume_surge:                                    score += 10
        if direction == "LONG"  and obv_curr > obv_prev:   score += 10
        if direction == "SHORT" and obv_curr < obv_prev:   score += 10

        # ── 2. D: KEKUATAN TREN / ADX (15 poin) ─────────────────────────────
        if adx_val > 20: score += 5
        if adx_val > 25: score += 5
        if adx_val > 35: score += 5

        # ── 2. E: PRICE ACTION & STRUKTUR (15 poin) ─────────────────────────
        if direction == "LONG":
            if close > vwap:               score += 8
            if close < (bb_upper * 0.98):  score += 4   # Belum overbought
            if close > open_c:             score += 3   # Candle bullish
        else:
            if close < vwap:               score += 8
            if close > (bb_lower * 1.02):  score += 4   # Belum oversold ekstrem
            if close < open_c:             score += 3   # Candle bearish

        # ── 3. BONUS MAKRO: BTC CONTEXT ─────────────────────────────────────
        btc = btc_context or {'bullish': True, 'strong': False}
        if direction == "LONG":
            if not btc['bullish']:   score -= 5    # BTC bearish = angin melawan
            elif btc['strong']:      score += 3    # BTC strong bull = bonus
        else:  # SHORT
            if btc['bullish']:       score -= 5    # BTC bullish = angin melawan SHORT

        # ── 4. BONUS: FUNDING RATE (Khusus Futures) ─────────────────────────
        funding_desc = "N/A"
        if market_type == "future":
            funding_rate = get_funding_rate(exchange, symbol)
            if funding_rate is not None:
                fr_pct = funding_rate * 100
                if direction == "LONG":
                    if funding_rate < -0.005:     # Short crowded → kondusif LONG
                        score += 5
                        funding_desc = f"{fr_pct:.4f}% 🟢 Short crowded"
                    elif funding_rate > 0.10:     # Long crowded → bahaya
                        score -= 5
                        funding_desc = f"{fr_pct:.4f}% 🔴 Long crowded"
                    else:
                        funding_desc = f"{fr_pct:.4f}% ⚪ Netral"
                else:  # SHORT
                    if funding_rate > 0.05:       # Long crowded → kondusif SHORT
                        score += 5
                        funding_desc = f"{fr_pct:.4f}% 🟢 Long crowded"
                    elif funding_rate < -0.01:    # Short crowded → bahaya SHORT
                        score -= 3
                        funding_desc = f"{fr_pct:.4f}% 🔴 Short crowded"
                    else:
                        funding_desc = f"{fr_pct:.4f}% ⚪ Netral"

        # ── 5. SISTEM PENALTI ────────────────────────────────────────────────
        atr_pct = (atr / close) * 100 if close > 0 else 0

        if atr_pct > 5:   # Volatilitas ekstrem (micin liar)
            score -= 10

        # Divergence check: harga & RSI berlawanan arah (sinyal melemah)
        if len(df) > 5:
            rsi_5ago   = df['RSI'].iloc[-5]
            close_5ago = df['close'].iloc[-5]
            if direction == "LONG"  and close > close_5ago and rsi < rsi_5ago:
                score -= 8   # Bearish divergence untuk LONG
            if direction == "SHORT" and close < close_5ago and rsi > rsi_5ago:
                score -= 8   # Bullish divergence untuk SHORT

        # ── 6. KEPUTUSAN FINAL ───────────────────────────────────────────────
        if score >= 65:
            signal = f"💥 STRONG {'LONG' if direction == 'LONG' else 'SHORT'}"
        elif score >= 45:
            signal = f"{'🚀 LONG' if direction == 'LONG' else '🩸 SHORT'}"
        else:
            return None   # Tidak cukup kuat → skip

        # ── KALKULASI LEVEL HARGA (ATR-based) ───────────────────────────────
        if direction == "LONG":
            sl_price  = close - (1.5 * atr)
            tp1_price = close + (1.5 * atr)
            tp2_price = close + (3.0 * atr)
        else:
            sl_price  = close + (1.5 * atr)
            tp1_price = close - (1.5 * atr)
            tp2_price = close - (3.0 * atr)

        risk    = abs(close - sl_price)
        rr      = round(abs(tp1_price - close) / risk, 2) if risk > 0 else 1.0
        tp1_pct = round(abs(tp1_price - close) / close * 100, 2)
        tp2_pct = round(abs(tp2_price - close) / close * 100, 2)
        sl_pct  = round(abs(close - sl_price)  / close * 100, 2)

        # ── REKOMENDASI LEVERAGE (Berbasis Volatilitas ATR) ──────────────────
        margin_mode = "-"
        leverage    = "-"
        if market_type == "future":
            if atr_pct > 3.0:
                margin_mode, leverage = "Isolated",       "3x – 5x"
            elif atr_pct > 1.5:
                margin_mode, leverage = "Isolated",       "5x – 10x"
            elif atr_pct > 0.8:
                margin_mode, leverage = "Cross/Isolated", "10x – 15x"
            else:                                         # BTC/ETH stabil
                margin_mode, leverage = "Cross",          "20x – 50x"

        return {
            "ticker":       symbol,
            "signal":       signal,
            "direction":    direction,
            "score":        score,
            "close":        close,
            "rsi":          round(rsi, 1),
            "adx":          round(adx_val, 1),
            "macd":         "Bullish" if macd_l > macd_s else "Bearish",
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
        return None   # Silenced — hindari spam log saat scan ratusan koin


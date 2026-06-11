import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# Cache global agar kita tidak mendownload data Macro IHSG berulang kali untuk setiap saham
MACRO_DATA = {}

def get_macro_data():
    global MACRO_DATA
    if 'ihsg' not in MACRO_DATA:
        try:
            # Mengambil data IHSG (Market Regime Filter)
            ihsg = yf.Ticker('^JKSE')
            hist_ihsg = ihsg.history(period="2y")
            hist_ihsg['SMA_200'] = ta.sma(hist_ihsg['Close'], length=200)
            MACRO_DATA['ihsg'] = hist_ihsg
            
            # Mengambil data USD/IDR (Macro Sentiment)
            usdidr = yf.Ticker('IDR=X')
            hist_usdidr = usdidr.history(period="1mo")
            MACRO_DATA['usdidr'] = hist_usdidr
        except:
            MACRO_DATA['ihsg'] = None
            MACRO_DATA['usdidr'] = None
    return MACRO_DATA

def get_stock_recommendation(ticker: str):
    try:
        ticker_symbol = f"{ticker}.JK" if not ticker.endswith('.JK') else ticker
        stock = yf.Ticker(ticker_symbol)
        
        # 1. TAHAP PERSIAPAN DATA (Ditingkatkan jadi 2 Tahun untuk Weekly TF)
        hist = stock.history(period="2y")
        if hist.empty or len(hist) < 100:
            return None
            
        macro = get_macro_data()
        
        # --- FEATURE ENGINEERING (INDIKATOR TEKNIKAL & QUANT) ---
        
        # Trend (Daily)
        hist['EMA_20'] = ta.ema(hist['Close'], length=20)
        hist['EMA_50'] = ta.ema(hist['Close'], length=50)
        
        # Momentum
        hist['RSI'] = ta.rsi(hist['Close'], length=14)
        macd = ta.macd(hist['Close'], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            hist = pd.concat([hist, macd], axis=1)
            
        # Volatilitas & Risk (ATR & Bollinger Bands)
        hist['ATR'] = ta.atr(hist['High'], hist['Low'], hist['Close'], length=14)
        bbands = ta.bbands(hist['Close'], length=20, std=2)
        if bbands is not None and not bbands.empty:
            hist = pd.concat([hist, bbands], axis=1)
            
        # Trend Strength (ADX) -> Untuk menghindari Sideways Market
        adx = ta.adx(hist['High'], hist['Low'], hist['Close'], length=14)
        if adx is not None and not adx.empty:
            hist = pd.concat([hist, adx], axis=1)
            
        # Institutional / Smart Money Flow (OBV & A/D Line)
        hist['OBV'] = ta.obv(hist['Close'], hist['Volume'])
        hist['AD_Line'] = ta.ad(hist['High'], hist['Low'], hist['Close'], hist['Volume'])
        
        # Multi-Timeframe Confirmation (Weekly)
        # Resample data harian ke mingguan
        weekly = hist['Close'].resample('W-FRI').last()
        weekly_ema20 = ta.ema(weekly, length=20)
        weekly_ema50 = ta.ema(weekly, length=50)
        
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        
        # --- EKSTRAKSI VARIABEL UTAMA ---
        close_price = last['Close']
        open_price = last['Open']
        high_price = last['High']
        low_price = last['Low']
        volume = last['Volume']
        
        ema_20 = last.get('EMA_20', close_price)
        ema_50 = last.get('EMA_50', close_price)
        rsi = last.get('RSI', 50)
        macd_line = last.get('MACD_12_26_9', 0)
        macd_signal = last.get('MACDs_12_26_9', 0)
        atr = last.get('ATRr_14', close_price * 0.02)
        adx_val = last.get('ADX_14', 0)
        
        obv_current = last.get('OBV', 0)
        obv_prev10 = hist['OBV'].iloc[-10] if len(hist) > 10 else 0
        ad_current = last.get('AD_Line', 0)
        ad_prev = prev.get('AD_Line', 0)
        
        # --- PERHITUNGAN FILTER KHUSUS (QUANT RULES) ---
        
        # 1. Market Regime Filter (IHSG harus di atas MA-200)
        ihsg_regime_bullish = False
        ihsg_df = macro.get('ihsg')
        if ihsg_df is not None and not ihsg_df.empty:
            last_ihsg = ihsg_df.iloc[-1]
            ihsg_ma200 = last_ihsg.get('SMA_200', 0)
            if last_ihsg['Close'] > ihsg_ma200:
                ihsg_regime_bullish = True
                
        # 2. Multi-Timeframe Filter (Weekly Trend)
        weekly_bullish = False
        if weekly_ema20 is not None and weekly_ema50 is not None and len(weekly_ema20) > 0:
            weekly_bullish = (close_price > weekly_ema20.iloc[-1]) and (weekly_ema20.iloc[-1] > weekly_ema50.iloc[-1])
            
        # 3. Relative Strength vs Index (Performa 3 Bulan / ~60 hari)
        rs_outperform = False
        if ihsg_df is not None and len(hist) > 60 and len(ihsg_df) > 60:
            stock_return = (close_price - hist['Close'].iloc[-60]) / hist['Close'].iloc[-60]
            ihsg_return = (ihsg_df['Close'].iloc[-1] - ihsg_df['Close'].iloc[-60]) / ihsg_df['Close'].iloc[-60]
            if stock_return > ihsg_return:
                rs_outperform = True
                
        # 4. Price Action & Gap Check
        is_bullish_candle = close_price > open_price
        gap_up_pct = (open_price - prev['Close']) / prev['Close']
        is_safe_gap = gap_up_pct < 0.03 # Ditolak jika Gap Up terlalu liar (>3%)
        
        # 5. Smart Money Flow
        is_accumulation = (obv_current > obv_prev10) and (ad_current > ad_prev)
        
        # 6. Trend Strength
        is_strong_trend = adx_val > 25
        
        # --- SCORING & DECISION TREE (ENSEMBLE RULE-BASED) ---
        
        is_daily_uptrend = close_price > ema_20 and ema_20 > ema_50
        
        score = 0
        signal = "Tunggu"
        action = "Wait & See"
        target_hold = "-"
        stop_loss = "-"
        alasan = "Kondisi pasar atau saham belum memenuhi kriteria probabilitas tinggi (Win Rate rendah)."
        
        # === STRONG BUY SETUP (INSTITUTIONAL GRADE) ===
        if ihsg_regime_bullish and weekly_bullish and is_daily_uptrend and is_strong_trend and is_accumulation and rs_outperform and is_bullish_candle and is_safe_gap:
            score = 10
            signal = "Strong Buy"
            action = "BELI SEKARANG (Buy at Current Price)"
            target_hold = "Swing 1-3 Minggu (Trend Following)"
            stop_loss = f"Cut Loss jika harga tutup di bawah Rp {int(ema_20 - atr)} (EMA-20 - ATR)"
            alasan = "PERFECT SETUP: ADX>25 (Tren Kuat), Multi-Timeframe Weekly Bullish, Smart Money Akumulasi (OBV Naik), dan Outperform IHSG."
            
        # === OVERSOLD REVERSAL (MEAN REVERSION) ===
        elif rsi < 35 and is_bullish_candle and is_accumulation and is_safe_gap:
            score = 8
            signal = "Buy"
            action = "CICIL BELI (Buy on Weakness)"
            target_hold = "Short-term Rebound (Hold 3-5 Hari)"
            stop_loss = f"Cut Loss ketat di bawah harga terendah hari ini: Rp {int(low_price * 0.98)}"
            alasan = "MEAN REVERSION: Saham sudah Oversold ekstrem. Smart Money mulai masuk hari ini (konfirmasi Candle Bullish & OBV)."
            
        # === BUY SETUP (STANDARD BREAKOUT) ===
        elif is_daily_uptrend and is_accumulation and (macd_line > macd_signal) and is_bullish_candle:
            score = 6
            signal = "Buy"
            action = "BELI TERBATAS (Partial Position)"
            target_hold = "Swing Pendek (Hold selama belum tembus EMA-20)"
            stop_loss = f"Cut Loss di bawah EMA-20: Rp {int(ema_20)}"
            alasan = "UPTREND MILD: MACD Bullish dan ada indikasi akumulasi, walau Macro IHSG / Weekly belum konfirmasi sempurna."
            
        # === SELL SETUP ===
        elif close_price < ema_50 and macd_line < macd_signal:
            score = -8
            signal = "Strong Sell"
            action = "JUAL / CUT LOSS"
            target_hold = "-"
            stop_loss = "-"
            alasan = "BEARISH TREN: Patah tren jangka menengah (EMA-50) dan distribusi sedang berlangsung."
            
        # Format Strategy Output agar lebih rapi untuk Telegram & Web
        strategy = f"👉 **Tindakan**: {action}\n"
        strategy += f"⏱️ **Target Hold**: {target_hold}\n"
        strategy += f"🛑 **Stop Loss**: {stop_loss}\n"
        strategy += f"💡 **Alasan Khusus**: {alasan}"
        
        info = stock.info
        pe = info.get('trailingPE', None)
        pbv = info.get('priceToBook', None)
        
        return {
            "ticker": ticker,
            "signal": signal,
            "strategy": strategy,
            "score": score,
            "rsi": rsi,
            "macd": "Bullish" if (macd_line > macd_signal) else "Bearish",
            "close": close_price,
            "pe": round(pe, 2) if pe else "N/A",
            "pbv": round(pbv, 2) if pbv else "N/A"
        }
    except Exception as e:
        return None

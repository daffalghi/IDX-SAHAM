import yfinance as yf
import pandas as pd
import pandas_ta as ta

def get_stock_recommendation(ticker: str):
    """
    Kombinasi berbagai parameter teknikal (Trend, Momentum, Volatilitas, Volume)
    untuk mencari titik entri yang presisi (Confluence Strategy).
    """
    try:
        ticker_symbol = f"{ticker}.JK" if not ticker.endswith('.JK') else ticker
        stock = yf.Ticker(ticker_symbol)
        
        hist = stock.history(period="6mo")
        if hist.empty or len(hist) < 50:
            return None
            
        # 1. Momentum: RSI
        hist['RSI'] = ta.rsi(hist['Close'], length=14)
        
        # 2. Trend: MACD
        macd = ta.macd(hist['Close'], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            hist = pd.concat([hist, macd], axis=1)
            
        # 3. Trend: EMA 20 & 50
        hist['EMA_20'] = ta.ema(hist['Close'], length=20)
        hist['EMA_50'] = ta.ema(hist['Close'], length=50)
        
        # 4. Volatilitas: Bollinger Bands
        bbands = ta.bbands(hist['Close'], length=20, std=2)
        if bbands is not None and not bbands.empty:
            hist = pd.concat([hist, bbands], axis=1)
            
        # 5. Volume: SMA Volume 10 Hari
        hist['SMA_Vol_10'] = ta.sma(hist['Volume'], length=10)
        
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        
        # Ekstraksi Nilai
        close_price = last['Close']
        open_price = last['Open']
        volume = last['Volume']
        sma_vol = last.get('SMA_Vol_10', volume)
        rsi = last.get('RSI', 50)
        macd_line = last.get('MACD_12_26_9', 0)
        macd_signal = last.get('MACDs_12_26_9', 0)
        prev_macd_line = prev.get('MACD_12_26_9', 0)
        prev_macd_signal = prev.get('MACDs_12_26_9', 0)
        ema_20 = last.get('EMA_20', close_price)
        ema_50 = last.get('EMA_50', close_price)
        bb_upper = last.get('BBU_20_2.0', close_price * 1.1)
        bb_lower = last.get('BBL_20_2.0', close_price * 0.9)
        
        # --- LOGIKA REKOMENDASI BERBASIS CONFLUENCE (KOMBINASI PARAMETER) ---
        signal = "Hold"
        strategy = "Pantau pergerakan. Belum ada kombinasi sinyal yang cukup kuat untuk entri yang aman."
        score = 0
        
        # Filter 1: Apakah sedang dalam konfirmasi Uptrend?
        is_uptrend = close_price > ema_20 and ema_20 > ema_50
        
        # Filter 2: Momentum sehat (tidak overbought, tapi sedang melaju)
        is_momentum_healthy = 45 <= rsi <= 65
        
        # Filter 3: Ada lonjakan akumulasi/volume (Bandar/Institusi masuk)
        is_high_volume = volume > (sma_vol * 1.2)
        
        # Filter 4: MACD Bullish Crossover & Trend
        is_macd_bullish = macd_line > macd_signal
        is_macd_golden_cross = (prev_macd_line <= prev_macd_signal) and (macd_line > macd_signal)
        
        # Filter 5: Ruang tumbuh (Jarak ke Upper Bollinger Band)
        # Mencegah beli di pucuk (harga tidak boleh sedang menabrak atap resistance)
        room_to_grow = close_price < (bb_upper * 0.98)
        
        # --- PENENTUAN STRONG BUY ---
        # SETUP 1: TREND FOLLOWING CONFLUENCE (Semua bintang sejajar)
        if is_uptrend and is_momentum_healthy and is_macd_bullish and is_high_volume and room_to_grow:
            signal = "Strong Buy"
            strategy = "PERFECT CONFLUENCE: Harga uptrend di atas EMA, volume melonjak >120%, MACD Bullish, dan belum nabrak resistance band. Beli!"
            score = 10
            
        # SETUP 2: OVERSOLD REVERSAL (Pantulan Banteng)
        elif rsi < 35 and close_price > open_price and is_macd_golden_cross:
            signal = "Strong Buy"
            strategy = "BOTTOM REVERSAL: Saham sangat murah (Oversold), membentuk candle hijau, ditambah MACD Golden Cross! Sangat cocok untuk dibeli di harga bawah."
            score = 9
            
        # --- PENENTUAN BUY BIASA ---
        elif is_macd_golden_cross and is_momentum_healthy:
            signal = "Buy"
            strategy = "EARLY TREND: Terjadi MACD Golden Cross. Mulai cicil beli secara bertahap."
            score = 7
        elif is_uptrend and rsi > 50 and room_to_grow:
            signal = "Buy"
            strategy = "UPTREND MILD: Saham dalam tren naik stabil. Cocok untuk strategi Trend Following standar."
            score = 6
            
        # --- PENENTUAN SELL ---
        elif rsi > 75:
            signal = "Strong Sell"
            strategy = "OVERBOUGHT EXTREME: Harga sudah terlalu tinggi dan rawan dibanting profit taking. Segera amankan keuntungan Anda!"
            score = -10
        elif close_price < ema_20 and not is_macd_bullish:
            signal = "Sell"
            strategy = "DOWNTREND: Harga patah support EMA-20 dan MACD mengarah ke bawah. Jauhi saham ini untuk sementara waktu."
            score = -5
            
        # Fundamental sebagai data pelengkap
        info = stock.info
        pe = info.get('trailingPE', None)
        pbv = info.get('priceToBook', None)
        
        return {
            "ticker": ticker,
            "signal": signal,
            "strategy": strategy,
            "score": score,
            "rsi": rsi,
            "macd": "Bullish" if is_macd_bullish else "Bearish",
            "close": close_price,
            "pe": round(pe, 2) if pe else "N/A",
            "pbv": round(pbv, 2) if pbv else "N/A"
        }
    except Exception as e:
        return None

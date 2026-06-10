import yfinance as yf
import pandas as pd
import pandas_ta as ta

def get_stock_recommendation(ticker: str):
    """
    Menggabungkan analisis teknikal (Momentum, Trend) 
    dan fundamental (Valuation) untuk memberikan sinyal rekomendasi.
    """
    try:
        ticker_symbol = f"{ticker}.JK" if not ticker.endswith('.JK') else ticker
        stock = yf.Ticker(ticker_symbol)
        
        # Ambil data 6 bulan terakhir untuk analisis teknikal
        hist = stock.history(period="6mo")
        if hist.empty or len(hist) < 50:
            return None
            
        # 1. Analisis Teknikal: RSI (Momentum)
        hist['RSI'] = ta.rsi(hist['Close'], length=14)
        
        # 2. Analisis Teknikal: MACD (Trend Momentum)
        macd = ta.macd(hist['Close'], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            hist = pd.concat([hist, macd], axis=1)
            
        # 3. Analisis Teknikal: EMA (Trend Direction)
        hist['EMA_20'] = ta.ema(hist['Close'], length=20)
        hist['EMA_50'] = ta.ema(hist['Close'], length=50)
        
        # Data hari terakhir
        last = hist.iloc[-1]
        
        signal = "Hold"
        score = 0
        strategy = "Pantau pergerakan harga. Saat ini belum ada sinyal yang mengkonfirmasi arah yang kuat."
        
        # --- SCORING SYSTEM ---
        # 1. RSI
        rsi = last['RSI']
        if pd.isna(rsi): rsi = 50
        
        if rsi < 30:
            score += 2 # Oversold (Potensi naik)
        elif rsi > 70:
            score -= 2 # Overbought (Potensi turun)
        elif rsi > 50:
            score += 1 # Uptrend momentum
            
        # 2. MACD
        macd_line = last.get('MACD_12_26_9', 0)
        macd_signal = last.get('MACDs_12_26_9', 0)
        if macd_line > macd_signal:
            score += 2 # MACD Bullish Crossover
        else:
            score -= 1 # MACD Bearish
            
        # 3. EMA / Trend
        close_price = last['Close']
        if close_price > last.get('EMA_20', close_price) and close_price > last.get('EMA_50', close_price):
            score += 2 # Uptrend kuat
        elif close_price < last.get('EMA_20', close_price) and close_price < last.get('EMA_50', close_price):
            score -= 2 # Downtrend kuat
            
        # 4. Fundamental Valuation (Bonus)
        info = stock.info
        pe = info.get('trailingPE', None)
        pbv = info.get('priceToBook', None)
        
        if pe is not None and pe < 15 and pe > 0:
            score += 1 # Undervalued P/E
        elif pe is not None and pe > 30:
            score -= 1 # Overvalued P/E
            
        if pbv is not None and pbv < 1.5 and pbv > 0:
            score += 1 # Undervalued PBV
            
        # --- GENERATE SIGNAL & STRATEGY ---
        if score >= 5:
            signal = "Strong Buy"
            if rsi < 40 and macd_line > macd_signal:
                strategy = "Swing Trading: Beli sekarang dan HOLD untuk beberapa minggu. Harga sedang rebound dari area oversold dengan fundamental yang mendukung."
            else:
                strategy = "Trend Following: Momentum uptrend sedang sangat kuat. Cocok untuk beli pagi dan hold selama EMA-20 belum tembus ke bawah."
        elif score >= 2:
            signal = "Buy"
            strategy = "Cicil Beli (DCA): Harga berpotensi naik namun butuh konfirmasi. Strategi Buy on Weakness (Beli saat koreksi) sangat disarankan."
        elif score <= -3:
            signal = "Strong Sell"
            strategy = "Cut Loss / Take Profit: Trend turun sangat kuat. Jauhi saham ini untuk sementara waktu atau jual posisi Anda."
        elif score <= -1:
            signal = "Sell"
            strategy = "Kurangi Porsi: Harga berpotensi koreksi lebih lanjut. Jual saham saat ada pantulan teknikal kecil (Sell on Strength)."
            
        return {
            "ticker": ticker,
            "signal": signal,
            "strategy": strategy,
            "score": score,
            "rsi": rsi,
            "macd": "Bullish" if macd_line > macd_signal else "Bearish",
            "close": close_price,
            "pe": round(pe, 2) if pe else "N/A",
            "pbv": round(pbv, 2) if pbv else "N/A"
        }
    except Exception as e:
        return None

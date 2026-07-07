import pandas as pd
import pandas_ta as ta

def get_crypto_recommendation(exchange, symbol: str, market_type: str = "future", timeframe: str = "4h"):
    """
    Menganalisis koin menggunakan CCXT exchange instance.
    market_type: "future" atau "spot"
    """
    try:
        # Ambil 100 candle terakhir
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        if not ohlcv or len(ohlcv) < 50:
            return None
            
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Hitung Indikator Teknikal
        df['EMA_9'] = ta.ema(df['close'], length=9)
        df['EMA_21'] = ta.ema(df['close'], length=21)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        
        df['RSI'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            df = pd.concat([df, macd], axis=1)
            
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Ekstrak data candle terakhir
        last = df.iloc[-1]
        
        close = last['close']
        ema9 = last.get('EMA_9', close)
        ema21 = last.get('EMA_21', close)
        ema50 = last.get('EMA_50', close)
        rsi = last.get('RSI', 50)
        macd_l = last.get('MACD_12_26_9', 0)
        macd_s = last.get('MACDs_12_26_9', 0)
        atr = last.get('ATRr_14', close * 0.02)
        
        # Volume Surge Detector (Apakah volume saat ini 2x lipat dari rata-rata volume 20 candle terakhir?)
        avg_vol = df['volume'].rolling(20).mean().iloc[-2]
        current_vol = df['volume'].iloc[-1]
        volume_surge = current_vol > (avg_vol * 1.5)
        
        # Logika LONG (Beli)
        long_cond = close > ema50 and ema9 > ema21 and rsi > 50 and macd_l > macd_s
        
        # Logika SHORT (Jual) (HANYA UNTUK FUTURES)
        short_cond = close < ema50 and ema9 < ema21 and rsi < 50 and macd_l < macd_s
        
        signal = "Neutral"
        action = "Wait & See"
        target = "-"
        stop_loss = "-"
        score = 50
        
        if long_cond:
            if market_type == "spot" and not volume_surge:
                # Untuk spot (terutama micin), butuh ledakan volume untuk dianggap kuat
                pass
            else:
                signal = "LONG 🚀"
                action = "Beli Spot" if market_type == "spot" else "Beli / Long Position"
                target = f"{close + (2 * atr):.6f}"
                stop_loss = f"{close - (1.5 * atr):.6f}"
                score = 80
                if volume_surge:
                    score += 15 # Poin plus untuk ledakan volume
                    signal = "STRONG BUY 💥"
                    
        elif short_cond and market_type == "future":
            signal = "SHORT 🩸"
            action = "Jual / Short Position"
            target = f"{close - (2 * atr):.6f}"
            stop_loss = f"{close + (1.5 * atr):.6f}"
            score = 75
            
        if signal == "Neutral":
            return None # Skip jika netral
            
        return {
            "ticker": symbol,
            "signal": signal,
            "action": action,
            "close": close,
            "rsi": rsi,
            "target": target,
            "stop_loss": stop_loss,
            "score": score,
            "market": market_type.upper()
        }
        
    except Exception as e:
        # Silenced error to avoid spamming the logs when scanning 300 coins
        return None

import ccxt
import pandas as pd
import pandas_ta as ta

def get_crypto_recommendation(symbol: str, timeframe: str = "4h"):
    try:
        # Gunakan CCXT untuk menarik data Binance USDT Futures
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })
        
        # Ambil 100 candle terakhir
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        if df.empty or len(df) < 50:
            return None
            
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
        
        # Logika LONG (Beli)
        long_cond = close > ema50 and ema9 > ema21 and rsi > 50 and macd_l > macd_s
        
        # Logika SHORT (Jual)
        short_cond = close < ema50 and ema9 < ema21 and rsi < 50 and macd_l < macd_s
        
        signal = "Neutral"
        action = "Wait & See"
        target = "-"
        stop_loss = "-"
        score = 50
        
        if long_cond:
            signal = "LONG 🚀"
            action = "Beli / Long Position"
            # Target 2x ATR, Stop Loss 1.5x ATR
            target = f"{close + (2 * atr):.4f}"
            stop_loss = f"{close - (1.5 * atr):.4f}"
            score = 80
        elif short_cond:
            signal = "SHORT 🩸"
            action = "Jual / Short Position"
            # Target 2x ATR, Stop Loss 1.5x ATR ke atas
            target = f"{close - (2 * atr):.4f}"
            stop_loss = f"{close + (1.5 * atr):.4f}"
            score = 20
            
        if signal == "Neutral":
            return None # Skip jika netral agar tidak memenuhi pesan Telegram
            
        return {
            "ticker": symbol,
            "signal": signal,
            "action": action,
            "close": close,
            "rsi": rsi,
            "target": target,
            "stop_loss": stop_loss,
            "score": score
        }
        
    except Exception as e:
        print(f"[ERROR] Gagal memproses {symbol}: {e}")
        return None

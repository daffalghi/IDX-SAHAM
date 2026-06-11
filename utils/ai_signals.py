import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import sqlite3
import os

MACRO_DATA = {}

def get_db_connection():
    db_path = 'IDX-API/data/database.sqlite'
    if os.path.exists(db_path):
        return sqlite3.connect(db_path)
    return None

def get_foreign_net(ticker: str, days=3):
    conn = get_db_connection()
    if not conn: return False
    try:
        query = f"SELECT foreign_net FROM stock_summary WHERE code='{ticker}' ORDER BY date DESC LIMIT {days}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if len(df) > 0 and df['foreign_net'].sum() > 0:
            return True
        return False
    except:
        return False

def get_macro_data():
    global MACRO_DATA
    if 'ihsg' not in MACRO_DATA:
        try:
            ihsg = yf.Ticker('^JKSE')
            hist_ihsg = ihsg.history(period="2y")
            hist_ihsg['SMA_200'] = ta.sma(hist_ihsg['Close'], length=200)
            hist_ihsg['ADX'] = ta.adx(hist_ihsg['High'], hist_ihsg['Low'], hist_ihsg['Close'], length=14)['ADX_14']
            MACRO_DATA['ihsg'] = hist_ihsg
        except:
            MACRO_DATA['ihsg'] = None
    return MACRO_DATA

def get_stock_recommendation(ticker: str):
    try:
        ticker_symbol = f"{ticker}.JK" if not ticker.endswith('.JK') else ticker
        stock = yf.Ticker(ticker_symbol)
        
        # --- PERSIAPAN DATA ---
        hist = stock.history(period="2y")
        if hist.empty or len(hist) < 100:
            return None
            
        macro = get_macro_data()
        
        # --- FEATURE ENGINEERING ---
        hist['EMA_20'] = ta.ema(hist['Close'], length=20)
        hist['EMA_50'] = ta.ema(hist['Close'], length=50)
        hist['VWAP'] = ta.vwap(hist['High'], hist['Low'], hist['Close'], hist['Volume'])
        
        hist['RSI'] = ta.rsi(hist['Close'], length=14)
        macd = ta.macd(hist['Close'], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            hist = pd.concat([hist, macd], axis=1)
            
        stoch = ta.stoch(hist['High'], hist['Low'], hist['Close'])
        if stoch is not None and not stoch.empty:
            hist = pd.concat([hist, stoch], axis=1)
            
        hist['ATR'] = ta.atr(hist['High'], hist['Low'], hist['Close'], length=14)
        bbands = ta.bbands(hist['Close'], length=20, std=2)
        if bbands is not None and not bbands.empty:
            hist = pd.concat([hist, bbands], axis=1)
            
        adx = ta.adx(hist['High'], hist['Low'], hist['Close'], length=14)
        if adx is not None and not adx.empty:
            hist = pd.concat([hist, adx], axis=1)
            
        hist['OBV'] = ta.obv(hist['Close'], hist['Volume'])
        hist['AD_Line'] = ta.ad(hist['High'], hist['Low'], hist['Close'], hist['Volume'])
        hist['SMA_Vol_10'] = ta.sma(hist['Volume'], length=10)
        
        weekly = hist['Close'].resample('W-FRI').last()
        weekly_ema20 = ta.ema(weekly, length=20)
        
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        
        # --- EKSTRAKSI VARIABEL ---
        close = last['Close']
        open_pr = last['Open']
        high = last['High']
        low = last['Low']
        vol = last['Volume']
        
        ema20 = last.get('EMA_20', close)
        ema50 = last.get('EMA_50', close)
        vwap = last.get('VWAP_D', close)
        rsi = last.get('RSI', 50)
        macd_l = last.get('MACD_12_26_9', 0)
        macd_s = last.get('MACDs_12_26_9', 0)
        macd_hist = last.get('MACDh_12_26_9', 0)
        stoch_k = last.get('STOCHk_14_3_3', 50)
        stoch_d = last.get('STOCHd_14_3_3', 50)
        
        atr = last.get('ATRr_14', close * 0.02)
        adx_val = last.get('ADX_14', 0)
        bb_upper = last.get('BBU_20_2.0', close * 1.1)
        
        obv_curr = last.get('OBV', 0)
        obv_prev10 = hist['OBV'].iloc[-10] if len(hist) > 10 else 0
        ad_curr = last.get('AD_Line', 0)
        ad_prev = prev.get('AD_Line', 0)
        avg_vol = last.get('SMA_Vol_10', vol)
        
        # Fundamental Data
        info = stock.info
        roe = info.get('returnOnEquity', 0) or 0
        earning_growth = info.get('earningsGrowth', 0) or 0
        per = info.get('trailingPE', 999) or 999
        
        net_foreign_buy = get_foreign_net(ticker, days=3)
        
        # --- 1. MANDATORY FILTERS ---
        ihsg_df = macro.get('ihsg')
        ihsg_bullish = True
        dynamic_threshold = 85
        
        if ihsg_df is not None and not ihsg_df.empty:
            last_ihsg = ihsg_df.iloc[-1]
            if last_ihsg['Close'] < last_ihsg.get('SMA_200', 0):
                ihsg_bullish = False
            if last_ihsg.get('ADX', 0) > 30 and last_ihsg['Close'] > last_ihsg.get('SMA_200', 0):
                dynamic_threshold = 82 # Bull market kuat
                
        w_ema20 = weekly_ema20.iloc[-1] if (weekly_ema20 is not None and len(weekly_ema20)>0) else close
        
        if not ihsg_bullish or adx_val < 25 or close < w_ema20 or close >= (bb_upper * 0.98) or rsi > 75:
            return {
                "ticker": ticker,
                "signal": "Skip",
                "strategy": "Gagal Mandatory Filter (Bukan tren yang kuat atau risiko tinggi).",
                "score": 0,
                "rsi": rsi,
                "macd": "Bullish" if macd_l > macd_s else "Bearish",
                "close": close,
                "pe": round(per, 2) if per != 999 else "N/A",
                "pbv": round(info.get('priceToBook', 0) or 0, 2)
            }
            
        # --- 2. CORE SCORE (100 POIN) ---
        score = 0
        
        # A. Trend Strength (22)
        if close > ema20: score += 8
        if ema20 > ema50: score += 7
        if close > w_ema20: score += 5
        if close > vwap: score += 2
        
        # B. Smart Money Flow (23)
        if obv_curr > obv_prev10: score += 9
        if ad_curr > ad_prev: score += 8
        if net_foreign_buy: score += 6
        
        # C. Fundamental & Catalyst (22)
        if roe > 0.15: score += 8
        if earning_growth > 0.10: score += 8
        if per < 25 and per > 0: score += 4
        # Bonus catalyst (Jika volume pecah rekor, asumsikan ada news)
        if vol > (avg_vol * 2.5): score += 2
        
        # D. Momentum (18)
        if macd_l > macd_s and macd_hist > 0: score += 9
        if stoch_k > stoch_d and stoch_k > 30: score += 9
        
        # E. Price Action & Volume (15)
        if close > open_pr and vol > avg_vol: score += 7
        gap = (open_pr - prev['Close']) / prev['Close']
        if gap < 0.04: score += 3
        if vol > (avg_vol * 1.2): score += 5
        
        # --- PENALTY SYSTEM ---
        # Volatility Regime (Mencegah beli saham gorengan liar)
        atr_pct = atr / close
        if atr_pct > 0.08: # ATR > 8% sehari = sangat liar
            score -= 8
            
        # Bearish Divergence Sederhana (Harga naik tapi RSI turun)
        if close > hist['Close'].iloc[-10] and rsi < hist['RSI'].iloc[-10]:
            score -= 10
            
        # --- THRESHOLD DECISION ---
        if score >= dynamic_threshold:
            signal = "Strong Buy"
            action = "BELI (Aggressive)"
            target = "Swing Hold (1-3 Minggu) selama harga di atas EMA-20"
            stop_loss = f"Trailing Stop/Cut Loss jika tutup di bawah Rp {int(close - (1.5 * atr))}"
            alasan = f"SCORE {score}/100: Trend & Fundamental luar biasa. Market regime sangat mendukung."
        elif score >= 70:
            signal = "Buy"
            action = "BELI (Partial)"
            target = "Swing Pendek (Hold sampai resisten/Upper BB)"
            stop_loss = f"Cut Loss jika tutup di bawah EMA-20 (Rp {int(ema20)})"
            alasan = f"SCORE {score}/100: Memenuhi standar kuantitatif institusi, momentum stabil."
        else:
            return {
                "ticker": ticker,
                "signal": "Neutral",
                "strategy": f"Skor terlalu rendah ({score}/100) untuk masuk kriteria Buy.",
                "score": score,
                "rsi": rsi,
                "macd": "Bullish" if macd_l > macd_s else "Bearish",
                "close": close,
                "pe": round(per, 2) if per != 999 else "N/A",
                "pbv": round(info.get('priceToBook', 0) or 0, 2)
            }
            
        strategy = f"👉 **Tindakan**: {action}\n"
        strategy += f"⏱️ **Target Hold**: {target}\n"
        strategy += f"🛑 **Risk / Exit Rule**: {stop_loss}\n"
        strategy += f"💡 **Catatan**: Jual jika terjadi MACD Death Cross!\n"
        strategy += f"🎯 **Alasan**: {alasan}"
        
        return {
            "ticker": ticker,
            "signal": signal,
            "strategy": strategy,
            "score": score,
            "rsi": rsi,
            "macd": "Bullish" if macd_l > macd_s else "Bearish",
            "close": close,
            "pe": round(per, 2) if per != 999 else "N/A",
            "pbv": round(info.get('priceToBook', 0) or 0, 2)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

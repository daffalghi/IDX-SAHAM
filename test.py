from utils.ai_signals import get_stock_recommendation
import yfinance as yf

print("Testing BMRI...")
res = get_stock_recommendation('BMRI')
print(res)

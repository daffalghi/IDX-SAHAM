import yfinance as yf
info = yf.Ticker('BMRI.JK').info
print("ROE:", info.get('returnOnEquity'))
print("EarningsGrowth:", info.get('earningsGrowth'))
print("Beta:", info.get('beta'))

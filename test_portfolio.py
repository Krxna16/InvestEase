import pandas as pd
import yfinance as yf
import numpy as np

symbols = ["AAPL", "MSFT"]
data = yf.download(symbols, start="2023-01-01", end="2024-01-01", interval="1d")
historical_df = data['Adj Close'] if 'Adj Close' in data.columns else data['Close']
print(type(historical_df.index))

weights = pd.Series([0.5, 0.5], index=symbols)
daily_returns = historical_df.pct_change()
portfolio_daily_returns = (daily_returns * weights).sum(axis=1).dropna()

print(type(portfolio_daily_returns.index))
# Try to resample
try:
    monthly_returns = (1 + portfolio_daily_returns).resample('M').prod() - 1
    print("Resampled successfully")
except Exception as e:
    print(f"Error: {e}")


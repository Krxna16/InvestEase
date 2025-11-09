import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

_price_cache = {}
_info_cache = {} # Cache for ticker info (used to get sector)

def get_live_price(symbol):
    """Fetches the latest closing price for a single stock symbol."""
    symbol = symbol.upper()
    current_time = datetime.now()
    
    if symbol in _price_cache and (current_time - _price_cache[symbol]['time']) < timedelta(minutes=5):
        return _price_cache[symbol]['price']
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get('regularMarketPrice') or info.get('currentPrice')
        
        if price:
            _price_cache[symbol] = {'price': price, 'time': current_time}
            # Cache the full info object for sector fetching
            _info_cache[symbol] = info 
            return price
        else:
            return None
            
    except Exception as e:
        # print(f"Error fetching live price for {symbol}: {e}")
        return None

def get_sector_info(symbol):
    """Fetches the sector information for a given stock symbol."""
    symbol = symbol.upper()
    
    # Check if info is already in the cache (from the price fetch)
    if symbol in _info_cache:
        info = _info_cache[symbol]
    else:
        # If not in cache, fetch the info directly (this is slower)
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            _info_cache[symbol] = info
        except Exception:
            return "N/A"
            
    # Extract the sector, defaulting to 'N/A' if not found
    return info.get('sector', 'N/A')

def get_historical_prices(symbols, start_date, end_date, include_benchmark=False):
    """
    Fetches adjusted closing historical prices for a list of symbols.
    Optionally includes the S&P 500 benchmark (^GSPC).
    """
    fetch_symbols = symbols.copy()
    if include_benchmark and '^GSPC' not in fetch_symbols:
        fetch_symbols.append('^GSPC')

    if not fetch_symbols:
        return pd.DataFrame()
        
    try:
        data = yf.download(fetch_symbols, start=start_date, end=end_date, interval="1d")
        
        if isinstance(fetch_symbols, str) or len(fetch_symbols) == 1:
            sym = fetch_symbols[0] if isinstance(fetch_symbols, list) else fetch_symbols
            if 'Adj Close' in data.columns:
                return data[['Adj Close']].rename(columns={'Adj Close': sym})
            else:
                return data[['Close']].rename(columns={'Close': sym})

        # For multiple symbols, select the Adjusted Close prices
        if 'Adj Close' in data.columns:
            historical_df = data['Adj Close']
        else:
            historical_df = data['Close'] 
            
        return historical_df
        
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return pd.DataFrame()

def get_benchmark_returns(benchmark_symbol='^GSPC', start_date=None, end_date=None):
    """Fetches historical data for a benchmark (default: S&P 500) and calculates cumulative returns."""
    if start_date is None:
        start_date = (datetime.now() - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    try:
        data = yf.download(benchmark_symbol, start=start_date, end=end_date, interval="1d")
        
        if data.empty or 'Adj Close' not in data.columns:
            return pd.DataFrame()

        benchmark_prices = data['Adj Close']
        
        benchmark_daily_returns = benchmark_prices.pct_change().dropna()
        benchmark_cumulative_growth = (1 + benchmark_daily_returns).cumprod()
        
        benchmark_df = benchmark_cumulative_growth.reset_index()
        benchmark_df.columns = ['Date', 'Benchmark_Growth']
        
        if not benchmark_df.empty:
            start_value = benchmark_df['Benchmark_Growth'].iloc[0]
            benchmark_df['Benchmark_Growth'] = benchmark_df['Benchmark_Growth'] / start_value

        return benchmark_df

    except Exception as e:
        print(f"Error fetching benchmark data for {benchmark_symbol}: {e}")
        return pd.DataFrame()
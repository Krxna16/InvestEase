import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import logging
import time

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

def fetch_with_retry(symbol, start_date=None, end_date=None, base_retry=True):
    """Fetches yfinance data with a retry limit, auto-appending .NS for Indian stocks."""
    retries = 3
    for attempt in range(retries):
        try:
            data = yf.download(
                symbol, 
                start=start_date, 
                end=end_date, 
                progress=False, 
                threads=False
            )
            if data is not None and not data.empty and not data.isna().all().all():
                return data
            time.sleep((attempt + 1) * 0.5)
        except Exception as e:
            logging.warning(f"Error fetching historical data for {symbol} on attempt {attempt+1}: {e}")
            time.sleep((attempt + 1) * 0.5)
            
    # Auto-append .NS fallback for Indian stocks if no suffix exists
    if base_retry and '.' not in symbol and '^' not in symbol:
        ns_symbol = symbol + ".NS"
        logging.warning(f"Falling back to {ns_symbol} as base symbol {symbol} failed.")
        return fetch_with_retry(ns_symbol, start_date, end_date, base_retry=False)
        
    logging.warning(f"Failed fetch for {symbol} after {retries} retries.")
    return None

@st.cache_data(ttl=3600)
def fetch_data_cached(symbol, start_date, end_date):
    """Cached wrapper around fetch_with_retry."""
    return fetch_with_retry(symbol, start_date, end_date)

def get_historical_prices(symbols, start_date, end_date, include_benchmark=False):
    """
    Fetches adjusted closing historical prices for a list of symbols sequentially.
    Optionally includes the S&P 500 benchmark (^GSPC).
    """
    fetch_symbols = symbols.copy()
    if include_benchmark and '^GSPC' not in fetch_symbols:
        fetch_symbols.append('^GSPC')

    if not fetch_symbols:
        return pd.DataFrame()
        
    compiled_data = {}
    
    for sym in fetch_symbols:
        data = fetch_data_cached(sym, start_date, end_date)
        if data is not None and not data.empty:
            # Squeeze guarantees we flatten possible MultiIndex from yfinance updates
            price_col = data['Adj Close'] if 'Adj Close' in data.columns else data['Close']
            if isinstance(price_col, pd.DataFrame):
                price_col = price_col.squeeze()
            compiled_data[sym] = price_col
            
    if not compiled_data:
        return pd.DataFrame()
        
    historical_df = pd.DataFrame(compiled_data)
    return historical_df

def get_benchmark_returns(benchmark_symbol='^GSPC', start_date=None, end_date=None):
    """Fetches historical data for a benchmark (default: S&P 500) and calculates cumulative returns."""
    if start_date is None:
        start_date = (datetime.now() - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    try:
        data = fetch_data_cached(benchmark_symbol, start_date, end_date)
        
        if data is None or data.empty or ('Adj Close' not in data.columns and 'Close' not in data.columns):
            return pd.DataFrame()

        benchmark_prices = data['Adj Close'] if 'Adj Close' in data.columns else data['Close']
        if isinstance(benchmark_prices, pd.DataFrame):
            benchmark_prices = benchmark_prices.squeeze()
        
        benchmark_daily_returns = benchmark_prices.pct_change().dropna()
        benchmark_cumulative_growth = (1 + benchmark_daily_returns).cumprod()
        
        benchmark_df = benchmark_cumulative_growth.reset_index()
        benchmark_df.columns = ['Date', 'Benchmark_Growth']
        
        if not benchmark_df.empty:
            start_value = benchmark_df['Benchmark_Growth'].iloc[0]
            benchmark_df['Benchmark_Growth'] = benchmark_df['Benchmark_Growth'] / start_value

        return benchmark_df

    except Exception as e:
        logging.warning(f"Error fetching benchmark data for {benchmark_symbol}: {e}")
        return pd.DataFrame()
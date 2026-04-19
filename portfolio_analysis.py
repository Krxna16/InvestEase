import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import gmean
from sklearn.linear_model import LinearRegression 

RISK_FREE_RATE = 0.03 

def calculate_stock_performance(holdings_df, live_prices, stock_betas):
    """
    Calculates current value, cost basis, P/L, gain percentage, 
    and adds the pre-calculated Beta for each stock.
    """
    if holdings_df.empty:
        return pd.DataFrame()

    results = []
    
    for index, row in holdings_df.iterrows():
        symbol = row['symbol']
        quantity = row['quantity']
        purchase_price = row['purchase_price']
        
        current_price = live_prices.get(symbol)
        
        if current_price is None:
            continue
            
        cost_basis = quantity * purchase_price
        current_value = quantity * current_price
        
        profit_loss = current_value - cost_basis
        gain_percent = (profit_loss / cost_basis) * 100 if cost_basis else 0
        
        # Add the Beta value from the dictionary
        beta = stock_betas.get(symbol, 'N/A')

        results.append({
            'id': row['id'],
            'Symbol': symbol,
            'Quantity': quantity,
            'Purchase Price': purchase_price,
            'Current Price': current_price,
            'Cost Basis': cost_basis,
            'Current Value': current_value,
            'Profit/Loss': profit_loss,
            'Gain (%)': gain_percent,
            'Beta': beta,  # NEW COLUMN
            'Purchase Date': row['purchase_date']
        })
        
    return pd.DataFrame(results)

def calculate_stock_beta(historical_df, benchmark_symbol='^GSPC'):
    """
    Calculates the Beta for each stock in the DataFrame against the benchmark.
    Beta = Covariance(Stock Returns, Market Returns) / Variance(Market Returns)
    """
    if historical_df.empty or benchmark_symbol not in historical_df.columns:
        return {}

    market_returns = historical_df[benchmark_symbol].pct_change().dropna()
    market_variance = market_returns.var()
    
    if market_variance == 0:
        return {}
        
    betas = {}
    
    for stock in historical_df.columns:
        if stock == benchmark_symbol:
            betas[stock] = 1.0 # Benchmark always has a Beta of 1.0
            continue
            
        stock_returns = historical_df[stock].pct_change().dropna()
        
        # Align returns to the same dates as the market returns
        aligned_df = pd.DataFrame({
            'Stock': stock_returns, 
            'Market': market_returns
        }).dropna()
        
        if len(aligned_df) < 30: # Need sufficient data points
            betas[stock] = 'N/A'
            continue
            
        # Calculate covariance between stock and market returns
        covariance = aligned_df['Stock'].cov(aligned_df['Market'])
        
        # Calculate Beta
        beta = covariance / market_variance
        betas[stock] = beta
        
    return betas

def calculate_portfolio_summary(performance_df):
    """Calculates the total portfolio value and overall P/L metrics."""
    if performance_df.empty:
        return {
            'Total Cost Basis': 0.0,
            'Total Current Value': 0.0,
            'Total Profit/Loss': 0.0,
            'Overall Gain (%)': 0.0
        }
        
    total_cost = performance_df['Cost Basis'].sum()
    total_value = performance_df['Current Value'].sum()
    total_pl = total_value - total_cost
    overall_gain_percent = (total_pl / total_cost) * 100 if total_cost else 0
    
    return {
        'Total Cost Basis': total_cost,
        'Total Current Value': total_value,
        'Total Profit/Loss': total_pl,
        'Overall Gain (%)': overall_gain_percent
    }

def calculate_time_series_metrics(holdings_df, historical_df):
    """Calculates time-series metrics like Sharpe Ratio and volatility."""
    
    default_metrics = {
        'Annualized Average Return': 0.0,
        'Annualized Volatility (Std Dev)': 0.0,
        'Sharpe Ratio (Risk-Adjusted)': 0.0,
        'Last 7-Day Return': 0.0,
        'Last 30-Day Return': 0.0,
    }

    if holdings_df.empty or historical_df.empty:
        return default_metrics, pd.DataFrame()

    # 1. Defense: Ensure historical_df has a proper DatetimeIndex
    if not isinstance(historical_df.index, pd.DatetimeIndex):
        historical_df.index = pd.to_datetime(historical_df.index, errors='coerce')
        historical_df = historical_df[historical_df.index.notna()]

    if historical_df.empty:
        return default_metrics, pd.DataFrame()

    current_values = holdings_df.set_index('symbol')['quantity'] * historical_df.iloc[-1]
    weights = current_values / current_values.sum()
    
    portfolio_symbols = holdings_df['symbol'].unique().tolist()
    historical_df = historical_df[historical_df.columns.intersection(portfolio_symbols)]

    weights = weights[weights.index.isin(historical_df.columns)].fillna(0)
    
    # Defensive check for zero weight sum
    weight_sum = weights.sum()
    if weight_sum == 0:
        return default_metrics, pd.DataFrame()
        
    weights = weights / weight_sum

    # Ensure strictly sorted chronological order
    historical_df = historical_df.sort_index()
    
    # Fill backwards and forwards strictly guaranteeing no null-gaps when calculating percentage shifts
    historical_df = historical_df.ffill().bfill()
    
    daily_returns = historical_df.pct_change()
    
    # Use min_count=1 to avoid 0.0 for completely NaN rows, then explicitly drop them
    portfolio_daily_returns = (daily_returns * weights).sum(axis=1, min_count=1).dropna()
    
    # Debug logging for the returned array lengths
    print(f"DEBUG [portfolio_analysis]: portfolio_daily_returns length: {len(portfolio_daily_returns)}")
    print(f"DEBUG [portfolio_analysis]: portfolio_daily_returns head:\n{portfolio_daily_returns.head(3)}")
    
    # 2. Defense: Ensure portfolio_daily_returns has a proper DatetimeIndex
    if not isinstance(portfolio_daily_returns.index, pd.DatetimeIndex):
        print(f"DEBUG: Converted portfolio_daily_returns index from {type(portfolio_daily_returns.index)} to DatetimeIndex")
        portfolio_daily_returns.index = pd.to_datetime(portfolio_daily_returns.index, errors='coerce')
    
    # Clean up any bad dates
    portfolio_daily_returns = portfolio_daily_returns[portfolio_daily_returns.index.notna()]
    
    # 3. Defense: Handle empty data safely before resampling
    if portfolio_daily_returns.empty:
        return default_metrics, pd.DataFrame()
    
    ANNUAL_FACTOR = 252 
    
    try:
        # 1 + returns can't be negative for stocks, but gmean throws on negative
        geometric_daily_return = gmean(np.maximum(1 + portfolio_daily_returns, 0.0001)) - 1
    except Exception:
        geometric_daily_return = 0
        
    annualized_return = geometric_daily_return * ANNUAL_FACTOR
    
    annualized_std_dev = portfolio_daily_returns.std() * np.sqrt(ANNUAL_FACTOR)
    
    sharpe_ratio = (annualized_return - RISK_FREE_RATE) / annualized_std_dev if annualized_std_dev else 0

    # 4. Compatibility with latest pandas (Python 3.13)
    # Older pandas used 'M' and 'W', pandas 2.2+ requires 'ME' and 'W-FRI' for end of month/week.
    try:
        weekly_returns = (1 + portfolio_daily_returns).resample('W-FRI').prod() - 1
        monthly_returns = (1 + portfolio_daily_returns).resample('ME').prod() - 1
    except ValueError:
        # Fallback for pandas versions < 2.2
        weekly_returns = (1 + portfolio_daily_returns).resample('W').prod() - 1
        monthly_returns = (1 + portfolio_daily_returns).resample('M').prod() - 1

    metrics = {
        'Annualized Average Return': annualized_return,
        'Annualized Volatility (Std Dev)': annualized_std_dev,
        'Sharpe Ratio (Risk-Adjusted)': sharpe_ratio,
        'Last 7-Day Return': weekly_returns.iloc[-1] if not weekly_returns.empty else 0,
        'Last 30-Day Return': monthly_returns.iloc[-1] if not monthly_returns.empty else 0,
    }
    
    cumulative_returns = (1 + portfolio_daily_returns).cumprod()
    
    cumulative_returns_df = cumulative_returns.reset_index()
    cumulative_returns_df.columns = ['Date', 'Cumulative_Growth']
    
    return metrics, cumulative_returns_df

def predict_stock_growth(cumulative_returns_df, days_to_predict=30, historical_window=60):
    """Performs a basic linear regression forecast on the cumulative returns."""
    if cumulative_returns_df.empty or len(cumulative_returns_df) < historical_window:
        return pd.DataFrame()

    data = cumulative_returns_df.tail(historical_window).copy()
    data['Days'] = np.arange(len(data))
    X = data[['Days']].values
    y = data['Cumulative_Growth'].values

    model = LinearRegression()
    model.fit(X, y)
    
    last_day_index = data['Days'].iloc[-1]
    future_days = np.arange(last_day_index + 1, last_day_index + 1 + days_to_predict).reshape(-1, 1)

    predicted_growth = model.predict(future_days)
    
    last_date = data['Date'].iloc[-1]
    prediction_dates = pd.date_range(start=last_date, periods=days_to_predict + 1, freq='B')[1:]
    
    prediction_df = pd.DataFrame({
        'Date': prediction_dates,
        'Cumulative_Growth': predicted_growth
    })
    
    return prediction_df
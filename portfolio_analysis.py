import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import gmean
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score


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

def evaluate_models(X_train, y_train, X_test, y_test):
    """Evaluates Linear Regression and Random Forest models natively resolving RMSE and R2 parameters."""
    # Linear Regression
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    lr_preds = lr_model.predict(X_test)
    lr_rmse = np.sqrt(mean_squared_error(y_test, lr_preds))
    lr_r2 = r2_score(y_test, lr_preds)
    
    # Random Forest Regressor (Anti-overfit bounds adjusted for deeper pattern recognition)
    rf_model = RandomForestRegressor(n_estimators=150, max_depth=10, min_samples_split=5, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_preds))
    rf_r2 = r2_score(y_test, rf_preds)
    
    return {
        "Linear Regression": {"rmse": lr_rmse, "r2": lr_r2, "model": lr_model},
        "Random Forest": {"rmse": rf_rmse, "r2": rf_r2, "model": rf_model}
    }

def predict_stock_growth(cumulative_returns_df, days_to_predict=30, historical_window=60):
    """
    Performs time-series aware evaluation against dual regression models yielding structured prediction datasets conditionally.
    """
    if cumulative_returns_df.empty or len(cumulative_returns_df) < historical_window:
        return None

    data = cumulative_returns_df.tail(historical_window).copy()
    
    # Feature Engineering strictly isolated to prior data to prevent structural data leakage
    data['lag_1'] = data['Cumulative_Growth'].shift(1)
    data['lag_2'] = data['Cumulative_Growth'].shift(2)
    data['lag_3'] = data['Cumulative_Growth'].shift(3)
    
    data['returns'] = data['Cumulative_Growth'].pct_change().shift(1)
    data['rolling_mean'] = data['Cumulative_Growth'].rolling(window=5).mean().shift(1)
    data['volatility_5'] = data['Cumulative_Growth'].rolling(window=5).std().shift(1)
    data['momentum'] = data['Cumulative_Growth'].shift(1) - data['Cumulative_Growth'].shift(3)
    
    data = data.dropna()
    if len(data) < 20:  # Failsafe if data is extremely disjointed
        return None
        
    X = data[['lag_1', 'lag_2', 'lag_3', 'rolling_mean', 'returns', 'volatility_5', 'momentum']].values
    y = data['Cumulative_Growth'].values

    # Time-series aware split (80/20 configuration avoiding randomized leakage)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    try:
        evaluation_results = evaluate_models(X_train, y_train, X_test, y_test)
    except Exception as e:
        print(f"DEBUG: Model configuration failed: {e}")
        return None

    best_model_name = "Random Forest" if evaluation_results["Random Forest"]["rmse"] < evaluation_results["Linear Regression"]["rmse"] else "Linear Regression"

    last_date = data['Date'].iloc[-1]
    prediction_dates = pd.date_range(start=last_date, periods=days_to_predict + 1, freq='B')[1:]
    
    output_payload = {
        "best_model": best_model_name,
        "metrics": evaluation_results
    }
    
    # Generate explicit forecast vectors bound to retrained contexts spanning the FULL dataset
    for model_name, metrics in evaluation_results.items():
        # Retrain strictly on complete historical data for valid extrapolation
        final_model = LinearRegression() if model_name == "Linear Regression" else RandomForestRegressor(n_estimators=150, max_depth=10, min_samples_split=5, random_state=42)
        final_model.fit(X, y)
        
        predicted_growth = []
        current_y = y[-1]
        y_window = list(data['Cumulative_Growth'].values[-10:])
        
        # Autoregressive extrapolation recursively maintaining feature architecture into unknowns
        for i in range(days_to_predict):
            f_lag_1 = y_window[-1]
            f_lag_2 = y_window[-2]
            f_lag_3 = y_window[-3]
            f_returns = (y_window[-1] - y_window[-2]) / y_window[-2] if y_window[-2] != 0 else 0
            f_mean = np.mean(y_window[-5:])
            f_volatility = np.std(y_window[-5:], ddof=1) if len(y_window) >= 5 else 0
            f_momentum = y_window[-1] - y_window[-3]
            
            features_t = [f_lag_1, f_lag_2, f_lag_3, f_mean, f_returns, f_volatility, f_momentum]
            
            next_y = final_model.predict([features_t])[0]
            
            # Injecting realistic simulated market noise
            raw_noise = np.random.normal(0, f_volatility * 0.3 if f_volatility > 0 else 0.005)
            # Apply dynamic clipping directly limiting erratic standard variation explosions
            cap_limit = f_volatility * 2 if f_volatility > 0 else 0.015
            noise = np.clip(raw_noise, -cap_limit, cap_limit)
            next_y += noise
            
            # Stabilize Linear Regression prediction to prevent exponential explosion
            if model_name == "Linear Regression":
                max_val = current_y * 1.05
                min_val = current_y * 0.95
                next_y = max(min_val, min(next_y, max_val))
                
            predicted_growth.append(next_y)
            y_window.append(next_y)
            y_window.pop(0)  # Keep window length 10
            current_y = next_y
            
        predicted_growth = np.array(predicted_growth)
        
        # Calculate isolated historical volatility dynamically tracking pct shifts vs absolute sizes
        historical_volatility = np.std(data['Cumulative_Growth'].pct_change().dropna()) if len(data) > 0 else 0.02
        time_steps = np.arange(1, days_to_predict + 1)
        
        # Proper scaling: Confidence Bound geometrically expands independently along volatility loops
        cumulative_uncertainty = historical_volatility * np.sqrt(time_steps)
        
        prediction_df = pd.DataFrame({
            'Date': prediction_dates,
            'Cumulative_Growth': predicted_growth,
            'Upper_Bound': predicted_growth + cumulative_uncertainty,
            'Lower_Bound': predicted_growth - cumulative_uncertainty
        })
        output_payload[model_name] = prediction_df
        
    return output_payload
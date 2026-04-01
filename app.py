import streamlit as st
import pandas as pd
import numpy as np
import base64
from datetime import datetime
import os

# Import custom modules
import database as db
import data_fetch as dfetch
import portfolio_analysis as analysis
import visualization as viz

# --- CONFIGURATION ---
st.set_page_config(
    page_title="InvestEase",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- HELPER FUNCTIONS ---

@st.cache_data
def convert_df_to_csv(df):
    """Converts DataFrame to CSV for download."""
    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    return df.to_csv(index=False).encode('utf-8')

def format_currency(value):
    """Formats a number as US currency."""
    return f"${value:,.2f}"

def format_percentage(value):
    """Formats a number as a percentage."""
    return f"{value:,.2f}%"

def format_beta(value):
    """Formats Beta to 2 decimal places or displays N/A."""
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return value

def color_code_pl(value):
    """Returns the color (red or green) based on profit/loss value."""
    if value >= 0:
        return 'green'
    else:
        return 'red'

@st.cache_data(ttl=300) # Cache for 5 minutes
def fetch_and_calculate_portfolio(holdings_df_json):
    """
    Fetches live data and performs all necessary calculations, including sector data.
    """
    import io
    holdings_df = pd.read_json(io.StringIO(holdings_df_json))
    
    perf_df, summary, cumulative_growth_df, metrics, benchmark_df = pd.DataFrame(), {}, pd.DataFrame(), {}, pd.DataFrame()
    stock_betas = {}
        
    if holdings_df.empty:
        return perf_df, summary, cumulative_growth_df, metrics, benchmark_df, stock_betas
        
    symbols = holdings_df['symbol'].unique().tolist()
    
    # 1. Fetch live prices and sector info
    live_prices = {}
    sector_map = {}
    for symbol in symbols:
        price = dfetch.get_live_price(symbol)
        sector = dfetch.get_sector_info(symbol)
        
        if price is not None:
            live_prices[symbol] = price
            sector_map[symbol] = sector
    
    holdings_df['symbol'] = holdings_df['symbol'].apply(lambda x: x if live_prices.get(x) is not None else None)
    holdings_df = holdings_df.dropna(subset=['symbol'])
    
    if holdings_df.empty:
        return perf_df, summary, cumulative_growth_df, metrics, benchmark_df, stock_betas
    
    # Add Sector to holdings_df
    holdings_df['Sector'] = holdings_df['symbol'].map(sector_map).fillna('N/A')

    # 2. Define date range based on oldest purchase or 1 year
    if not holdings_df.empty:
        earliest_purchase_date = pd.to_datetime(holdings_df['purchase_date'], errors='coerce').min()
    else:
        earliest_purchase_date = (datetime.now() - pd.DateOffset(years=1))

    one_year_ago = datetime.now() - pd.DateOffset(years=1)
    
    start_date = max(earliest_purchase_date, one_year_ago).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 3. Fetch historical prices (INCLUDING BENCHMARK)
    historical_df = dfetch.get_historical_prices(symbols, start_date, end_date, include_benchmark=True)
    benchmark_df = dfetch.get_benchmark_returns('^GSPC', start_date, end_date)
    
    # 4. Calculate Beta
    stock_betas = analysis.calculate_stock_beta(historical_df, benchmark_symbol='^GSPC')

    # 5. Calculate individual stock performance (now includes Sector and Beta)
    perf_df = analysis.calculate_stock_performance(holdings_df, live_prices, stock_betas)
    perf_df['Sector'] = perf_df['Symbol'].map(sector_map).fillna('N/A') # Re-map sector to performance DF

    summary = analysis.calculate_portfolio_summary(perf_df)

    # 6. Calculate time-series metrics
    metrics, cumulative_growth_df = analysis.calculate_time_series_metrics(
        holdings_df, historical_df
    )
    
    return perf_df, summary, cumulative_growth_df, metrics, benchmark_df, stock_betas

# --- STREAMLIT PAGES ---

def page_home():
    """Home page with welcome and overall summary."""
    st.title("🏡 Portfolio Evaluation Dashboard")
    st.markdown("""
        Welcome to your local stock portfolio evaluation tool.
    """)
    st.divider()

    holdings_df = db.get_all_holdings()
    
    if holdings_df.empty:
        st.warning("Your portfolio is empty. Navigate to **Add/Manage Holdings** to get started!")
        return
        
    # Run the full calculation
    with st.spinner('Fetching live prices and historical data...'):
        perf_df, summary, cumulative_growth_df, metrics, benchmark_df, _ = fetch_and_calculate_portfolio(holdings_df.to_json())

    if perf_df.empty:
        st.warning("Could not fetch data for any of your holdings. Check symbols and try again.")
        return
    
    st.header("Overall Portfolio Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_pl_formatted = format_currency(summary['Total Profit/Loss'])
    overall_gain_formatted = format_percentage(summary['Overall Gain (%)'])
    pl_color = color_code_pl(summary['Total Profit/Loss'])
    
    pl_display = f"""
    <div style='text-align: center; font-size: 20px;'>
        Total Profit/Loss
    </div>
    <div style='text-align: center; font-size: 36px; color: {pl_color}; font-weight: bold;'>
        {total_pl_formatted}
    </div>
    <div style='text-align: center; font-size: 16px; color: {pl_color};'>
        {overall_gain_formatted}
    </div>
    """
    
    col1.metric("Total Current Value", format_currency(summary['Total Current Value']), delta=None, delta_color="off")
    col2.markdown(pl_display, unsafe_allow_html=True)
    col3.metric("Annualized Return", format_percentage(metrics['Annualized Average Return'] * 100))
    col4.metric("Sharpe Ratio (Risk-Adj)", f"{metrics['Sharpe Ratio (Risk-Adjusted)']:.2f}")

    st.markdown("---")
    
    st.header("Visual Analysis: Diversification Comparison")
    
    col_cost_basis, col_current_value = st.columns(2)
    
    with col_cost_basis:
        st.subheader("Where You Put Money (Cost Basis)")
        st.plotly_chart(viz.create_sector_distribution_chart(perf_df, value_type='Cost Basis'), use_container_width=True)
        st.caption("Shows initial investment allocation by sector.")
    
    with col_current_value:
        st.subheader("Where Your Money Is Now (Current Value)")
        st.plotly_chart(viz.create_sector_distribution_chart(perf_df, value_type='Current Value'), use_container_width=True)
        st.caption("Shows current allocation and sector growth/loss.")


    st.subheader("Growth History")
    st.plotly_chart(viz.create_growth_line_chart(cumulative_growth_df, benchmark_df), use_container_width=True)


def page_add_manage():
    """Page for adding, viewing, editing, and deleting holdings."""
    st.title("➕ Manage Holdings")

    st.header("Add New Stock Holding")
    with st.form("add_holding_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        symbol = col1.text_input("Stock Symbol (e.g., MSFT)", max_chars=10).upper()
        quantity = col2.number_input("Quantity", min_value=0.01, step=0.01, format="%.2f")
        
        col3, col4 = st.columns(2)
        purchase_price = col3.number_input("Purchase Price", min_value=0.01, step=0.01, format="%.2f")
        purchase_date = col4.date_input("Purchase Date", max_value=datetime.now())
        
        submitted = st.form_submit_button("Add Holding")
        
        if submitted:
            if symbol and quantity > 0 and purchase_price > 0:
                try:
                    db.add_holding(symbol, quantity, purchase_price, purchase_date.strftime('%Y-%m-%d'))
                    st.success(f"Added {quantity} shares of {symbol}!")
                    fetch_and_calculate_portfolio.clear()
                    st.rerun() 
                except Exception as e:
                    st.error(f"Error adding holding: {e}")
            else:
                st.error("Please fill in all fields with valid data.")

    st.divider()
    
    st.header("Current Portfolio Holdings")
    holdings_df = db.get_all_holdings()

    if holdings_df.empty:
        st.info("No holdings recorded.")
        return

    display_df = holdings_df[['id', 'symbol', 'quantity', 'purchase_price', 'purchase_date']].copy()
    display_df.columns = ['ID', 'Symbol', 'Quantity', 'Price', 'Date']
    
    edited_df = st.data_editor(
        display_df,
        key="holdings_editor",
        disabled=('ID',),
        use_container_width=True
    )

    if st.button("Save/Update Changes"):
        try:
            for index, row in edited_df.iterrows():
                db.update_holding(
                    row['ID'], 
                    row['Symbol'], 
                    row['Quantity'], 
                    row['Price'], 
                    str(row['Date'])
                )
            st.success("Portfolio holdings updated successfully!")
            fetch_and_calculate_portfolio.clear() 
            st.rerun() 
        except Exception as e:
            st.error(f"Error updating holdings: {e}")
            
    st.markdown("---")
    st.subheader("Delete Holding")
    with st.form("delete_holding_form"):
        holding_ids = holdings_df['id'].tolist()
        id_to_delete = st.selectbox("Select ID to Delete", options=holding_ids)
        delete_submitted = st.form_submit_button("Delete Holding")
        
        if delete_submitted and id_to_delete:
            try:
                db.delete_holding(id_to_delete)
                st.success(f"Holding with ID {id_to_delete} deleted.")
                fetch_and_calculate_portfolio.clear() 
                st.rerun() 
            except Exception as e:
                st.error(f"Error deleting holding: {e}")

def page_analysis():
    """Detailed performance analysis and metrics page."""
    st.title("📈 Performance Analysis")
    
    holdings_df = db.get_all_holdings()
    
    if holdings_df.empty:
        st.warning("Your portfolio is empty. Add holdings to see analysis.")
        return

    perf_df, summary, cumulative_growth_df, metrics, benchmark_df, stock_betas = fetch_and_calculate_portfolio(holdings_df.to_json())

    if perf_df.empty:
        return

    st.header("Stock-by-Stock Performance")
    
    # Format the columns for display
    display_perf_df = perf_df.copy()
    for col in ['Purchase Price', 'Current Price', 'Cost Basis', 'Current Value', 'Profit/Loss']:
        display_perf_df[col] = display_perf_df[col].apply(format_currency)
    display_perf_df['Gain (%)'] = display_perf_df['Gain (%)'].apply(format_percentage)
    
    # Format the Beta column
    display_perf_df['Beta'] = display_perf_df['Beta'].apply(format_beta)
    
    # Include Sector in the detailed table
    display_perf_df = display_perf_df[['Symbol', 'Sector', 'Quantity', 'Purchase Price', 'Current Price', 'Cost Basis', 'Current Value', 'Profit/Loss', 'Gain (%)', 'Beta', 'Purchase Date']]
    display_perf_df = display_perf_df.drop(columns=['id'], errors='ignore')
    
    st.dataframe(display_perf_df, use_container_width=True)
    st.caption("Beta measures volatility relative to the S&P 500: Beta > 1.0 means higher risk/volatility.")

    st.divider()

    st.header("Risk-Adjusted Metrics & Returns")
    
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    col1.metric("Annualized Return", format_percentage(metrics['Annualized Average Return'] * 100))
    col2.metric("Annualized Volatility (Std Dev)", format_percentage(metrics['Annualized Volatility (Std Dev)'] * 100))
    col3.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio (Risk-Adjusted)']:.2f}")

    col4.metric("Last 7-Day Return", format_percentage(metrics['Last 7-Day Return'] * 100))
    col5.metric("Last 30-Day Return", format_percentage(metrics['Last 30-Day Return'] * 100))
    col6.metric("Total Cost Basis", format_currency(summary['Total Cost Basis']))
    
    st.markdown("""
    ---
    *Sharpe Ratio* measures return per unit of risk (volatility). A higher ratio is better.
    """)


def page_prediction():
    """Page for displaying portfolio forecast."""
    st.title("🔮 Portfolio Forecast (30-Day Outlook)")
    
    st.warning("""
        **Disclaimer:** This is a basic **Linear Regression** forecast based purely on your portfolio's recent historical returns. 
    """)
    
    holdings_df = db.get_all_holdings()
    
    if holdings_df.empty:
        st.warning("Your portfolio is empty. Add holdings to enable prediction.")
        return

    perf_df, summary, cumulative_growth_df, metrics, benchmark_df, _ = fetch_and_calculate_portfolio(holdings_df.to_json())
    
    if cumulative_growth_df.empty or len(cumulative_growth_df) < 60:
        st.error("Cannot perform prediction. Historical data is insufficient (need at least 60 days of data).")
        return

    prediction_df = analysis.predict_stock_growth(cumulative_growth_df, days_to_predict=30, historical_window=60)

    if prediction_df.empty:
        st.error("Prediction failed. Ensure you have sufficient historical data (typically 60+ trading days).")
        return

    st.header("Growth Trajectory: Historical vs. Forecast")
    st.plotly_chart(viz.create_prediction_line_chart(cumulative_growth_df, prediction_df), use_container_width=True)

    st.divider()
    
    st.header("Prediction Summary")
    
    last_historical_value = cumulative_returns_df['Cumulative_Growth'].iloc[-1]
    final_predicted_value = prediction_df['Cumulative_Growth'].iloc[-1]
    
    forecasted_gain_factor = final_predicted_value / last_historical_value
    forecasted_gain_percent = (forecasted_gain_factor - 1) * 100
    
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Current Growth Factor", f"{last_historical_value:.4f}")
    col2.metric(
        "Predicted Factor (30 Days)", 
        f"{final_predicted_value:.4f}",
        f"{forecasted_gain_factor - 1:.2%} change"
    )
    col3.metric("Projected 30-Day Return", format_percentage(forecasted_gain_percent))
    
    
def page_import_export():
    """Page for importing and exporting portfolio data."""
    st.title("📤 Import / Export Data")

    st.header("Import Portfolio (CSV)")
    uploaded_file = st.file_uploader(
        "Upload a CSV file with columns: Symbol, Quantity, Purchase_Price, Purchase_Date",
        type=['csv']
    )

    if uploaded_file is not None:
        if st.button("Import Data (Replaces current portfolio)"):
            temp_file_path = "temp_uploaded_portfolio.csv"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            success, message = db.import_csv(temp_file_path)
            
            os.remove(temp_file_path)

            if success:
                st.success(message + " Navigate to **Manage Holdings** to verify.")
                fetch_and_calculate_portfolio.clear() 
            else:
                st.error(message)

    st.divider()

    st.header("Export Portfolio (CSV)")
    holdings_df = db.get_all_holdings()

    if holdings_df.empty:
        st.warning("No data to export.")
    else:
        csv_data = convert_df_to_csv(holdings_df)
        st.download_button(
            label="Download Current Portfolio as CSV",
            data=csv_data,
            file_name="my_stock_portfolio.csv",
            mime="text/csv"
        )
        
        st.subheader("Current Data Format (Example)")
        st.dataframe(holdings_df.drop(columns=['id']), use_container_width=True)


# --- MAIN APP LOGIC ---

PAGES = {
    "Home & Overview": page_home,
    "Add/Manage Holdings": page_add_manage,
    "Detailed Analysis": page_analysis,
    "Prediction": page_prediction, 
    "Import/Export Data": page_import_export,
}

# Add custom project header at the top of the sidebar
st.sidebar.markdown(
    "<h1 style='text-align: center; font-size: 24px; color: #4CAF50;'>📊 InvestEase</h1>", 
    unsafe_allow_html=True
)
st.sidebar.markdown("---") 

st.sidebar.title("Navigation Menu")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

page = PAGES[selection]
page()
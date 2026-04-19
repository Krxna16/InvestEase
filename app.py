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
import authentication as auth

# --- CONFIGURATION ---
st.set_page_config(
    page_title="InvestEase",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STRICT RENDER SEPARATION (AUTHENTICATION) ---
# If user is not logged in, render login UI and stop execution immediately
if not auth.render_login_ui():
    st.stop()

def inject_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif !important;
            }
            
            /* --- KEYFRAMES --- */
            @keyframes gradientBG {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            @keyframes glowPulse {
                0% { opacity: 0.3; filter: blur(4px); }
                100% { opacity: 0.8; filter: blur(6px); }
            }
            @keyframes slideInPill {
                0% { opacity: 0; transform: scaleX(0.8) translateY(2px); }
                100% { opacity: 1; transform: scaleX(1) translateY(0); }
            }
            @keyframes fadeInUp {
                0% { opacity: 0; transform: translateY(15px); }
                100% { opacity: 1; transform: translateY(0); }
            }

            /* Main background */
            .stApp {
                background: linear-gradient(-45deg, #0B0F19, #0f1626, #141226, #0B0F19) !important;
                background-size: 400% 400% !important;
                animation: gradientBG 15s ease infinite !important;
                color: #ffffff;
            }
            
            /* Hide Streamlit headers and footers */
            header {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Sidebar Styling */
            [data-testid="stSidebar"], [data-testid="collapsedControl"] {
                display: none !important;
            }
            
            /* --- MASTER NAVBAR CONTAINER (Logo + Tabs + Profile) --- */
            div[data-testid="stHorizontalBlock"]:has(.logo-marker) {
                background: rgba(15, 20, 30, 0.6) !important;
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.05); /* subtle fallback */
                padding: 12px 24px;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4), 0 0 20px rgba(59, 130, 246, 0.15); /* Soft outer glow */
                align-items: center;
                margin-bottom: 2rem;
                position: relative;
                isolation: isolate;
            }
            /* Glowing gradient pseudo-border */
            div[data-testid="stHorizontalBlock"]:has(.logo-marker)::after {
                content: "";
                position: absolute;
                inset: -1px;
                border-radius: 17px;
                background: linear-gradient(90deg, #3B82F6, #8B5CF6, #06B6D4);
                z-index: -1;
                animation: glowPulse 3s infinite alternate;
            }

            /* --- UNIFIED TABS INNER CONTAINER (Center Section) --- */
            div[data-testid="stHorizontalBlock"]:has(.tab-marker):not(:has(.logo-marker)) {
                background: rgba(30, 40, 50, 0.4) !important;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                padding: 4px;
                gap: 0 !important;
            }
            
            /* Remove column gaps strictly inside inner nav container */
            div[data-testid="stHorizontalBlock"]:has(.tab-marker):not(:has(.logo-marker)) > div[data-testid="column"] {
                width: auto !important;
                flex: 1 1 0% !important;
            }
            
            /* Button tab design inside unified container */
            div[data-testid="stHorizontalBlock"]:has(.tab-marker):not(:has(.logo-marker)) .stButton>button {
                background: transparent !important;
                border: none !important;
                border-radius: 26px !important;
                box-shadow: none !important;
                color: #9CA3AF;
                font-weight: 500;
                transition: all 0.3s ease;
                padding: 8px 0px;
                width: 100%;
            }
            
            /* Hover style */
            div[data-testid="stHorizontalBlock"]:has(.tab-marker):not(:has(.logo-marker)) .stButton>button:hover:not([kind="primary"]) {
                color: #FFFFFF !important;
                background: rgba(255, 255, 255, 0.05) !important;
                transform: none; /* Block jumping inside unified pill */
            }
            
            /* Active Tab Style with Slide Animation */
            div[data-testid="stHorizontalBlock"]:has(.tab-marker):not(:has(.logo-marker)) .stButton>button[kind="primary"] {
                color: #FFFFFF !important;
                background: linear-gradient(90deg, rgba(59, 130, 246, 0.9), rgba(6, 182, 212, 0.9)) !important;
                box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4) !important;
                animation: slideInPill 0.3s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
            }
            
            /* Clear ::after underlines completely */
            div[data-testid="stHorizontalBlock"]:has(.tab-marker):not(:has(.logo-marker)) .stButton>button::after {
                display: none !important;
            }

            /* Glassmorphism Metric Cards & Section FadeIn */
            .glass-card {
                position: relative;
                isolation: isolate;
                background: rgba(20, 25, 35, 0.6);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                padding: 20px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.4s ease;
                margin-bottom: 1rem;
                animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            
            /* Advanced Gradient Glow Hover on Glass Cards */
            .glass-card::before {
                content: "";
                position: absolute;
                inset: 0;
                border-radius: 16px;
                padding: 1px;
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.6), rgba(139, 92, 246, 0.2));
                -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                -webkit-mask-composite: xor;
                mask-composite: exclude;
                opacity: 0;
                transition: opacity 0.4s ease;
                z-index: -1;
            }
            .glass-card:hover::before {
                opacity: 1;
            }
            .glass-card:hover {
                transform: scale(1.02) translateY(-4px);
                border-color: transparent;
                box-shadow: 0 12px 40px 0 rgba(59, 130, 246, 0.25);
            }
            
            .metric-label {
                font-size: 14px;
                color: #9CA3AF;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
                font-weight: 500;
            }
            .metric-value {
                font-size: 28px;
                font-weight: 700;
            }
            
            .profit { color: #22C55E; text-shadow: 0 0 12px rgba(34, 197, 94, 0.5); }
            .loss { color: #EF4444; text-shadow: 0 0 12px rgba(239, 68, 68, 0.5); }
            .neutral { color: #3B82F6; }
            
            /* Dataframes styling */
            [data-testid="stDataFrame"] {
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.08);
            }
            
            /* User profile pill globally styled */
            .user-pill {
                background: rgba(20, 25, 35, 0.8);
                backdrop-filter: blur(10px);
                padding: 6px 16px;
                border-radius: 24px;
                border: 1px solid rgba(255,255,255,0.08);
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                width: 100%;
                height: 100%;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: border 0.3s ease;
            }
            .user-pill:hover {
                border-color: rgba(59, 130, 246, 0.4);
            }
            .user-avatar {
                background: linear-gradient(135deg, #3B82F6, #22C55E);
                border-radius: 50%;
                width: 26px;
                height: 26px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 13px;
                font-weight: bold;
                color: white;
            }
            .user-name {
                color: #E5E7EB;
                font-weight: 600;
                font-size: 14px;
            }
            
            /* Logout Button Specifically Targeting Last Nav Col */
            div[data-testid="column"]:has(.logout-marker) .stButton>button {
                background: rgba(239, 68, 68, 0.1) !important;
                color: #EF4444 !important;
                border: 1px solid rgba(239, 68, 68, 0.3) !important;
                border-radius: 20px !important;
                box-shadow: none !important;
            }
            div[data-testid="column"]:has(.logout-marker) .stButton>button:hover {
                background: rgba(239, 68, 68, 0.2) !important;
                box-shadow: 0 0 15px rgba(239, 68, 68, 0.2) !important;
                transform: translateY(-2px);
            }
            div[data-testid="column"]:has(.logout-marker) .stButton>button::after {
                display: none !important;
            }
            
            /* Sticky Header simulation via block targeting */
            [data-testid="block-container"] {
                padding-top: 1rem;
            }
            
            /* --- Strict Dropdown (Non-Editable) --- */
            /* Force selectboxes to look and act like strict dropdowns, forbidding text typing */
            div[data-baseweb="select"] input {
                caret-color: transparent !important;
                pointer-events: none !important;
            }
            div[data-baseweb="select"] {
                cursor: pointer !important;
            }
        </style>
    """, unsafe_allow_html=True)

def create_metric_card(title, value, is_profit=None, icon=""):
    """Generates HTML for a custom glassmorphism metric card."""
    color_class = "neutral"
    if is_profit is True:
        color_class = "profit"
    elif is_profit is False:
        color_class = "loss"
        
    html = f"""
    <div class="glass-card">
        <div class="metric-label">{icon} {title}</div>
        <div class="metric-value {color_class}">{value}</div>
    </div>
    """
    return html

# Execute CSS injection globally
inject_custom_css()

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

def safe_metric(value, is_pct=True):
    """Formats a metric safely, returning 'N/A' if None or exactly 0."""
    if value is None or value == 0:
        return "N/A"
    return format_percentage(value * 100) if is_pct else f"{value:.2f}"

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
    
    # Use min() to get the full historical range if older than 1 year, 
    # BUT if recent, still fetch at least 1 year for predictions!
    start_date = min(earliest_purchase_date, one_year_ago).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Debug logging for date range
    print(f"DEBUG [Data Fetch]: min_date: {start_date}, max_date: {end_date}")
    
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

    holdings_df = db.get_all_holdings(st.session_state['user_id'])
    
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
    
    # Debug trace of metrics
    print(f"DEBUG: metrics keys loaded: {metrics.keys()}")
    
    pl_display = create_metric_card("Total Profit/Loss", total_pl_formatted, is_profit=(summary['Total Profit/Loss'] >= 0), icon="💎")
    
    col1.markdown(create_metric_card("Total Current Value", format_currency(summary['Total Current Value']), icon="💰"), unsafe_allow_html=True)
    col2.markdown(pl_display, unsafe_allow_html=True)
    col3.markdown(create_metric_card("Annualized Return", safe_metric(metrics.get('Annualized Average Return', 0), is_pct=True), is_profit=(metrics.get('Annualized Average Return', 0) >= 0), icon="📈"), unsafe_allow_html=True)
    col4.markdown(create_metric_card("Sharpe Ratio (Risk-Adj)", safe_metric(metrics.get('Sharpe Ratio (Risk-Adjusted)', 0), is_pct=False), icon="⚖️"), unsafe_allow_html=True)

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
                    db.add_holding(
                        st.session_state['user_id'],
                        symbol, 
                        quantity, 
                        purchase_price, 
                        purchase_date.strftime('%Y-%m-%d')
                    )
                    st.toast(f"Added {quantity} shares of {symbol}!", icon="✅")
                    fetch_and_calculate_portfolio.clear()
                    st.rerun() 
                except Exception as e:
                    st.toast(f"Error adding holding: {e}", icon="⚠️")
            else:
                st.toast("Please fill in all fields with valid data.", icon="⚠️")

    st.divider()
    
    st.header("Current Portfolio Holdings")
    holdings_df = db.get_all_holdings(st.session_state['user_id'])

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
                    st.session_state['user_id'],
                    row['ID'], 
                    row['Symbol'], 
                    row['Quantity'], 
                    row['Price'], 
                    str(row['Date'])
                )
            st.toast("Portfolio holdings updated successfully!", icon="✅")
            fetch_and_calculate_portfolio.clear() 
            st.rerun() 
        except Exception as e:
            st.toast(f"Error updating holdings: {e}", icon="⚠️")
            
    st.markdown("---")
    st.subheader("Delete Holding")
    with st.form("delete_holding_form"):
        holding_ids = holdings_df['id'].tolist()
        id_to_delete = st.selectbox("Select ID to Delete", options=holding_ids)
        delete_submitted = st.form_submit_button("Delete Holding")
        
        if delete_submitted and id_to_delete:
            try:
                db.delete_holding(st.session_state['user_id'], id_to_delete)
                st.toast(f"Holding with ID {id_to_delete} deleted.", icon="✅")
                fetch_and_calculate_portfolio.clear() 
                st.rerun() 
            except Exception as e:
                st.toast(f"Error deleting holding: {e}", icon="⚠️")

def page_analysis():
    """Detailed performance analysis and metrics page."""
    st.title("📈 Performance Analysis")
    
    holdings_df = db.get_all_holdings(st.session_state['user_id'])
    
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
    
    # Debug trace for detail analysis
    print(f"DEBUG [page_analysis]: metrics keys: {metrics.keys()}")
    
    col1.markdown(create_metric_card("Annualized Return", safe_metric(metrics.get('Annualized Average Return', 0), is_pct=True), is_profit=(metrics.get('Annualized Average Return', 0) >= 0), icon="📈"), unsafe_allow_html=True)
    col2.markdown(create_metric_card("Annual. Volatility (Std Dev)", safe_metric(metrics.get('Annualized Volatility (Std Dev)', 0), is_pct=True), icon="📉"), unsafe_allow_html=True)
    col3.markdown(create_metric_card("Sharpe Ratio", safe_metric(metrics.get('Sharpe Ratio (Risk-Adjusted)', 0), is_pct=False), icon="⚖️"), unsafe_allow_html=True)

    col4.markdown(create_metric_card("Last 7-Day Return", safe_metric(metrics.get('Last 7-Day Return', 0), is_pct=True), is_profit=(metrics.get('Last 7-Day Return', 0) >= 0), icon="📅"), unsafe_allow_html=True)
    col5.markdown(create_metric_card("Last 30-Day Return", safe_metric(metrics.get('Last 30-Day Return', 0), is_pct=True), is_profit=(metrics.get('Last 30-Day Return', 0) >= 0), icon="🗓️"), unsafe_allow_html=True)
    col6.markdown(create_metric_card("Total Cost Basis", format_currency(summary.get('Total Cost Basis', 0)), icon="💵"), unsafe_allow_html=True)
    
    st.markdown("""
    ---
    *Sharpe Ratio* measures return per unit of risk (volatility). A higher ratio is better.
    """)


def page_prediction():
    """Page for displaying portfolio forecast."""
    st.title("🔮 Portfolio Forecast (30-Day Outlook)")
    
    holdings_df = db.get_all_holdings(st.session_state['user_id'])
    
    if holdings_df.empty:
        st.warning("Your portfolio is empty. Add holdings to enable prediction.")
        return

    perf_df, summary, cumulative_growth_df, metrics, benchmark_df, _ = fetch_and_calculate_portfolio(holdings_df.to_json())
    
    if cumulative_growth_df.empty:
        st.error("Cannot perform prediction. Historical data is completely missing.")
        return
        
    if len(cumulative_growth_df) < 20:
        st.warning("⚠️ Very small dataset detected. Prediction requires more historical data to generate reliable structural trends.")
        return
        
    if len(cumulative_growth_df) < 60:
        st.info("ℹ️ Dataset contains less than 60 days. Forecast may be highly sensitive to short-term variance.")

    try:
        prediction_results = analysis.predict_stock_growth(cumulative_growth_df, days_to_predict=30, historical_window=60)
    except Exception as e:
        st.error(f"Prediction logic encountered a critical boundary error: {e}")
        return

    if not prediction_results:
        st.error("Prediction failed. Feature generation could not complete reliably given incoming price action limits.")
        return

    best_model = prediction_results["best_model"]
    
    st.header("⚙️ Model Comparison & Selection")
    col_sel, col_metrics = st.columns([1, 2])
    
    with col_sel:
        st.success(f"🏆 Best Auto-Selected Model:\n**{best_model}**")
        selected_model = st.selectbox(
            "Select Prediction Model:", 
            ["Linear Regression", "Random Forest"],
            index=0 if best_model == "Linear Regression" else 1
        )
        
        # Calculate algorithmic confidence natively mapping absolute underlying trend variances
        obs_vol = cumulative_growth_df['Cumulative_Growth'].pct_change().std()
        if obs_vol < 0.015:
            conf_tier, conf_color = "High", "green"
        elif obs_vol < 0.03:
            conf_tier, conf_color = "Medium", "orange"
        else:
            conf_tier, conf_color = "Low", "red"
            
        st.markdown(f"**Prediction Confidence:** <span style='color:{conf_color}'>{conf_tier}</span>", unsafe_allow_html=True)
        
    with col_metrics:
        # Building explanatory metrics table resolving data-science jargon for external recruiters
        st.markdown("Metrics Explanation: \n* **RMSE**: Average error bound per tick *(Lower is better)* \n* **R²**: Percentage of financial variance successfully interpreted *(0 to 1 scaling, Higher is better)*", help="Valid R² bounds rest strictly beneath 1.0. Extreme negatives assert model logic breakage.")
        metrics_data = {
            "Model": ["Linear Regression", "Random Forest"],
            "RMSE (Error)": [
                f"{prediction_results['metrics']['Linear Regression']['rmse']:.4f}",
                f"{prediction_results['metrics']['Random Forest']['rmse']:.4f}"
            ],
            "R² Score": [
                f"{prediction_results['metrics']['Linear Regression']['r2']:.4f}",
                f"{prediction_results['metrics']['Random Forest']['r2']:.4f}"
            ]
        }
        st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)
        
    prediction_df = prediction_results[selected_model]

    st.header("Growth Trajectory: Historical vs. Forecast")
    st.plotly_chart(viz.create_prediction_line_chart(cumulative_growth_df, prediction_df), use_container_width=True)

    st.divider()
    
    st.header("Prediction Summary")
    
    # Debug print to verify variables
    print(f"DEBUG [page_prediction]: cumulative_growth_df has {len(cumulative_growth_df)} rows.")
    print(f"DEBUG [page_prediction]: prediction_df has {len(prediction_df)} rows.")
    
    try:
        # Fixed NameError: Changed cumulative_returns_df -> cumulative_growth_df
        last_historical_value = cumulative_growth_df['Cumulative_Growth'].iloc[-1]
        final_predicted_value = prediction_df['Cumulative_Growth'].iloc[-1]
        
        # Safe check to prevent division by zero
        if last_historical_value == 0:
            forecasted_gain_factor = 1.0
        else:
            forecasted_gain_factor = final_predicted_value / last_historical_value
            
        forecasted_gain_percent = (forecasted_gain_factor - 1) * 100
        
        col1, col2, col3 = st.columns(3)
        
        col1.markdown(create_metric_card("Current Growth Factor", f"{last_historical_value:.4f}", icon="📊"), unsafe_allow_html=True)
        col2.markdown(create_metric_card("Predicted Factor (30 Days)", f"{final_predicted_value:.4f}", is_profit=(forecasted_gain_factor >= 1), icon="🔮"), unsafe_allow_html=True)
        col3.markdown(create_metric_card("Projected 30-Day Return", format_percentage(forecasted_gain_percent), is_profit=(forecasted_gain_percent >= 0), icon="🚀"), unsafe_allow_html=True)
        
    except (KeyError, IndexError) as e:
        st.error(f"Unable to load summary data. Missing expected columns or rows. Error: {e}")
    
    
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
            
            success, message = db.import_csv(temp_file_path, st.session_state['user_id'])
            
            os.remove(temp_file_path)

            if success:
                st.toast(message + " Navigate to **Manage Holdings** to verify.", icon="✅")
                fetch_and_calculate_portfolio.clear() 
            else:
                st.toast(message, icon="⚠️")

    st.divider()

    st.header("Export Portfolio (CSV)")
    holdings_df = db.get_all_holdings(st.session_state['user_id'])

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
    "Home": {"func": page_home, "icon": "🏠"},
    "Holdings": {"func": page_add_manage, "icon": "➕"},
    "Analysis": {"func": page_analysis, "icon": "📊"},
    "Prediction": {"func": page_prediction, "icon": "🔮"}, 
    "Import/Export": {"func": page_import_export, "icon": "📤"},
}

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Home"

# Build Top Navigation Bar Layout
header_cols = st.columns([2, 5.5, 2.5], vertical_alignment="center")

logo_html = """
<div style="display: flex; align-items: center; gap: 10px; margin-top: 5px;">
    <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="32" height="32" rx="8" fill="url(#paint0_linear)"/>
        <path d="M8 20L14 12L18 16L24 8" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M24 8V14M24 8H18" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        <defs>
            <linearGradient id="paint0_linear" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                <stop stop-color="#3B82F6"/>
                <stop offset="1" stop-color="#22C55E"/>
            </linearGradient>
        </defs>
    </svg>
    <h3 style="margin:0; font-weight:700; font-size: 22px; background: -webkit-linear-gradient(45deg, #3B82F6, #22C55E); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">InvestEase</h3>
</div>
"""

# Logo
with header_cols[0]:
    st.markdown('<div class="logo-marker" style="display:none;"></div>', unsafe_allow_html=True)
    st.markdown(logo_html, unsafe_allow_html=True)

# Navigation Buttons (Unified Container)
with header_cols[1]:
    nav_tabs = st.columns(len(PAGES))
    for i, (page_name, page_data) in enumerate(PAGES.items()):
        with nav_tabs[i]:
            # Critical tracking marker tying styles flawlessly back to this exact block without crashing
            st.markdown('<div class="tab-marker" style="display:none;"></div>', unsafe_allow_html=True)
            btn_type = "primary" if st.session_state['current_page'] == page_name else "secondary"
            if st.button(f"{page_data['icon']} {page_name}", use_container_width=True, type=btn_type):
                st.session_state['current_page'] = page_name
                st.rerun()

# User Settings (Top Right)
with header_cols[2]:
    profile_cols = st.columns([2, 1], vertical_alignment="center")
    
    with profile_cols[0]:
        # Extract first letter of username for avatar
        initial = st.session_state["username"][0].upper() if st.session_state["username"] else "U"
        st.markdown(
            f'''
            <div class="user-pill">
                <div class="user-avatar">{initial}</div>
                <span class="user-name">{st.session_state["username"]}</span>
            </div>
            ''', 
            unsafe_allow_html=True
        )
        
    with profile_cols[1]:
        st.markdown('<div class="logout-marker" style="display:none;"></div>', unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_id'] = None
            st.session_state['username'] = None
            st.cache_data.clear()
            st.rerun()

st.markdown("---")

# Render active page
PAGES[st.session_state['current_page']]["func"]()
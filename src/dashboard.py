import streamlit as st
import pandas as pd
import sqlite3
import os
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta
from db import initialize_db

# Ensure the database structure exists immediately
initialize_db()

# --- CONFIGURATION & PATHING ---
STARTING_CASH = 100000.0
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fisr_trading.db")

def get_data(query, params=None):
    """Safely fetch data from the SQLite database."""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def update_config(key, value):
    """Update system settings like Target Duration and Kill Switch."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE config SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

def get_live_prices(tickers):
    """Fetches prices with institutional-grade fallbacks for after-hours."""
    if not tickers:
        return {}
    try:
        # Try live 1-minute data first
        data = yf.download(tickers, period="1d", interval="1m", progress=False)
        
        # If market is closed, fall back to last 5 days of daily data
        if data.empty or 'Close' not in data:
            data = yf.download(tickers, period="5d", interval="1d", progress=False)
            
        prices = {}
        for t in tickers:
            # Handle pandas multi-index vs single index
            ticker_data = data['Close'][t] if len(tickers) > 1 else data['Close']
            valid_prices = ticker_data.dropna()
            
            if not valid_prices.empty:
                prices[t] = float(valid_prices.iloc[-1])
            else:
                prices[t] = 0.0
        return prices
    except Exception as e:
        st.sidebar.error(f"Market Data Error: {e}")
        return {t: 0.0 for t in tickers}

# --- UI SETUP ---
st.set_page_config(page_title="FISR Institutional Dashboard", layout="wide")
st.title("🏛️ FISR Quantitative Bond Desk")

# --- SIDEBAR: COMMAND CENTER ---
st.sidebar.header("Strategy Control")
if os.path.exists(DB_PATH):
    # Kill Switch Toggle
    config_df = get_data("SELECT key, value FROM config")
    if not config_df.empty:
        current_ks = config_df[config_df['key'] == 'kill_switch']['value'].iloc[0]
        new_ks = st.sidebar.toggle("System Kill Switch", value=(current_ks == 1.0), 
                                   help="Toggle to 0 to stop all automated trading immediately.")
        update_config('kill_switch', 1.0 if new_ks else 0.0)
        
        # Target Duration Slider
        current_target = config_df[config_df['key'] == 'target_duration']['value'].iloc[0]
        new_target = st.sidebar.slider("Target Portfolio Duration (Yrs)", 2.0, 15.0, float(current_target))
        if new_target != current_target:
            update_config('target_duration', new_target)
        
        st.sidebar.divider()
        st.sidebar.info(f"**Status:** {'RUNNING' if new_ks else 'STOPPED'}")

# --- MAIN CONTENT ---

# 1. LIVE ALLOCATION PIE CHART
st.header("📊 Live Portfolio Allocation")
trades_all = get_data("SELECT * FROM trades")

# Initialize totals with explicit float types to prevent Metric TypeErrors
total_market_value = 0.0
cash_pos = STARTING_CASH

if not trades_all.empty:
    # --- NET CASH IMPACT LOGIC ---
    # We calculate the net effect of all trades to handle rebalances correctly
    net_impact = 0.0
    for _, row in trades_all.iterrows():
        if row['side'] == 'BUY':
            net_impact += row['trade_value']
        else:
            net_impact -= row['trade_value']
    
    cash_pos = STARTING_CASH - net_impact
    
    # Calculate current holdings and actual market value
    holdings = trades_all.groupby('ticker')['qty'].sum().to_dict()
    active_tickers = [t for t, q in holdings.items() if q > 0.01] # Filter out 'dust'
    
    if active_tickers:
        prices = get_live_prices(active_tickers)
        portfolio_stats = []
        
        for t in active_tickers:
            qty = holdings[t]
            current_price = prices.get(t, 0.0)
            mkt_val = float(qty * current_price)
            total_market_value += mkt_val
            portfolio_stats.append({"Ticker": t, "Value": mkt_val, "Qty": qty})
        
        # Display Pie Chart
        df_pie = pd.DataFrame(portfolio_stats)
        fig = px.pie(df_pie, values='Value', names='Ticker', hole=0.4,
                     title="Current Asset Allocation",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        
        c1, c2 = st.columns([2, 1])
        c1.plotly_chart(fig, use_container_width=True)
        
        # Portfolio Summary Metrics
        c2.metric("Market Value", f"${total_market_value:,.2f}")
        c2.metric("Cash Balance", f"${max(0.0, cash_pos):,.2f}")
        c2.metric("Total Equity", f"${(total_market_value + cash_pos):,.2f}")
    else:
        st.info("Portfolio currently holds 100% Cash.")
        st.metric("Cash Balance", f"${cash_pos:,.2f}")
else:
    st.warning("Waiting for GitHub Action to execute initial trades...")
    st.metric("Cash Balance", f"${STARTING_CASH:,.2f}")

st.divider()

# 2. TRADE HISTORY
st.header("📜 Trade History & Interval Analysis")
col_a, col_b = st.columns(2)
start_date = col_a.date_input("Start Date", datetime.now() - timedelta(days=7))
end_date = col_b.date_input("End Date", datetime.now())

# Filtered Trade Query
query = "SELECT * FROM trades WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC"
filtered_trades = get_data(query, (start_date.isoformat(), f"{end_date.isoformat()} 23:59:59"))

if not filtered_trades.empty:
    st.dataframe(filtered_trades[['timestamp', 'ticker', 'side', 'qty', 'price', 'trade_value', 'status']], 
                 use_container_width=True)
else:
    st.info(f"No trades recorded between {start_date} and {end_date}.")

# 3. SYSTEM LOGS
with st.expander("View System Audit Logs"):
    logs = get_data("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 20")
    if not logs.empty:
        st.table(logs)
    else:
        st.write("No system logs available.")

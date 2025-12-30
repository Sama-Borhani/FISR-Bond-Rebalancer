import streamlit as st
import pandas as pd
import sqlite3
import os
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta
from db import initialize_db


initialize_db()

# --- CONFIGURATION & PATHING ---
STARTING_CASH = 100000
# Ensure we point to the root DB file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fisr_trading.db")

def get_data(query, params=None):
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def update_config(key, value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE config SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

def get_live_prices(tickers):
    if not tickers: return {}
    data = yf.download(tickers, period="1d", interval="1m", progress=False)
    return {t: data['Close'][t].iloc[-1] for t in tickers}

# --- UI SETUP ---
st.set_page_config(page_title="FISR Institutional Dashboard", layout="wide")
st.title("🏛️ FISR Quantitative Bond Desk")

# --- SIDEBAR: COMMAND CENTER ---
st.sidebar.header("🕹️ Strategy Control")
if os.path.exists(DB_PATH):
    # Kill Switch Toggle
    current_ks = get_data("SELECT value FROM config WHERE key='kill_switch'").iloc[0,0]
    new_ks = st.sidebar.toggle("System Kill Switch", value=(current_ks == 1.0), 
                               help="Toggle to 0 to stop all automated trading immediately.")
    update_config('kill_switch', 1.0 if new_ks else 0.0)
    
    # Target Duration Slider
    current_target = get_data("SELECT value FROM config WHERE key='target_duration'").iloc[0,0]
    new_target = st.sidebar.slider("Target Portfolio Duration (Yrs)", 2.0, 15.0, float(current_target))
    if new_target != current_target:
        update_config('target_duration', new_target)
    
    st.sidebar.divider()
    st.sidebar.info(f"**Status:** {'RUNNING' if new_ks else 'STOPPED'}")

# --- MAIN CONTENT ---

# 1. LIVE ALLOCATION PIE CHART
st.header("📊 Live Portfolio Allocation")
trades_all = get_data("SELECT * FROM trades")

if not trades_all.empty:
    # Calculate current holdings (Sum of Buy qty - Sum of Sell qty)
    holdings = trades_all.groupby('ticker')['qty'].sum().to_dict()
    active_tickers = [t for t, q in holdings.items() if q > 0]
    
    if active_tickers:
        prices = get_live_prices(active_tickers)
        
        portfolio_stats = []
        total_market_value = 0
        for t in active_tickers:
            qty = holdings[t]
            mkt_val = qty * prices[t]
            total_market_value += mkt_val
            portfolio_stats.append({"Ticker": t, "Value": mkt_val, "Qty": qty})
        
        # Display Pie Chart
        df_pie = pd.DataFrame(portfolio_stats)
        fig = px.pie(df_pie, values='Value', names='Ticker', hole=0.4,
                     title="Current Market Value Distribution",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        
        c1, c2 = st.columns([2, 1])
        c1.plotly_chart(fig, use_container_width=True)
        
        # Portfolio Summary Metrics
        c2.metric("Market Value", f"${total_market_value:,.2f}")
        cash_pos = STARTING_CASH - (trades_all['qty'] * trades_all['price']).sum()
        c2.metric("Cash Balance", f"${max(0, cash_pos):,.2f}")
    else:
        st.info("Portfolio currently holds 100% Cash.")
else:
    st.warning("No trade history found. Run the GitHub Action to generate data.")

st.divider()

# 2. TRADE HISTORY WITH DATE FILTER
st.header("📜 Trade History & Interval Analysis")

# Date Interval Selector
col_a, col_b = st.columns(2)
start_date = col_a.date_input("Start Date", datetime.now() - timedelta(days=7))
end_date = col_b.date_input("End Date", datetime.now())

# Convert dates to string for SQL query
query = "SELECT * FROM trades WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC"
filtered_trades = get_data(query, (start_date.isoformat(), f"{end_date.isoformat()} 23:59:59"))

if not filtered_trades.empty:
    # Analysis of Changes
    buy_vol = filtered_trades[filtered_trades['side'] == 'BUY']['qty'].sum()
    st.write(f"**Period Summary:** {len(filtered_trades)} trades executed. Total volume: {buy_vol:,.0f} shares.")
    
    # Display Table
    st.dataframe(filtered_trades[['timestamp', 'ticker', 'side', 'qty', 'price', 'status']], 
                 use_container_width=True)
else:
    st.info(f"No trades found between {start_date} and {end_date}.")

# 3. SYSTEM LOGS
with st.expander("View System Audit Logs"):
    logs = get_data("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 20")
    st.table(logs)
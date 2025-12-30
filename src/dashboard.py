import streamlit as st
import pandas as pd
import sqlite3
import os
import yfinance as yf
import plotly.express as px

# --- CONFIGURATION ---
STARTING_CASH = 100000
TICKERS = ['SHY', 'IEF', 'TLT']

# --- DYNAMIC PATHING ---
current_dir = os.path.dirname(os.path.abspath(__file__)) 
DB_PATH = os.path.join(os.path.dirname(current_dir), 'fisr_trading.db')

def get_data(query):
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_live_prices(tickers):
    data = yf.download(tickers, period="1d", interval="1m", progress=False)
    return {t: data['Close'][t].iloc[-1] for t in tickers}

# --- UI SETUP ---
st.set_page_config(page_title="FISR Dashboard", layout="wide")
st.title("🏛️ FISR Fixed-Income Portfolio")
st.markdown(f"**Status:** 24/7 Monitoring | **Database:** {DB_PATH}")

# --- DATA LOADING ---
trades_df = get_data("SELECT * FROM trades")
signals_df = get_data("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 1")

# 1. CURRENT PORTFOLIO SECTION
st.header("📊 Current Portfolio Composition")
if not trades_df.empty:
    # Calculate current share quantities
    # (Sum of BUYs minus Sum of SELLs - though our bot currently only BUYs)
    holdings = trades_df.groupby('ticker')['qty'].sum().to_dict()
    prices = get_live_prices(list(holdings.keys()))
    
    # Calculate Market Value
    portfolio_data = []
    total_market_value = 0
    for t, qty in holdings.items():
        val = qty * prices[t]
        total_market_value += val
        portfolio_data.append({"Ticker": t, "Shares": qty, "Price": f"${prices[t]:.2f}", "Value": val})
    
    # Add Remaining Cash (Simplified for mock)
    cash = STARTING_CASH - trades_df[trades_df['side'] == 'BUY']['trade_value'].sum()
    total_equity = total_market_value + max(0, cash)
    
    # Display Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Equity", f"${total_equity:,.2f}")
    c2.metric("Portfolio Value", f"${total_market_value:,.2f}")
    c3.metric("Current Target", f"{signals_df['target_duration'].iloc[0]} yrs" if not signals_df.empty else "N/A")

    # Show Allocation Chart
    df_plot = pd.DataFrame(portfolio_data)
    fig = px.pie(df_plot, values='Value', names='Ticker', title="Asset Allocation")
    st.plotly_chart(fig)
    st.table(df_plot)
else:
    st.info("Portfolio is currently 100% Cash. Waiting for the first signal to execute trades.")

# 2. TRADE HISTORY REPORT
st.header("Execution Report (Trade History)")
if not trades_df.empty:
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    st.dataframe(trades_df.sort_values('timestamp', ascending=False), use_container_width=True)
else:
    st.write("No trades executed yet.")

# 3. SYSTEM LOGS (The "Pulse")
st.sidebar.header("System Pulse")
logs_df = get_data("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 5")
if not logs_df.empty:
    for _, row in logs_df.iterrows():
        st.sidebar.write(f"**{row['timestamp']}**")
        st.sidebar.write(f"{row['message']}")
        st.sidebar.divider()
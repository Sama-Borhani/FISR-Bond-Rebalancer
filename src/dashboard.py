import streamlit as st
import pandas as pd
import sqlite3
import os
import yfinance as yf          # ADDED
import plotly.express as px     # ADDED

# --- CONFIGURATION ---
STARTING_CASH = 100000          # ADDED

# --- DYNAMIC PATHING FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root = os.path.dirname(current_dir)
DB_PATH = os.path.join(project_root, 'fisr_trading.db')

def get_data(query):
    # Check if the database actually exists before trying to open it
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at {DB_PATH}")
        # DEBUG: List files to see what Streamlit sees
        st.write("Current Directory Files:", os.listdir(os.path.dirname(DB_PATH)) if os.path.exists(os.path.dirname(DB_PATH)) else "Data folder missing")
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_current_prices(tickers):
    data = yf.download(tickers, period="1d", interval="1m", progress=False)
    return {ticker: data['Close'][ticker].iloc[-1] for ticker in tickers}

# --- DASHBOARD UI ---
st.set_page_config(page_title="FISR Quantitative Dashboard", layout="wide")
st.title("🏛️ FISR Fixed-Income Rebalancer")
st.markdown(f"**Status:** 24/7 Automated Production Logic | **Region:** Toronto (Mock Execution)")

# 1. METRICS SECTION
try:
    trades_df = get_data("SELECT * FROM trades")
    
    if not trades_df.empty:
        # Calculate current holdings
        holdings = trades_df.groupby('ticker')['qty'].sum().to_dict()
        prices = get_current_prices(list(holdings.keys()))
        
        # Calculate Equity
        current_value = sum(holdings[t] * prices[t] for t in holdings)
        total_equity = current_value 
        pnl = total_equity - STARTING_CASH
        pnl_pct = (pnl / STARTING_CASH) * 100

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Portfolio Value", f"${total_equity:,.2f}")
        col2.metric("Total P/L", f"${pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
        col3.metric("Trade Count", len(trades_df))

        # 2. PERFORMANCE CHART
        st.subheader("📈 Mock Performance (Equity Curve)")
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        trades_df = trades_df.sort_values('timestamp')
        trades_df['trade_value'] = trades_df['qty'] * trades_df['price']
        trades_df['cumulative_equity'] = trades_df['trade_value'].cumsum()
        
        fig = px.line(trades_df, x='timestamp', y='cumulative_equity', 
                      title="Cumulative Portfolio Exposure",
                      labels={'cumulative_equity': 'Exposure ($)', 'timestamp': 'Date'})
        st.plotly_chart(fig, use_container_wide=True)

        # 3. RECENT TRADES TABLE
        st.subheader("📜 Recent Executions")
        st.dataframe(trades_df[['timestamp', 'ticker', 'side', 'qty', 'price', 'status']].sort_values('timestamp', ascending=False), use_container_width=True)

    else:
        st.info("Waiting for the first automated trade... (Bot runs every hour)")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")

# 4. RISK STATUS
st.sidebar.header("Risk Gatekeeper Settings")
st.sidebar.write("Max Concentration: 80%")
st.sidebar.write("Min Duration: 1.5 yrs")
st.sidebar.write("Max Duration: 15.0 yrs")

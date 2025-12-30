import yfinance as yf
import pandas as pd
import sqlite3
import os
from db import get_config, log_event, initialize_db, DB_PATH, log_signal
from risk import RiskGatekeeper
from broker import log_mock_trade

# --- 1. DATA ACQUISITION ---
def get_current_prices(tickers=['SHY', 'IEF', 'TLT']):
    data = yf.download(tickers, period="1d", interval="1m", progress=False)
    return {ticker: data['Close'][ticker].iloc[-1] for ticker in tickers}

def get_current_holdings():
    if not os.path.exists(DB_PATH): return {}
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT ticker, SUM(qty) as total_qty FROM trades GROUP BY ticker", conn)
    conn.close()
    return dict(zip(df['ticker'], df['total_qty']))

# --- 2. STRATEGY MATH ---
def calculate_weights(target_duration, durations):
    weights = {'SHY': 0.0, 'IEF': 0.0, 'TLT': 0.0}
    if durations['SHY'] <= target_duration < durations['IEF']:
        den = durations['IEF'] - durations['SHY']
        weights['IEF'] = (target_duration - durations['SHY']) / den
        weights['SHY'] = 1.0 - weights['IEF']
    elif durations['IEF'] <= target_duration <= durations['TLT']:
        den = durations['TLT'] - durations['IEF']
        weights['TLT'] = (target_duration - durations['IEF']) / den
        weights['IEF'] = 1.0 - weights['TLT']
    return weights

# --- 3. MAIN EXECUTION ---
if __name__ == "__main__":
    # STEP 1: INITIALIZE FIRST. This creates 'config' before we do anything else.
    initialize_db()
    
    # STEP 2: NOW it is safe to fetch the config
    target_duration = get_config('target_duration')
    
    gatekeeper = RiskGatekeeper()
    DURATIONS = {'SHY': 1.92, 'IEF': 7.45, 'TLT': 16.80}
    DRIFT_THRESHOLD = 0.2
    PORTFOLIO_CASH = 100000.0
    
    live_prices = get_current_prices(list(DURATIONS.keys()))
    current_holdings = get_current_holdings()
    
    # Calculate current duration state
    total_val = sum(current_holdings[t] * live_prices[t] for t in current_holdings if t in live_prices)
    curr_dur = sum(((current_holdings[t] * live_prices[t]) / total_val) * DURATIONS.get(t, 0) for t in current_holdings) if total_val > 0 else 0
    
    drift = abs(curr_dur - target_duration)
    
    # STEP 3: REBALANCE LOGIC
    if drift < DRIFT_THRESHOLD and curr_dur != 0:
        log_event("INFO", f"No rebalance: Drift ({drift:.2f}) < 0.2")
    else:
        target_weights = calculate_weights(target_duration, DURATIONS)
        log_signal(target_duration, target_weights)

        for ticker, weight in target_weights.items():
            price = live_prices[ticker]
            target_qty = (weight * PORTFOLIO_CASH) / price
            current_qty = current_holdings.get(ticker, 0)
            trade_qty = target_qty - current_qty
            
            if abs(trade_qty) > 0.1:
                order_val = abs(trade_qty * price)
                is_safe, msg = gatekeeper.check_trade(order_val)
                if is_safe:
                    side = "BUY" if trade_qty > 0 else "SELL"
                    log_mock_trade(ticker, abs(round(trade_qty, 2)), round(price, 2), side, round(order_val, 2))
                else:
                    log_event("RISK_REJECT", f"{ticker}: {msg}")

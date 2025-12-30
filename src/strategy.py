import yfinance as yf
import pandas as pd
import sqlite3
import os
from db import get_config, log_event, initialize_db, DB_PATH, log_signal
from risk import RiskGatekeeper
from broker import log_mock_trade

# --- 1. DATA ACQUISITION ---
def get_current_prices(tickers=['SHY', 'IEF', 'TLT']):
    """Fetches real-time prices using yfinance."""
    data = yf.download(tickers, period="1d", interval="1m", progress=False)
    prices = {ticker: data['Close'][ticker].iloc[-1] for ticker in tickers}
    return prices

def get_current_holdings():
    """Calculates current share holdings from the trade history."""
    if not os.path.exists(DB_PATH):
        return {}
    conn = sqlite3.connect(DB_PATH)
    # Sum of BUYs (ignoring SELLs for this mock version)
    df = pd.read_sql_query("SELECT ticker, SUM(qty) as total_qty FROM trades GROUP BY ticker", conn)
    conn.close()
    return dict(zip(df['ticker'], df['total_qty']))

# --- 2. STRATEGY MATH ---
def calculate_weights(target_duration, durations):
    """Calculates weights for a 'Two-Prong' portfolio to match a target duration."""
    weights = {'SHY': 0.0, 'IEF': 0.0, 'TLT': 0.0}
    
    if durations['SHY'] <= target_duration < durations['IEF']:
        denominator = durations['IEF'] - durations['SHY']
        weights['IEF'] = (target_duration - durations['SHY']) / denominator
        weights['SHY'] = 1.0 - weights['IEF']
    elif durations['IEF'] <= target_duration <= durations['TLT']:
        denominator = durations['TLT'] - durations['IEF']
        weights['TLT'] = (target_duration - durations['IEF']) / denominator
        weights['IEF'] = 1.0 - weights['TLT']
    return weights

def calculate_portfolio_duration(holdings, prices, durations):
    """Calculates the weighted average duration of the current portfolio."""
    total_value = sum(holdings[t] * prices[t] for t in holdings if t in prices)
    if total_value == 0:
        return 0
    
    current_dur = 0
    for t, qty in holdings.items():
        weight = (qty * prices[t]) / total_value
        current_dur += weight * durations.get(t, 0)
    return current_dur

# --- 3. EXECUTION LOOP ---
if __name__ == "__main__":
    # 1. Initialize DB first to ensure 'config' table and defaults exist
    initialize_db()
    gatekeeper = RiskGatekeeper()
    
    # 2. Desk Constants
    DURATIONS = {'SHY': 1.92, 'IEF': 7.45, 'TLT': 16.80}
    DRIFT_THRESHOLD = 0.2  # Desk Rule: Only rebalance if drift > 0.2 yrs
    PORTFOLIO_CASH = 100000.0
    
    # 3. Get Configuration and Market Data
    target_duration = get_config('target_duration')
    live_prices = get_current_prices(list(DURATIONS.keys()))
    current_holdings = get_current_holdings()
    
    # 4. Check Drift
    curr_dur = calculate_portfolio_duration(current_holdings, live_prices, DURATIONS)
    drift = abs(curr_dur - target_duration)
    
    print(f"Current Duration: {curr_dur:.2f} | Target: {target_duration:.2f} | Drift: {drift:.2f}")

    if drift < DRIFT_THRESHOLD and curr_dur != 0:
        log_event("INFO", f"No rebalance: Drift ({drift:.2f}) < Threshold ({DRIFT_THRESHOLD})")
        exit()

    # 5. Calculate Target State
    target_weights = calculate_weights(target_duration, DURATIONS)
    log_signal(target_duration, target_weights)

    # 6. Risk-Managed Execution
    for ticker, weight in target_weights.items():
        if weight > 0:
            price = live_prices[ticker]
            # Calculate total shares needed for this target weight
            target_qty = (weight * PORTFOLIO_CASH) / price
            # Simple rebalancer: current logic just resets to target quantities
            current_qty = current_holdings.get(ticker, 0)
            trade_qty = target_qty - current_qty
            
            if abs(trade_qty) > 0.1: # Avoid tiny fractional trades
                order_val = abs(trade_qty * price)
                is_safe, msg = gatekeeper.check_trade(order_val)
                
                if is_safe:
                    side = "BUY" if trade_qty > 0 else "SELL"
                    log_mock_trade(ticker, abs(round(trade_qty, 2)), round(price, 2), side, round(order_val, 2))
                else:
                    log_event("RISK_REJECT", f"{ticker}: {msg}")

    log_event("STRATEGY_RUN", "Strategy execution completed.")

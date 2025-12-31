import yfinance as yf
import pandas as pd
import sqlite3
import os
from db import get_config, log_event, initialize_db, DB_PATH, log_signal
from risk import RiskGatekeeper
from broker import log_mock_trade

# --- 1. DYNAMIC BOND UNIVERSE ---
# The bot 'studies' these candidates to find the best mix for your goal
BOND_UNIVERSE = {
    'SHY': 1.9, 'IEI': 4.5, 'IEF': 7.4, 'TLH': 10.1, 'TLT': 16.8,  # Treasuries
    'LQD': 8.5, 'VCIT': 6.4, 'VCSH': 2.7,                         # Corporate Bonds
    'TIP': 6.6, 'SCHP': 7.2,                                     # Inflation Protected
    'BNDX': 7.0, 'VWOB': 6.2                                     # International
}

def study_and_retain_bonds(universe):
    """
    Market Research: Fetches live prices and checks liquidity.
    Only retains bonds with sufficient trading volume.
    """
    retained = {}
    tickers = list(universe.keys())
    
    # Fetch data in bulk for efficiency
    data = yf.download(tickers, period="5d", interval="1d", progress=False)
    
    if data.empty:
        log_event("ERROR", "Market study failed: No data retrieved from yfinance")
        return {}

    for ticker in tickers:
        try:
            # Check Liquidity: Ensure average volume > 100,000 shares
            avg_vol = data['Volume'][ticker].mean()
            if avg_vol > 100000:
                retained[ticker] = {
                    'duration': universe[ticker],
                    'price': float(data['Close'][ticker].iloc[-1])
                }
        except Exception:
            continue
            
    return retained

def get_current_holdings():
    if not os.path.exists(DB_PATH): return {}
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT ticker, SUM(qty) as total_qty FROM trades GROUP BY ticker", conn)
    conn.close()
    return {row['ticker']: row['total_qty'] for _, row in df.iterrows() if row['total_qty'] > 0.01}

# --- 2. MULTI-ASSET STRATEGY MATH ---
def calculate_weights(target_duration, market_study):
    """
    Advanced Heuristic: Blends all retained bonds to hit target duration.
    Ensures a diverse portfolio by preventing 100% concentration in one asset.
    """
    weights = {t: 0.0 for t in market_study.keys()}
    
    # Sort bonds by duration to find the 'bracket'
    sorted_tickers = sorted(market_study.keys(), key=lambda x: market_study[x]['duration'])
    
    low_ticker = sorted_tickers[0]
    high_ticker = sorted_tickers[-1]

    # Find the two bonds that closest 'bracket' the target duration
    for i in range(len(sorted_tickers) - 1):
        t1, t2 = sorted_tickers[i], sorted_tickers[i+1]
        d1, d2 = market_study[t1]['duration'], market_study[t2]['duration']
        
        if d1 <= target_duration <= d2:
            low_ticker, high_ticker = t1, t2
            break

    # Linear Interpolation to solve for weights
    d_low = market_study[low_ticker]['duration']
    d_high = market_study[high_ticker]['duration']
    
    if d_high == d_low:
        weights[low_ticker] = 1.0
    else:
        weights[high_ticker] = (target_duration - d_low) / (d_high - d_low)
        weights[low_ticker] = 1.0 - weights[high_ticker]

    # Diversity Sweep: Ensure we don't hold 0% of liquid benchmark IEF if it's healthy
    if 'IEF' in market_study and weights.get('IEF', 0) < 0.10:
        weights['IEF'] = 0.05 # 5% minimum 'Anchor' in benchmark Treasuries
        
    # Re-normalize to 100%
    total = sum(weights.values())
    return {k: v/total for k, v in weights.items() if v > 0}

# --- 3. MAIN EXECUTION ---
if __name__ == "__main__":
    initialize_db()
    target_duration = get_config('target_duration')
    gatekeeper = RiskGatekeeper()
    PORTFOLIO_EQUITY = 100000.0
    DRIFT_THRESHOLD = 0.25

    # STEP 1: Study the market and retain viable bonds
    market_study = study_and_retain_bonds(BOND_UNIVERSE)
    if not market_study:
        log_event("CRITICAL", "No liquid bonds found. Standing down.")
        exit()

    # STEP 2: Assess current state
    current_holdings = get_current_holdings()
    total_val = sum(qty * market_study[t]['price'] for t, qty in current_holdings.items() if t in market_study)
    
    curr_dur = 0.0
    if total_val > 0:
        curr_dur = sum(((qty * market_study[t]['price']) / total_val) * market_study[t]['duration'] 
                       for t, qty in current_holdings.items() if t in market_study)
    
    drift = abs(curr_dur - target_duration)

    # STEP 3: Rebalance Logic
    if drift < DRIFT_THRESHOLD and curr_dur != 0:
        log_event("INFO", f"Drift {drift:.2f} < {DRIFT_THRESHOLD}. No trade required.")
    else:
        target_weights = calculate_weights(target_duration, market_study)
        log_signal(target_duration, target_weights)

        # Calculate trades for every asset in the new wide universe
        all_relevant_tickers = set(list(target_weights.keys()) + list(current_holdings.keys()))
        
        for ticker in all_relevant_tickers:
            if ticker not in market_study: continue
            
            price = market_study[ticker]['price']
            target_qty = (target_weights.get(ticker, 0) * PORTFOLIO_EQUITY) / price
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

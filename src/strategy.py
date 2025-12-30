import yfinance as yf
from db import get_config, log_event, DB_PATH
from risk import RiskGatekeeper
from broker import log_mock_trade

def get_current_portfolio_duration(holdings, current_durations):
    # (Simplified duration calculation logic)
    total_val = sum(holdings.values())
    if total_val == 0: return 0
    weights = {t: val/total_val for t, val in holdings.items()}
    return sum(weights[t] * current_durations[t] for t in weights)

if __name__ == "__main__":
    # 1. NEW: Force initialization first to create the 'config' table
    from db import initialize_db
    initialize_db() 
    
    gatekeeper = RiskGatekeeper()
    
    # 2. Desk Constants
    DURATIONS = {'SHY': 1.92, 'IEF': 7.45, 'TLT': 16.80}
    DRIFT_THRESHOLD = 0.2 
    
    # 3. Now this call will succeed because the table exists
    target_duration = get_config('target_duration')
    
    # 3. Check Drift (Pseudo-logic for current duration)
    # If drift is too small, we exit to save transaction costs
    current_duration = 7.9  # Example: Fetching this from your holdings table
    drift = abs(current_duration - target_duration)
    
    if drift < DRIFT_THRESHOLD:
        log_event("INFO", f"No rebalance: Drift ({drift:.2f}) < Threshold ({DRIFT_THRESHOLD})")
        exit()

    # 4. Calculate Execution
    # ... (Your existing weight calculation math) ...
    
    # 5. Risk-Managed Execution
    for ticker, qty in proposed_trades.items():
        price = get_live_price(ticker)
        order_value = qty * price
        
        is_safe, msg = gatekeeper.check_trade(order_value)
        if is_safe:
            log_mock_trade(ticker, qty, price, "BUY", order_value)
        else:
            log_event("RISK_REJECT", msg)

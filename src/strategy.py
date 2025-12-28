import yfinance as yf
import pandas as pd
from db import log_signal, initialize_db, log_event
from risk import RiskGatekeeper
from broker import log_mock_trade

# --- 1. DATA ACQUISITION ---
def get_current_prices(tickers=['SHY', 'IEF', 'TLT']):
    """Fetches real-time prices using yfinance."""
    print(f"📡 Fetching live prices for {tickers}...")
    data = yf.download(tickers, period="1d", interval="1m", progress=False)
    # Get the last available 'Close' price for each ticker
    prices = {ticker: data['Close'][ticker].iloc[-1] for ticker in tickers}
    return prices

# --- 2. STRATEGY MATH ---
def calculate_weights(target_duration, durations):
    """Calculates weights for a 'Two-Prong' portfolio to match a target duration."""
    weights = {'SHY': 0.0, 'IEF': 0.0, 'TLT': 0.0}
    
    # Logic: Barbell vs Bullet
    if durations['SHY'] <= target_duration < durations['IEF']:
        denominator = durations['IEF'] - durations['SHY']
        weights['IEF'] = (target_duration - durations['SHY']) / denominator
        weights['SHY'] = 1.0 - weights['IEF']
        
    elif durations['IEF'] <= target_duration <= durations['TLT']:
        denominator = durations['TLT'] - durations['IEF']
        weights['TLT'] = (target_duration - durations['IEF']) / denominator
        weights['IEF'] = 1.0 - weights['TLT']
        
    return weights

# --- 3. EXECUTION LOOP ---
if __name__ == "__main__":
    # Initialize DB (Ensures tables exist in data/fisr_trading.db)
    initialize_db()
    gatekeeper = RiskGatekeeper()
    
    # Configuration
    TICKERS = ['SHY', 'IEF', 'TLT']
    CURRENT_DURATIONS = {'SHY': 1.92, 'IEF': 7.45, 'TLT': 16.80} # Benchmark metrics
    MY_TARGET = 8.0 # Target Portfolio Duration
    PORTFOLIO_CASH = 100000 # Your starting paper-trading balance
    
    # 1. Get Live Prices
    try:
        live_prices = get_current_prices(TICKERS)
    except Exception as e:
        log_event("DATA_ERROR", f"Failed to fetch prices: {str(e)}")
        print(f"❌ Error fetching prices: {e}")
        exit()

    # 2. Calculate the target weights
    target_weights = calculate_weights(MY_TARGET, CURRENT_DURATIONS)
    
    # 3. ASK THE GATEKEEPER if it's safe
    is_safe, message = gatekeeper.check_weights(target_weights)
    
    if is_safe:
        print(f"✅ Risk Check Passed: {message}")
        log_signal(MY_TARGET, target_weights)
        
        # 4. EXECUTE MOCK TRADES
        # We simulate buying the shares needed to reach the target weights
        for ticker, weight in target_weights.items():
            if weight > 0:
                price = live_prices[ticker]
                # Calculate how many shares to buy (Weight * Total Cash / Price)
                target_qty = (weight * PORTFOLIO_CASH) / price
                
                # Send to our Mock Broker to log in the database
                log_mock_trade(ticker, round(target_qty, 2), round(price, 2), "BUY")
        
        log_event("STRATEGY_RUN", "Successfully rebalanced portfolio.")
    else:
        print(f"⚠️ Risk Check Failed: {message}")
        log_event("RISK_REJECT", message)

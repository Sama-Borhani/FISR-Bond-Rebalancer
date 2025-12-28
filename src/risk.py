import sqlite3

class RiskGatekeeper:
    def __init__(self, db_name="fisr_trading.db"):
        self.db_name = db_name
        self.max_daily_turnover = 0.20  # Don't trade more than 20% of account/day
        self.max_position_size = 0.60   # No single ETF should be > 60%

    def check_weights(self, proposed_weights):
        """
        Validates if the math output is safe to trade.
        Returns (is_safe, reason)
        """
        for ticker, weight in proposed_weights.items():
            # Rule 1: Position Concentration
            if weight > self.max_position_size:
                return False, f"REJECTED: {ticker} weight ({weight:.2%}) exceeds 60% limit."
            
            # Rule 2: Negative weights (No Shorting)
            if weight < 0:
                return False, f"REJECTED: {ticker} weight is negative. Long-only only."

        return True, "ACCEPTED: Risk checks passed."

    def is_kill_switch_active(self):
        """Placeholder for a manual emergency stop."""
        # For now, we assume it's always safe. 
        # In Milestone 4, we will link this to a button on your dashboard.
        return False
    
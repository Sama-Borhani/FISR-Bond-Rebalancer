import sqlite3
import os
from datetime import datetime

class RiskGatekeeper:
    def __init__(self):
        # Use the same pathing as db.py
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "fisr_trading.db")
        self.equity = 100000.0
        self.turnover_limit = 0.20   # 20% total equity per day
        self.fat_finger_limit = 1 # 5% max per single order

    def is_kill_switch_active(self):
        conn = sqlite3.connect(self.db_path)
        val = conn.execute("SELECT value FROM config WHERE key='kill_switch'").fetchone()[0]
        conn.close()
        return val == 0.0

    def check_trade(self, order_value):
        """Institutional pre-trade verification."""
        # 1. Check Kill Switch
        if self.is_kill_switch_active():
            return False, "REJECTED: Kill Switch is ACTIVE (Stop)"

        # 2. Fat-Finger Check (Is this order too big?)
        if order_value > (self.equity * self.fat_finger_limit):
            return False, f"REJECTED: Order value ${order_value:,.2f} exceeds 5% limit"

        # 3. Daily Turnover Cap
        conn = sqlite3.connect(self.db_path)
        today = datetime.now().strftime('%Y-%m-%d')
        daily_executed = conn.execute(
            "SELECT SUM(trade_value) FROM trades WHERE timestamp LIKE ?", 
            (f"{today}%",)).fetchone()[0] or 0.0
        conn.close()

        if (daily_executed + order_value) > (self.equity * self.turnover_limit):
            return False, "REJECTED: Daily 20% turnover cap reached"

        return True, "ACCEPTED: Risk checks passed"

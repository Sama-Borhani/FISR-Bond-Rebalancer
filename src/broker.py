import os
import sqlite3
from datetime import datetime

# Centralized pathing to ensure Bot and Dashboard see the same file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fisr_trading.db")

def log_mock_trade(ticker, qty, price, side, order_value):
    """
    Simulates a trade execution and saves it to the database.
    Now matches the 5-argument signature required by strategy.py.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure the table matches the new institutional schema (includes trade_value)
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       timestamp TEXT, ticker TEXT, qty REAL, 
                       price REAL, side TEXT, trade_value REAL, status TEXT)''')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # We now map the 5th argument (order_value) into the database
    cursor.execute("""
        INSERT INTO trades (timestamp, ticker, qty, price, side, trade_value, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, ticker, qty, price, side, order_value, "FILLED"))

    conn.commit()
    conn.close()
    print(f" MOCK {side}: {qty} {ticker} at ${price} (Total: ${order_value:,.2f})")

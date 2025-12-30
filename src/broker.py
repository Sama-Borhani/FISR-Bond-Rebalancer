import os
import sqlite3
import datetime

# Point to the same root file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fisr_trading.db")

def log_mock_trade(ticker, qty, price, side):
    conn = sqlite3.connect(DB_PATH) # Use DB_PATH
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       timestamp TEXT, ticker TEXT, qty REAL, 
                       price REAL, side TEXT, status TEXT)''')

    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO trades (timestamp, ticker, qty, price, side, status) VALUES (?, ?, ?, ?, ?, ?)",
                   (timestamp, ticker, qty, price, side, "FILLED"))

    conn.commit()
    conn.close()
    print(f"✅ MOCK {side}: {qty} shares of {ticker} at ${price}")

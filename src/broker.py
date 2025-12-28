import sqlite3
import datetime

def log_mock_trade(ticker, qty, price, side):
    """Records a simulated trade in the database."""
    conn = sqlite3.connect('data/fisr_trading.db')
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
import os
import sqlite3
import json
from datetime import datetime

# Centralized pathing
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fisr_trading.db")

def initialize_db():
    """Creates the database tables with the new dynamic signals schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: Configuration
    cursor.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value REAL)''')
    cursor.execute("INSERT OR IGNORE INTO config VALUES ('kill_switch', 1.0)")
    cursor.execute("INSERT OR IGNORE INTO config VALUES ('target_duration', 8.0)")

    # Table 2: Signals (REWRITTEN FOR DYNAMIC UNIVERSES)
    # We removed shy_w, ief_w, and tlt_w in favor of a single weights_json column
    cursor.execute('''CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME, 
            target_duration REAL,
            weights_json TEXT)''')

    # Table 3: Trades (With trade_value column)
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            timestamp TEXT, ticker TEXT, qty REAL, 
            price REAL, side TEXT, trade_value REAL, status TEXT)''')

    # Table 4: Logs
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME, level TEXT, message TEXT)''')

    conn.commit()
    conn.close()

def get_config(key):
    conn = sqlite3.connect(DB_PATH)
    val = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()[0]
    conn.close()
    return val

def log_signal(target, weights):
    """
    Saves the target allocation to the database.
    Stores the weights as a JSON string to handle any number of tickers.
    """
    conn = sqlite3.connect(DB_PATH)
    weights_json = json.dumps(weights) 
    
    conn.execute("""
        INSERT INTO signals (timestamp, target_duration, weights_json) 
        VALUES (?, ?, ?)
    """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), float(target), weights_json))
    
    conn.commit()
    conn.close()

def log_event(level, message):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)', 
                 (datetime.now(), level, message))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()

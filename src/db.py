import os
import sqlite3
from datetime import datetime

# Centralized pathing to ensure Bot and Dashboard see the same file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fisr_trading.db")

_DB_INITIALIZED = False

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: Configuration (The "Command Center")
    cursor.execute('''CREATE TABLE IF NOT EXISTS config 
                      (key TEXT PRIMARY KEY, value REAL)''')
    
    # Initialize defaults: Kill Switch (1=ON, 0=OFF) and Target Duration
    cursor.execute("INSERT OR IGNORE INTO config VALUES ('kill_switch', 1.0)")
    cursor.execute("INSERT OR IGNORE INTO config VALUES ('target_duration', 8.0)")

    # Table 2: Signals (Strategy audit trail)
    cursor.execute('''CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            target_duration REAL,
            shy_w REAL, ief_w REAL, tlt_w REAL)''')

    # Table 3: Trades (Execution history)
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            timestamp TEXT, ticker TEXT, qty REAL, 
            price REAL, side TEXT, trade_value REAL, status TEXT)''')

    # Table 4: Logs (System health)
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME, level TEXT, message TEXT)''')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

def _ensure_db():
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return
    # Best-effort ensure DB exists and tables are present
    try:
        initialize_db()
    except Exception:
        # If initialization fails for some reason, re-raise so caller can see the failure
        raise
    finally:
        _DB_INITIALIZED = True

def get_config(key):
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    finally:
        conn.close()

    if row is None:
        raise KeyError(f"Config key '{key}' not found in database. Ensure the config table has been initialized.")
    return row[0]

def log_event(level, message):
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)', 
                     (datetime.now(), level, message))
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    # Allow running db.py directly for local initialization
    initialize_db()
import sqlite3
from datetime import datetime

DB_NAME = "fisr_trading.db"

def initialize_db():
    """Creates the database tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table 1: Store our rebalancing decisions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            target_duration REAL,
            shy_w REAL,
            ief_w REAL,
            tlt_w REAL
        )
    ''')

    # Table 2: Store logs (for debugging)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            level TEXT,
            message TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_NAME}")

def log_signal(target, weights):
    """Saves a calculation result to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO signals (timestamp, target_duration, shy_w, ief_w, tlt_w)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now(), target, weights['SHY'], weights['IEF'], weights['TLT']))
    conn.commit()
    conn.close()

def log_event(level, message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)', 
                   (datetime.now(), level, message))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
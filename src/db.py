import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "fisr_trading.db")

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value REAL)''')
    cursor.execute("INSERT OR IGNORE INTO config VALUES ('kill_switch', 1.0)")
    cursor.execute("INSERT OR IGNORE INTO config VALUES ('target_duration', 8.0)")
    cursor.execute('''CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME, target_duration REAL,
            shy_w REAL, ief_w REAL, tlt_w REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            timestamp TEXT, ticker TEXT, qty REAL, 
            price REAL, side TEXT, trade_value REAL, status TEXT)''')
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
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''INSERT INTO signals (timestamp, target_duration, shy_w, ief_w, tlt_w)
                    VALUES (?, ?, ?, ?, ?)''', 
                 (datetime.now(), target, weights['SHY'], weights['IEF'], weights['TLT']))
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

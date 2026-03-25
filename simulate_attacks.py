import sqlite3
import time
from datetime import datetime
import random

DB_FILE = 'blocked_ips.db'

dummy_data = [
    ("103.44.55.66", "Tokyo, Japan"),
    ("45.33.22.11", "New York, USA"),
    ("192.168.1.50", "Mumbai, India"),
    ("88.99.100.122", "Berlin, Germany")
]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS blocked_ips
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     ip TEXT, blocked_at TEXT, geo TEXT)''')
    conn.close()

def add_mock():
    ip, city = random.choice(dummy_data)
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO blocked_ips (ip, blocked_at, geo) VALUES (?, ?, ?)", (ip, now, city))
    conn.commit()
    conn.close()
    print(f"Added: {ip}")

if __name__ == "__main__":
    init_db()
    for _ in range(10):
        add_mock()
        time.sleep(0.2)
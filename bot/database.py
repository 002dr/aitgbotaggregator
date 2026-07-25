import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from bot.config import DATABASE_PATH


def init_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_paid INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_text TEXT,
            amount REAL,
            status TEXT DEFAULT 'new',
            operator_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    try:
        cursor.execute("ALTER TABLE requests ADD COLUMN amount REAL")
    except sqlite3.OperationalError:
        pass
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            currency TEXT,
            payment_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_user(user_id: int) -> Optional[dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_user(user_id: int, username: str, full_name: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO users (user_id, username, full_name, is_paid, created_at)
           VALUES (?, ?, ?, COALESCE((SELECT is_paid FROM users WHERE user_id = ?), 0), 
           COALESCE((SELECT created_at FROM users WHERE user_id = ?), CURRENT_TIMESTAMP))""",
        (user_id, username, full_name, user_id, user_id),
    )
    conn.commit()
    conn.close()


def set_user_paid(user_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_paid = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def create_request(user_id: int, request_text: str, amount: float | None = None) -> int:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requests (user_id, request_text, amount) VALUES (?, ?, ?)",
        (user_id, request_text, amount),
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return request_id


def create_payment(user_id: int, amount: float, currency: str, payment_id: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO payments (user_id, amount, currency, payment_id) VALUES (?, ?, ?, ?)",
        (user_id, amount, currency, payment_id),
    )
    conn.commit()
    conn.close()


def update_payment_status(payment_id: str, status: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE payments SET status = ? WHERE payment_id = ?",
        (status, payment_id),
    )
    conn.commit()
    conn.close()


def log_security_event(user_id: int, event_type: str, content: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO security_events (user_id, event_type, content) VALUES (?, ?, ?)",
        (user_id, event_type, content[:500]),
    )
    conn.commit()
    conn.close()

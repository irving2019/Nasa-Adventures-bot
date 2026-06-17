import sqlite3
import os

DB_PATH = "data/users.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            score INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            total_answers INTEGER DEFAULT 0,
            last_quiz_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT score, correct_answers, total_answers, last_quiz_date, username FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'score': row[0],
            'correct_answers': row[1],
            'total_answers': row[2],
            'last_quiz_date': row[3],
            'username': row[4]
        }
    return None

def save_user(user_id: int, username: str, score: int, correct_answers: int, total_answers: int, last_quiz_date: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username, score, correct_answers, total_answers, last_quiz_date)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            score = excluded.score,
            correct_answers = excluded.correct_answers,
            total_answers = excluded.total_answers,
            last_quiz_date = COALESCE(excluded.last_quiz_date, users.last_quiz_date)
    """, (user_id, username, score, correct_answers, total_answers, last_quiz_date))
    conn.commit()
    conn.close()

def get_leaderboard(limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, score, correct_answers FROM users ORDER BY score DESC, correct_answers DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

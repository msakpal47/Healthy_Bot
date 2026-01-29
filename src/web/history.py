import os
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional
from src.config import BASE_DIR, INDEX_DIR

DB_DIR = BASE_DIR / "storage"
DB_PATH = DB_DIR / "history.sqlite"

def ensure_db() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH.as_posix())
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cur.execute("CREATE TABLE IF NOT EXISTS cache (question TEXT PRIMARY KEY, answer TEXT, index_version REAL)")
    conn.commit()
    conn.close()

def current_index_version() -> float:
    try:
        return INDEX_DIR.stat().st_mtime
    except Exception:
        return 0.0

def save_message(session_id: str, role: str, content: str) -> None:
    ensure_db()
    conn = sqlite3.connect(DB_PATH.as_posix())
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    conn.commit()
    conn.close()

def get_history(session_id: str) -> List[Tuple[str, str]]:
    ensure_db()
    conn = sqlite3.connect(DB_PATH.as_posix())
    cur = conn.cursor()
    cur.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,))
    rows = cur.fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]

def find_cached_answer(question: str) -> Optional[str]:
    ensure_db()
    conn = sqlite3.connect(DB_PATH.as_posix())
    cur = conn.cursor()
    cur.execute("SELECT answer, index_version FROM cache WHERE question=?", (question,))
    row = cur.fetchone()
    conn.close()
    ver = current_index_version()
    if row and abs(row[1] - ver) < 1e-6:
        return row[0]
    return None

def save_cached_answer(question: str, answer: str) -> None:
    ensure_db()
    conn = sqlite3.connect(DB_PATH.as_posix())
    cur = conn.cursor()
    cur.execute("REPLACE INTO cache (question, answer, index_version) VALUES (?, ?, ?)", (question, answer, current_index_version()))
    conn.commit()
    conn.close()

import json
import os
import sqlite3
from typing import Optional


def init_db(db_path="messages.db"):
    if os.path.exists(db_path):
        print(f"✅ 데이터베이스가 이미 존재합니다: {db_path}")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()
    print(f"✅ 데이터베이스가 초기화되었습니다: {db_path}")


def save_message(
    id: str,
    role: str,
    content: str,
    metadata: Optional[dict] = None,
    db_path="messages.db",
):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (id, role, content, metadata) VALUES (?, ?, ?, ?)",
        (id, role, content, json.dumps(metadata or {})),
    )
    conn.commit()
    conn.close()


def load_messages(db_path="messages.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages")
    messages = cursor.fetchall()
    conn.close()
    return messages


def clear_db(db_path="messages.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    print(f"✅ 데이터베이스가 초기화되었습니다: {db_path}")

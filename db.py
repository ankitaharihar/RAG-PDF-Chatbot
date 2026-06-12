import sqlite3
from pathlib import Path

DB_PATH = Path("chat_history.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chats(id)
        )
        '''
    )

    conn.commit()
    conn.close()


def create_chat(session_id: str, title: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO chats (session_id, title) VALUES (?,?)', (session_id, title))
    conn.commit()
    chat_id = c.lastrowid
    conn.close()
    return chat_id


def get_or_create_session_chat(session_id: str, title: str = 'Session Chat'):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id FROM chats WHERE session_id=? ORDER BY created_at DESC LIMIT 1', (session_id,))
    row = c.fetchone()
    if row:
        chat_id = row[0]
    else:
        c.execute('INSERT INTO chats (session_id, title) VALUES (?,?)', (session_id, title))
        conn.commit()
        chat_id = c.lastrowid
    conn.close()
    return chat_id


def add_message(chat_id: int, role: str, content: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO messages (chat_id, role, content) VALUES (?,?,?)', (chat_id, role, content))
    conn.commit()
    conn.close()


def get_chats(session_id: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id, title, created_at FROM chats WHERE session_id=? ORDER BY created_at DESC', (session_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_messages(chat_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT role, content, created_at FROM messages WHERE chat_id=? ORDER BY created_at', (chat_id,))
    rows = c.fetchall()
    conn.close()
    return rows

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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
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

    # Backward-compatible schema migration for existing SQLite databases.
    c.execute("PRAGMA table_info(chats)")
    columns = {row[1] for row in c.fetchall()}
    if "user_id" not in columns:
        c.execute("ALTER TABLE chats ADD COLUMN user_id INTEGER")

    conn.commit()
    conn.close()


def create_user(username: str, email: str, password_hash: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email.lower().strip(), password_hash),
    )
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, username, email, password_hash FROM users WHERE email = ?",
        (email.lower().strip(),),
    )
    row = c.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row


def create_chat(session_id: str, title: str, user_id: int | None = None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO chats (user_id, session_id, title) VALUES (?, ?, ?)",
        (user_id, session_id, title),
    )
    conn.commit()
    chat_id = c.lastrowid
    conn.close()
    return chat_id


def get_or_create_session_chat(session_id: str, title: str = 'Session Chat', user_id: int | None = None):
    conn = get_conn()
    c = conn.cursor()
    if user_id is None:
        c.execute(
            'SELECT id FROM chats WHERE session_id=? AND user_id IS NULL ORDER BY created_at DESC LIMIT 1',
            (session_id,),
        )
    else:
        c.execute(
            'SELECT id FROM chats WHERE session_id=? AND user_id=? ORDER BY created_at DESC LIMIT 1',
            (session_id, user_id),
        )
    row = c.fetchone()
    if row:
        chat_id = row[0]
    else:
        c.execute(
            'INSERT INTO chats (user_id, session_id, title) VALUES (?, ?, ?)',
            (user_id, session_id, title),
        )
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


def get_chats(session_id: str, user_id: int | None = None):
    conn = get_conn()
    c = conn.cursor()
    if user_id is None:
        c.execute(
            'SELECT id, title, created_at FROM chats WHERE session_id=? AND user_id IS NULL ORDER BY created_at DESC',
            (session_id,),
        )
    else:
        c.execute(
            'SELECT id, title, created_at FROM chats WHERE session_id=? AND user_id=? ORDER BY created_at DESC',
            (session_id, user_id),
        )
    rows = c.fetchall()
    conn.close()
    return rows


def get_chats_for_user(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, title, created_at FROM chats WHERE user_id=? ORDER BY created_at DESC',
        (user_id,),
    )
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

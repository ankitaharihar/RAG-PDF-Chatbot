import sqlite3
import json
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
        CREATE TABLE IF NOT EXISTS pdfs (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
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
            pdf_ids TEXT,
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

    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        '''
    )

    # Backward-compatible schema migration for existing SQLite databases.
    c.execute("PRAGMA table_info(chats)")
    columns = {row[1] for row in c.fetchall()}
    if "user_id" not in columns:
        c.execute("ALTER TABLE chats ADD COLUMN user_id INTEGER")
    if "pdf_ids" not in columns:
        c.execute("ALTER TABLE chats ADD COLUMN pdf_ids TEXT")

    c.execute("PRAGMA table_info(pdfs)")
    pdf_columns = {row[1] for row in c.fetchall()}
    if pdf_columns and "stored_name" not in pdf_columns:
        c.execute("ALTER TABLE pdfs ADD COLUMN stored_name TEXT")

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


def update_user_password(user_id: int, password_hash: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password_hash=? WHERE id=?",
        (password_hash, user_id),
    )
    conn.commit()
    conn.close()


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


def create_password_reset_token(user_id: int, token_hash: str, expires_at: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, token_hash, expires_at),
    )
    conn.commit()
    reset_id = c.lastrowid
    conn.close()
    return reset_id


def get_active_password_reset(token_hash: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, user_id, expires_at, used_at
        FROM password_resets
        WHERE token_hash=?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (token_hash,),
    )
    row = c.fetchone()
    conn.close()
    return row


def mark_password_reset_used(reset_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE password_resets SET used_at=CURRENT_TIMESTAMP WHERE id=?",
        (reset_id,),
    )
    conn.commit()
    conn.close()


def add_pdf(user_id: int, original_name: str, stored_name: str, stored_path: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO pdfs (user_id, original_name, stored_name, stored_path) VALUES (?, ?, ?, ?)",
        (user_id, original_name, stored_name, stored_path),
    )
    conn.commit()
    pdf_id = c.lastrowid
    conn.close()
    return pdf_id


def get_pdfs_for_user(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, original_name, stored_name, stored_path, created_at FROM pdfs WHERE user_id=? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_pdfs_by_ids(user_id: int, pdf_ids: list[int]):
    if not pdf_ids:
        return []

    placeholders = ",".join(["?"] * len(pdf_ids))
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        f"SELECT id, original_name, stored_name, stored_path, created_at FROM pdfs WHERE user_id=? AND id IN ({placeholders}) ORDER BY created_at DESC",
        [user_id, *pdf_ids],
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_pdf_by_id(pdf_id: int, user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, original_name, stored_name, stored_path, created_at FROM pdfs WHERE id=? AND user_id=?",
        (pdf_id, user_id),
    )
    row = c.fetchone()
    conn.close()
    return row


def delete_pdf(pdf_id: int, user_id: int):
    row = get_pdf_by_id(pdf_id, user_id)
    if not row:
        return False

    path = Path(row[3])
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM pdfs WHERE id=? AND user_id=?", (pdf_id, user_id))
    conn.commit()
    conn.close()
    return True


def set_chat_pdf_ids(chat_id: int, pdf_ids: list[int]):
    conn = get_conn()
    c = conn.cursor()
    pdf_ids_json = json.dumps(pdf_ids)
    c.execute("UPDATE chats SET pdf_ids=? WHERE id=?", (pdf_ids_json, chat_id))
    conn.commit()
    conn.close()


def get_chat_pdf_ids(chat_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT pdf_ids FROM chats WHERE id=?", (chat_id,))
    row = c.fetchone()
    conn.close()

    if not row or not row[0]:
        return []

    try:
        value = json.loads(row[0])
        return [int(pdf_id) for pdf_id in value]
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def create_chat(session_id: str, title: str, user_id: int | None = None, pdf_ids: list[int] | None = None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO chats (user_id, session_id, title, pdf_ids) VALUES (?, ?, ?, ?)",
        (user_id, session_id, title, json.dumps(pdf_ids or [])),
    )
    conn.commit()
    chat_id = c.lastrowid
    conn.close()
    return chat_id


def get_or_create_session_chat(
    session_id: str,
    title: str = 'Session Chat',
    user_id: int | None = None,
    pdf_ids: list[int] | None = None,
):
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
            'INSERT INTO chats (user_id, session_id, title, pdf_ids) VALUES (?, ?, ?, ?)',
            (user_id, session_id, title, json.dumps(pdf_ids or [])),
        )
        conn.commit()
        chat_id = c.lastrowid
    conn.close()
    return chat_id


def add_message(chat_id: int, role: str, content: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO messages (chat_id, role, content) VALUES (?,?,?)',
              (chat_id, role, content))
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


def update_chat_title(chat_id: int, title: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE chats SET title=? WHERE id=?", (title, chat_id))
    conn.commit()
    conn.close()


def get_messages(chat_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT role, content, created_at FROM messages WHERE chat_id=? ORDER BY created_at', (chat_id,))
    rows = c.fetchall()
    conn.close()
    return rows

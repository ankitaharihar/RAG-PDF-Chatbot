import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt

import database.db as db


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_reset_token(user_id: int):
    token = secrets.token_urlsafe(16)
    token_hash = hash_reset_token(token)
    expires_at = (datetime.now() + timedelta(minutes=20)
                  ).isoformat(timespec="seconds")
    db.create_password_reset_token(user_id, token_hash, expires_at)
    return token, expires_at


def reset_user_password(email: str, token: str, new_password: str):
    user = db.get_user_by_email(email)
    if not user:
        return False, "Email not found."

    token_hash = hash_reset_token(token.strip())
    reset_row = db.get_active_password_reset(token_hash)
    if not reset_row:
        return False, "Invalid reset token."

    reset_id, reset_user_id, expires_at, used_at = reset_row
    if used_at:
        return False, "This reset token has already been used."

    try:
        expires_at_value = datetime.fromisoformat(expires_at)
    except ValueError:
        return False, "Stored reset token is invalid. Please generate a new one."

    if datetime.now() > expires_at_value:
        return False, "Reset token expired. Generate a new one."

    if reset_user_id != user[0]:
        return False, "Reset token does not match this email."

    password_hash = bcrypt.hashpw(new_password.encode(
        "utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.update_user_password(user[0], password_hash)
    db.mark_password_reset_used(reset_id)
    return True, "Password updated successfully."

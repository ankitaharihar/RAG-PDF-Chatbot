import re
import uuid
from datetime import datetime

import bcrypt
import streamlit as st

import database.db as db

from auth.password_reset import create_reset_token, reset_user_password


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,25}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.match(username.strip()))


def validate_password(password: str):
    errors = []

    if len(password) < 8:
        errors.append("Minimum 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("At least 1 uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("At least 1 lowercase letter")
    if not re.search(r"\d", password):
        errors.append("At least 1 number")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("At least 1 special character")

    return errors


def password_strength_level(password: str):
    checks = [
        len(password) >= 8,
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"\d", password)),
        bool(re.search(r"[^A-Za-z0-9]", password)),
    ]
    score = sum(1 for check in checks if check)

    if score <= 2:
        return "Weak", 0.33, "#ef4444"
    if score == 3 or score == 4:
        return "Medium", 0.66, "#f59e0b"
    return "Strong", 1.0, "#22c55e"


def clear_session_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def set_authenticated_user(user_row):
    st.session_state.authenticated = True
    st.session_state.user_id = user_row[0]
    st.session_state.username = user_row[1]
    st.session_state.email = user_row[2]
    st.session_state.login_time = datetime.now().isoformat(timespec="seconds")
    st.session_state.history = []
    st.session_state.current_chat_id = None
    st.session_state.active_pdf_ids = []


def logout_user():
    clear_session_state()


def initialize_auth():
    defaults = {
        "authenticated": False,
        "user_id": None,
        "username": "",
        "email": "",
        "session_id": str(uuid.uuid4()),
        "login_time": "",
        "history": [],
        "current_chat_id": None,
        "active_pdf_ids": [],
        "memory_turns": 6,
        "sidebar_upload_counter": 0,
        "auth_mode": "Login",
        "pending_reset_email": "",
        "pending_reset_token": "",
        "auth_notice": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_auth_sidebar():
    with st.sidebar:
        st.markdown("## 🔐 Account")
        st.caption("Login, create an account, or reset your password.")

        if st.session_state.get("auth_notice"):
            st.info(st.session_state.auth_notice)
            st.session_state.auth_notice = ""

        auth_mode = st.radio(
            "Mode",
            ["Login", "Sign Up", "Forgot Password", "Reset Password"],
            horizontal=False,
            index=["Login", "Sign Up", "Forgot Password",
                   "Reset Password"].index(st.session_state.auth_mode)
            if st.session_state.auth_mode in ["Login", "Sign Up", "Forgot Password", "Reset Password"]
            else 0,
        )
        st.session_state.auth_mode = auth_mode

        if auth_mode == "Login":
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                show_password = st.checkbox(
                    "Show Password", key="login_show_password")
                password = st.text_input(
                    "Password", type="default" if show_password else "password")
                submitted = st.form_submit_button("Login")

            if submitted:
                email_value = email.strip().lower()

                if not email_value or not password:
                    st.error("❌ Email and password are required.")
                    return

                if not is_valid_email(email_value):
                    st.error("❌ Enter a valid email address.")
                    return

                user = db.get_user_by_email(email_value)
                if not user:
                    st.error("❌ Email not found. Please sign up first.")
                    return

                stored_hash = user[3]
                if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                    st.error("❌ Incorrect password. Please try again.")
                    return

                set_authenticated_user(user)
                st.success(f"✅ Welcome back, {user[1]}!")
                st.rerun()

        elif auth_mode == "Sign Up":
            with st.form("signup_form"):
                username = st.text_input("Username", placeholder="ankita_123")
                email = st.text_input("Email", placeholder="you@example.com")
                show_password = st.checkbox(
                    "Show Password", key="signup_show_password")
                password = st.text_input(
                    "Password", type="default" if show_password else "password")

                if password:
                    strength_label, strength_ratio, strength_color = password_strength_level(
                        password)
                    st.markdown(f"**Password Strength: {strength_label}**")
                    st.progress(strength_ratio)
                    st.caption(
                        "Use at least 8 characters, with uppercase, lowercase, number, and special character.")

                submitted = st.form_submit_button("Sign Up")

            if submitted:
                username_value = username.strip()
                email_value = email.strip().lower()

                if not username_value or not email_value or not password:
                    st.error("❌ Username, email, and password are required.")
                    return

                if not is_valid_username(username_value):
                    st.error(
                        "❌ Username must be 3-25 characters and use only letters, numbers, or _.")
                    return

                if not is_valid_email(email_value):
                    st.error("❌ Enter a valid email address.")
                    return

                password_errors = validate_password(password)
                if password_errors:
                    st.error("❌ " + "; ".join(password_errors))
                    return

                if db.get_user_by_email(email_value):
                    st.error("❌ An account with this email already exists.")
                    return

                password_hash = bcrypt.hashpw(password.encode(
                    "utf-8"), bcrypt.gensalt()).decode("utf-8")
                user_id = db.create_user(
                    username_value, email_value, password_hash)

                user = (user_id, username_value, email_value, password_hash)
                set_authenticated_user(user)
                st.success(
                    "🎉 Account created successfully! Welcome to AI Study Assistant.")
                st.rerun()

        elif auth_mode == "Forgot Password":
            with st.form("forgot_password_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                submitted = st.form_submit_button("Generate Reset Token")

            if submitted:
                email_value = email.strip().lower()

                if not email_value:
                    st.error("❌ Email is required.")
                    return

                if not is_valid_email(email_value):
                    st.error("❌ Enter a valid email address.")
                    return

                user = db.get_user_by_email(email_value)
                if not user:
                    st.error("❌ Email not found.")
                    return

                token, _expires_at = create_reset_token(user[0])
                st.session_state.pending_reset_email = email_value
                st.session_state.pending_reset_token = token
                st.session_state.auth_mode = "Reset Password"
                st.session_state.auth_notice = "✅ Reset token generated. The reset form is ready."
                st.rerun()

        else:
            with st.form("reset_password_form"):
                email_default = st.session_state.get("pending_reset_email", "")
                token_default = st.session_state.get("pending_reset_token", "")
                email = st.text_input(
                    "Email", value=email_default, placeholder="you@example.com")
                token = st.text_input(
                    "Reset Token", value=token_default, placeholder="Paste reset token here")
                show_password = st.checkbox(
                    "Show Password", key="reset_show_password")
                new_password = st.text_input(
                    "New Password", type="default" if show_password else "password")
                confirm_password = st.text_input(
                    "Confirm New Password", type="default" if show_password else "password")

                if new_password:
                    strength_label, strength_ratio, _ = password_strength_level(
                        new_password)
                    st.markdown(f"**Password Strength: {strength_label}**")
                    st.progress(strength_ratio)

                submitted = st.form_submit_button("Update Password")

            if submitted:
                email_value = email.strip().lower()

                if not email_value or not token or not new_password or not confirm_password:
                    st.error("❌ All reset fields are required.")
                    return

                if new_password != confirm_password:
                    st.error("❌ Passwords do not match.")
                    return

                password_errors = validate_password(new_password)
                if password_errors:
                    st.error("❌ " + "; ".join(password_errors))
                    return

                success, message = reset_user_password(
                    email_value, token, new_password)
                if not success:
                    st.error(f"❌ {message}")
                    return

                st.session_state.auth_notice = f"✅ {message} Please log in with your new password."
                st.session_state.auth_mode = "Login"
                st.session_state.pending_reset_email = ""
                st.session_state.pending_reset_token = ""
                st.rerun()

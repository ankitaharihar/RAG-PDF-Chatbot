import re
import uuid
from datetime import datetime

import bcrypt
import streamlit as st

import database.db as db
from auth.password_reset import request_password_reset, reset_user_password
from components.forgot_password import render_forgot_password
from components.reset_password import render_reset_password

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,25}$")

AUTH_MODES = [
    "Login",
    "Sign Up",
    "Forgot Password",
    "Reset Password",
]


# =========================================================
# VALIDATION
# =========================================================

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

    score = sum(checks)

    if score <= 2:
        return "Weak", 0.33

    if score <= 4:
        return "Medium", 0.66

    return "Strong", 1.0


# =========================================================
# SESSION
# =========================================================

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
        "auth_page": "login",
        "auth_mode": "Login",
        "pending_reset_email": "",
        "pending_reset_token": "",
        "auth_notice": "",

    }

    # Initialize session state
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # -----------------------------------------
    # Handle password-reset link from email
    # Example:
    # ?mode=reset&email=user@gmail.com&token=abc123
    # -----------------------------------------
    mode = st.query_params.get("mode")
    reset_email = st.query_params.get("email")
    reset_token = st.query_params.get("token")

    if mode == "reset" and reset_email and reset_token:
     st.session_state.auth_page = "reset"
     st.session_state.pending_reset_email = reset_email
     st.session_state.pending_reset_token = reset_token

def clear_session_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def set_authenticated_user(user_row):
    st.session_state.authenticated = True
    st.session_state.user_id = user_row[0]
    st.session_state.username = user_row[1]
    st.session_state.email = user_row[2]
    st.session_state.login_time = datetime.now().isoformat(
        timespec="seconds"
    )

    st.session_state.history = []
    st.session_state.current_chat_id = None
    st.session_state.active_pdf_ids = []


def logout_user():
    clear_session_state()


# =========================================================
# MODE CHANGE
# =========================================================

def auth_mode_changed():
    st.session_state.auth_mode = st.session_state.auth_mode_selector


# =========================================================
# LOGIN
# =========================================================

def render_login():
    with st.form("login_form"):

        email = st.text_input(
            "Email",
            placeholder="you@example.com",
        )

        show_password = st.checkbox(
            "Show Password",
            key="login_show_password",
        )

        password = st.text_input(
            "Password",
            type="default" if show_password else "password",
        )

        submitted = st.form_submit_button(
            "Login",
            width="stretch",
        )

    if not submitted:
        return

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

    try:
        password_correct = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
    except Exception:
        st.error("❌ Unable to verify password.")
        return

    if not password_correct:
        st.error("❌ Incorrect password.")
        return

    set_authenticated_user(user)

    st.session_state.auth_notice = (
        f"✅ Welcome back, {user[1]}!"
    )

    st.rerun()


# =========================================================
# SIGN UP
# =========================================================

def render_signup():
    with st.form("signup_form"):

        username = st.text_input(
            "Username",
            placeholder="ankita_123",
        )

        email = st.text_input(
            "Email",
            placeholder="you@example.com",
        )

        show_password = st.checkbox(
            "Show Password",
            key="signup_show_password",
        )

        password = st.text_input(
            "Password",
            type="default" if show_password else "password",
        )

        if password:
            strength_label, strength_ratio = (
                password_strength_level(password)
            )

            st.markdown(
                f"**Password Strength: {strength_label}**"
            )

            st.progress(strength_ratio)

            st.caption(
                "Use 8+ characters with uppercase, lowercase, "
                "number and special character."
            )

        submitted = st.form_submit_button(
            "Create Account",
            width="stretch",
        )

    if not submitted:
        return

    username_value = username.strip()
    email_value = email.strip().lower()

    if not username_value or not email_value or not password:
        st.error(
            "❌ Username, email and password are required."
        )
        return

    if not is_valid_username(username_value):
        st.error(
            "❌ Username must be 3-25 characters and contain "
            "only letters, numbers or _."
        )
        return

    if not is_valid_email(email_value):
        st.error("❌ Enter a valid email address.")
        return

    password_errors = validate_password(password)

    if password_errors:
        st.error(
            "❌ " + "; ".join(password_errors)
        )
        return

    if db.get_user_by_email(email_value):
        st.error(
            "❌ An account with this email already exists."
        )
        return

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    user_id = db.create_user(
        username_value,
        email_value,
        password_hash,
    )

    user = (
        user_id,
        username_value,
        email_value,
        password_hash,
    )

    set_authenticated_user(user)

    st.session_state.auth_notice = (
        "🎉 Account created successfully!"
    )

    st.rerun()


# =========================================================
# FORGOT PASSWORD
# =========================================================

def render_forgot_password():
    st.markdown("### 🔑 Forgot Password")

    st.caption(
        "Enter your registered email and we'll send "
        "you a password reset link."
    )

    with st.form("forgot_password_form"):

        email = st.text_input(
            "Registered Email",
            placeholder="you@example.com",
        )

        submitted = st.form_submit_button(
            "📧 Send Reset Email",
            width="stretch",
        )

    if not submitted:
        return

    email_value = email.strip().lower()

    if not email_value:
        st.error("❌ Email is required.")
        return

    if not is_valid_email(email_value):
        st.error("❌ Enter a valid email address.")
        return

    with st.spinner("Sending reset email..."):
        success, message = request_password_reset(
            email_value
        )

    if not success:
        st.error(f"❌ {message}")
        return

    st.session_state.pending_reset_email = email_value

    st.success(
        "📧 Reset email sent! Please check your inbox."
    )

    st.caption(
        "The reset link expires in 20 minutes."
    )


# =========================================================
# RESET PASSWORD
# =========================================================

def render_reset_password():
    st.markdown("### 🔐 Reset Password")

    st.caption(
        "Enter your email, reset token and new password."
    )

    email_default = st.session_state.get(
        "pending_reset_email",
        "",
    )

    token_default = st.session_state.get(
        "pending_reset_token",
        "",
    )

    with st.form("reset_password_form"):

        email = st.text_input(
            "Email",
            value=email_default,
            placeholder="you@example.com",
        )

        token = st.text_input(
            "Reset Token",
            value=token_default,
            type="password",
        )

        show_password = st.checkbox(
            "Show Password",
            key="reset_show_password",
        )

        new_password = st.text_input(
            "New Password",
            type="default" if show_password else "password",
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="default" if show_password else "password",
        )

        if new_password:
            strength_label, strength_ratio = (
                password_strength_level(new_password)
            )

            st.markdown(
                f"**Password Strength: {strength_label}**"
            )

            st.progress(strength_ratio)

        submitted = st.form_submit_button(
            "🔐 Update Password",
            width="stretch",
        )

    if not submitted:
        return

    email_value = email.strip().lower()
    token_value = token.strip()

    if (
        not email_value
        or not token_value
        or not new_password
        or not confirm_password
    ):
        st.error("❌ All reset fields are required.")
        return

    if not is_valid_email(email_value):
        st.error("❌ Enter a valid email address.")
        return

    if new_password != confirm_password:
        st.error("❌ Passwords do not match.")
        return

    password_errors = validate_password(
        new_password
    )

    if password_errors:
        st.error(
            "❌ " + "; ".join(password_errors)
        )
        return

    success, message = reset_user_password(
        email_value,
        token_value,
        new_password,
    )

    if not success:
        st.error(f"❌ {message}")
        return

    st.session_state.pending_reset_email = ""
    st.session_state.pending_reset_token = ""

    st.session_state.auth_notice = (
        "✅ Password changed successfully. "
        "Please login with your new password."
    )

    # Important:
    # Change radio BEFORE next rerun.
    st.session_state.auth_mode = "Login"
    st.session_state.auth_mode_selector = "Login"

    st.rerun()


# =========================================================
# AUTH SIDEBAR
# =========================================================

def render_auth_sidebar():

    initialize_auth()

    with st.sidebar:

        st.markdown("## 🔐 Account")

        st.caption(
            "Login, create an account, or reset your password."
        )

        # -----------------------------------------
        # Notice
        # -----------------------------------------

        notice = st.session_state.get(
            "auth_notice",
            "",
        )

        if notice:
            st.info(notice)
            st.session_state.auth_notice = ""

        # -----------------------------------------
        # Initialize radio state BEFORE widget
        # -----------------------------------------

        if "auth_mode_selector" not in st.session_state:

            current_mode = st.session_state.get(
                "auth_mode",
                "Login",
            )

            if current_mode not in AUTH_MODES:
                current_mode = "Login"

            st.session_state.auth_mode_selector = (
                current_mode
            )

        # -----------------------------------------
        # Auth navigation
        # -----------------------------------------

        st.radio(
            "Mode",
            AUTH_MODES,
            key="auth_mode_selector",
            on_change=auth_mode_changed,
        )

        auth_mode = st.session_state.auth_mode_selector
        if auth_mode == "Forgot Password":
         st.session_state.auth_page = "forgot"
         st.rerun()
        # -----------------------------------------
        # Render selected screen
        # -----------------------------------------

        if auth_mode == "Login":
            render_login()

        elif auth_mode == "Sign Up":
            render_signup()

        elif auth_mode == "Forgot Password":
            render_forgot_password()

        elif auth_mode == "Reset Password":
            render_reset_password()
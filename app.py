import os
import re
import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import bcrypt
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

import database.db as db

from utils.pdf_utils import (
    save_uploaded_pdfs,
    load_documents_from_pdfs,
    build_citations
)

from utils.rag_utils import (
    create_vectorstore,
    retrieve_context
)

from utils.ui_utils import (
    render_turns
)


def apply_ui_theme():
    st.markdown(
        """
                <style>
                    .stApp {
                        background:
                            radial-gradient(circle at top left, rgba(37, 99, 235, 0.20), transparent 30%),
                            radial-gradient(circle at top right, rgba(20, 184, 166, 0.16), transparent 26%),
                            linear-gradient(180deg, #07111F 0%, #0B1220 100%);
                        color: #E5EEF9;
                    }

                    .block-container {
                        padding-top: 1.5rem;
                        padding-bottom: 2.5rem;
                        max-width: 1280px;
                    }

                    section[data-testid="stSidebar"] {
                        background: linear-gradient(180deg, #0A1322 0%, #07111F 100%);
                        border-right: 1px solid rgba(148, 163, 184, 0.14);
                    }

                    section[data-testid="stSidebar"] .block-container {
                        padding-top: 1rem;
                    }

                    [data-testid="stChatMessage"] {
                        border-radius: 18px;
                        padding: 0.2rem 0.2rem;
                    }

                    [data-testid="stChatMessage"] > div:first-child {
                        border-radius: 999px;
                    }

                    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
                        font-size: 1.0rem;
                        line-height: 1.65;
                    }

                    .hero-card {
                        border: 1px solid rgba(148, 163, 184, 0.16);
                        background: rgba(15, 23, 42, 0.72);
                        backdrop-filter: blur(16px);
                        border-radius: 24px;
                        padding: 1.2rem 1.35rem;
                        box-shadow: 0 20px 60px rgba(2, 6, 23, 0.35);
                        margin-bottom: 1rem;
                    }

                    .hero-title {
                        font-size: 2rem;
                        font-weight: 800;
                        margin: 0;
                        letter-spacing: -0.03em;
                    }

                    .hero-subtitle {
                        color: #94A3B8;
                        margin-top: 0.35rem;
                        margin-bottom: 0;
                    }

                    .metric-card {
                        border: 1px solid rgba(148, 163, 184, 0.16);
                        background: rgba(15, 23, 42, 0.66);
                        border-radius: 18px;
                        padding: 0.85rem 1rem;
                    }

                    .metric-label {
                        color: #94A3B8;
                        font-size: 0.78rem;
                        text-transform: uppercase;
                        letter-spacing: 0.08em;
                        margin-bottom: 0.25rem;
                    }

                    .metric-value {
                        color: #F8FAFC;
                        font-size: 1.5rem;
                        font-weight: 700;
                    }

                    .stButton > button {
                        border-radius: 14px;
                        border: 1px solid rgba(96, 165, 250, 0.35);
                        background: linear-gradient(135deg, #2563EB 0%, #14B8A6 100%);
                        color: white;
                        font-weight: 700;
                        padding: 0.55rem 1rem;
                    }

                    .stButton > button:hover {
                        border-color: rgba(255, 255, 255, 0.25);
                        filter: brightness(1.05);
                    }

                    .stTextInput input, .stSelectbox, .stMultiSelect, .stTextArea textarea {
                        border-radius: 14px !important;
                    }

                    .stChatInput textarea {
                        border-radius: 18px !important;
                    }
                </style>
                """,
        unsafe_allow_html=True,
    )


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
    score = 0
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


st.set_page_config(page_title="Multi-PDF RAG Chatbot",
                   page_icon="📄", layout="wide")
apply_ui_theme()


load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

if not api_key:
    st.error("OPENROUTER_API_KEY missing in .env")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)


db.init_db()


def initialize_state():
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


def load_chat_history(chat_id: int):
    turns = []
    current_turn = None

    for role, content, _ in db.get_messages(chat_id):
        if role == "user":
            current_turn = {"question": content, "answer": "", "sources": []}
            turns.append(current_turn)
        elif role == "bot" and current_turn is not None:
            current_turn["answer"] = content
        elif role == "source" and current_turn is not None:
            if "||" in content:
                citation, excerpt = content.split("||", 1)
            else:
                citation, excerpt = content, ""
            current_turn["sources"].append(
                {"citation": citation, "excerpt": excerpt})

    return turns


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
            key="auth_mode_radio",
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
                st.session_state.auth_mode_radio = "Reset Password"
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
                st.session_state.auth_mode_radio = "Login"
                st.session_state.pending_reset_email = ""
                st.session_state.pending_reset_token = ""
                st.rerun()


def load_chat_into_state(chat_id: int):
    st.session_state.current_chat_id = chat_id
    st.session_state.history = load_chat_history(chat_id)
    st.session_state.active_pdf_ids = db.get_chat_pdf_ids(chat_id)


initialize_state()

if not st.session_state.authenticated:
    render_auth_sidebar()

    hero_col1, hero_col2 = st.columns([1.4, 1])

    with hero_col1:
        st.markdown(
            """
            <div class='hero-card' style='padding: 2rem 2.2rem;'>
                <p class='hero-subtitle' style='font-size:0.9rem; letter-spacing:0.14em; text-transform:uppercase;'>AI Study Assistant</p>
                <h1 class='hero-title' style='font-size:3rem; margin-top:0.25rem;'>Chat with PDFs using AI</h1>
                <p class='hero-subtitle' style='font-size:1.1rem; max-width: 720px;'>Generate notes, summaries, MCQs, and interview questions from your documents while keeping every chat tied to your account.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        feature_cols = st.columns(4)
        feature_labels = ["Generate Notes",
                          "Summaries", "MCQs", "Interview Questions"]
        for col, label in zip(feature_cols, feature_labels):
            with col:
                st.markdown(
                    f"""
                    <div class='metric-card'>
                        <div class='metric-label'>Feature</div>
                        <div class='metric-value' style='font-size:1rem;'>{label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with hero_col2:
        st.markdown(
            """
            <div class='hero-card'>
                <div class='metric-label'>Get started</div>
                <p style='margin:0.25rem 0 1rem 0; color:#E5EEF9;'>Use the actions below to jump straight into the auth flow.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Login", use_container_width=True):
                st.session_state.auth_mode = "Login"
                st.session_state.auth_mode_radio = "Login"
                st.rerun()
        with c2:
            if st.button("Sign Up", use_container_width=True):
                st.session_state.auth_mode = "Sign Up"
                st.session_state.auth_mode_radio = "Sign Up"
                st.rerun()

        st.markdown(
            """
            <div class='hero-card' style='margin-top:1rem;'>
                <div class='metric-label'>Why sign in?</div>
                <p style='margin:0.5rem 0 0 0; color:#CBD5E1;'>Private PDF library, saved chats, and resettable account access.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()

user_record = db.get_user_by_id(st.session_state.user_id)
if user_record:
    st.session_state.username = user_record[1]
    st.session_state.email = user_record[2]


with st.sidebar:
    logo_path = Path("assets/logo.svg")
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 👤 Account")

    st.markdown(
        f"""
        <div class='hero-card' style='padding: 1rem 1.05rem; margin-bottom: 0.9rem;'>
            <div class='metric-label'>Signed in as</div>
            <div style='font-size:1.2rem; font-weight:700; color:#F8FAFC;'>{st.session_state.username}</div>
            <div style='color:#94A3B8; margin-top:0.2rem;'>{st.session_state.email}</div>
            <div style='border-top:1px solid rgba(148,163,184,0.16); margin:0.85rem 0 0.6rem 0;'></div>
            <div style='color:#CBD5E1; font-size:0.9rem;'>Login time: {st.session_state.login_time or 'N/A'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.history = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("## 💬 Chat History")
    st.caption("Open previous conversations")
    user_chats = db.get_chats_for_user(st.session_state.user_id)
    chat_options = [(None, "(new chat)")] + [(chat_id, title)
                                             for chat_id, title, _ in user_chats]

    default_index = 0
    if st.session_state.current_chat_id is not None:
        for index, (chat_id, _title) in enumerate(chat_options):
            if chat_id == st.session_state.current_chat_id:
                default_index = index
                break

    selected_chat = st.selectbox(
        "Open saved chat",
        options=chat_options,
        index=default_index,
        format_func=lambda item: item[1],
    )

    if selected_chat[0] is None:
        if st.session_state.current_chat_id is not None:
            st.session_state.current_chat_id = None
            st.session_state.history = []
    elif st.session_state.current_chat_id != selected_chat[0]:
        load_chat_into_state(selected_chat[0])
        st.rerun()

    st.markdown("## 📚 My PDFs")
    st.caption("Upload once, use forever")
    library_upload_key = f"library_upload_{st.session_state.sidebar_upload_counter}"

    with st.form("library_upload_form", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "Upload PDFs once and reuse them forever",
            type="pdf",
            accept_multiple_files=True,
            key=library_upload_key,
        )
        upload_submit = st.form_submit_button("Save to Library")

    if upload_submit and uploaded_files:
        new_pdf_ids = save_uploaded_pdfs(
            uploaded_files,
            st.session_state.user_id,
            db
        )
        st.session_state.active_pdf_ids = list(dict.fromkeys(
            [*st.session_state.active_pdf_ids, *new_pdf_ids]))
        st.session_state.sidebar_upload_counter += 1
        st.success(f"Saved {len(new_pdf_ids)} PDF(s) to your library.")
        st.rerun()

    pdf_rows = db.get_pdfs_for_user(st.session_state.user_id)

    if pdf_rows:
        pdf_options = pdf_rows

        default_selection = [
            row for row in pdf_options
            if row[0] in st.session_state.active_pdf_ids
        ]

        if not default_selection:
            default_selection = pdf_options
            st.session_state.active_pdf_ids = [
                row[0] for row in pdf_options
            ]

        selected_pdf_rows = st.multiselect(
            "My PDFs",
            options=pdf_options,
            default=default_selection,
            format_func=lambda row: row[1],
            key="library_multiselect",
        )

        st.session_state.active_pdf_ids = [
            row[0] for row in selected_pdf_rows
        ]

        st.caption(
            "Selected PDFs are used for retrieval in the active chat."
        )

        if st.button(
            "Delete selected PDFs",
            use_container_width=True
        ):

            for pdf_row in selected_pdf_rows:

                db.delete_pdf(
                    pdf_row[0],
                    st.session_state.user_id
                )

            st.success("Selected PDF(s) deleted.")
            st.rerun()

    else:

        st.info(
            "Upload PDFs here once. They will stay in your library until you delete them."
        )
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        clear_session_state()
        st.rerun()


st.markdown("""
<div style='text-align:center; padding-top:40px;'>

<h1>📚 AI Study Assistant</h1>

<p style='font-size:22px; color:#B8C1EC;'>
Chat with PDFs, generate notes,
MCQs and interview questions instantly.
</p>

</div>
""", unsafe_allow_html=True)
if st.session_state.history:
    render_turns(st.session_state.history)

selected_pdf_ids = st.session_state.active_pdf_ids[:]
if not selected_pdf_ids and db.get_pdfs_for_user(st.session_state.user_id):
    selected_pdf_ids = [row[0]
                        for row in db.get_pdfs_for_user(st.session_state.user_id)]

selected_pdf_rows = db.get_pdfs_by_ids(
    st.session_state.user_id, selected_pdf_ids)


if not selected_pdf_rows:
    st.markdown("""
<div style='text-align:center; margin-top:80px;'>

<h1>📂 No PDFs Selected</h1>

<p style='font-size:20px; color:#B8C1EC;'>
Upload PDFs from the sidebar to start chatting with your documents.
</p>

</div>
""", unsafe_allow_html=True)

    st.stop()
    st.stop()

with st.spinner("📖 Reading PDFs..."):
    documents = load_documents_from_pdfs(
        selected_pdf_rows
    )

if not documents:
    st.error("No readable content found in the selected PDFs.")
    st.stop()

pdf_key = "_".join(
    str(row[0]) for row in selected_pdf_rows
)

if (
    "vectorstore" not in st.session_state
    or st.session_state.get("pdf_key") != pdf_key
):
    st.session_state.vectorstore = create_vectorstore(
        documents
    )
    st.session_state.pdf_key = pdf_key

vectorstore = st.session_state.vectorstore

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    summary_btn = st.button(
        "📝 Summary",
        use_container_width=True
    )

with col2:
    notes_btn = st.button(
        "📚 Notes",
        use_container_width=True
    )

with col3:
    mcq_btn = st.button(
        "❓ MCQs",
        use_container_width=True
    )

with col4:
    interview_btn = st.button(
        "🎯 Interview",
        use_container_width=True
    )

with col5:
    resume_btn = st.button(
        "📄 Resume",
        use_container_width=True
    )

st.divider()
question = None

if summary_btn:
    question = """
    Generate a complete summary of the uploaded PDFs.
    """

elif notes_btn:
    question = """
    Create detailed study notes with headings,
    bullet points and key concepts.
    """

elif mcq_btn:
    question = """
    Generate 15 MCQs from the uploaded PDFs.

    Format:

    Q1.
    A.
    B.
    C.
    D.

    Correct Answer:
    """

elif interview_btn:
    question = """
    Generate interview questions and answers
    from the uploaded PDFs.
    """

elif resume_btn:
    question = """
    Analyze the resume and provide:

    1. Resume Score out of 10
    2. Strengths
    3. Weaknesses
    4. Missing Skills
    5. ATS Improvement Tips
    """

user_input = st.chat_input(
    "💬 Ask anything about your PDFs..."
)

if user_input:
    question = user_input

if question:
    matched_docs, context = retrieve_context(
        vectorstore,
        question
    )

    recent_turns = st.session_state.history[
        -st.session_state.memory_turns:
    ]

    memory_context = "\n\n".join(
        f"User: {turn['question']}\nAssistant: {turn['answer']}"
        for turn in recent_turns
    )

    prompt = f"""
You are a helpful PDF assistant.

Recent conversation:
{memory_context if memory_context else 'None'}

Context:
{context}

Question:
{question}
"""

    with st.spinner("🧠 Analyzing PDFs..."):
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

    answer = response.choices[0].message.content
    if answer:
        st.download_button(
            "📥 Download Response",
            answer,
            file_name="pdf_response.txt",
            mime="text/plain"
        )
    citation_entries = build_citations(matched_docs)

    if st.session_state.current_chat_id is None:
        chat_title = ", ".join(row[1] for row in selected_pdf_rows[:3])

        if len(selected_pdf_rows) > 3:
            chat_title += "..."

        if not chat_title:
            chat_title = "New Chat"

        st.session_state.current_chat_id = db.get_or_create_session_chat(
            st.session_state.session_id,
            chat_title,
            user_id=st.session_state.user_id,
            pdf_ids=selected_pdf_ids,
        )
    else:
        db.set_chat_pdf_ids(
            st.session_state.current_chat_id,
            selected_pdf_ids
        )

    db.add_message(
        st.session_state.current_chat_id,
        "user",
        question
    )

    db.add_message(
        st.session_state.current_chat_id,
        "bot",
        answer
    )

    for citation, excerpt in citation_entries:
        db.add_message(
            st.session_state.current_chat_id,
            "source",
            f"{citation}||{excerpt}"
        )

    st.session_state.history.append(
        {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "citation": citation,
                    "excerpt": excerpt
                }
                for citation, excerpt in citation_entries
            ],
        }
    )

    st.rerun()

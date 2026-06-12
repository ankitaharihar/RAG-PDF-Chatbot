import os
import uuid
from pathlib import Path

import bcrypt
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

import db
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


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

st.set_page_config(page_title="Multi-PDF RAG Chatbot", page_icon="📄", layout="wide")

db.init_db()


def initialize_state():
    defaults = {
        "authenticated": False,
        "user_id": None,
        "username": "",
        "email": "",
        "session_id": str(uuid.uuid4()),
        "history": [],
        "current_chat_id": None,
        "active_pdf_ids": [],
        "memory_turns": 6,
        "sidebar_upload_counter": 0,
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
            current_turn["sources"].append({"citation": citation, "excerpt": excerpt})

    return turns


def render_turns(turns):
    for turn in turns:
        with st.chat_message("user", avatar="👤"):
            st.markdown(turn["question"])

        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(turn["answer"])
            if turn.get("sources"):
                with st.expander("Sources", expanded=False):
                    for index, source in enumerate(turn["sources"], start=1):
                        st.markdown(f"**{index}. {source['citation']}**")
                        if source.get("excerpt"):
                            st.markdown(f"> {source['excerpt']}")


def build_citations(matched_docs):
    citation_entries = []
    seen = set()

    for doc in matched_docs:
        source_name = doc.metadata.get("display_source") or Path(
            doc.metadata.get("source", "Unknown source")
        ).name
        page = doc.metadata.get("page")
        page_label = f"Page {page + 1}" if isinstance(page, int) else "Page N/A"
        citation = f"{source_name} ({page_label})"

        if citation in seen:
            continue

        seen.add(citation)
        excerpt = doc.page_content.strip().replace("\n", " ")
        if len(excerpt) > 300:
            excerpt = excerpt[:300].rsplit(" ", 1)[0] + "..."
        citation_entries.append((citation, excerpt))

    return citation_entries


def save_uploaded_pdfs(uploaded_files, user_id: int):
    library_dir = Path("pdf_library") / f"user_{user_id}"
    library_dir.mkdir(parents=True, exist_ok=True)

    new_pdf_ids = []
    for uploaded_file in uploaded_files:
        stored_name = f"{uuid.uuid4().hex}_{Path(uploaded_file.name).name}"
        file_path = library_dir / stored_name
        with open(file_path, "wb") as file_handle:
            file_handle.write(uploaded_file.getbuffer())

        pdf_id = db.add_pdf(
            user_id=user_id,
            original_name=uploaded_file.name,
            stored_name=stored_name,
            stored_path=str(file_path),
        )
        new_pdf_ids.append(pdf_id)

    return new_pdf_ids


def load_documents_from_pdfs(pdf_rows):
    documents = []

    for pdf_row in pdf_rows:
        pdf_id, original_name, _stored_name, stored_path, _created_at = pdf_row
        file_path = Path(stored_path)
        if not file_path.exists():
            continue

        loader = PyPDFLoader(str(file_path))
        loaded_docs = loader.load()

        for document in loaded_docs:
            document.metadata["display_source"] = original_name
            document.metadata["pdf_id"] = pdf_id

        documents.extend(loaded_docs)

    return documents


def render_auth_sidebar():
    with st.sidebar:
        st.markdown("## 🔐 Account")
        st.caption("Login or create an account to keep your chats and PDF library private.")

        auth_mode = st.radio("Mode", ["Login", "Sign Up"], horizontal=True)

        with st.form("auth_form"):
            username = ""
            if auth_mode == "Sign Up":
                username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(auth_mode)

        if submitted:
            email_value = email.strip().lower()

            if not email_value or not password:
                st.error("Email and password are required.")
                return

            if auth_mode == "Sign Up":
                if not username.strip():
                    st.error("Username is required for sign up.")
                    return

                if db.get_user_by_email(email_value):
                    st.error("An account with this email already exists.")
                    return

                password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                user_id = db.create_user(username.strip(), email_value, password_hash)

                st.session_state.authenticated = True
                st.session_state.user_id = user_id
                st.session_state.username = username.strip()
                st.session_state.email = email_value
                st.session_state.history = []
                st.session_state.current_chat_id = None
                st.session_state.active_pdf_ids = []
                st.success("Account created successfully.")
                st.rerun()

            user = db.get_user_by_email(email_value)
            if not user:
                st.error("No account found for this email.")
                return

            stored_hash = user[3]
            if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                st.error("Incorrect password.")
                return

            st.session_state.authenticated = True
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.email = user[2]
            st.session_state.history = []
            st.session_state.current_chat_id = None
            st.session_state.active_pdf_ids = []
            st.success("Logged in successfully.")
            st.rerun()


def load_chat_into_state(chat_id: int):
    st.session_state.current_chat_id = chat_id
    st.session_state.history = load_chat_history(chat_id)
    st.session_state.active_pdf_ids = db.get_chat_pdf_ids(chat_id)


initialize_state()

if not st.session_state.authenticated:
    render_auth_sidebar()
    st.markdown(
        """
        <div class="hero-card">
          <p class="hero-title">AI Document Intelligence Platform</p>
          <p class="hero-subtitle">Secure multi-PDF chat with citations, memory, and a persistent personal library.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    stats = [
        ("Login", "Secure"),
        ("PDF Library", "Persistent"),
        ("Chat Memory", "Enabled"),
        ("Sources", "Cited"),
    ]
    for column, (label, value) in zip(cols, stats):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.info("Create an account or log in from the sidebar to access your private chats and PDF library.")
    st.stop()


user_record = db.get_user_by_id(st.session_state.user_id)
if user_record:
    st.session_state.username = user_record[1]
    st.session_state.email = user_record[2]


with st.sidebar:
    logo_path = Path("assets/logo.svg")
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)

    st.markdown("## 👤 Profile")
    st.markdown(f"**{st.session_state.username}**")
    st.caption(st.session_state.email)

    st.markdown("### Quick Stats")
    user_pdf_count = len(db.get_pdfs_for_user(st.session_state.user_id))
    user_chat_count = len(db.get_chats_for_user(st.session_state.user_id))
    stat_cols = st.columns(2)
    with stat_cols[0]:
        st.metric("PDFs", user_pdf_count)
    with stat_cols[1]:
        st.metric("Chats", user_chat_count)

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.history = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("## 💬 Chat History")
    user_chats = db.get_chats_for_user(st.session_state.user_id)
    chat_options = [(None, "(new chat)")] + [(chat_id, title) for chat_id, title, _ in user_chats]

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

    st.markdown("## 📚 PDF Library")
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
        new_pdf_ids = save_uploaded_pdfs(uploaded_files, st.session_state.user_id)
        st.session_state.active_pdf_ids = list(dict.fromkeys([*st.session_state.active_pdf_ids, *new_pdf_ids]))
        st.session_state.sidebar_upload_counter += 1
        st.success(f"Saved {len(new_pdf_ids)} PDF(s) to your library.")
        st.rerun()

    pdf_rows = db.get_pdfs_for_user(st.session_state.user_id)
    if pdf_rows:
        pdf_options = pdf_rows
        default_selection = [row for row in pdf_options if row[0] in st.session_state.active_pdf_ids]
        if not default_selection:
            default_selection = pdf_options
            st.session_state.active_pdf_ids = [row[0] for row in pdf_options]

        selected_pdf_rows = st.multiselect(
            "My PDFs",
            options=pdf_options,
            default=default_selection,
            format_func=lambda row: row[1],
            key="library_multiselect",
        )
        st.session_state.active_pdf_ids = [row[0] for row in selected_pdf_rows]

        st.caption("Selected PDFs are used for retrieval in the active chat.")

        delete_pdf_rows = st.multiselect(
            "Delete PDFs",
            options=pdf_options,
            format_func=lambda row: row[1],
            key="delete_multiselect",
        )
        if st.button("Delete selected PDFs", use_container_width=True):
            for pdf_row in delete_pdf_rows:
                db.delete_pdf(pdf_row[0], st.session_state.user_id)
            st.session_state.active_pdf_ids = [pdf_id for pdf_id in st.session_state.active_pdf_ids if pdf_id not in {row[0] for row in delete_pdf_rows}]
            st.success("Selected PDF(s) deleted.")
            st.rerun()
    else:
        st.info("Upload PDFs here once. They will stay in your library until you delete them.")

    st.markdown("## 🧠 Conversation Memory")
    st.session_state.memory_turns = st.slider("Memory window (turns)", 2, 10, st.session_state.memory_turns)

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.username = ""
        st.session_state.email = ""
        st.session_state.history = []
        st.session_state.current_chat_id = None
        st.session_state.active_pdf_ids = []
        st.rerun()


st.title("📄 Multi-PDF RAG Assistant")

main_header = st.container()
with main_header:
    st.markdown(
        """
        <div class="hero-card">
          <p class="hero-title">Multi-PDF RAG Assistant</p>
          <p class="hero-subtitle">Chat with your saved PDF library in a clean, responsive interface with citations and memory.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.history:
    render_turns(st.session_state.history)

selected_pdf_ids = st.session_state.active_pdf_ids[:]
if not selected_pdf_ids and db.get_pdfs_for_user(st.session_state.user_id):
    selected_pdf_ids = [row[0] for row in db.get_pdfs_for_user(st.session_state.user_id)]

selected_pdf_rows = db.get_pdfs_by_ids(st.session_state.user_id, selected_pdf_ids)

summary_cols = st.columns(3)
with summary_cols[0]:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">Active PDFs</div>
          <div class="metric-value">{len(selected_pdf_rows)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with summary_cols[1]:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">Memory Window</div>
          <div class="metric-value">{st.session_state.memory_turns}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with summary_cols[2]:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">Chat Mode</div>
          <div class="metric-value">SaaS UI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if not selected_pdf_rows:
    st.info("Upload PDFs from the sidebar and select the ones you want to chat with.")
    st.stop()

documents = load_documents_from_pdfs(selected_pdf_rows)

if not documents:
    st.error("No readable content found in the selected PDFs.")
    st.stop()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
split_documents = text_splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(split_documents, embeddings)

st.success("Vector database ready ✅")
st.caption(f"Using {len(selected_pdf_rows)} PDF(s) from your library.")

question = st.chat_input("Ask a question from the selected PDFs")

if question:
    matched_docs = vectorstore.similarity_search(question)
    context = "\n".join(doc.page_content for doc in matched_docs)

    recent_turns = st.session_state.history[-st.session_state.memory_turns :]
    memory_context = "\n\n".join(
        f"User: {turn['question']}\nAssistant: {turn['answer']}" for turn in recent_turns
    )

    prompt = f"""
You are a helpful PDF assistant.
Use the selected PDF context first.
Use the recent conversation only when it helps resolve the question.

Recent conversation:
{memory_context if memory_context else 'None'}

Context:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.choices[0].message.content
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
        db.set_chat_pdf_ids(st.session_state.current_chat_id, selected_pdf_ids)

    db.add_message(st.session_state.current_chat_id, "user", question)
    db.add_message(st.session_state.current_chat_id, "bot", answer)
    for citation, excerpt in citation_entries:
        db.add_message(st.session_state.current_chat_id, "source", f"{citation}||{excerpt}")

    st.session_state.history.append(
        {
            "question": question,
            "answer": answer,
            "sources": [
                {"citation": citation, "excerpt": excerpt}
                for citation, excerpt in citation_entries
            ],
        }
    )

    st.rerun()
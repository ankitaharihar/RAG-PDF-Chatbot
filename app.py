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
        "pending_chat_reset": False,
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
        with st.chat_message("user"):
            st.markdown(turn["question"])

        with st.chat_message("assistant"):
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
    upload_dir = Path("uploaded_pdfs") / f"user_{user_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    documents = []

    for index, uploaded_file in enumerate(uploaded_files):
        safe_name = f"{index}_{Path(uploaded_file.name).name}"
        file_path = upload_dir / safe_name

        with open(file_path, "wb") as file_handle:
            file_handle.write(uploaded_file.getbuffer())

        loader = PyPDFLoader(str(file_path))
        loaded_docs = loader.load()

        for document in loaded_docs:
            document.metadata["display_source"] = uploaded_file.name

        documents.extend(loaded_docs)

    return documents


def render_auth_sidebar():
    with st.sidebar:
        st.markdown("## 🔐 Account")
        st.caption("Login or create an account to keep chats separate per user.")

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

                existing_user = db.get_user_by_email(email_value)
                if existing_user:
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
            st.success("Logged in successfully.")
            st.rerun()


initialize_state()

if not st.session_state.authenticated:
    render_auth_sidebar()
    st.title("📄 Multi-PDF RAG Chatbot")
    st.subheader("Login required")
    st.info("Create an account or log in from the sidebar to access your private chats and PDF uploads.")
    st.markdown(
        """
        This version already supports:
        - Multi-PDF upload
        - ChromaDB vector search
        - OpenRouter answers
        - Source citations
        - SQLite-backed chat history
        - User accounts with bcrypt password hashing
        """
    )
    st.stop()


user_record = db.get_user_by_id(st.session_state.user_id)
if user_record:
    st.session_state.username = user_record[1]
    st.session_state.email = user_record[2]


with st.sidebar:
    st.markdown("## 👤 Profile")
    st.markdown(f"**{st.session_state.username}**")
    st.caption(st.session_state.email)

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.history = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("## 💬 Chat History")
    user_chats = db.get_chats_for_user(st.session_state.user_id)
    chat_options = ["(new chat)"] + [f"{chat_id}: {title}" for chat_id, title, _ in user_chats]

    default_index = 0
    if st.session_state.current_chat_id is not None:
        current_label = next(
            (f"{chat_id}: {title}" for chat_id, title, _ in user_chats if chat_id == st.session_state.current_chat_id),
            "(new chat)",
        )
        if current_label in chat_options:
            default_index = chat_options.index(current_label)

    selected_chat_label = st.selectbox("Open saved chat", chat_options, index=default_index)

    if selected_chat_label == "(new chat)":
        if st.session_state.current_chat_id is not None:
            st.session_state.current_chat_id = None
            st.session_state.history = []
    else:
        selected_chat_id = int(selected_chat_label.split(":", 1)[0])
        if st.session_state.current_chat_id != selected_chat_id:
            st.session_state.current_chat_id = selected_chat_id
            st.session_state.history = load_chat_history(selected_chat_id)

    st.markdown("## 📄 Upload PDFs")
    uploaded_files = st.file_uploader(
        "Upload one or more PDFs",
        type="pdf",
        accept_multiple_files=True,
    )

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.username = ""
        st.session_state.email = ""
        st.session_state.history = []
        st.session_state.current_chat_id = None
        st.rerun()


st.title("📄 Multi-PDF RAG Assistant")
st.caption("Ask questions in a chat-style interface, and each answer includes source citations.")

if st.session_state.history:
    render_turns(st.session_state.history)

if not uploaded_files:
    st.info("Upload one or more PDFs from the sidebar to start chatting.")
    st.stop()

documents = save_uploaded_pdfs(uploaded_files, st.session_state.user_id)

if not documents:
    st.error("No readable content found in the uploaded PDFs.")
    st.stop()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
split_documents = text_splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(split_documents, embeddings)

st.success("Vector database ready ✅")

question = st.chat_input("Ask a question from the uploaded PDFs")

if question:
    matched_docs = vectorstore.similarity_search(question)
    context = "\n".join(doc.page_content for doc in matched_docs)

    recent_turns = st.session_state.history[-4:]
    memory_context = "\n\n".join(
        f"User: {turn['question']}\nAssistant: {turn['answer']}" for turn in recent_turns
    )

    prompt = f"""
You are a helpful PDF assistant.
Answer using the provided context and the recent conversation if it is relevant.

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
        chat_title = ", ".join(file.name for file in uploaded_files) if uploaded_files else "New Chat"
        st.session_state.current_chat_id = db.get_or_create_session_chat(
            st.session_state.session_id,
            chat_title,
            user_id=st.session_state.user_id,
        )

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
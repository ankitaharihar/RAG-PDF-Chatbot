import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

import streamlit as st

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import uuid
import db

# Load API key
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

if not api_key:
    st.error("OPENROUTER_API_KEY missing in .env")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# Streamlit UI
st.set_page_config(page_title="RAG PDF Chatbot")

st.title("📄 RAG PDF Chatbot")

# initialize DB and session id
db.init_db()
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Sidebar: saved chats
with st.sidebar:
    st.header("Saved Chats")
    chats = db.get_chats(st.session_state.session_id)
    chat_options = [f"{r[0]}: {r[1]}" for r in chats]
    selected = None
    if chat_options:
        selected = st.selectbox("Open chat", options=["(new chat)"] + chat_options, index=0)
    else:
        st.write("No saved chats yet")

    if selected and selected != "(new chat)":
        # parse chat id
        chat_id = int(selected.split(":", 1)[0])
        messages = db.get_messages(chat_id)
        # populate session history from DB
        st.session_state.history = []
        for role, content, _ in messages:
            if role == "user":
                st.session_state.history.append({"question": content, "answer": ""})
            elif role == "bot":
                # attach bot answer to last question
                if st.session_state.history:
                    st.session_state.history[-1]["answer"] = content
            elif role == "source":
                if st.session_state.history:
                    # append sources list
                    if "sources" not in st.session_state.history[-1]:
                        st.session_state.history[-1]["sources"] = []
                    # content expected as 'citation||excerpt'
                    if "||" in content:
                        citation, excerpt = content.split("||", 1)
                    else:
                        citation, excerpt = content, ""
                    st.session_state.history[-1]["sources"].append({"citation": citation, "excerpt": excerpt})


# Initialize chat history in session state
if "history" not in st.session_state:
    st.session_state.history = []

# Show chat history and clear option
if st.session_state.history:
    st.subheader("Chat History")
    for entry in reversed(st.session_state.history):
        st.markdown(f"**Q:** {entry['question']}")
        st.markdown(f"**A:** {entry['answer']}")
        if entry.get("sources"):
            st.markdown("**Sources:**")
            for i, s in enumerate(entry["sources"], start=1):
                st.markdown(f"{i}. {s.get('citation')}")
                if s.get('excerpt'):
                    st.markdown(f"> {s.get('excerpt')}")
        st.write("---")

    if st.button("Clear history"):
        st.session_state.history = []
        st.experimental_rerun()

uploaded_files = st.file_uploader(
    "Upload one or more PDFs",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:

    upload_dir = Path("uploaded_pdfs")
    upload_dir.mkdir(exist_ok=True)

    documents = []

    for idx, uploaded_file in enumerate(uploaded_files):

        safe_name = f"{idx}_{Path(uploaded_file.name).name}"
        file_path = upload_dir / safe_name

        # Save uploaded PDF
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Load PDF
        loader = PyPDFLoader(str(file_path))
        loaded_docs = loader.load()

        for doc in loaded_docs:
            doc.metadata["display_source"] = uploaded_file.name

        documents.extend(loaded_docs)

    st.success(f"{len(uploaded_files)} PDF(s) uploaded and read successfully ✅")

    if not documents:
        st.error("No readable content found in uploaded PDFs.")
        st.stop()

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    docs = text_splitter.split_documents(documents)

    # Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # Store in ChromaDB
    vectorstore = Chroma.from_documents(
        docs,
        embeddings
    )

    st.success("Vector Database Created ✅")

    st.write("Chunks Created:", len(docs))
    st.write("Files Indexed:", len(uploaded_files))

    # User question
    question = st.text_input(
        "Ask a question from the uploaded PDFs"
    )

    if question:

        # Similarity search
        matched_docs = vectorstore.similarity_search(
            question
        )

        context = "\n".join(
            [doc.page_content for doc in matched_docs]
        )

        prompt = f"""
Answer the question using the provided context.

Context:
{context}

Question:
{question}
"""

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

        citations = []
        citation_entries = []
        seen = set()

        for doc in matched_docs:
            source_name = doc.metadata.get("display_source") or Path(
                doc.metadata.get("source", "Unknown source")
            ).name

            page = doc.metadata.get("page")
            if isinstance(page, int):
                page_label = f"Page {page + 1}"
            else:
                page_label = "Page N/A"

            citation = f"{source_name} ({page_label})"

            if citation not in seen:
                seen.add(citation)
                # create a short excerpt for context
                excerpt = doc.page_content.strip().replace("\n", " ")
                if len(excerpt) > 300:
                    excerpt = excerpt[:300].rsplit(" ", 1)[0] + "..."
                citation_entries.append((citation, excerpt))

        st.subheader("Answer")
        st.write(answer)

        if citation_entries:
            st.subheader("Sources")
            for idx, (citation, excerpt) in enumerate(citation_entries, start=1):
                st.markdown(f"**{idx}. {citation}**")
                st.markdown(f"> {excerpt}")
                st.write("")

        # Append to chat history
        entry_sources = [
            {"citation": citation, "excerpt": excerpt}
            for (citation, excerpt) in citation_entries
        ]

        st.session_state.history.append(
            {"question": question, "answer": answer, "sources": entry_sources}
        )
        # Persist to SQLite
        session_id = st.session_state.session_id
        title = ", ".join([f.name for f in uploaded_files]) if uploaded_files else "Session Chat"
        chat_id = st.session_state.get("chat_id") or db.get_or_create_session_chat(session_id, title)
        st.session_state["chat_id"] = chat_id

        try:
            db.add_message(chat_id, "user", question)
            db.add_message(chat_id, "bot", answer)
            for (citation, excerpt) in citation_entries:
                db.add_message(chat_id, "source", f"{citation}||{excerpt}")
        except Exception:
            # avoid crashing the app if DB write fails
            pass
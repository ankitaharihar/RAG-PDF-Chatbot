import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

import streamlit as st

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

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
        documents.extend(loader.load())

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

        st.subheader("Answer")

        st.write(answer)
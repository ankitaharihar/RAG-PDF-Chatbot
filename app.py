import os
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

uploaded_file = st.file_uploader(
    "Upload a PDF",
    type="pdf"
)

if uploaded_file:

    # Save uploaded PDF
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("PDF Uploaded Successfully ✅")

    # Load PDF
    loader = PyPDFLoader(uploaded_file.name)

    documents = loader.load()

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

    # User question
    question = st.text_input(
        "Ask a question from the PDF"
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
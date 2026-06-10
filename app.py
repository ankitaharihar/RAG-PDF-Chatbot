import os
from dotenv import load_dotenv

import streamlit as st

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)

# Load API key
load_dotenv()

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
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001"
    )

    # Store in ChromaDB
    vectorstore = Chroma.from_documents(
        docs,
        embeddings
    )

    # User question
    question = st.text_input(
        "Ask a question from the PDF"
    )

    if question:

        # Similarity search
        matched_docs = vectorstore.similarity_search(
            question
        )

        # Gemini model
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3
        )

        context = "\n".join(
            [doc.page_content for doc in matched_docs]
        )

        prompt = f"""
Answer the question using the PDF context below.

Context:
{context}

Question:
{question}
"""

        response = llm.invoke(
            prompt
        )

        st.subheader("Answer")

        st.write(response.content)
from langchain_text_splitters import RecursiveCharacterTextSplitter
import streamlit as st

from langchain_community.embeddings import (
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import (
    Chroma
)


RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 200


def get_rag_config():
    return {
        "chunk_size": RAG_CHUNK_SIZE,
        "chunk_overlap": RAG_CHUNK_OVERLAP,
        "embedding_model": "all-MiniLM-L6-v2",
    }


@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=get_rag_config()["embedding_model"]
    )


def build_text_splitter():
    config = get_rag_config()
    return RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
    )


def create_vectorstore(documents):
    splitter = build_text_splitter()

    split_docs = splitter.split_documents(documents)

    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        split_docs,
        embeddings
    )

    return vectorstore


def retrieve_context(vectorstore, question):

    docs = vectorstore.similarity_search(
        question
    )

    context = "\n".join(
        doc.page_content
        for doc in docs
    )

    return docs, context
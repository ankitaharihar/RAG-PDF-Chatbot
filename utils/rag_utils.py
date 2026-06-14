from langchain_text_splitters import RecursiveCharacterTextSplitter
import streamlit as st

from langchain_community.embeddings import (
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import (
    Chroma
)


@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )


def create_vectorstore(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    split_docs = splitter.split_documents(
        documents
    )

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
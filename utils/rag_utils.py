from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.embeddings import (
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import (
    Chroma
)


def create_vectorstore(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    split_docs = splitter.split_documents(
        documents
    )

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

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
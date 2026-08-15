import os
import uuid
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

import database.db as db
from utils.pdf_utils import MAX_PDF_SIZE_BYTES, build_citations, load_documents_from_pdfs
from utils.rag_utils import get_rag_config, retrieve_context

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


load_dotenv()

API_TITLE = "RAG PDF Chatbot API"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")

app = FastAPI(title=API_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=500, detail="OPENROUTER_API_KEY is missing.")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


@lru_cache(maxsize=1)
def _get_embeddings() -> HuggingFaceEmbeddings:
    model_name = get_rag_config()["embedding_model"]
    return HuggingFaceEmbeddings(model_name=model_name)


def _create_vectorstore(documents):
    config = get_rag_config()
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
    )

    split_docs = splitter.split_documents(documents)

    if not split_docs:
        raise HTTPException(
            status_code=400, detail="No text chunks could be created from selected PDFs.")

    return Chroma.from_documents(split_docs, _get_embeddings())


def _chat_title_from_pdfs(pdf_rows) -> str:
    names = [row[1] for row in pdf_rows[:3]]
    if not names:
        return "New Chat"

    title = ", ".join(names)
    if len(pdf_rows) > 3:
        title += "..."

    return title


def _validate_pdf_bytes(file_name: str, file_bytes: bytes) -> None:
    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed.")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    if len(file_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=400, detail="Uploaded PDF exceeds the 20 MB limit.")


class ChatRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    question: str = Field(..., min_length=1)
    pdf_ids: list[int] = Field(..., min_length=1)
    chat_id: int | None = None
    session_id: str | None = None


class Citation(BaseModel):
    citation: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    chat_id: int


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_pdfs(
    user_id: int = Form(...),
    files: list[UploadFile] = File(...),
) -> dict:
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user_id.")

    if not files:
        raise HTTPException(
            status_code=400, detail="At least one PDF file is required.")

    library_dir = Path("assets") / "pdf_library" / f"user_{user_id}"
    library_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []

    for upload in files:
        raw_bytes = await upload.read()
        safe_name = Path(upload.filename or "").name
        _validate_pdf_bytes(safe_name, raw_bytes)

        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        stored_path = library_dir / stored_name

        with open(stored_path, "wb") as file_obj:
            file_obj.write(raw_bytes)

        pdf_id = db.add_pdf(
            user_id=user_id,
            original_name=safe_name,
            stored_name=stored_name,
            stored_path=str(stored_path),
        )

        uploaded.append(
            {
                "pdf_id": pdf_id,
                "original_name": safe_name,
                "stored_name": stored_name,
                "stored_path": str(stored_path),
            }
        )

    return {
        "message": f"Uploaded {len(uploaded)} PDF(s) successfully.",
        "uploaded": uploaded,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=400, detail="Question cannot be empty.")

    pdf_rows = db.get_pdfs_by_ids(request.user_id, request.pdf_ids)
    if not pdf_rows:
        raise HTTPException(
            status_code=404, detail="No matching PDFs found for this user.")

    found_ids = {row[0] for row in pdf_rows}
    missing_ids = [
        pdf_id for pdf_id in request.pdf_ids if pdf_id not in found_ids]
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Some PDFs were not found or not owned by this user: {missing_ids}",
        )

    documents = load_documents_from_pdfs(pdf_rows)
    if not documents:
        raise HTTPException(
            status_code=400, detail="No readable content found in selected PDFs.")

    vectorstore = _create_vectorstore(documents)
    matched_docs, context = retrieve_context(vectorstore, question)

    prompt = f"""
You are a helpful PDF assistant.

Context:
{context}

Question:
{question}
"""

    response = _get_client().chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = (response.choices[0].message.content or "").strip()
    citation_entries = build_citations(matched_docs)

    if request.chat_id is None:
        session_id = request.session_id or str(uuid.uuid4())
        chat_id = db.get_or_create_session_chat(
            session_id=session_id,
            title=_chat_title_from_pdfs(pdf_rows),
            user_id=request.user_id,
            pdf_ids=request.pdf_ids,
        )
    else:
        chat_id = request.chat_id
        db.set_chat_pdf_ids(chat_id, request.pdf_ids)

    db.add_message(chat_id, "user", question)
    db.add_message(chat_id, "bot", answer)

    for citation, excerpt in citation_entries:
        db.add_message(chat_id, "source", f"{citation}||{excerpt}")

    return ChatResponse(
        answer=answer,
        citations=[
            Citation(citation=citation, excerpt=excerpt)
            for citation, excerpt in citation_entries
        ],
        chat_id=chat_id,
    )

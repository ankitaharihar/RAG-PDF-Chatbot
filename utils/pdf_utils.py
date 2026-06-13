from pathlib import Path
import uuid

from langchain_community.document_loaders import PyPDFLoader


def save_uploaded_pdfs(uploaded_files, user_id, db):
    library_dir = Path("pdf_library") / f"user_{user_id}"
    library_dir.mkdir(parents=True, exist_ok=True)

    new_pdf_ids = []

    for uploaded_file in uploaded_files:
        stored_name = f"{uuid.uuid4().hex}_{Path(uploaded_file.name).name}"
        file_path = library_dir / stored_name

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

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
        pdf_id, original_name, _, stored_path, _ = pdf_row

        loader = PyPDFLoader(stored_path)
        docs = loader.load()

        for doc in docs:
            doc.metadata["display_source"] = original_name
            doc.metadata["pdf_id"] = pdf_id

        documents.extend(docs)

    return documents


def build_citations(matched_docs):
    citation_entries = []
    seen = set()

    for doc in matched_docs:
        source_name = doc.metadata.get(
            "display_source",
            "Unknown PDF"
        )

        page = doc.metadata.get("page")

        citation = f"{source_name} (Page {page+1})"

        if citation in seen:
            continue

        seen.add(citation)

        excerpt = doc.page_content[:300]

        citation_entries.append(
            (citation, excerpt)
        )

    return citation_entries
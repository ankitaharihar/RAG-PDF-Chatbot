from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from utils.pdf_utils import build_citations, validate_uploaded_file
from utils.rag_utils import build_text_splitter, get_rag_config


def test_build_text_splitter_uses_documentation_ready_rag_config():
    splitter = build_text_splitter()
    config = get_rag_config()

    assert config["chunk_size"] == 1000
    assert config["chunk_overlap"] == 200
    assert splitter._chunk_size == config["chunk_size"]
    assert splitter._chunk_overlap == config["chunk_overlap"]


def test_validate_uploaded_file_rejects_invalid_pdf_type():
    uploaded = SimpleNamespace(
        name="notes.txt", getbuffer=lambda: b"not-a-pdf")

    with pytest.raises(ValueError, match="PDF"):
        validate_uploaded_file(uploaded)


def test_validate_uploaded_file_rejects_oversized_files():
    oversized_bytes = b"a" * (21 * 1024 * 1024)
    uploaded = SimpleNamespace(
        name="large.pdf", getbuffer=lambda: oversized_bytes)

    with pytest.raises(ValueError, match="20 MB"):
        validate_uploaded_file(uploaded)


def test_build_citations_returns_unique_sources_with_excerpt():
    docs = [
        Document(page_content="Alpha content for answer generation.",
                 metadata={"page": 0, "display_source": "Alpha.pdf"}),
        Document(page_content="Alpha content for answer generation.",
                 metadata={"page": 0, "display_source": "Alpha.pdf"}),
        Document(page_content="Beta content from second page.",
                 metadata={"page": 1, "display_source": "Beta.pdf"}),
    ]

    citations = build_citations(docs)

    assert len(citations) == 2
    assert citations[0][0].startswith("Alpha.pdf")
    assert citations[1][0].startswith("Beta.pdf")
    assert all(len(excerpt) <= 300 for _, excerpt in citations)

"""
Build Chroma index from PDFs in frontend/public/textbooks/.

Run from repo root:  python backend/scripts/index_textbooks.py
Or from backend:      python scripts/index_textbooks.py

Requires NVIDIA embeddings credentials (same as app RAG) in backend/.env or langchain-rag-tutorial/.env.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
TEXTBOOKS_DIR = REPO_ROOT / "frontend" / "public" / "textbooks"
CHROMA_PATH = BACKEND_ROOT / "chroma"

CHUNK_SIZE = 300
CHUNK_OVERLAP = 100
HIGHLIGHT_LEN = 100


def _highlight_anchor(text: str, max_len: int = HIGHLIGHT_LEN) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    return cleaned[:max_len]


def _enrich_chunk(doc: Document, file_name: str) -> Document:
    meta = dict(doc.metadata) if doc.metadata else {}
    meta["file_name"] = file_name
    # PyPDFLoader uses 0-based page index in metadata["page"]
    p = meta.get("page")
    if p is not None:
        meta["page"] = int(p) + 1
    meta["highlight"] = _highlight_anchor(doc.page_content)
    return Document(page_content=doc.page_content, metadata=meta)


def load_and_chunk_pdf(pdf_path: Path) -> list[Document]:
    file_name = pdf_path.name
    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True,
    )
    chunks = splitter.split_documents(pages)
    return [_enrich_chunk(c, file_name) for c in chunks]


def main() -> None:
    load_dotenv(BACKEND_ROOT / ".env")
    load_dotenv(REPO_ROOT / "langchain-rag-tutorial" / ".env")

    if not TEXTBOOKS_DIR.is_dir():
        print(f"Missing textbooks directory: {TEXTBOOKS_DIR}", file=sys.stderr)
        sys.exit(1)

    pdfs = sorted(TEXTBOOKS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files in {TEXTBOOKS_DIR}", file=sys.stderr)
        sys.exit(1)

    all_chunks: list[Document] = []
    for pdf in pdfs:
        print(f"Indexing {pdf.name} ...")
        all_chunks.extend(load_and_chunk_pdf(pdf))

    print(f"Total chunks: {len(all_chunks)}")
    if not all_chunks:
        sys.exit(1)

    if CHROMA_PATH.exists():
        shutil.rmtree(CHROMA_PATH)

    embedding_function = NVIDIAEmbeddings()
    Chroma.from_documents(
        all_chunks,
        embedding_function,
        persist_directory=str(CHROMA_PATH),
    )
    print(f"Saved Chroma store to {CHROMA_PATH}")


if __name__ == "__main__":
    main()

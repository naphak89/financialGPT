import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from app.config import get_settings

PREVIEW_LEN = 400
HIGHLIGHT_FALLBACK = 100

PROMPT_TEMPLATE = """
You are a teaching assistant. Answer using only the context below. When you use information from a passage, cite it with [n] matching the source numbers (for example: "… as stated in the text [1].").

Sources (use these numbers in brackets in your answer):
{source_index}

---

Context:
{context}

---

Question: {question}

Answer clearly and cite [n] where you rely on a source.
"""

# Load API keys from backend .env and langchain tutorial .env (NVIDIA / DeepSeek)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv(_REPO_ROOT / "langchain-rag-tutorial" / ".env")


def _preview(text: str) -> str:
    if len(text) <= PREVIEW_LEN:
        return text
    return text[:PREVIEW_LEN] + "…"


def _source_display_fields(meta: dict, preview: str) -> tuple[str, int, str]:
    raw_name = meta.get("file_name") or ""
    if not raw_name and meta.get("source"):
        raw_name = Path(str(meta["source"])).name
    file_name = raw_name or "unknown.pdf"

    p = meta.get("page")
    if p is None:
        page = 1
    else:
        page = max(1, int(p))

    highlight = (meta.get("highlight") or "").strip()
    if not highlight:
        highlight = " ".join(preview.split())[:HIGHLIGHT_FALLBACK]

    return file_name, page, highlight


def _build_source_index(results: list) -> str:
    lines: list[str] = []
    for i, (doc, _score) in enumerate(results, start=1):
        meta = dict(doc.metadata) if doc.metadata else {}
        fn, page, _hl = _source_display_fields(meta, _preview(doc.page_content))
        lines.append(f"[{i}] {fn} — page {page}")
    return "\n".join(lines)


def run_rag(question: str) -> tuple[str, list[dict], bool]:
    """
    Returns (answer_text, source_chunks_info, low_confidence).
    """
    s = get_settings()
    chroma = s.chroma_path
    if not os.path.isdir(chroma):
        return (
            "The knowledge base is not available on the server (Chroma path missing). "
            "Set CHROMA_PATH or build the index with `python backend/scripts/index_textbooks.py` "
            "(see frontend/public/textbooks/).",
            [],
            True,
        )

    embedding_function = NVIDIAEmbeddings()
    db = Chroma(persist_directory=chroma, embedding_function=embedding_function)
    results = db.similarity_search_with_relevance_scores(question, k=s.rag_top_k)

    chunks_out: list[dict] = []
    for doc, score in results:
        meta = dict(doc.metadata) if doc.metadata else {}
        prev = _preview(doc.page_content)
        fn, page, highlight = _source_display_fields(meta, prev)
        chunks_out.append(
            {
                "content_preview": prev,
                "score": float(score),
                "metadata": meta,
                "file_name": fn,
                "page": page,
                "highlight": highlight,
            }
        )

    if len(results) == 0 or results[0][1] < s.rag_relevance_threshold:
        return (
            "I could not find relevant passages in the course materials for that question. "
            "Try rephrasing or asking about a topic covered in the reader.",
            chunks_out,
            True,
        )

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    source_index = _build_source_index(results)
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(
        context=context_text,
        question=question,
        source_index=source_index,
    )
    model = ChatDeepSeek(model="deepseek-chat")
    response_text = model.invoke(prompt).content
    return response_text, chunks_out, False

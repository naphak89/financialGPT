import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from app.config import get_settings

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

# Load API keys from backend .env and langchain tutorial .env (NVIDIA / DeepSeek)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv(_REPO_ROOT / "langchain-rag-tutorial" / ".env")


def run_rag(question: str) -> tuple[str, list[dict], bool]:
    """
    Returns (answer_text, source_chunks_info, low_confidence).
    """
    s = get_settings()
    chroma = s.chroma_path
    if not os.path.isdir(chroma):
        return (
            "The knowledge base is not available on the server (Chroma path missing). "
            "Set CHROMA_PATH or build the index under langchain-rag-tutorial/chroma.",
            [],
            True,
        )

    embedding_function = NVIDIAEmbeddings()
    db = Chroma(persist_directory=chroma, embedding_function=embedding_function)
    results = db.similarity_search_with_relevance_scores(question, k=s.rag_top_k)

    chunks_out: list[dict] = []
    for doc, score in results:
        meta = dict(doc.metadata) if doc.metadata else {}
        preview = doc.page_content[:400] + ("…" if len(doc.page_content) > 400 else "")
        chunks_out.append(
            {
                "content_preview": preview,
                "score": float(score),
                "metadata": meta,
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
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=question)
    model = ChatDeepSeek(model="deepseek-chat")
    response_text = model.invoke(prompt).content
    return response_text, chunks_out, False

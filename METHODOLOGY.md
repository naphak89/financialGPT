# Methodology

This document describes how the Financial GPT prototype is put together: what each mode does, which external services are involved, and how retrieval (RAG) picks text from your documents. It is meant to read like a lab report, not a marketing page.

## What you are looking at

The app is intentionally simple: one chat-style interface with three **manual** modes (Market, News, Education). The user chooses the mode before asking for anything. There is no automatic “intent router” in this version; that keeps behaviour predictable and makes evaluation easier for a final-year project.

The **FastAPI** service loads **market prices** only from **Alpha Vantage** `TIME_SERIES_DAILY` — **`ALPHA_VANTAGE_API_KEY`** must be set in `backend/.env`. **News** tries yfinance headlines first, then **Yahoo Finance RSS** (no key). The **education** mode uses **Chroma**, **NVIDIA embeddings**, and **DeepSeek**. The web UI is **Next.js** with **Recharts** for charts.

## Market data

For a ticker, the backend calls **only** Alpha Vantage **daily** bars. The UI asks for a **chart span in days**; the backend returns up to that many recent trading sessions (using `full` output when more than ~100 sessions are needed). Without a valid **`ALPHA_VANTAGE_API_KEY`**, `/market/data` returns **503**.

**Limitation:** Alpha Vantage free tier caps request rate (~25/day); heavy testing can hit the limit.

## News

Headlines come from **`Ticker.news`** first; if that is empty or errors, the backend uses **Yahoo Finance RSS** for the same symbol. No sentiment scoring — headlines and links only.

## Education mode and RAG

**Indexing (offline).** Documents are split with a recursive character splitter (chunk size 300, overlap 100 in the tutorial script), with `add_start_index` so offsets into the original file are available where the loader provides them. Chunks are embedded with **NVIDIAEmbeddings** and stored in **Chroma** under `langchain-rag-tutorial/chroma` (or the path you set in `CHROMA_PATH`).

**Query (online).** When you ask a question, the system:

1. Embeds the question with the same embedding model.
2. Runs **similarity search with relevance scores** and takes the top **k = 3** chunks.
3. Compares the **best** chunk’s relevance score to a **minimum threshold of 0.2** (same idea as in the original `query_data.py` script). If nothing clears the bar, the model is not asked to invent an answer from thin air; you get a short fallback message and any low-scoring chunks are still listed for transparency.
4. If results pass the filter, their text is concatenated into a single context block and passed to **ChatDeepSeek** with a strict prompt: answer **only** from that context.

**Why this is “similarity search”.** Chroma stores chunk vectors. At query time it ranks chunks by closeness to the question vector. The score you see in the API is that relevance signal (higher means a better match in this setup). The threshold is a guard against irrelevant retrieval when the question does not match the corpus.

**Citations.** Each returned chunk includes **metadata** from the loader (for PDFs, `page` and `source` often appear). The frontend surfaces previews and scores so you can trace answers back to the reader.

## Authentication and feedback

Users register with email and password; passwords are hashed with the **`bcrypt`** library (not passlib, which breaks on newer bcrypt releases), and sessions use **JWT** bearer tokens. Chat, market, news, education, and feedback routes expect `Authorization: Bearer …`.

Feedback is a simple row per user: message id, thumbs up or down, optional comment. It is stored in SQLite for demonstration and evaluation, not as a full analytics product.

## What we did not automate (and where the todo list points)

- **Intent classification:** modes are user-selected. A future version could add an “Auto” mode that classifies the message and routes it, at the cost of more failure modes and evaluation work.
- **Semantic chunking:** the current index uses fixed-size recursive splits. Semantic chunking (splitting on meaning) can improve coherence but requires another pass over the corpus and a new index build.
- **Keyword + embedding hybrids:** mentioned in your notes as an extension; not implemented here.

## How to run it locally

See the project [README](README.md) for ports and environment variables.

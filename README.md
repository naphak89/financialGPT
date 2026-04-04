# Financial GPT (FYP)

FastAPI backend + Next.js chat UI: **market charts** (Alpha Vantage daily + Recharts), **headlines** (yfinance with Yahoo RSS fallback), and **LangChain/Chroma RAG** for education.

## Prerequisites

- Python 3.10+ with `pip`
- Node 18+ and npm
- **ALPHA_VANTAGE_API_KEY** for **market** charts (free tier at [alphavantage.co](https://www.alphavantage.co/support/#api-key))
- API keys for **RAG**: **NVIDIA** (embeddings), **DeepSeek** (chat), plus **JWT secret** for auth
- **Finnhub is optional** — market and news do not use it

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # set JWT_SECRET and RAG keys; FINNHUB_API_KEY optional
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Smoke test (API running)

In another terminal:

```bash
cd backend
python scripts/smoke_test.py
```

This hits `/health`, registration, login, `/me`, and optional routes (market/news/education/feedback). Set `STRICT=1` if you want a non-zero exit when optional routes fail.

### Troubleshooting registration

Password hashing uses the **`bcrypt`** package directly (not passlib). If you previously installed `passlib` with an old bcrypt backend, run `pip install -r requirements.txt` again and delete `backend/users.db` once if you need a clean user table.

### Market & news data

- **Market:** **`ALPHA_VANTAGE_API_KEY`** is **required** in `backend/.env`. Prices come from Alpha Vantage **`TIME_SERIES_DAILY`** only (daily bars; free tier has rate limits). There is no Yahoo/yfinance price path.
- **News:** tries **yfinance** headlines first; if that fails, **Yahoo Finance RSS** (no key).

Important environment variables:

- `ALPHA_VANTAGE_API_KEY` — required for `/market/data`
- `JWT_SECRET` — use a long random string in production
- `CORS_ORIGINS` — default `http://localhost:3000`
- `CHROMA_PATH` — optional; defaults to `../langchain-rag-tutorial/chroma`
- `FINNHUB_API_KEY` — optional; not used by market/news in the current code

RAG keys can live in `backend/.env` or `langchain-rag-tutorial/.env` (both are loaded by the RAG service).

## Frontend

```bash
cd frontend
copy .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if needed
npm install
npm run dev
```

Open `http://localhost:3000`. Register, then use **Market**, **News**, or **Education** from the mode tabs.

## Methodology

See [METHODOLOGY.md](METHODOLOGY.md) for how retrieval, thresholds, and data sources work.

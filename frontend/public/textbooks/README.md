# Textbooks (public static)

PDFs in this folder are served by Next.js at `/textbooks/<filename>.pdf`.

Expected files (indexed for education RAG):

- `Full.pdf`
- `brealey-principles-of-corporate-finance-evergreen-2025.pdf`

Rebuild the vector index after adding or replacing files:

```bash
cd backend
python scripts/index_textbooks.py
```

Requires `NVIDIA_API_KEY` (or the env vars expected by `NVIDIAEmbeddings`) in `backend/.env` or `langchain-rag-tutorial/.env`.

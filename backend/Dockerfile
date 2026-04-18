# Financial GPT API — includes pre-built Chroma index under ./chroma/ (textbook embeddings).
# Build from this directory:  docker build -t financial-gpt-backend .
#
# Runtime secrets (JWT, Alpha Vantage, DeepSeek, NVIDIA) must be supplied via env / env_file,
# not baked into the image.

FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Persistent SQLite for registered users (mount a volume on /data in production)
    DATABASE_URL=sqlite:////data/users.db

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Writable dir for SQLite when using DATABASE_URL=sqlite:////data/users.db
RUN mkdir -p /data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=8s --start-period=25s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

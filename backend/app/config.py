import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent
_DEFAULT_CHROMA = _REPO_ROOT / "langchain-rag-tutorial" / "chroma"


def _default_sqlite_url() -> str:
    # Vercel serverless: only /tmp is writable; project dir is read-only → SQLite fails there.
    if os.environ.get("VERCEL"):
        return "sqlite:////tmp/users.db"
    return f"sqlite:///{_BACKEND_ROOT / 'users.db'}"


def _default_chroma_path() -> str:
    # Optional: copy your built index to backend/chroma/ so it ships with the API (e.g. Vercel).
    bundled = _BACKEND_ROOT / "chroma"
    if bundled.is_dir():
        return str(bundled)
    return str(_DEFAULT_CHROMA)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    cors_origins: str = "http://localhost:3000"

    # Override with DATABASE_URL in production (e.g. Postgres on Neon). Env wins over default.
    database_url: str = Field(default_factory=_default_sqlite_url)

    chroma_path: str = Field(default_factory=_default_chroma_path)

    # Required for /market: https://www.alphavantage.co/support/#api-key
    alpha_vantage_api_key: str = ""

    rag_relevance_threshold: float = 0.2
    rag_top_k: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()

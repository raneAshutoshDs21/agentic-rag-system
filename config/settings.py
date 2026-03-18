"""
Application settings loaded from environment variables.
Uses pydantic-settings for validation and type safety.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """
    Central settings class for the entire agentic RAG system.
    All values are loaded from .env file automatically.
    """

    # ── LLM ──────────────────────────────────────────────
    groq_api_key       : str   = Field(...,                       env="GROQ_API_KEY")
    groq_model         : str   = Field("llama-3.3-70b-versatile", env="GROQ_MODEL")
    groq_temperature   : float = Field(0.1,                       env="GROQ_TEMPERATURE")
    groq_max_tokens    : int   = Field(1024,                      env="GROQ_MAX_TOKENS")

    # ── Embeddings ───────────────────────────────────────
    embedding_model    : str   = Field("BAAI/bge-small-en-v1.5",  env="EMBEDDING_MODEL")
    embedding_device   : str   = Field("cpu",                     env="EMBEDDING_DEVICE")

    # ── Vector Store ─────────────────────────────────────
    faiss_index_path   : str   = Field("data/processed/faiss_index", env="FAISS_INDEX_PATH")

    # ── Database ─────────────────────────────────────────
    sqlite_db_path     : str   = Field("data/processed/memory.db",   env="SQLITE_DB_PATH")

    # ── Tools ─────────────────────────────────────────────
    tavily_api_key     : str   = Field(...,                       env="TAVILY_API_KEY")
    tavily_max_results : int   = Field(3,                         env="TAVILY_MAX_RESULTS")

    # ── RAG ───────────────────────────────────────────────
    chunk_size         : int   = Field(300,  env="CHUNK_SIZE")
    chunk_overlap      : int   = Field(50,   env="CHUNK_OVERLAP")
    retriever_k        : int   = Field(4,    env="RETRIEVER_K")
    retriever_fetch_k  : int   = Field(8,    env="RETRIEVER_FETCH_K")

    # ── Memory ────────────────────────────────────────────
    short_term_limit   : int   = Field(10,   env="SHORT_TERM_LIMIT")
    long_term_enabled  : bool  = Field(True, env="LONG_TERM_ENABLED")

    # ── Cache ─────────────────────────────────────────────
    cache_ttl          : int   = Field(3600, env="CACHE_TTL")
    cache_enabled      : bool  = Field(True, env="CACHE_ENABLED")

    # ── Evaluation ────────────────────────────────────────
    eval_min_score     : float = Field(6.0,  env="EVAL_MIN_SCORE")
    eval_enabled       : bool  = Field(True, env="EVAL_ENABLED")

    # ── Retry ─────────────────────────────────────────────
    max_retries        : int   = Field(3,    env="MAX_RETRIES")
    retry_min_wait     : int   = Field(2,    env="RETRY_MIN_WAIT")
    retry_max_wait     : int   = Field(10,   env="RETRY_MAX_WAIT")

    # ── API ───────────────────────────────────────────────
    api_host           : str   = Field("0.0.0.0", env="API_HOST")
    api_port           : int   = Field(8000,       env="API_PORT")
    api_reload         : bool  = Field(False,      env="API_RELOAD")

    # ── Observability ─────────────────────────────────────
    log_level          : str   = Field("INFO",          env="LOG_LEVEL")
    log_file           : str   = Field("logs/app.log",  env="LOG_FILE")
    environment        : str   = Field("development",   env="ENVIRONMENT")

    class Config:
        env_file         = ".env"
        env_file_encoding = "utf-8"
        extra            = "ignore"

    def get_faiss_path(self) -> Path:
        """Return FAISS index path as Path object."""
        return Path(self.faiss_index_path)

    def get_sqlite_path(self) -> Path:
        """Return SQLite DB path as Path object."""
        return Path(self.sqlite_db_path)

    def get_log_path(self) -> Path:
        """Return log file path as Path object."""
        return Path(self.log_file)

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


# ── Singleton instance ────────────────────────────────────
settings = Settings()
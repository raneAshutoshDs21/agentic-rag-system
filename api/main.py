"""
FastAPI application entry point.
Configures and mounts all API routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # ── Startup ───────────────────────────────────────────
    logger.info("=" * 50)
    logger.info("Agentic RAG System starting up")
    logger.info(f"Environment : {settings.environment}")
    logger.info(f"LLM Model   : {settings.groq_model}")
    logger.info(f"Embeddings  : {settings.embedding_model}")
    logger.info("=" * 50)

    # Pre-load embeddings model
    try:
        from vectorstore.embeddings import embedding_manager
        embedding_manager.load()
        logger.info("Embedding model pre-loaded")
    except Exception as e:
        logger.warning(f"Embedding pre-load failed: {e}")

    # Load FAISS index if exists
    try:
        from vectorstore.faiss_store import faiss_store
        faiss_store.load()
        logger.info(
            f"FAISS index loaded | "
            f"vectors={faiss_store.total_vectors}"
        )
    except Exception as e:
        logger.warning(
            f"FAISS index not found — run ingestion first: {e}"
        )

    yield

    # ── Shutdown ──────────────────────────────────────────
    logger.info("Agentic RAG System shutting down")


# ── Create FastAPI app ────────────────────────────────────
app = FastAPI(
    title       = "Agentic RAG System API",
    description = (
        "Production-ready Agentic RAG system with "
        "advanced retrieval, tools, memory, and evaluation"
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
    docs_url    = "/docs",
    redoc_url   = "/redoc"
)

# ── CORS middleware ───────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Import and mount routers ──────────────────────────────
from api.routes.health import router as health_router
from api.routes.query  import router as query_router

app.include_router(health_router)
app.include_router(query_router)


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "name"       : "Agentic RAG System",
        "version"    : "1.0.0",
        "status"     : "running",
        "docs"       : "/docs",
        "health"     : "/health",
        "environment": settings.environment
    }
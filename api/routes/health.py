"""
Health check and system status API routes.
"""

from fastapi import APIRouter
from core.logger import get_logger
from api.schemas.request_response import HealthResponse, MetricsResponse
from config.settings import settings

logger     = get_logger(__name__)
router     = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/",
    response_model = HealthResponse,
    summary        = "Basic health check"
)
async def health_check() -> HealthResponse:
    """
    Check if the API is running and healthy.

    Returns:
        HealthResponse with system status
    """
    logger.info("Health check requested")
    return HealthResponse(
        status      = "healthy",
        version     = "1.0.0",
        environment = settings.environment,
        components  = {
            "llm"        : "groq",
            "embeddings" : settings.embedding_model,
            "vector_store": "faiss",
            "database"   : "sqlite",
            "cache"      : "enabled" if settings.cache_enabled else "disabled",
        }
    )


@router.get(
    "/metrics",
    response_model = MetricsResponse,
    summary        = "System performance metrics"
)
async def get_metrics() -> MetricsResponse:
    """
    Get system performance metrics.

    Returns:
        MetricsResponse with current metrics
    """
    from observability.tracer            import tracer
    from observability.metrics_collector import metrics_collector

    tracer_metrics    = tracer.get_metrics()
    collector_metrics = metrics_collector.get_all_metrics()

    logger.info("Metrics requested")
    return MetricsResponse(
        total_requests = tracer_metrics.get("total_requests", 0),
        successful     = tracer_metrics.get("successful", 0),
        failed         = tracer_metrics.get("failed", 0),
        avg_latency_ms = tracer_metrics.get("avg_latency_ms", 0.0),
        cache_hits     = tracer_metrics.get("cache_hits", 0),
        cache_misses   = tracer_metrics.get("cache_misses", 0),
        uptime_seconds = collector_metrics.get("uptime_seconds", 0.0)
    )


@router.get(
    "/ready",
    summary = "Readiness check"
)
async def readiness_check() -> dict:
    """
    Check if all system components are ready.

    Returns:
        Dict with component readiness status
    """
    components = {}

    # Check LLM
    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            model   = settings.groq_model,
            api_key = settings.groq_api_key
        )
        llm.invoke("ping")
        components["llm"] = "ready"
    except Exception as e:
        components["llm"] = f"error: {str(e)[:50]}"

    # Check vector store
    try:
        from vectorstore.faiss_store import faiss_store
        if faiss_store.total_vectors > 0:
            components["vector_store"] = "ready"
        else:
            components["vector_store"] = "empty — run ingestion"
    except Exception as e:
        components["vector_store"] = f"error: {str(e)[:50]}"

    # Check database
    try:
        from database.sqlite_db import sqlite_db
        sqlite_db.get_stats()
        components["database"] = "ready"
    except Exception as e:
        components["database"] = f"error: {str(e)[:50]}"

    all_ready = all(
        "ready" in str(v)
        for v in components.values()
    )

    return {
        "ready"     : all_ready,
        "components": components
    }
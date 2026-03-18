"""
Query processing API routes.
Handles incoming queries and document ingestion.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from core.logger import get_logger
from api.schemas.request_response import (
    QueryRequest,
    QueryResponse,
    IngestRequest,
    IngestResponse,
)
from config.settings import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])


def get_orchestrator():
    """
    Lazy-load orchestrator to avoid circular imports.

    Returns:
        Orchestrator instance
    """
    from langchain_groq import ChatGroq
    from agents.orchestrator import Orchestrator

    llm = ChatGroq(
        model       = settings.groq_model,
        api_key     = settings.groq_api_key,
        temperature = settings.groq_temperature,
        max_tokens  = settings.groq_max_tokens
    )
    return Orchestrator(llm)


@router.post(
    "/",
    response_model = QueryResponse,
    summary        = "Process a query through the full pipeline"
)
async def process_query(request: QueryRequest) -> QueryResponse:
    """
    Process a user query through the full agentic RAG pipeline.

    Args:
        request: QueryRequest with query and options

    Returns:
        QueryResponse with answer and metadata
    """
    logger.info(f"API query received: {request.query[:60]}")

    try:
        orchestrator = get_orchestrator()
        result       = orchestrator.run(
            query      = request.query,
            session_id = request.session_id,
            use_cache  = request.use_cache
        )

        return QueryResponse(
            query         = result.get("query", request.query),
            answer        = result.get("answer", ""),
            route         = result.get("route"),
            sources       = result.get("sources", []),
            score         = result.get("score", 0.0),
            feedback      = result.get("feedback"),
            from_cache    = result.get("from_cache", False),
            session_id    = result.get("session_id"),
            trace_id      = result.get("trace_id"),
            total_time_ms = result.get("total_time_ms", 0.0),
            success       = result.get("success", False)
        )

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = f"Query processing failed: {str(e)}"
        )


@router.post(
    "/ingest",
    response_model = IngestResponse,
    summary        = "Ingest documents into the vector store"
)
async def ingest_documents(request: IngestRequest) -> IngestResponse:
    """
    Ingest text documents into the FAISS vector store.

    Args:
        request: IngestRequest with texts and source name

    Returns:
        IngestResponse with ingestion statistics
    """
    logger.info(f"Ingestion requested | source={request.source_name}")

    if not request.texts:
        raise HTTPException(
            status_code = 400,
            detail      = "No texts provided for ingestion"
        )

    try:
        from langchain.schema import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from vectorstore.faiss_store import faiss_store
        from vectorstore.embeddings  import embedding_manager

        # Create documents
        docs = [
            Document(
                page_content = text,
                metadata     = {
                    "source"  : request.source_name,
                    "index"   : i
                }
            )
            for i, text in enumerate(request.texts)
        ]

        # Chunk documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size    = settings.chunk_size,
            chunk_overlap = settings.chunk_overlap
        )
        chunks = splitter.split_documents(docs)

        # Add to vector store
        if faiss_store._vectorstore is not None:
            faiss_store.add_documents(chunks)
        else:
            faiss_store.build(chunks)

        faiss_store.save()

        logger.info(
            f"Ingestion complete | "
            f"docs={len(docs)} | chunks={len(chunks)}"
        )

        return IngestResponse(
            success       = True,
            docs_ingested = len(docs),
            chunks_created = len(chunks),
            message       = (
                f"Successfully ingested {len(docs)} documents "
                f"creating {len(chunks)} chunks"
            )
        )

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = f"Ingestion failed: {str(e)}"
        )


@router.get(
    "/history",
    summary = "Get recent query history"
)
async def get_history(
    session_id: str = None,
    limit     : int = 10
) -> dict:
    """
    Get recent query history from database.

    Args:
        session_id: Optional session filter
        limit     : Maximum records to return

    Returns:
        Dict with query history records
    """
    try:
        from database.sqlite_db import sqlite_db
        records = sqlite_db.get_recent_queries(
            session_id = session_id,
            limit      = limit
        )
        return {
            "records"  : records,
            "count"    : len(records),
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Get history failed: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = f"History retrieval failed: {str(e)}"
        )
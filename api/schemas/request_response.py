"""
Pydantic schemas for API request and response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema for incoming query requests."""

    query      : str   = Field(
        ...,
        min_length  = 1,
        max_length  = 2000,
        description = "User query string"
    )
    session_id : Optional[str] = Field(
        default     = None,
        description = "Session identifier for memory continuity"
    )
    use_cache  : bool  = Field(
        default     = True,
        description = "Whether to use response cache"
    )
    use_web    : bool  = Field(
        default     = False,
        description = "Whether to enable web search"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query"     : "What is RAG and how does it work?",
                "session_id": "user_123",
                "use_cache" : True,
                "use_web"   : False
            }
        }


class QueryResponse(BaseModel):
    """Schema for query response."""

    query        : str            = Field(..., description="Original query")
    answer       : str            = Field(..., description="Generated answer")
    route        : Optional[str]  = Field(None, description="Agent route used")
    sources      : List[str]      = Field(default=[], description="Source documents")
    score        : float          = Field(default=0.0, description="Evaluation score")
    feedback     : Optional[str]  = Field(None, description="Evaluation feedback")
    from_cache   : bool           = Field(default=False, description="Whether from cache")
    session_id   : Optional[str]  = Field(None, description="Session identifier")
    trace_id     : Optional[str]  = Field(None, description="Trace identifier")
    total_time_ms: float          = Field(default=0.0, description="Total latency ms")
    success      : bool           = Field(..., description="Whether succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "query"        : "What is RAG?",
                "answer"       : "RAG stands for Retrieval Augmented Generation...",
                "route"        : "RAG_AGENT",
                "sources"      : ["rag_overview.txt"],
                "score"        : 8.5,
                "feedback"     : "Clear and accurate response",
                "from_cache"   : False,
                "session_id"   : "user_123",
                "trace_id"     : "abc12345",
                "total_time_ms": 1250.5,
                "success"      : True
            }
        }


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status     : str  = Field(..., description="System status")
    version    : str  = Field(..., description="API version")
    environment: str  = Field(..., description="Running environment")
    components : dict = Field(default={}, description="Component statuses")


class IngestRequest(BaseModel):
    """Schema for document ingestion request."""

    texts      : Optional[List[str]] = Field(
        default     = None,
        description = "List of raw text strings to ingest"
    )
    source_name: Optional[str] = Field(
        default     = "api_ingestion",
        description = "Source label for ingested documents"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "texts"      : ["Document content here..."],
                "source_name": "my_document"
            }
        }


class IngestResponse(BaseModel):
    """Schema for document ingestion response."""

    success      : bool = Field(..., description="Whether ingestion succeeded")
    docs_ingested: int  = Field(..., description="Number of documents ingested")
    chunks_created: int = Field(..., description="Number of chunks created")
    message      : str  = Field(..., description="Status message")


class MetricsResponse(BaseModel):
    """Schema for system metrics response."""

    total_requests : int   = Field(..., description="Total requests processed")
    successful     : int   = Field(..., description="Successful requests")
    failed         : int   = Field(..., description="Failed requests")
    avg_latency_ms : float = Field(..., description="Average latency in ms")
    cache_hits     : int   = Field(..., description="Cache hit count")
    cache_misses   : int   = Field(..., description="Cache miss count")
    uptime_seconds : float = Field(..., description="System uptime in seconds")
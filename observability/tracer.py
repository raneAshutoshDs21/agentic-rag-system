"""
Observability tracer for tracking pipeline execution.
Records spans, latency, and errors across all nodes.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Span:
    """Represents a single traced operation within a trace."""
    span_id   : str
    name      : str
    start_time: float
    end_time  : float = 0.0
    duration_ms: float = 0.0
    status    : str   = "running"
    error     : str   = ""
    metadata  : Dict  = field(default_factory=dict)


@dataclass
class Trace:
    """Represents a full request trace across all pipeline nodes."""
    trace_id   : str
    query      : str
    spans      : List[Span] = field(default_factory=list)
    start_time : float      = field(default_factory=time.time)
    end_time   : float      = 0.0
    total_ms   : float      = 0.0
    success    : bool       = False
    session_id : str        = ""


class ObservabilityTracer:
    """
    Lightweight distributed tracer for the agentic RAG pipeline.
    Tracks spans, latency, and errors across all components.
    """

    def __init__(self):
        """Initialize tracer with empty trace store."""
        self.traces  : Dict[str, Trace] = {}
        self.metrics : Dict[str, float] = {
            "total_requests"  : 0,
            "successful"      : 0,
            "failed"          : 0,
            "total_latency_ms": 0.0,
            "avg_latency_ms"  : 0.0,
            "cache_hits"      : 0,
            "cache_misses"    : 0,
        }
        logger.info("ObservabilityTracer initialized")

    def start_trace(
        self,
        query     : str,
        session_id: str = ""
    ) -> str:
        """
        Start a new trace for a request.

        Args:
            query     : User query being traced
            session_id: Optional session identifier

        Returns:
            Trace ID string
        """
        trace_id = str(uuid.uuid4())[:8]
        self.traces[trace_id] = Trace(
            trace_id   = trace_id,
            query      = query,
            session_id = session_id
        )
        self.metrics["total_requests"] += 1
        logger.info(
            f"[TRACE START] id={trace_id} | "
            f"query={query[:50]}"
        )
        return trace_id

    def start_span(
        self,
        trace_id: str,
        name    : str,
        metadata: dict = None
    ) -> str:
        """
        Start a new span within a trace.

        Args:
            trace_id: Parent trace ID
            name    : Span name (node or component name)
            metadata: Optional span metadata

        Returns:
            Span ID string
        """
        span_id = str(uuid.uuid4())[:6]
        span    = Span(
            span_id    = span_id,
            name       = name,
            start_time = time.time(),
            metadata   = metadata or {}
        )

        if trace_id in self.traces:
            self.traces[trace_id].spans.append(span)

        logger.info(f"  [SPAN START] {name} ({span_id})")
        return span_id

    def end_span(
        self,
        trace_id: str,
        span_id : str,
        status  : str = "ok",
        error   : str = ""
    ):
        """
        End a span and record its duration.

        Args:
            trace_id: Parent trace ID
            span_id : Span to end
            status  : Completion status (ok or error)
            error   : Optional error message
        """
        if trace_id not in self.traces:
            return

        for span in self.traces[trace_id].spans:
            if span.span_id == span_id:
                span.end_time   = time.time()
                span.duration_ms = (
                    span.end_time - span.start_time
                ) * 1000
                span.status = status
                span.error  = error
                logger.info(
                    f"  [SPAN END] {span.name} | "
                    f"{span.duration_ms:.1f}ms | {status}"
                )
                break

    def end_trace(
        self,
        trace_id: str,
        success : bool = True
    ):
        """
        End a trace and compute total duration.

        Args:
            trace_id: Trace to end
            success : Whether the trace completed successfully
        """
        if trace_id not in self.traces:
            return

        trace           = self.traces[trace_id]
        trace.end_time  = time.time()
        trace.total_ms  = (trace.end_time - trace.start_time) * 1000
        trace.success   = success

        # Update metrics
        if success:
            self.metrics["successful"] += 1
        else:
            self.metrics["failed"] += 1

        self.metrics["total_latency_ms"] += trace.total_ms
        self.metrics["avg_latency_ms"]    = (
            self.metrics["total_latency_ms"] /
            self.metrics["total_requests"]
        )

        logger.info(
            f"[TRACE END] id={trace_id} | "
            f"{trace.total_ms:.1f}ms | success={success}"
        )

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Get a trace by ID.

        Args:
            trace_id: Trace identifier

        Returns:
            Trace object or None
        """
        return self.traces.get(trace_id)

    def get_trace_summary(self, trace_id: str) -> dict:
        """
        Get a formatted summary of a trace.

        Args:
            trace_id: Trace identifier

        Returns:
            Dict with trace summary
        """
        trace = self.traces.get(trace_id)
        if not trace:
            return {}

        return {
            "trace_id"  : trace.trace_id,
            "query"     : trace.query[:60],
            "session_id": trace.session_id,
            "total_ms"  : round(trace.total_ms, 1),
            "success"   : trace.success,
            "num_spans" : len(trace.spans),
            "spans"     : [
                {
                    "name"       : s.name,
                    "duration_ms": round(s.duration_ms, 1),
                    "status"     : s.status,
                    "error"      : s.error
                }
                for s in trace.spans
            ]
        }

    def get_metrics(self) -> dict:
        """
        Get aggregated system metrics.

        Returns:
            Dict with all system metrics
        """
        return {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in self.metrics.items()
        }

    def get_slowest_spans(self, n: int = 5) -> List[dict]:
        """
        Get the slowest spans across all traces.

        Args:
            n: Number of slowest spans to return

        Returns:
            List of span dicts sorted by duration
        """
        all_spans = []
        for trace in self.traces.values():
            for span in trace.spans:
                all_spans.append({
                    "trace_id"   : trace.trace_id,
                    "span_name"  : span.name,
                    "duration_ms": round(span.duration_ms, 1),
                    "status"     : span.status
                })

        return sorted(
            all_spans,
            key=lambda x: x["duration_ms"],
            reverse=True
        )[:n]

    def reset(self):
        """Clear all traces and reset metrics."""
        self.traces = {}
        for key in self.metrics:
            self.metrics[key] = 0
        logger.info("ObservabilityTracer reset")


# ── Singleton instance ────────────────────────────────────
tracer = ObservabilityTracer()
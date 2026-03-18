"""
System metrics collector for the agentic RAG pipeline.
Tracks performance, usage, and health metrics over time.
"""

import time
from collections import defaultdict
from typing import Dict, List
from core.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """
    Collects and aggregates system-level performance metrics.
    Tracks latency, throughput, error rates, and resource usage.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._counters  : Dict[str, int]         = defaultdict(int)
        self._gauges    : Dict[str, float]        = defaultdict(float)
        self._histograms: Dict[str, List[float]]  = defaultdict(list)
        self._start_time: float                   = time.time()
        logger.info("MetricsCollector initialized")

    def increment(self, metric: str, value: int = 1):
        """
        Increment a counter metric.

        Args:
            metric: Metric name
            value : Increment amount
        """
        self._counters[metric] += value
        logger.debug(f"Counter {metric} = {self._counters[metric]}")

    def gauge(self, metric: str, value: float):
        """
        Set a gauge metric to a specific value.

        Args:
            metric: Metric name
            value : Gauge value
        """
        self._gauges[metric] = value
        logger.debug(f"Gauge {metric} = {value}")

    def histogram(self, metric: str, value: float):
        """
        Record a value in a histogram metric.

        Args:
            metric: Metric name
            value : Value to record
        """
        self._histograms[metric].append(value)
        logger.debug(f"Histogram {metric} += {value}")

    def record_latency(self, operation: str, latency_ms: float):
        """
        Record operation latency.

        Args:
            operation : Operation name
            latency_ms: Latency in milliseconds
        """
        self.histogram(f"{operation}_latency_ms", latency_ms)
        self.increment(f"{operation}_calls")

    def record_error(self, component: str):
        """
        Record an error for a component.

        Args:
            component: Component that errored
        """
        self.increment(f"{component}_errors")
        self.increment("total_errors")

    def record_cache_hit(self):
        """Record a cache hit."""
        self.increment("cache_hits")

    def record_cache_miss(self):
        """Record a cache miss."""
        self.increment("cache_misses")

    def get_histogram_stats(self, metric: str) -> dict:
        """
        Compute statistics for a histogram metric.

        Args:
            metric: Histogram metric name

        Returns:
            Dict with count, mean, min, max, p95
        """
        values = self._histograms.get(metric, [])
        if not values:
            return {"count": 0, "mean": 0, "min": 0, "max": 0, "p95": 0}

        sorted_vals = sorted(values)
        p95_idx     = int(len(sorted_vals) * 0.95)

        return {
            "count": len(values),
            "mean" : round(sum(values) / len(values), 2),
            "min"  : round(min(values), 2),
            "max"  : round(max(values), 2),
            "p95"  : round(sorted_vals[p95_idx], 2)
        }

    def get_cache_hit_rate(self) -> float:
        """
        Compute cache hit rate.

        Returns:
            Hit rate as float between 0 and 1
        """
        hits   = self._counters.get("cache_hits", 0)
        misses = self._counters.get("cache_misses", 0)
        total  = hits + misses
        return round(hits / total, 3) if total > 0 else 0.0

    def get_error_rate(self, component: str = None) -> float:
        """
        Compute error rate for a component or overall.

        Args:
            component: Optional component name

        Returns:
            Error rate as float between 0 and 1
        """
        if component:
            errors = self._counters.get(f"{component}_errors", 0)
            calls  = self._counters.get(f"{component}_calls", 0)
        else:
            errors = self._counters.get("total_errors", 0)
            calls  = self._counters.get("total_requests", 0)

        return round(errors / calls, 3) if calls > 0 else 0.0

    def get_uptime_seconds(self) -> float:
        """Get system uptime in seconds."""
        return round(time.time() - self._start_time, 1)

    def get_all_metrics(self) -> dict:
        """
        Get complete metrics snapshot.

        Returns:
            Dict with all counters, gauges, and histogram stats
        """
        histogram_stats = {
            metric: self.get_histogram_stats(metric)
            for metric in self._histograms
        }

        return {
            "uptime_seconds" : self.get_uptime_seconds(),
            "counters"       : dict(self._counters),
            "gauges"         : dict(self._gauges),
            "histograms"     : histogram_stats,
            "cache_hit_rate" : self.get_cache_hit_rate(),
            "error_rate"     : self.get_error_rate(),
        }

    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._start_time = time.time()
        logger.info("MetricsCollector reset")


# ── Singleton instance ────────────────────────────────────
metrics_collector = MetricsCollector()
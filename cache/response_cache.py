"""
Response cache using SQLite backend.
Avoids redundant LLM calls for identical queries.
"""

import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Optional
from core.logger import get_logger
from core.exceptions import CacheException
from config.settings import settings

logger = get_logger(__name__)


class ResponseCache:
    """
    SQLite-backed response cache with TTL expiration.
    Significantly reduces latency for repeated queries.
    """

    def __init__(
        self,
        db_path: str = None,
        ttl    : int = None,
        enabled: bool = None
    ):
        """
        Initialize response cache.

        Args:
            db_path: Path to SQLite database
            ttl    : Time-to-live in seconds
            enabled: Whether cache is active
        """
        self.db_path = Path(db_path or settings.sqlite_db_path)
        self.ttl     = ttl     or settings.cache_ttl
        self.enabled = enabled if enabled is not None else settings.cache_enabled

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_table()

        logger.info(
            f"ResponseCache initialized | "
            f"ttl={self.ttl}s | enabled={self.enabled}"
        )

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(str(self.db_path))

    def _init_table(self):
        """Create cache table if not exists."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key  TEXT PRIMARY KEY,
                    query      TEXT NOT NULL,
                    response   TEXT NOT NULL,
                    score      REAL DEFAULT 0.0,
                    hit_count  INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    last_hit   REAL
                )
            """)
            conn.commit()

    def _make_key(self, query: str) -> str:
        """
        Generate a cache key from query string.

        Args:
            query: User query

        Returns:
            MD5 hash string as cache key
        """
        return hashlib.md5(
            query.lower().strip().encode()
        ).hexdigest()

    def get(self, query: str) -> Optional[dict]:
        """
        Retrieve cached response if exists and not expired.

        Args:
            query: User query string

        Returns:
            Cached response dict or None if miss/expired
        """
        if not self.enabled:
            return None

        key = self._make_key(query)

        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT query, response, score, hit_count, created_at
                    FROM response_cache
                    WHERE cache_key=?
                    """,
                    (key,)
                )
                row = cursor.fetchone()

            if not row:
                logger.info(f"Cache MISS: {query[:50]}")
                return None

            age = time.time() - row[4]

            # Check TTL
            if age > self.ttl:
                logger.info(
                    f"Cache EXPIRED: {query[:50]} "
                    f"(age={age:.0f}s)"
                )
                self.delete(query)
                return None

            # Update hit count
            self._increment_hits(key)

            logger.info(
                f"Cache HIT: {query[:50]} "
                f"(age={age:.0f}s | hits={row[3]+1})"
            )

            return {
                "query"     : row[0],
                "response"  : row[1],
                "score"     : row[2],
                "hit_count" : row[3] + 1,
                "age_secs"  : round(age, 1),
                "from_cache": True
            }

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None

    def set(
        self,
        query   : str,
        response: str,
        score   : float = 0.0
    ):
        """
        Store a response in cache.

        Args:
            query   : User query
            response: Generated response
            score   : Evaluation score
        """
        if not self.enabled:
            return

        key = self._make_key(query)

        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO response_cache
                    (cache_key, query, response, score, hit_count, created_at, last_hit)
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                    """,
                    (key, query, response, score, time.time(), time.time())
                )
                conn.commit()
            logger.info(f"Cache SET: {query[:50]} | score={score}")

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            raise CacheException(f"Cache set failed: {e}")

    def delete(self, query: str):
        """
        Remove a specific entry from cache.

        Args:
            query: Query whose cache entry to delete
        """
        key = self._make_key(query)
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "DELETE FROM response_cache WHERE cache_key=?",
                    (key,)
                )
                conn.commit()
            logger.info(f"Cache DELETE: {query[:50]}")

        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            raise CacheException(f"Cache delete failed: {e}")

    def clear_expired(self) -> int:
        """
        Remove all expired cache entries.

        Returns:
            Number of entries removed
        """
        cutoff = time.time() - self.ttl
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "DELETE FROM response_cache WHERE created_at < ?",
                    (cutoff,)
                )
                conn.commit()
                count = cursor.rowcount

            logger.info(f"Cleared {count} expired cache entries")
            return count

        except Exception as e:
            logger.error(f"Cache clear expired failed: {e}")
            return 0

    def clear_all(self) -> int:
        """
        Clear entire cache.

        Returns:
            Number of entries removed
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute("DELETE FROM response_cache")
                conn.commit()
                count = cursor.rowcount

            logger.info(f"Cache fully cleared | removed={count}")
            return count

        except Exception as e:
            logger.error(f"Cache clear all failed: {e}")
            return 0

    def _increment_hits(self, key: str):
        """Increment hit counter for a cache entry."""
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    UPDATE response_cache
                    SET hit_count=hit_count+1, last_hit=?
                    WHERE cache_key=?
                    """,
                    (time.time(), key)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Increment hits failed: {e}")

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with entry count, avg score, total hits
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*),
                        AVG(score),
                        SUM(hit_count),
                        AVG(hit_count)
                    FROM response_cache
                    """
                )
                row = cursor.fetchone()

            return {
                "total_entries": row[0] or 0,
                "avg_score"    : round(row[1] or 0.0, 2),
                "total_hits"   : row[2] or 0,
                "avg_hits"     : round(row[3] or 0.0, 2),
                "ttl_seconds"  : self.ttl,
                "enabled"      : self.enabled
            }

        except Exception as e:
            logger.error(f"Cache stats failed: {e}")
            return {}
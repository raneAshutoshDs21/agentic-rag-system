"""
SQLite database manager for the agentic RAG system.
Provides high-level CRUD operations using raw SQLite.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
from core.logger import get_logger
from core.exceptions import DatabaseToolException
from config.settings import settings

logger = get_logger(__name__)


class SQLiteDB:
    """
    High-level SQLite database manager.
    Uses raw SQLite to avoid ORM schema conflicts.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize SQLite database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or settings.sqlite_db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"SQLiteDB ready | path={self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        """Get a new database connection."""
        return sqlite3.connect(str(self.db_path))

    def save_query(
        self,
        session_id: str,
        query     : str,
        answer    : str,
        route     : str   = "",
        score     : float = 0.0,
        success   : bool  = True
    ) -> int:
        """
        Save a query and answer to history.

        Args:
            session_id: Session identifier
            query     : User query
            answer    : Generated answer
            route     : Agent route used
            score     : Evaluation score
            success   : Whether generation succeeded

        Returns:
            Record ID
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO query_history
                    (session_id, query, answer, score, route, timestamp)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        session_id,
                        query[:500],
                        answer[:2000],
                        score,
                        route,
                    )
                )
                conn.commit()
                record_id = cursor.lastrowid

            logger.info(
                f"Saved query | id={record_id} | session={session_id}"
            )
            return record_id

        except Exception as e:
            logger.error(f"Save query failed: {e}")
            raise DatabaseToolException(f"Save query failed: {e}")

    def save_tool_result(
        self,
        tool_name: str,
        query    : str,
        result   : str,
        success  : bool = True,
        metadata : str  = ""
    ) -> int:
        """
        Save a tool execution result.

        Args:
            tool_name: Name of tool
            query    : Input query or code
            result   : Tool output
            success  : Whether execution succeeded
            metadata : Additional metadata string

        Returns:
            Record ID
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO tool_results
                    (tool_name, query, result, success, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        tool_name,
                        query[:500],
                        result[:1000],
                        int(success),
                        metadata
                    )
                )
                conn.commit()
                record_id = cursor.lastrowid

            logger.info(
                f"Saved tool result | id={record_id} | tool={tool_name}"
            )
            return record_id

        except Exception as e:
            logger.error(f"Save tool result failed: {e}")
            raise DatabaseToolException(f"Save tool result failed: {e}")

    def get_recent_queries(
        self,
        session_id: str = None,
        limit     : int = 10
    ) -> List[dict]:
        """
        Get recent query history.

        Args:
            session_id: Optional session filter
            limit     : Maximum records to return

        Returns:
            List of query history dicts
        """
        try:
            with self._get_conn() as conn:
                if session_id:
                    cursor = conn.execute(
                        """
                        SELECT session_id, query, answer, score, route, timestamp
                        FROM query_history
                        WHERE session_id=?
                        ORDER BY id DESC LIMIT ?
                        """,
                        (session_id, limit)
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT session_id, query, answer, score, route, timestamp
                        FROM query_history
                        ORDER BY id DESC LIMIT ?
                        """,
                        (limit,)
                    )
                cols = [d[0] for d in cursor.description]
                rows = cursor.fetchall()

            return [dict(zip(cols, row)) for row in rows]

        except Exception as e:
            logger.error(f"Get recent queries failed: {e}")
            return []

    def get_avg_score(self, session_id: str = None) -> float:
        """
        Get average evaluation score.

        Args:
            session_id: Optional session filter

        Returns:
            Average score float
        """
        try:
            with self._get_conn() as conn:
                if session_id:
                    result = conn.execute(
                        "SELECT AVG(score) FROM query_history WHERE session_id=?",
                        (session_id,)
                    ).fetchone()[0]
                else:
                    result = conn.execute(
                        "SELECT AVG(score) FROM query_history"
                    ).fetchone()[0]

            return round(result or 0.0, 2)

        except Exception as e:
            logger.error(f"Get avg score failed: {e}")
            return 0.0

    def get_stats(self) -> dict:
        """
        Get database statistics.

        Returns:
            Dict with record counts and averages
        """
        try:
            with self._get_conn() as conn:
                query_count = conn.execute(
                    "SELECT COUNT(*) FROM query_history"
                ).fetchone()[0]
                tool_count  = conn.execute(
                    "SELECT COUNT(*) FROM tool_results"
                ).fetchone()[0]
                avg_score   = conn.execute(
                    "SELECT AVG(score) FROM query_history"
                ).fetchone()[0]

            return {
                "query_history": query_count,
                "tool_results" : tool_count,
                "avg_score"    : round(avg_score or 0.0, 2),
                "db_path"      : self.db_path
            }

        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {}


# ── Singleton instance ────────────────────────────────────
sqlite_db = SQLiteDB()
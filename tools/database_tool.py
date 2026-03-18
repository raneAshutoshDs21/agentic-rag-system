"""
Database tool for storing and retrieving tool results.
Uses SQLite as the backend storage engine.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from core.base_tool import BaseTool
from core.logger import get_logger
from core.exceptions import DatabaseToolException
from config.settings import settings

logger = get_logger(__name__)


class DatabaseTool(BaseTool):
    """
    SQLite database tool for persisting tool results and queries.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize database tool.

        Args:
            db_path: Path to SQLite database file
        """
        super().__init__(
            name        = "database",
            description = "Store and retrieve data from SQLite database"
        )
        self.db_path = Path(db_path or settings.sqlite_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
        logger.info(f"DatabaseTool initialized | path={self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        """Get a new database connection."""
        return sqlite3.connect(str(self.db_path))

    def _init_tables(self):
        """Create required tables if they don't exist."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_results (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    query     TEXT NOT NULL,
                    result    TEXT NOT NULL,
                    success   INTEGER NOT NULL,
                    metadata  TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    query      TEXT NOT NULL,
                    answer     TEXT NOT NULL,
                    score      REAL,
                    route      TEXT,
                    timestamp  TEXT NOT NULL
                )
            """)
            conn.commit()
        logger.info("Database tables initialized")

    def execute(self, input_data: str, **kwargs) -> dict:
        """
        Execute a read-only SQL query.

        Args:
            input_data: SQL SELECT query string

        Returns:
            Dict with query results
        """
        if not input_data.strip().upper().startswith("SELECT"):
            return self._error_response(
                "Only SELECT queries are allowed via this interface"
            )

        try:
            with self._get_conn() as conn:
                cursor = conn.execute(input_data)
                rows   = cursor.fetchall()
                cols   = [d[0] for d in cursor.description]

            results = [dict(zip(cols, row)) for row in rows]
            logger.info(f"Query returned {len(results)} rows")

            return self._success_response(
                result   = results,
                metadata = {"row_count": len(results), "columns": cols}
            )

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise DatabaseToolException(f"Query failed: {e}")

    def save_tool_result(
        self,
        tool_name: str,
        query    : str,
        result   : str,
        success  : bool,
        metadata : dict = None
    ):
        """
        Save a tool execution result.

        Args:
            tool_name: Name of the tool
            query    : Input query or code
            result   : Tool output
            success  : Whether execution succeeded
            metadata : Additional metadata dict
        """
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO tool_results
                    (tool_name, query, result, success, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tool_name,
                        query[:500],
                        result[:1000],
                        int(success),
                        json.dumps(metadata or {}),
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
            logger.info(f"Saved tool result | tool={tool_name}")

        except Exception as e:
            logger.error(f"Save tool result failed: {e}")
            raise DatabaseToolException(f"Save failed: {e}")

    def save_query_history(
        self,
        session_id: str,
        query     : str,
        answer    : str,
        score     : float = 0.0,
        route     : str   = ""
    ):
        """Save a query and its answer to history."""
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO query_history
                    (session_id, query, answer, score, route, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        query[:500],
                        answer[:2000],
                        score,
                        route,
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
            logger.info(f"Saved query history | session={session_id}")

        except Exception as e:
            logger.error(f"Save query history failed: {e}")
            raise DatabaseToolException(f"Save history failed: {e}")

    def get_recent_queries(
        self,
        session_id: str = None,
        limit     : int = 10
    ) -> List[dict]:
        """
        Get recent query history.

        Args:
            session_id: Optional session filter
            limit     : Maximum results

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

    def get_stats(self) -> dict:
        """Get database statistics."""
        try:
            with self._get_conn() as conn:
                tool_count  = conn.execute(
                    "SELECT COUNT(*) FROM tool_results"
                ).fetchone()[0]
                query_count = conn.execute(
                    "SELECT COUNT(*) FROM query_history"
                ).fetchone()[0]
                avg_score   = conn.execute(
                    "SELECT AVG(score) FROM query_history"
                ).fetchone()[0]

            return {
                "tool_results" : tool_count,
                "query_history": query_count,
                "avg_score"    : round(avg_score or 0.0, 2)
            }
        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {}


# ── Singleton instance ────────────────────────────────────
database_tool = DatabaseTool()
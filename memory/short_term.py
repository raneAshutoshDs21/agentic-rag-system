"""
Short-term memory using SQLite.
Stores conversation history for the current session.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from core.logger import get_logger
from core.exceptions import ShortTermMemoryException
from config.settings import settings

logger = get_logger(__name__)


class ShortTermMemory:
    """
    Session-scoped conversation memory backed by SQLite.
    Stores recent messages for context window building.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize short-term memory.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path or settings.sqlite_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_table()
        logger.info(f"ShortTermMemory initialized | path={self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(str(self.db_path))

    def _init_table(self):
        """Create short term memory table if not exists."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS short_term_memory (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    session   TEXT NOT NULL,
                    role      TEXT NOT NULL,
                    content   TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def save(
        self,
        session: str,
        role   : str,
        content: str
    ):
        """
        Save a message to short-term memory.

        Args:
            session: Session identifier
            role   : Message role (user or assistant)
            content: Message content

        Raises:
            ShortTermMemoryException: If save fails
        """
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO short_term_memory
                    (session, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        session,
                        role,
                        content[:2000],
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
            logger.debug(f"Saved [{role}] to session {session}")

        except Exception as e:
            logger.error(f"ShortTermMemory save failed: {e}")
            raise ShortTermMemoryException(f"Save failed: {e}")

    def get(
        self,
        session: str,
        limit  : int = None
    ) -> List[Tuple[str, str, str]]:
        """
        Retrieve recent messages for a session.

        Args:
            session: Session identifier
            limit  : Maximum messages to return

        Returns:
            List of (role, content, timestamp) tuples oldest first

        Raises:
            ShortTermMemoryException: If retrieval fails
        """
        limit = limit or settings.short_term_limit

        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT role, content, timestamp
                    FROM short_term_memory
                    WHERE session=?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session, limit)
                )
                rows = cursor.fetchall()

            logger.debug(
                f"Retrieved {len(rows)} messages for session {session}"
            )
            return list(reversed(rows))

        except Exception as e:
            logger.error(f"ShortTermMemory get failed: {e}")
            raise ShortTermMemoryException(f"Get failed: {e}")

    def build_context_string(
        self,
        session: str,
        limit  : int = None
    ) -> str:
        """
        Build a formatted conversation history string.

        Args:
            session: Session identifier
            limit  : Maximum messages

        Returns:
            Formatted conversation string for LLM context
        """
        messages = self.get(session, limit)
        if not messages:
            return "No previous conversation."

        lines = []
        for role, content, _ in messages:
            lines.append(f"{role.upper()}: {content[:300]}")
        return "\n".join(lines)

    def clear(self, session: str):
        """
        Clear all messages for a session.

        Args:
            session: Session identifier
        """
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "DELETE FROM short_term_memory WHERE session=?",
                    (session,)
                )
                conn.commit()
            logger.info(f"Cleared short-term memory for session {session}")

        except Exception as e:
            logger.error(f"ShortTermMemory clear failed: {e}")
            raise ShortTermMemoryException(f"Clear failed: {e}")

    def count(self, session: str) -> int:
        """Get message count for a session."""
        with self._get_conn() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM short_term_memory WHERE session=?",
                (session,)
            ).fetchone()
        return result[0] if result else 0


# ── Singleton instance ────────────────────────────────────
short_term_memory = ShortTermMemory()
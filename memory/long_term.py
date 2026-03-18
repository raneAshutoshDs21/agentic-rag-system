"""
Long-term memory using SQLite.
Stores important facts and knowledge across sessions.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from core.logger import get_logger
from core.exceptions import LongTermMemoryException
from config.settings import settings

logger = get_logger(__name__)


class LongTermMemory:
    """
    Persistent cross-session memory backed by SQLite.
    Stores important facts, user preferences, and learned knowledge.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize long-term memory.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path or settings.sqlite_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_table()
        logger.info(f"LongTermMemory initialized | path={self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(str(self.db_path))

    def _init_table(self):
        """Create long term memory table if not exists."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    key       TEXT UNIQUE NOT NULL,
                    value     TEXT NOT NULL,
                    category  TEXT DEFAULT 'general',
                    metadata  TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def save(
        self,
        key     : str,
        value   : str,
        category: str  = "general",
        metadata: dict = None
    ):
        """
        Save a fact to long-term memory.

        Args:
            key     : Unique identifier for this fact
            value   : Fact content to store
            category: Category for grouping facts
            metadata: Optional additional metadata

        Raises:
            LongTermMemoryException: If save fails
        """
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO long_term_memory
                    (key, value, category, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        key,
                        value[:5000],
                        category,
                        json.dumps(metadata or {}),
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
            logger.info(f"Saved long-term fact | key={key} | category={category}")

        except Exception as e:
            logger.error(f"LongTermMemory save failed: {e}")
            raise LongTermMemoryException(f"Save failed: {e}")

    def get(self, key: str) -> Optional[str]:
        """
        Retrieve a fact by key.

        Args:
            key: Fact identifier

        Returns:
            Fact value string or None if not found
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    "SELECT value FROM long_term_memory WHERE key=?",
                    (key,)
                )
                row = cursor.fetchone()

            if row:
                logger.debug(f"Retrieved long-term fact | key={key}")
                return row[0]
            return None

        except Exception as e:
            logger.error(f"LongTermMemory get failed: {e}")
            raise LongTermMemoryException(f"Get failed: {e}")

    def get_by_category(self, category: str) -> List[Tuple[str, str]]:
        """
        Get all facts in a category.

        Args:
            category: Category name to filter by

        Returns:
            List of (key, value) tuples
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT key, value FROM long_term_memory
                    WHERE category=?
                    ORDER BY timestamp DESC
                    """,
                    (category,)
                )
                rows = cursor.fetchall()

            logger.debug(
                f"Retrieved {len(rows)} facts | category={category}"
            )
            return rows

        except Exception as e:
            logger.error(f"LongTermMemory get_by_category failed: {e}")
            raise LongTermMemoryException(f"Category get failed: {e}")

    def search(self, keyword: str) -> List[Tuple[str, str, str]]:
        """
        Search facts by keyword in key or value.

        Args:
            keyword: Search keyword

        Returns:
            List of (key, value, category) tuples
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute(
                    """
                    SELECT key, value, category FROM long_term_memory
                    WHERE value LIKE ? OR key LIKE ?
                    ORDER BY timestamp DESC
                    """,
                    (f"%{keyword}%", f"%{keyword}%")
                )
                rows = cursor.fetchall()

            logger.debug(
                f"Search '{keyword}' returned {len(rows)} results"
            )
            return rows

        except Exception as e:
            logger.error(f"LongTermMemory search failed: {e}")
            raise LongTermMemoryException(f"Search failed: {e}")

    def delete(self, key: str):
        """
        Delete a fact by key.

        Args:
            key: Fact identifier to delete
        """
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "DELETE FROM long_term_memory WHERE key=?",
                    (key,)
                )
                conn.commit()
            logger.info(f"Deleted long-term fact | key={key}")

        except Exception as e:
            logger.error(f"LongTermMemory delete failed: {e}")
            raise LongTermMemoryException(f"Delete failed: {e}")

    def get_all_categories(self) -> List[str]:
        """Get list of all unique categories."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT category FROM long_term_memory"
            )
            return [row[0] for row in cursor.fetchall()]

    def count(self) -> int:
        """Get total number of stored facts."""
        with self._get_conn() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM long_term_memory"
            ).fetchone()
        return result[0] if result else 0


# ── Singleton instance ────────────────────────────────────
long_term_memory = LongTermMemory()
"""
Memory manager combining short-term and long-term memory.
Provides unified interface for all memory operations.
"""

from typing import List, Optional, Tuple
from core.logger import get_logger
from core.exceptions import MemoryException
from memory.short_term import ShortTermMemory, short_term_memory
from memory.long_term  import LongTermMemory,  long_term_memory

logger = get_logger(__name__)


class MemoryManager:
    """
    Unified memory manager for the agentic RAG system.
    Combines short-term and long-term memory with a clean API.
    """

    def __init__(
        self,
        session_id   : str,
        short_term   : ShortTermMemory = None,
        long_term    : LongTermMemory  = None,
    ):
        """
        Initialize memory manager for a session.

        Args:
            session_id: Unique session identifier
            short_term: ShortTermMemory instance
            long_term : LongTermMemory instance
        """
        self.session_id = session_id
        self.stm        = short_term or short_term_memory
        self.ltm        = long_term  or long_term_memory
        logger.info(f"MemoryManager initialized | session={session_id}")

    # ── Short-term operations ─────────────────────────────

    def remember(self, role: str, content: str):
        """
        Save a message to short-term memory.

        Args:
            role   : Message role (user or assistant)
            content: Message content
        """
        try:
            self.stm.save(self.session_id, role, content)
        except Exception as e:
            logger.error(f"Remember failed: {e}")
            raise MemoryException(f"Short-term save failed: {e}")

    def recall_recent(self, limit: int = 6) -> list:
        """
        Get recent conversation messages.

        Args:
            limit: Maximum number of messages

        Returns:
            List of (role, content, timestamp) tuples
        """
        try:
            return self.stm.get(self.session_id, limit)
        except Exception as e:
            logger.error(f"Recall recent failed: {e}")
            return []

    def build_context(self, limit: int = 6) -> str:
        """
        Build conversation context string for LLM prompt.

        Args:
            limit: Maximum messages to include

        Returns:
            Formatted conversation history string
        """
        return self.stm.build_context_string(self.session_id, limit)

    def clear_session(self):
        """Clear all short-term memory for current session."""
        try:
            self.stm.clear(self.session_id)
            logger.info(f"Session cleared: {self.session_id}")
        except Exception as e:
            logger.error(f"Clear session failed: {e}")
            raise MemoryException(f"Session clear failed: {e}")

    # ── Long-term operations ──────────────────────────────

    def learn(
        self,
        key     : str,
        value   : str,
        category: str  = "general",
        metadata: dict = None
    ):
        """
        Save important fact to long-term memory.

        Args:
            key     : Unique fact identifier
            value   : Fact content
            category: Fact category
            metadata: Optional metadata
        """
        try:
            self.ltm.save(key, value, category, metadata)
        except Exception as e:
            logger.error(f"Learn failed: {e}")
            raise MemoryException(f"Long-term save failed: {e}")

    def recall_fact(self, key: str) -> Optional[str]:
        """
        Retrieve a specific fact from long-term memory.

        Args:
            key: Fact identifier

        Returns:
            Fact value or None
        """
        try:
            return self.ltm.get(key)
        except Exception as e:
            logger.error(f"Recall fact failed: {e}")
            return None

    def recall_category(self, category: str) -> List[Tuple[str, str]]:
        """
        Get all facts in a category.

        Args:
            category: Category name

        Returns:
            List of (key, value) tuples
        """
        try:
            return self.ltm.get_by_category(category)
        except Exception as e:
            logger.error(f"Recall category failed: {e}")
            return []

    def search_memory(self, keyword: str) -> List[Tuple]:
        """
        Search long-term memory by keyword.

        Args:
            keyword: Search term

        Returns:
            List of matching (key, value, category) tuples
        """
        try:
            return self.ltm.search(keyword)
        except Exception as e:
            logger.error(f"Search memory failed: {e}")
            return []

    # ── Combined operations ───────────────────────────────

    def get_full_context(self, limit: int = 6) -> dict:
        """
        Get both conversation history and relevant long-term facts.

        Args:
            limit: Short-term message limit

        Returns:
            Dict with conversation and facts
        """
        return {
            "conversation" : self.build_context(limit),
            "session_id"   : self.session_id,
            "message_count": self.stm.count(self.session_id),
            "fact_count"   : self.ltm.count()
        }

    def get_user_profile(self) -> dict:
        """
        Get stored user profile and preferences.

        Returns:
            Dict with user profile information
        """
        return {
            "expertise"  : self.recall_fact("user_expertise"),
            "preferences": self.recall_fact("user_preferences"),
            "project"    : self.recall_fact("project_name"),
            "model"      : self.recall_fact("preferred_model"),
        }

    def save_qa_pair(
        self,
        question: str,
        answer  : str,
        score   : float = 0.0
    ):
        """
        Save a high-quality QA pair to long-term memory.

        Args:
            question: User question
            answer  : Generated answer
            score   : Quality score
        """
        if score >= 7.0:
            key   = f"qa_{hash(question) % 100000}"
            value = f"Q: {question[:200]}\nA: {answer[:500]}"
            self.learn(key, value, category="qa_history")
            logger.info(f"Saved QA pair to long-term memory | score={score}")

    def get_stats(self) -> dict:
        """Get memory statistics."""
        return {
            "session_id"    : self.session_id,
            "short_term_msgs": self.stm.count(self.session_id),
            "long_term_facts": self.ltm.count(),
            "categories"    : self.ltm.get_all_categories()
        }
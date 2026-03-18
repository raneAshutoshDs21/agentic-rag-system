"""
Unit tests for memory components.
Tests short-term, long-term memory, and memory manager.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest


# ── Short Term Memory Tests ───────────────────────────────

class TestShortTermMemory:
    """Tests for ShortTermMemory."""

    @pytest.fixture
    def stm(self, tmp_path):
        """Create short term memory with temp database."""
        from memory.short_term import ShortTermMemory
        return ShortTermMemory(db_path=str(tmp_path / "test.db"))

    def test_save_and_retrieve(self, stm):
        """Should save and retrieve messages."""
        stm.save("session1", "user",      "Hello")
        stm.save("session1", "assistant", "Hi there!")

        messages = stm.get("session1")
        assert len(messages) == 2
        assert messages[0][0] == "user"
        assert messages[1][0] == "assistant"

    def test_session_isolation(self, stm):
        """Different sessions should be isolated."""
        stm.save("session1", "user", "Message for session 1")
        stm.save("session2", "user", "Message for session 2")

        msgs1 = stm.get("session1")
        msgs2 = stm.get("session2")

        assert len(msgs1) == 1
        assert len(msgs2) == 1
        assert msgs1[0][1] != msgs2[0][1]

    def test_limit_works(self, stm):
        """Should respect message limit."""
        for i in range(10):
            stm.save("session1", "user", f"Message {i}")

        messages = stm.get("session1", limit=3)
        assert len(messages) == 3

    def test_clear_removes_messages(self, stm):
        """Clear should remove all session messages."""
        stm.save("session1", "user", "test message")
        stm.clear("session1")

        messages = stm.get("session1")
        assert len(messages) == 0

    def test_count_returns_correct_number(self, stm):
        """Count should return correct message count."""
        stm.save("session1", "user", "msg 1")
        stm.save("session1", "user", "msg 2")
        stm.save("session1", "user", "msg 3")

        count = stm.count("session1")
        assert count == 3

    def test_build_context_string(self, stm):
        """Context string should include all messages."""
        stm.save("session1", "user",      "What is RAG?")
        stm.save("session1", "assistant", "RAG is Retrieval...")

        context = stm.build_context_string("session1")
        assert "USER"      in context
        assert "ASSISTANT" in context
        assert "RAG"       in context

    def test_empty_session_returns_no_history(self, stm):
        """Empty session should return no conversation message."""
        context = stm.build_context_string("empty_session")
        assert "No previous" in context


# ── Long Term Memory Tests ────────────────────────────────

class TestLongTermMemory:
    """Tests for LongTermMemory."""

    @pytest.fixture
    def ltm(self, tmp_path):
        """Create long term memory with temp database."""
        from memory.long_term import LongTermMemory
        return LongTermMemory(db_path=str(tmp_path / "test.db"))

    def test_save_and_retrieve(self, ltm):
        """Should save and retrieve facts."""
        ltm.save("user_name", "Ashutosh", category="profile")
        value = ltm.get("user_name")
        assert value == "Ashutosh"

    def test_get_nonexistent_returns_none(self, ltm):
        """Getting nonexistent key should return None."""
        value = ltm.get("nonexistent_key")
        assert value is None

    def test_upsert_on_duplicate_key(self, ltm):
        """Saving same key should update value."""
        ltm.save("key1", "value1")
        ltm.save("key1", "value2")
        value = ltm.get("key1")
        assert value == "value2"

    def test_get_by_category(self, ltm):
        """Should retrieve all facts in a category."""
        ltm.save("key1", "value1", category="project")
        ltm.save("key2", "value2", category="project")
        ltm.save("key3", "value3", category="other")

        results = ltm.get_by_category("project")
        assert len(results) == 2

    def test_search_by_keyword(self, ltm):
        """Should find facts containing keyword."""
        ltm.save("rag_info",  "RAG is Retrieval Augmented Generation")
        ltm.save("faiss_info", "FAISS is a vector search library")

        results = ltm.search("RAG")
        assert len(results) >= 1
        assert any("RAG" in r[1] for r in results)

    def test_delete_removes_fact(self, ltm):
        """Delete should remove a fact."""
        ltm.save("temp_key", "temp_value")
        ltm.delete("temp_key")
        value = ltm.get("temp_key")
        assert value is None

    def test_count_returns_total(self, ltm):
        """Count should return total stored facts."""
        ltm.save("k1", "v1")
        ltm.save("k2", "v2")
        ltm.save("k3", "v3")
        assert ltm.count() == 3

    def test_get_all_categories(self, ltm):
        """Should return all unique categories."""
        ltm.save("k1", "v1", category="cat1")
        ltm.save("k2", "v2", category="cat2")
        ltm.save("k3", "v3", category="cat1")

        categories = ltm.get_all_categories()
        assert "cat1" in categories
        assert "cat2" in categories
        assert len(set(categories)) == len(categories)


# ── Memory Manager Tests ──────────────────────────────────

class TestMemoryManager:
    """Tests for MemoryManager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create memory manager with temp databases."""
        from memory.short_term   import ShortTermMemory
        from memory.long_term    import LongTermMemory
        from memory.memory_manager import MemoryManager

        db_path = str(tmp_path / "test.db")
        stm     = ShortTermMemory(db_path=db_path)
        ltm     = LongTermMemory(db_path=db_path)
        return MemoryManager(
            session_id = "test_session",
            short_term = stm,
            long_term  = ltm
        )

    def test_remember_and_recall(self, manager):
        """Should save and recall messages."""
        manager.remember("user",      "What is RAG?")
        manager.remember("assistant", "RAG is a technique...")

        messages = manager.recall_recent()
        assert len(messages) == 2

    def test_learn_and_recall_fact(self, manager):
        """Should save and recall long-term facts."""
        manager.learn("project", "Agentic RAG System")
        value = manager.recall_fact("project")
        assert value == "Agentic RAG System"

    def test_build_context_returns_string(self, manager):
        """build_context should return formatted string."""
        manager.remember("user",      "Hello")
        manager.remember("assistant", "Hi!")

        context = manager.build_context()
        assert isinstance(context, str)
        assert len(context) > 0

    def test_clear_session(self, manager):
        """clear_session should remove short-term messages."""
        manager.remember("user", "test message")
        manager.clear_session()

        messages = manager.recall_recent()
        assert len(messages) == 0

    def test_save_qa_pair_only_high_score(self, manager):
        """save_qa_pair should only save high-scoring pairs."""
        manager.save_qa_pair("Q: What?", "A: answer", score=8.0)
        manager.save_qa_pair("Q: Bad?",  "A: bad",    score=4.0)

        results = manager.search_memory("What?")
        assert len(results) >= 1

    def test_get_full_context(self, manager):
        """get_full_context should return dict with all info."""
        manager.remember("user", "test")
        manager.learn("key1", "value1")

        context = manager.get_full_context()
        assert "conversation"  in context
        assert "session_id"    in context
        assert "message_count" in context
        assert "fact_count"    in context

    def test_get_stats(self, manager):
        """get_stats should return memory statistics."""
        stats = manager.get_stats()
        assert "session_id"     in stats
        assert "short_term_msgs" in stats
        assert "long_term_facts" in stats
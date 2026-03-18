"""
Unit tests for agent components.
Tests router, reasoning, RAG agent, and orchestrator.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from unittest.mock import MagicMock, patch


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def mock_llm():
    """Mock LLM instance."""
    llm        = MagicMock()
    llm.invoke = MagicMock(
        return_value=MagicMock(content="RAG_AGENT")
    )
    return llm


@pytest.fixture
def mock_retriever():
    """Mock document retriever."""
    from langchain.schema import Document
    retriever        = MagicMock()
    retriever.invoke = MagicMock(return_value=[
        Document(
            page_content = "RAG is Retrieval Augmented Generation",
            metadata     = {"source": "test.txt"}
        )
    ])
    return retriever


# ── Base Agent Tests ──────────────────────────────────────

class TestBaseAgent:
    """Tests for BaseAgent abstract class."""

    def test_base_agent_stats(self):
        """BaseAgent should track call statistics."""
        from core.base_agent import BaseAgent

        class ConcreteAgent(BaseAgent):
            def run(self, query, **kwargs):
                return {"answer": "test", "success": True}

        agent = ConcreteAgent("test_agent")
        agent("query 1")
        agent("query 2")

        stats = agent.get_stats()
        assert stats["calls"]  == 2
        assert stats["errors"] == 0

    def test_base_agent_error_handling(self):
        """BaseAgent should handle errors gracefully."""
        from core.base_agent import BaseAgent

        class FailingAgent(BaseAgent):
            def run(self, query, **kwargs):
                raise Exception("Test error")

        agent  = FailingAgent("failing_agent")
        result = agent("query")
        assert result["success"] == False
        assert "error" in result

    def test_base_agent_repr(self):
        """BaseAgent repr should include class and name."""
        from core.base_agent import BaseAgent

        class ConcreteAgent(BaseAgent):
            def run(self, query, **kwargs):
                return {"answer": "", "success": True}

        agent = ConcreteAgent("my_agent")
        assert "my_agent" in repr(agent)


# ── Router Agent Tests ────────────────────────────────────
# ── Router Agent Tests ────────────────────────────────────

class TestRouterAgent:
    """Tests for RouterAgent."""

    def test_router_init(self, mock_llm):
        """RouterAgent should initialize correctly."""
        from agents.router_agent import RouterAgent
        router = RouterAgent(mock_llm)
        assert router.name == "router"

    def test_router_returns_valid_route(self, mock_llm):
        """RouterAgent should return a valid route."""
        from agents.router_agent import RouterAgent
        from config.constants import VALID_ROUTES

        router       = RouterAgent(mock_llm)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value="RAG_AGENT")

        result = router.run("What is RAG?")

        assert result["success"] == True
        assert result["route"] in VALID_ROUTES

    def test_router_defaults_on_invalid(self, mock_llm):
        """RouterAgent should default to RAG_AGENT on invalid route."""
        from agents.router_agent import RouterAgent
        from config.constants import ROUTE_RAG_AGENT

        router       = RouterAgent(mock_llm)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value="INVALID_ROUTE")

        result = router.run("test query")
        assert result["route"] == ROUTE_RAG_AGENT

    def test_router_batch(self, mock_llm):
        """RouterAgent should handle batch routing."""
        from agents.router_agent import RouterAgent

        router       = RouterAgent(mock_llm)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value="RAG_AGENT")

        queries = ["query 1", "query 2", "query 3"]
        routes  = router.batch_route(queries)
        assert len(routes) == 3


# ── Reasoning Agent Tests ─────────────────────────────────

class TestReasoningAgent:
    """Tests for ReasoningAgent."""

    def test_reasoning_init(self, mock_llm):
        """ReasoningAgent should initialize correctly."""
        from agents.reasoning_agent import ReasoningAgent
        agent = ReasoningAgent(mock_llm)
        assert agent.name == "reasoning"

    def test_reasoning_returns_steps(self, mock_llm):
        """ReasoningAgent should parse reasoning steps."""
        from agents.reasoning_agent import ReasoningAgent

        agent       = ReasoningAgent(mock_llm)
        agent.chain = MagicMock()
        agent.chain.invoke = MagicMock(return_value=(
            "STEP 1: First consider the context\n"
            "STEP 2: Analyze the information\n"
            "CONCLUSION: RAG reduces hallucinations"
        ))

        result = agent.run("How does RAG reduce hallucinations?")

        assert result["success"]   == True
        assert len(result["steps"]) >= 2
        assert result["conclusion"] != ""

    def test_reasoning_without_retriever(self, mock_llm):
        """ReasoningAgent should work without retriever."""
        from agents.reasoning_agent import ReasoningAgent

        agent       = ReasoningAgent(mock_llm, retriever=None)
        agent.chain = MagicMock()
        agent.chain.invoke = MagicMock(
            return_value="CONCLUSION: test answer"
        )

        result = agent.run("test", use_rag=False)

        assert result["success"] == True
        assert result["used_rag"] == False



# ── RAG Agent Tests ───────────────────────────────────────

class TestRAGAgent:
    """Tests for RAGAgent."""

    def test_rag_agent_init(self, mock_llm):
        """RAGAgent should initialize correctly."""
        from agents.rag_agent import RAGAgent
        agent = RAGAgent(mock_llm)
        assert agent.name == "rag_agent"

    def test_rag_agent_without_pipeline(self, mock_llm):
        """RAGAgent should handle missing pipeline gracefully."""
        from agents.rag_agent import RAGAgent
        agent  = RAGAgent(mock_llm, rag_pipeline=None)
        result = agent.run("What is RAG?")
        assert "RAG pipeline not configured" in result["answer"]

    def test_rag_agent_with_memory(self, mock_llm):
        """RAGAgent should save to memory when provided."""
        from agents.rag_agent import RAGAgent
        from memory.memory_manager import MemoryManager

        mock_memory = MagicMock(spec=MemoryManager)
        mock_memory.build_context = MagicMock(return_value="")
        mock_memory.remember      = MagicMock()

        agent  = RAGAgent(mock_llm, rag_pipeline=None)
        result = agent.run("test", memory_manager=mock_memory)

        mock_memory.remember.assert_called()


# ── Graph State Tests ─────────────────────────────────────

class TestAgentState:
    """Tests for LangGraph state management."""

    def test_create_initial_state(self):
        """create_initial_state should return valid state."""
        from graph.state import create_initial_state

        state = create_initial_state(
            query      = "test query",
            session_id = "test_session"
        )

        assert state["query"]       == "test query"
        assert state["session_id"]  == "test_session"
        assert state["is_safe"]     == True
        assert state["route"]       == ""
        assert state["success"]     == False
        assert state["retry_count"] == 0

    def test_state_has_all_fields(self):
        """State should have all required fields."""
        from graph.state import create_initial_state, AgentState

        state    = create_initial_state("query", "session")
        required = [
            "query", "session_id", "is_safe", "safety_reason",
            "clean_query", "route", "retrieved_docs", "context",
            "sources", "web_results", "code_output", "reasoning",
            "answer", "eval_score", "eval_feedback", "needs_retry",
            "retry_count", "error", "success", "total_ms"
        ]

        for field in required:
            assert field in state, f"Missing field: {field}"
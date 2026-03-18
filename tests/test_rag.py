"""
Unit tests for RAG pipeline components.
Tests retriever, reranker, compressor, and pipeline.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from unittest.mock import MagicMock, patch
from langchain.schema import Document


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def sample_docs():
    """Sample documents for testing."""
    return [
        Document(
            page_content = "RAG stands for Retrieval Augmented Generation.",
            metadata     = {"source": "rag.txt", "topic": "RAG"}
        ),
        Document(
            page_content = "FAISS is a vector similarity search library.",
            metadata     = {"source": "faiss.txt", "topic": "VectorDB"}
        ),
        Document(
            page_content = "LangGraph enables stateful agentic workflows.",
            metadata     = {"source": "langgraph.txt", "topic": "Framework"}
        ),
    ]


@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls."""
    llm          = MagicMock()
    llm.invoke   = MagicMock(return_value=MagicMock(content="Mock LLM response"))
    return llm


@pytest.fixture
def mock_embeddings():
    """Mock embeddings for testing without model loading."""
    embeddings = MagicMock()
    embeddings.embed_query     = MagicMock(return_value=[0.1] * 384)
    embeddings.embed_documents = MagicMock(return_value=[[0.1] * 384])
    return embeddings


# ── Embedding Tests ───────────────────────────────────────

class TestEmbeddingManager:
    """Tests for EmbeddingManager."""

    def test_singleton_pattern(self):
        """EmbeddingManager should be a singleton."""
        from vectorstore.embeddings import EmbeddingManager
        em1 = EmbeddingManager()
        em2 = EmbeddingManager()
        assert em1 is em2

    def test_embedding_manager_init(self):
        """EmbeddingManager should initialize with correct model."""
        from vectorstore.embeddings import embedding_manager
        from config.settings import settings
        assert embedding_manager.model_name == settings.embedding_model


# ── FAISS Store Tests ─────────────────────────────────────

class TestFAISSStore:
    """Tests for FAISSStore."""

    def test_faiss_store_init(self):
        """FAISSStore should initialize correctly."""
        from vectorstore.faiss_store import FAISSStore
        store = FAISSStore()
        assert store is not None
        assert store.index_path is not None

    def test_faiss_build_raises_on_empty(self):
        """FAISSStore.build should raise on empty documents."""
        from vectorstore.faiss_store import FAISSStore
        from core.exceptions import FAISSException
        store = FAISSStore()
        with pytest.raises(FAISSException):
            store.build([])

    def test_total_vectors_zero_when_not_initialized(self):
        """total_vectors should be 0 when store not built."""
        from vectorstore.faiss_store import FAISSStore
        store = FAISSStore()
        store._vectorstore = None
        assert store.total_vectors == 0


# ── Retriever Tests ───────────────────────────────────────

class TestFAISSRetriever:
    """Tests for FAISSRetriever."""

    def test_retriever_init(self):
        """FAISSRetriever should initialize with defaults."""
        from rag.retriever import FAISSRetriever
        from config.settings import settings
        retriever = FAISSRetriever()
        assert retriever.k == settings.retriever_k
        assert retriever.name == "faiss_retriever"

    def test_retriever_returns_empty_on_error(self):
        """Retriever should return empty list on error."""
        from rag.retriever import FAISSRetriever
        retriever = FAISSRetriever()
        result    = retriever("test query")
        assert isinstance(result, list)

    def test_format_docs_empty(self):
        """format_docs should handle empty list."""
        from rag.retriever import FAISSRetriever
        retriever = FAISSRetriever()
        result    = retriever.format_docs([])
        assert "No relevant" in result

    def test_format_docs_with_documents(self, sample_docs):
        """format_docs should format documents correctly."""
        from rag.retriever import FAISSRetriever
        retriever = FAISSRetriever()
        result    = retriever.format_docs(sample_docs)
        assert "RAG" in result
        assert "Source:" in result

    def test_get_sources(self, sample_docs):
        """get_sources should extract source metadata."""
        from rag.retriever import FAISSRetriever
        retriever = FAISSRetriever()
        sources   = retriever.get_sources(sample_docs)
        assert "rag.txt"   in sources
        assert "faiss.txt" in sources


# ── Reranker Tests ────────────────────────────────────────

class TestLLMReranker:
    """Tests for LLMReranker."""

    def test_reranker_init(self, mock_llm):
        """LLMReranker should initialize correctly."""
        from rag.reranker import LLMReranker
        reranker = LLMReranker(mock_llm, top_k=3)
        assert reranker.top_k == 3

    def test_rerank_empty_returns_empty(self, mock_llm):
        """Reranker should return empty list for empty input."""
        from rag.reranker import LLMReranker
        reranker = LLMReranker(mock_llm)
        result   = reranker.rerank("query", [])
        assert result == []

    def test_score_document_returns_float(self, mock_llm):
        """score_document should return a float."""
        from rag.reranker import LLMReranker
        mock_llm.invoke = MagicMock(
            return_value=MagicMock(content="7")
        )
        reranker = LLMReranker(mock_llm)
        score    = reranker.score_document("query", "document text")
        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0

    def test_score_handles_invalid_response(self, mock_llm):
        """score_document should handle non-numeric LLM response."""
        from rag.reranker import LLMReranker
        mock_llm.invoke = MagicMock(
            return_value=MagicMock(content="not a number")
        )
        reranker = LLMReranker(mock_llm)
        score    = reranker.score_document("query", "document")
        assert score == 5.0


# ── Compressor Tests ──────────────────────────────────────

class TestContextCompressor:
    """Tests for ContextCompressor."""

    def test_compressor_init(self, mock_llm):
        """ContextCompressor should initialize correctly."""
        from rag.compressor import ContextCompressor
        compressor = ContextCompressor(mock_llm)
        assert compressor.min_length == 20

    def test_compress_empty_returns_empty(self, mock_llm):
        """Compress should return empty list for empty input."""
        from rag.compressor import ContextCompressor
        compressor = ContextCompressor(mock_llm)
        result     = compressor.compress("query", [])
        assert result == []

    def test_compress_not_relevant_removes_doc(
        self, mock_llm, sample_docs
    ):
        """Compress should remove NOT_RELEVANT docs."""
        from rag.compressor import ContextCompressor

        compressor       = ContextCompressor(mock_llm)
        compressor.chain = MagicMock()
        compressor.chain.invoke = MagicMock(return_value="NOT_RELEVANT")

        result = compressor.compress("query", [sample_docs[0]])
        assert len(result) == 0

# ── RAG Pipeline Tests ────────────────────────────────────

class TestRAGPipeline:
    """Tests for RAGPipeline."""

    def test_pipeline_init(self, mock_llm):
        """RAGPipeline should initialize with correct settings."""
        from rag.pipeline import RAGPipeline
        pipeline = RAGPipeline(
            llm          = mock_llm,
            use_rerank   = True,
            use_compress = True
        )
        assert pipeline.use_rerank   == True
        assert pipeline.use_compress == True
        assert pipeline.reranker     is not None
        assert pipeline.compressor   is not None

    def test_pipeline_no_rerank(self, mock_llm):
        """RAGPipeline without reranking should have None reranker."""
        from rag.pipeline import RAGPipeline
        pipeline = RAGPipeline(mock_llm, use_rerank=False)
        assert pipeline.reranker is None

    def test_format_docs_empty(self, mock_llm):
        """_format_docs should handle empty list."""
        from rag.pipeline import RAGPipeline
        pipeline = RAGPipeline(mock_llm)
        result   = pipeline._format_docs([])
        assert "No relevant" in result

    def test_format_docs_with_content(self, mock_llm, sample_docs):
        """_format_docs should format docs correctly."""
        from rag.pipeline import RAGPipeline
        pipeline = RAGPipeline(mock_llm)
        result   = pipeline._format_docs(sample_docs)
        assert "RAG" in result
        assert "Source:" in result
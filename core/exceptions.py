"""
Custom exceptions for the agentic RAG system.
Provides clear, specific error types for each component.
"""


class AgenticRAGException(Exception):
    """Base exception for all agentic RAG system errors."""

    def __init__(self, message: str, component: str = "unknown"):
        self.message   = message
        self.component = component
        super().__init__(f"[{component}] {message}")


# ── LLM Exceptions ───────────────────────────────────────
class LLMException(AgenticRAGException):
    """Raised when LLM call fails."""

    def __init__(self, message: str):
        super().__init__(message, component="LLM")


class LLMTimeoutException(LLMException):
    """Raised when LLM call times out."""
    pass


class LLMRateLimitException(LLMException):
    """Raised when LLM API rate limit is hit."""
    pass


# ── RAG Exceptions ────────────────────────────────────────
class RAGException(AgenticRAGException):
    """Raised when RAG pipeline fails."""

    def __init__(self, message: str):
        super().__init__(message, component="RAG")


class RetrieverException(RAGException):
    """Raised when document retrieval fails."""
    pass


class RerankerException(RAGException):
    """Raised when reranking fails."""
    pass


class CompressorException(RAGException):
    """Raised when context compression fails."""
    pass


# ── Vector Store Exceptions ───────────────────────────────
class VectorStoreException(AgenticRAGException):
    """Raised when vector store operations fail."""

    def __init__(self, message: str):
        super().__init__(message, component="VectorStore")


class FAISSException(VectorStoreException):
    """Raised when FAISS specific operations fail."""
    pass


class EmbeddingException(VectorStoreException):
    """Raised when embedding generation fails."""
    pass


# ── Tool Exceptions ───────────────────────────────────────
class ToolException(AgenticRAGException):
    """Raised when a tool execution fails."""

    def __init__(self, message: str, tool_name: str = "unknown"):
        super().__init__(message, component=f"Tool:{tool_name}")


class WebSearchException(ToolException):
    """Raised when web search fails."""

    def __init__(self, message: str):
        super().__init__(message, tool_name="web_search")


class PythonExecutorException(ToolException):
    """Raised when Python execution fails."""

    def __init__(self, message: str):
        super().__init__(message, tool_name="python_executor")


class DatabaseToolException(ToolException):
    """Raised when database tool fails."""

    def __init__(self, message: str):
        super().__init__(message, tool_name="database")


# ── Memory Exceptions ─────────────────────────────────────
class MemoryException(AgenticRAGException):
    """Raised when memory operations fail."""

    def __init__(self, message: str):
        super().__init__(message, component="Memory")


class ShortTermMemoryException(MemoryException):
    """Raised when short term memory fails."""
    pass


class LongTermMemoryException(MemoryException):
    """Raised when long term memory fails."""
    pass


# ── Agent Exceptions ──────────────────────────────────────
class AgentException(AgenticRAGException):
    """Raised when an agent fails."""

    def __init__(self, message: str, agent_name: str = "unknown"):
        super().__init__(message, component=f"Agent:{agent_name}")


class RouterException(AgentException):
    """Raised when router agent fails."""

    def __init__(self, message: str):
        super().__init__(message, agent_name="router")


class ReasoningException(AgentException):
    """Raised when reasoning agent fails."""

    def __init__(self, message: str):
        super().__init__(message, agent_name="reasoning")


# ── Graph Exceptions ──────────────────────────────────────
class GraphException(AgenticRAGException):
    """Raised when LangGraph workflow fails."""

    def __init__(self, message: str):
        super().__init__(message, component="Graph")


class NodeException(GraphException):
    """Raised when a specific graph node fails."""

    def __init__(self, message: str, node_name: str = "unknown"):
        self.node_name = node_name
        super().__init__(f"Node '{node_name}': {message}")


# ── Guardrail Exceptions ──────────────────────────────────
class GuardrailException(AgenticRAGException):
    """Raised when guardrail check fails."""

    def __init__(self, message: str):
        super().__init__(message, component="Guardrail")


class InputGuardrailException(GuardrailException):
    """Raised when input fails guardrail check."""
    pass


class OutputGuardrailException(GuardrailException):
    """Raised when output fails guardrail check."""
    pass


# ── Evaluation Exceptions ─────────────────────────────────
class EvaluationException(AgenticRAGException):
    """Raised when evaluation fails."""

    def __init__(self, message: str):
        super().__init__(message, component="Evaluation")


# ── Cache Exceptions ──────────────────────────────────────
class CacheException(AgenticRAGException):
    """Raised when cache operations fail."""

    def __init__(self, message: str):
        super().__init__(message, component="Cache")


# ── Config Exceptions ─────────────────────────────────────
class ConfigException(AgenticRAGException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str):
        super().__init__(message, component="Config")
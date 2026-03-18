"""
LangGraph state definition for the agentic RAG pipeline.
Defines the shared state object passed between all nodes.
"""

from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    """
    Shared state object passed between all LangGraph nodes.
    Every node reads from and writes to this state.
    """

    # ── Input ─────────────────────────────────────────────
    query         : str
    session_id    : str

    # ── Guardrails ────────────────────────────────────────
    is_safe       : bool
    safety_reason : str
    clean_query   : str

    # ── Routing ───────────────────────────────────────────
    route         : str

    # ── Retrieval ─────────────────────────────────────────
    retrieved_docs: List[str]
    context       : str
    sources       : List[str]

    # ── Tools ─────────────────────────────────────────────
    web_results   : str
    code_output   : str

    # ── Agent outputs ─────────────────────────────────────
    reasoning     : str
    answer        : str

    # ── Evaluation ────────────────────────────────────────
    eval_score    : float
    eval_feedback : str
    needs_retry   : bool

    # ── Metadata ──────────────────────────────────────────
    retry_count   : int
    error         : Optional[str]
    success       : bool
    total_ms      : float


def create_initial_state(
    query     : str,
    session_id: str = "default"
) -> AgentState:
    """
    Create a fresh initial state for a new query.

    Args:
        query     : User query string
        session_id: Session identifier

    Returns:
        AgentState with all fields initialized to defaults
    """
    return AgentState(
        query          = query,
        session_id     = session_id,
        is_safe        = True,
        safety_reason  = "",
        clean_query    = "",
        route          = "",
        retrieved_docs = [],
        context        = "",
        sources        = [],
        web_results    = "",
        code_output    = "",
        reasoning      = "",
        answer         = "",
        eval_score     = 0.0,
        eval_feedback  = "",
        needs_retry    = False,
        retry_count    = 0,
        error          = None,
        success        = False,
        total_ms       = 0.0
    )
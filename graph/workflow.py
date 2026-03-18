"""
LangGraph workflow definition for the agentic RAG pipeline.
Wires all nodes together with conditional routing logic.
"""

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from core.logger import get_logger
from graph.state import AgentState
from graph.nodes import PipelineNodes
from config.constants import (
    NODE_INPUT_GUARD,
    NODE_ROUTER,
    NODE_RETRIEVER,
    NODE_WEB_SEARCH,
    NODE_PYTHON,
    NODE_REASONING,
    NODE_GENERATOR,
    NODE_OUTPUT_GUARD,
    ROUTE_RAG_AGENT,
    ROUTE_WEB_SEARCH,
    ROUTE_PYTHON_AGENT,
    ROUTE_REASONING_AGENT,
    ROUTE_DIRECT_ANSWER,
)

logger = get_logger(__name__)


def should_continue_after_guard(state: AgentState) -> str:
    """
    Edge function — after input guard node.
    Routes to router if safe, output guard if blocked.

    Args:
        state: Current pipeline state

    Returns:
        Next node name string
    """
    if not state["is_safe"]:
        logger.info("Input blocked — routing to output guard")
        return "blocked"
    return "continue"


def route_after_router(state: AgentState) -> str:
    """
    Edge function — after router node.
    Directs to correct processing node based on route.

    Args:
        state: Current pipeline state

    Returns:
        Next node name string
    """
    route = state.get("route", ROUTE_RAG_AGENT)
    logger.info(f"Routing to: {route}")

    route_map = {
        ROUTE_RAG_AGENT      : NODE_RETRIEVER,
        ROUTE_WEB_SEARCH     : NODE_WEB_SEARCH,
        ROUTE_PYTHON_AGENT   : NODE_PYTHON,
        ROUTE_REASONING_AGENT: NODE_REASONING,
        ROUTE_DIRECT_ANSWER  : NODE_GENERATOR,
    }
    return route_map.get(route, NODE_RETRIEVER)


def build_workflow(
    llm         : ChatGroq,
    retriever   = None,
    web_search  = None,
    python_tool = None,
) -> StateGraph:
    """
    Build and compile the full agentic RAG workflow.

    Args:
        llm        : ChatGroq LLM instance
        retriever  : Document retriever instance
        web_search : Web search tool instance
        python_tool: Python executor tool instance

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize nodes
    nodes = PipelineNodes(
        llm         = llm,
        retriever   = retriever,
        web_search  = web_search,
        python_tool = python_tool,
    )

    # Create graph
    workflow = StateGraph(AgentState)

    # ── Register all nodes ────────────────────────────────
    workflow.add_node(NODE_INPUT_GUARD , nodes.node_input_guard)
    workflow.add_node(NODE_ROUTER      , nodes.node_router)
    workflow.add_node(NODE_RETRIEVER   , nodes.node_retriever)
    workflow.add_node(NODE_WEB_SEARCH  , nodes.node_web_search)
    workflow.add_node(NODE_PYTHON      , nodes.node_python_executor)
    workflow.add_node(NODE_REASONING   , nodes.node_reasoning)
    workflow.add_node(NODE_GENERATOR   , nodes.node_generator)
    workflow.add_node(NODE_OUTPUT_GUARD, nodes.node_output_guard)

    # ── Set entry point ───────────────────────────────────
    workflow.set_entry_point(NODE_INPUT_GUARD)

    # ── Conditional edge after input guard ────────────────
    workflow.add_conditional_edges(
        NODE_INPUT_GUARD,
        should_continue_after_guard,
        {
            "continue": NODE_ROUTER,
            "blocked" : NODE_OUTPUT_GUARD
        }
    )

    # ── Conditional edge after router ─────────────────────
    workflow.add_conditional_edges(
        NODE_ROUTER,
        route_after_router,
        {
            NODE_RETRIEVER : NODE_RETRIEVER,
            NODE_WEB_SEARCH: NODE_WEB_SEARCH,
            NODE_PYTHON    : NODE_PYTHON,
            NODE_REASONING : NODE_REASONING,
            NODE_GENERATOR : NODE_GENERATOR,
        }
    )

    # ── Processing nodes → generator ──────────────────────
    workflow.add_edge(NODE_RETRIEVER , NODE_GENERATOR)
    workflow.add_edge(NODE_WEB_SEARCH, NODE_GENERATOR)
    workflow.add_edge(NODE_PYTHON    , NODE_GENERATOR)

    # ── Reasoning → output guard (already has answer) ─────
    workflow.add_edge(NODE_REASONING , NODE_OUTPUT_GUARD)

    # ── Generator → output guard ──────────────────────────
    workflow.add_edge(NODE_GENERATOR , NODE_OUTPUT_GUARD)

    # ── Output guard → END ────────────────────────────────
    workflow.add_edge(NODE_OUTPUT_GUARD, END)

    compiled = workflow.compile()
    logger.info("LangGraph workflow compiled successfully")
    return compiled


def create_app(
    llm         : ChatGroq,
    retriever   = None,
    web_search  = None,
    python_tool = None,
):
    """
    Factory function to create the compiled workflow app.

    Args:
        llm        : ChatGroq LLM instance
        retriever  : Document retriever
        web_search : Web search tool
        python_tool: Python executor tool

    Returns:
        Compiled LangGraph app
    """
    return build_workflow(
        llm         = llm,
        retriever   = retriever,
        web_search  = web_search,
        python_tool = python_tool,
    )
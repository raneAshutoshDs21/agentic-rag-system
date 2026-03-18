"""Prompts package — exports all prompt templates."""

from prompts.router_prompts     import (
    ROUTER_PROMPT,
    ROUTER_WITH_HISTORY_PROMPT,
)
from prompts.reasoning_prompts  import (
    REASONING_PROMPT,
    CHAIN_OF_THOUGHT_PROMPT,
    COMPARISON_PROMPT,
)
from prompts.rag_prompts        import (
    RAG_PROMPT,
    RAG_WITH_WEB_PROMPT,
    GENERATOR_PROMPT,
    CONDENSE_PROMPT,
)
from prompts.evaluation_prompts import (
    JUDGE_PROMPT,
    FACTUAL_CHECK_PROMPT,
    HALLUCINATION_CHECK_PROMPT,
)

__all__ = [
    "ROUTER_PROMPT",
    "ROUTER_WITH_HISTORY_PROMPT",
    "REASONING_PROMPT",
    "CHAIN_OF_THOUGHT_PROMPT",
    "COMPARISON_PROMPT",
    "RAG_PROMPT",
    "RAG_WITH_WEB_PROMPT",
    "GENERATOR_PROMPT",
    "CONDENSE_PROMPT",
    "JUDGE_PROMPT",
    "FACTUAL_CHECK_PROMPT",
    "HALLUCINATION_CHECK_PROMPT",
]
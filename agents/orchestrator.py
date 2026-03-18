"""
Orchestrator agent that coordinates all other agents.
Acts as the main entry point for the agentic system.
"""

from langchain_groq import ChatGroq
from core.base_agent import BaseAgent
from core.logger import get_logger
from core.exceptions import AgentException
from agents.router_agent    import RouterAgent
from agents.reasoning_agent import ReasoningAgent
from agents.rag_agent       import RAGAgent
from tools.web_search       import WebSearchTool
from tools.python_executor  import PythonExecutorTool
from tools.database_tool    import DatabaseTool
from memory.memory_manager  import MemoryManager
from guardrails.input_guard  import InputGuard
from guardrails.output_guard import OutputGuard
from evaluation.evaluator   import Evaluator
from cache.response_cache   import ResponseCache
from observability.tracer   import ObservabilityTracer
from config.settings        import settings
from config.constants       import (
    ROUTE_RAG_AGENT,
    ROUTE_WEB_SEARCH,
    ROUTE_PYTHON_AGENT,
    ROUTE_REASONING_AGENT,
    ROUTE_DIRECT_ANSWER,
)

logger = get_logger(__name__)


class Orchestrator(BaseAgent):
    """
    Master orchestrator that coordinates all system components.
    Manages the full pipeline from input to output.
    """

    def __init__(self, llm: ChatGroq):
        """
        Initialize orchestrator with all components.

        Args:
            llm: ChatGroq LLM instance
        """
        super().__init__(
            name        = "orchestrator",
            description = "Coordinates all agents and tools"
        )
        self.llm = llm

        # ── Initialize all components ─────────────────────
        self.input_guard  = InputGuard()
        self.output_guard = OutputGuard()
        self.tracer       = ObservabilityTracer()
        self.cache        = ResponseCache()
        self.evaluator    = Evaluator(llm)
        self.db_tool      = DatabaseTool()

        # ── Initialize tools ──────────────────────────────
        self.web_search_tool = WebSearchTool()
        self.python_tool     = PythonExecutorTool()

        # ── Initialize agents ─────────────────────────────
        self.router    = RouterAgent(llm)
        self.rag_agent = self._build_rag_agent()
        self.reasoning = ReasoningAgent(
            llm        = llm,
            web_search = self.web_search_tool
        )

        logger.info("Orchestrator initialized — all components ready")

    def _build_rag_agent(self) -> RAGAgent:
        """Build RAG agent with full pipeline."""
        from rag.pipeline import RAGPipeline
        from rag.retriever import faiss_retriever

        pipeline = RAGPipeline(
            llm          = self.llm,
            retriever    = faiss_retriever,
            use_rerank   = False,
            use_compress = False
        )
        return RAGAgent(self.llm, rag_pipeline=pipeline)

    def run(
        self,
        query      : str,
        session_id : str  = None,
        use_cache  : bool = True,
        **kwargs
    ) -> dict:
        """
        Run the full orchestrated pipeline.

        Args:
            query     : User query
            session_id: Session identifier
            use_cache : Whether to use response cache

        Returns:
            Dict with answer and full metadata
        """
        import time
        from datetime import datetime

        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()

        # ── Start trace ───────────────────────────────────
        trace_id = self.tracer.start_trace(query)
        logger.info(f"Orchestrator | session={session_id} | trace={trace_id}")

        try:
            # ── Input guardrails ──────────────────────────
            guard_result = self.input_guard.check(query)
            if not guard_result["is_safe"]:
                self.tracer.end_trace(trace_id, success=False)
                return {
                    "answer"    : f"Query blocked: {guard_result['reason']}",
                    "success"   : False,
                    "blocked"   : True,
                    "session_id": session_id,
                    "trace_id"  : trace_id
                }

            clean_query = guard_result["clean_query"]

            # ── Cache check ───────────────────────────────
            if use_cache:
                cached = self.cache.get(clean_query)
                if cached:
                    self.tracer.end_trace(trace_id, success=True)
                    return {
                        "answer"       : cached["response"],
                        "score"        : cached["score"],
                        "from_cache"   : True,
                        "session_id"   : session_id,
                        "trace_id"     : trace_id,
                        "success"      : True,
                        "route"        : "CACHE",
                        "sources"      : [],
                        "total_time_ms": 0.0
                    }

            # ── Memory ────────────────────────────────────
            memory = MemoryManager(session_id)

            # ── Route query ───────────────────────────────
            route_result = self.router(clean_query)
            route        = route_result.get("route", ROUTE_RAG_AGENT)

            # ── Execute appropriate agent/tool ────────────
            answer  = ""
            sources = []

            if route == ROUTE_RAG_AGENT:
                result  = self.rag_agent(
                    clean_query,
                    memory_manager = memory
                )
                answer  = result["answer"]
                sources = result.get("sources", [])

            elif route == ROUTE_WEB_SEARCH:
                result = self.web_search_tool(clean_query)
                answer = result.get("result", "")

            elif route == ROUTE_PYTHON_AGENT:
                # Step 1 — Generate code
                gen_result = self.llm.invoke(
                    f"Write Python code to answer this question.\n"
                    f"Use print() to show the result.\n"
                    f"Return ONLY executable Python code.\n\n"
                    f"Question: {clean_query}"
                )
                # Step 2 — Execute code
                exec_result = self.python_tool(gen_result.content)
                code_output = exec_result.get("result", "")

                # Step 3 — Wrap output in natural language answer
                if exec_result.get("success") and code_output:
                    wrap_prompt = (
                        f"The user asked: {clean_query}\n"
                        f"Python code was executed and produced:\n"
                        f"{code_output}\n\n"
                        f"Write a clear natural language answer explaining the result."
                    )
                    wrap_response = self.llm.invoke(wrap_prompt)
                    answer        = wrap_response.content
                else:
                    answer = (
                        f"Code execution failed: "
                        f"{exec_result.get('error', 'Unknown error')}"
                    )

            elif route == ROUTE_REASONING_AGENT:
                result  = self.reasoning(
                    clean_query,
                    use_rag = True,
                    history = memory.build_context()
                )
                answer  = result["answer"]
                sources = result.get("sources", [])

            elif route == ROUTE_DIRECT_ANSWER:
                response = self.llm.invoke(clean_query)
                answer   = response.content

            else:
                result  = self.rag_agent(clean_query)
                answer  = result["answer"]
                sources = result.get("sources", [])

            # ── Output guardrails ─────────────────────────
            out_result   = self.output_guard.check(answer)
            clean_answer = out_result.get("clean_output", answer)

            # ── Evaluate ──────────────────────────────────
            eval_result = self.evaluator.evaluate(clean_query, clean_answer)
            score       = eval_result["scores"].get("overall", 0.0)

            # ── Save to memory and DB ─────────────────────
            memory.remember("user",      clean_query)
            memory.remember("assistant", clean_answer[:500])
            memory.save_qa_pair(clean_query, clean_answer, score)

            self.db_tool.save_query_history(
                session_id = session_id,
                query      = clean_query,
                answer     = clean_answer,
                score      = score,
                route      = route
            )

            # ── Cache successful responses ─────────────────
            if use_cache and score >= settings.eval_min_score:
                self.cache.set(clean_query, clean_answer, score=score)

            # ── End trace ─────────────────────────────────
            self.tracer.end_trace(trace_id, success=True)

            total_ms = (time.time() - start_time) * 1000

            return {
                "query"        : clean_query,
                "answer"       : clean_answer,
                "route"        : route,
                "sources"      : sources,
                "score"        : score,
                "feedback"     : eval_result.get("feedback", ""),
                "from_cache"   : False,
                "session_id"   : session_id,
                "trace_id"     : trace_id,
                "total_time_ms": round(total_ms, 1),
                "success"      : True
            }

        except Exception as e:
            self.tracer.end_trace(trace_id, success=False)
            logger.error(f"Orchestrator failed: {e}")
            raise AgentException(
                f"Orchestrator failed: {e}",
                agent_name="orchestrator"
            )
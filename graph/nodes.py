"""
LangGraph node definitions for the agentic RAG pipeline.
Each node handles one stage of the pipeline.
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from core.logger import get_logger
from graph.state import AgentState
from guardrails.input_guard  import InputGuard
from guardrails.output_guard import OutputGuard
from config.constants import (
    VALID_ROUTES,
    ROUTE_RAG_AGENT,
    ROUTE_WEB_SEARCH,
    ROUTE_PYTHON_AGENT,
    ROUTE_REASONING_AGENT,
    ROUTE_DIRECT_ANSWER,
)

logger = get_logger(__name__)


class PipelineNodes:
    """
    Collection of all LangGraph node functions.
    Each method is a node in the workflow graph.
    """

    def __init__(
        self,
        llm          : ChatGroq,
        retriever    = None,
        web_search   = None,
        python_tool  = None,
        input_guard  : InputGuard  = None,
        output_guard : OutputGuard = None,
    ):
        """
        Initialize pipeline nodes with all dependencies.

        Args:
            llm         : ChatGroq LLM instance
            retriever   : Document retriever
            web_search  : Web search tool
            python_tool : Python executor tool
            input_guard : Input guardrail
            output_guard: Output guardrail
        """
        self.llm          = llm
        self.retriever    = retriever
        self.web_search   = web_search
        self.python_tool  = python_tool
        self.input_guard  = input_guard  or InputGuard()
        self.output_guard = output_guard or OutputGuard()
        logger.info("PipelineNodes initialized")

    def node_input_guard(self, state: AgentState) -> AgentState:
        """
        Node 1 — Validate and sanitize user input.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with safety check results
        """
        logger.info(
            f"[NODE] input_guard | query={state['query'][:50]}"
        )

        result = self.input_guard.check(state["query"])

        if not result["is_safe"]:
            return {
                **state,
                "is_safe"      : False,
                "safety_reason": result["reason"],
                "clean_query"  : "",
                "answer"       : f"Query blocked: {result['reason']}",
                "success"      : False
            }

        return {
            **state,
            "is_safe"      : True,
            "safety_reason": "Input is safe",
            "clean_query"  : result["clean_query"]
        }

    def node_router(self, state: AgentState) -> AgentState:
        """
        Node 2 — Route query to appropriate agent.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with route decision
        """
        logger.info(
            f"[NODE] router | query={state['clean_query'][:50]}"
        )

        ROUTER_PROMPT = ChatPromptTemplate.from_template("""
You are a routing agent. Choose EXACTLY ONE option:
- RAG_AGENT      : Needs knowledge base information
- WEB_SEARCH     : Needs current live information
- PYTHON_AGENT   : Needs code execution or computation
- REASONING_AGENT: Needs multi-step complex reasoning
- DIRECT_ANSWER  : Simple question answered directly

Respond with ONLY the agent name.

Query: {query}
Agent:
""")
        try:
            chain = ROUTER_PROMPT | self.llm | StrOutputParser()
            route = chain.invoke(
                {"query": state["clean_query"]}
            ).strip().upper()

            if route not in VALID_ROUTES:
                logger.warning(
                    f"Invalid route '{route}' — defaulting to RAG_AGENT"
                )
                route = ROUTE_RAG_AGENT

            logger.info(f"Routed to: {route}")
            return {**state, "route": route}

        except Exception as e:
            logger.error(f"Router node failed: {e}")
            return {**state, "route": ROUTE_RAG_AGENT, "error": str(e)}

    def node_retriever(self, state: AgentState) -> AgentState:
        """
        Node 3 — Retrieve relevant documents from vector store.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with retrieved docs and context
        """
        logger.info(
            f"[NODE] retriever | query={state['clean_query'][:50]}"
        )

        try:
            if self.retriever is None:
                return {
                    **state,
                    "context": "No retriever configured",
                    "sources": []
                }

            docs    = self.retriever.invoke(state["clean_query"])
            context = "\n\n".join(
                f"[Source: {d.metadata.get('source', 'unknown')}]\n"
                f"{d.page_content}"
                for d in docs
            )
            sources = [
                d.metadata.get("source", "unknown")
                for d in docs
            ]

            logger.info(f"Retrieved {len(docs)} docs")
            return {
                **state,
                "retrieved_docs": [d.page_content for d in docs],
                "context"       : context,
                "sources"       : sources
            }

        except Exception as e:
            logger.error(f"Retriever node failed: {e}")
            return {
                **state,
                "context": "",
                "sources": [],
                "error"  : str(e)
            }

    def node_web_search(self, state: AgentState) -> AgentState:
        """
        Node 4 — Search web for current information.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with web search results
        """
        logger.info(
            f"[NODE] web_search | query={state['clean_query'][:50]}"
        )

        try:
            if self.web_search is None:
                return {**state, "web_results": "Web search not configured"}

            result      = self.web_search(state["clean_query"])
            web_results = result.get("result", "No results found")

            logger.info("Web search complete")
            return {**state, "web_results": web_results}

        except Exception as e:
            logger.error(f"Web search node failed: {e}")
            return {
                **state,
                "web_results": "",
                "error"      : str(e)
            }

    def node_python_executor(self, state: AgentState) -> AgentState:
        """
        Node 5 — Generate and execute Python code.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with code execution output
        """
        logger.info(
            f"[NODE] python_executor | query={state['clean_query'][:50]}"
        )

        try:
            # Ask LLM to generate code
            code_prompt = (
                f"Write Python code to answer this question.\n"
                f"Return ONLY executable Python code.\n"
                f"Use print() for output.\n\n"
                f"Question: {state['clean_query']}\n\nCode:"
            )
            code_response = self.llm.invoke(code_prompt).content

            # Extract from markdown if needed
            if "```python" in code_response:
                code = code_response.split(
                    "```python"
                )[1].split("```")[0].strip()
            elif "```" in code_response:
                code = code_response.split(
                    "```"
                )[1].split("```")[0].strip()
            else:
                code = code_response.strip()

            # Execute code
            if self.python_tool is None:
                return {
                    **state,
                    "code_output": "Python tool not configured"
                }

            result      = self.python_tool(code)
            code_output = (
                result.get("result", "")
                if result.get("success")
                else f"Execution error: {result.get('error', '')}"
            )

            logger.info("Python execution complete")
            return {**state, "code_output": code_output}

        except Exception as e:
            logger.error(f"Python executor node failed: {e}")
            return {
                **state,
                "code_output": f"Execution failed: {str(e)}",
                "error"      : str(e)
            }

    def node_reasoning(self, state: AgentState) -> AgentState:
        """
        Node 6 — Apply multi-step reasoning to complex queries.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with reasoning output
        """
        logger.info(
            f"[NODE] reasoning | query={state['clean_query'][:50]}"
        )

        REASONING_PROMPT = ChatPromptTemplate.from_template("""
You are an expert reasoning agent. Break down the question step by step.

Format:
STEP 1: [First step]
STEP 2: [Second step]
STEP 3: [Continue as needed]
CONCLUSION: [Final answer]

Context: {context}
Question: {question}

Reasoning:
""")
        try:
            chain    = REASONING_PROMPT | self.llm | StrOutputParser()
            response = chain.invoke({
                "context" : state.get("context", "No context available"),
                "question": state["clean_query"]
            })

            logger.info("Reasoning complete")
            return {
                **state,
                "reasoning": response,
                "answer"   : response
            }

        except Exception as e:
            logger.error(f"Reasoning node failed: {e}")
            return {
                **state,
                "reasoning": "",
                "error"    : str(e)
            }

    def node_generator(self, state: AgentState) -> AgentState:
        """
        Node 7 — Generate final answer from all gathered context.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with final answer
        """
        logger.info(f"[NODE] generator | route={state['route']}")

        GENERATOR_PROMPT = ChatPromptTemplate.from_template("""
You are an expert AI assistant. Generate a clear accurate answer.
Use the provided context and always cite sources when available.

Knowledge Base Context:
{context}

Web Search Results:
{web_results}

Code Execution Output:
{code_output}

Question: {question}

Answer:
""")
        try:
            chain  = GENERATOR_PROMPT | self.llm | StrOutputParser()
            answer = chain.invoke({
                "context"    : state.get("context", "")     or "None",
                "web_results": state.get("web_results", "") or "None",
                "code_output": state.get("code_output", "") or "None",
                "question"   : state["clean_query"]
            })

            logger.info("Generator complete")
            return {
                **state,
                "answer" : answer,
                "success": True
            }

        except Exception as e:
            logger.error(f"Generator node failed: {e}")
            return {
                **state,
                "answer" : f"Generation failed: {str(e)}",
                "success": False,
                "error"  : str(e)
            }

    def node_output_guard(self, state: AgentState) -> AgentState:
        """
        Node 8 — Validate final output before returning to user.

        Args:
            state: Current pipeline state

        Returns:
            Updated state with validated clean answer
        """
        logger.info("[NODE] output_guard")

        result = self.output_guard.check(state.get("answer", ""))

        return {
            **state,
            "answer" : result["clean_output"],
            "success": result["is_valid"]
        }
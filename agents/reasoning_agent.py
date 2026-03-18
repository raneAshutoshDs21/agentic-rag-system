"""
Reasoning agent for complex multi-step queries.
Uses chain-of-thought prompting with RAG + web search context.
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from core.base_agent import BaseAgent
from core.logger import get_logger
from core.exceptions import ReasoningException

logger = get_logger(__name__)

REASONING_PROMPT = ChatPromptTemplate.from_template("""
You are an expert reasoning agent. Break down complex questions
into clear reasoning steps before giving a final answer.

Use this EXACT format:
STEP 1: [First reasoning step]
STEP 2: [Second reasoning step]
STEP 3: [Continue as needed]
CONCLUSION: [Final answer based on all steps]

Knowledge Base Context:
{context}

Web Search Results:
{web_results}

Conversation History:
{history}

Question: {question}

Reasoning:
""")


class ReasoningAgent(BaseAgent):
    """
    Multi-step reasoning agent combining RAG and web search.
    Produces structured chain-of-thought responses.
    """

    def __init__(self, llm: ChatGroq, retriever=None, web_search=None):
        """
        Initialize reasoning agent.

        Args:
            llm       : ChatGroq LLM instance
            retriever : Document retriever instance
            web_search: Web search tool instance
        """
        super().__init__(
            name        = "reasoning",
            description = "Multi-step reasoning with RAG and web search"
        )
        self.llm        = llm
        self.retriever  = retriever
        self.web_search = web_search
        self.chain      = REASONING_PROMPT | llm | StrOutputParser()
        logger.info("ReasoningAgent initialized")

    def run(
        self,
        query    : str,
        use_rag  : bool = True,
        use_web  : bool = False,
        history  : str  = "",
        **kwargs
    ) -> dict:
        """
        Run multi-step reasoning on a query.

        Args:
            query  : User query
            use_rag: Whether to use RAG retrieval
            use_web: Whether to use web search
            history: Conversation history string

        Returns:
            Dict with reasoning steps, conclusion, and full answer
        """
        try:
            self.logger.info(f"Reasoning on: {query[:60]}...")

            # Retrieve context
            context = ""
            sources = []
            if use_rag and self.retriever:
                docs    = self.retriever.invoke(query)
                context = self._format_docs(docs)
                sources = [d.metadata.get("source") for d in docs]
                self.logger.info(f"Retrieved {len(docs)} docs")

            # Web search
            web_results = ""
            if use_web and self.web_search:
                result      = self.web_search(query)
                web_results = result.get("result", "")
                self.logger.info("Web search completed")

            # Run reasoning chain
            response = self.chain.invoke({
                "context"    : context     or "No knowledge base context",
                "web_results": web_results or "No web search results",
                "history"    : history     or "No conversation history",
                "question"   : query
            })

            # Parse reasoning steps
            lines      = response.strip().split("\n")
            steps      = [l.strip() for l in lines if l.strip().startswith("STEP")]
            conclusion = next(
                (l.split("CONCLUSION:", 1)[1].strip()
                 for l in lines if "CONCLUSION:" in l),
                ""
            )

            self.logger.info(
                f"Reasoning complete | steps={len(steps)}"
            )

            return {
                "answer"     : response,
                "steps"      : steps,
                "conclusion" : conclusion,
                "sources"    : sources,
                "used_rag"   : use_rag,
                "used_web"   : use_web,
                "success"    : True,
                "agent"      : self.name
            }

        except Exception as e:
            self.logger.error(f"Reasoning failed: {e}")
            raise ReasoningException(f"Reasoning failed: {e}")

    def _format_docs(self, docs: list) -> str:
        """Format documents into context string."""
        if not docs:
            return "No relevant documents found."
        return "\n\n".join(
            f"[Source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
            for d in docs
        )
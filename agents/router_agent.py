"""
Router agent that directs queries to the appropriate agent.
Uses LLM to analyze query intent and select best handler.
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from core.base_agent import BaseAgent
from core.logger import get_logger
from core.exceptions import RouterException
from config.constants import VALID_ROUTES, ROUTE_RAG_AGENT
from config.settings import settings

logger = get_logger(__name__)

ROUTER_PROMPT = ChatPromptTemplate.from_template("""
You are a routing agent for an advanced AI system with a knowledge base.
Analyze the user query and decide which agent should handle it.
Choose EXACTLY ONE of these options:

- RAG_AGENT      : Default choice for ANY question about concepts, topics,
                   technology, AI, systems, or anything that could be in docs
- WEB_SEARCH     : ONLY for current news, today's prices, live events,
                   or anything requiring information from after 2024
- PYTHON_AGENT   : ONLY for math calculations or code execution requests
- REASONING_AGENT: ONLY for complex multi-part analysis requiring comparison
- DIRECT_ANSWER  : ONLY for casual greetings like hello, hi, how are you

When in doubt always choose RAG_AGENT.

Respond with ONLY the agent name. Nothing else.

Query: {query}

Agent:
""")


class RouterAgent(BaseAgent):
    """
    Routes incoming queries to the most appropriate agent.
    Uses LLM classification with fallback to RAG_AGENT.
    """

    def __init__(self, llm: ChatGroq = None):
        """
        Initialize router agent.

        Args:
            llm: ChatGroq LLM instance
        """
        super().__init__(
            name        = "router",
            description = "Routes queries to appropriate agents"
        )
        self.llm   = llm
        self.chain = ROUTER_PROMPT | llm | StrOutputParser()
        logger.info("RouterAgent initialized")

    def run(self, query: str, **kwargs) -> dict:
        """
        Route a query to the appropriate agent.

        Args:
            query: User query string

        Returns:
            Dict with route and metadata
        """
        try:
            self.logger.info(f"Routing query: {query[:60]}...")

            raw_route = self.chain.invoke({"query": query})
            route     = raw_route.strip().upper()

            # Validate route
            if route not in VALID_ROUTES:
                self.logger.warning(
                    f"Invalid route '{route}' — defaulting to RAG_AGENT"
                )
                route = ROUTE_RAG_AGENT

            self.logger.info(f"Query routed to: {route}")

            return {
                "route"    : route,
                "query"    : query,
                "success"  : True,
                "agent"    : self.name,
                "raw_route": raw_route.strip()
            }

        except Exception as e:
            self.logger.error(f"Routing failed: {e}")
            raise RouterException(f"Routing failed: {e}")

    def batch_route(self, queries: list) -> list:
        """
        Route multiple queries at once.

        Args:
            queries: List of query strings

        Returns:
            List of route strings
        """
        routes = []
        for query in queries:
            result = self(query)
            routes.append(result.get("route", ROUTE_RAG_AGENT))
        return routes
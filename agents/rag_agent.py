"""
RAG agent for knowledge base queries.
Combines advanced retrieval with memory-aware generation.
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from core.base_agent import BaseAgent
from core.logger import get_logger
from core.exceptions import AgentException
from rag.pipeline import RAGPipeline

logger = get_logger(__name__)

RAG_AGENT_PROMPT = ChatPromptTemplate.from_template("""
You are an expert RAG agent with access to a knowledge base.
Answer questions accurately using the retrieved context.
Always cite your sources. Be concise but complete.

If the context does not contain the answer, say:
"I don't have enough information in my knowledge base to answer this."

Retrieved Context:
{context}

Conversation History:
{history}

Question: {question}

Answer:
""")


class RAGAgent(BaseAgent):
    """
    Knowledge base QA agent using advanced RAG pipeline.
    Supports memory-aware context building.
    """

    def __init__(self, llm: ChatGroq, rag_pipeline: RAGPipeline = None):
        """
        Initialize RAG agent.

        Args:
            llm         : ChatGroq LLM instance
            rag_pipeline: RAGPipeline instance
        """
        super().__init__(
            name        = "rag_agent",
            description = "Knowledge base QA with advanced RAG"
        )
        self.llm          = llm
        self.rag_pipeline = rag_pipeline
        self.chain        = RAG_AGENT_PROMPT | llm | StrOutputParser()
        logger.info("RAGAgent initialized")

    def run(
        self,
        query          : str,
        history        : str  = "",
        memory_manager = None,
        **kwargs
    ) -> dict:
        """
        Run RAG pipeline on a query.

        Args:
            query         : User query
            history       : Conversation history string
            memory_manager: Optional MemoryManager instance

        Returns:
            Dict with answer, sources, and metadata
        """
        try:
            self.logger.info(f"RAG agent processing: {query[:60]}...")

            # Get conversation history from memory
            if memory_manager and not history:
                history = memory_manager.build_context(limit=4)

            # Run RAG pipeline
            if self.rag_pipeline:
                result  = self.rag_pipeline.run(query, history=history)
                answer  = result["answer"]
                sources = result["sources"]
                context = result["context"]
                num_docs = result["num_docs"]
            else:
                answer   = "RAG pipeline not configured"
                sources  = []
                context  = ""
                num_docs = 0

            # Save to memory
            if memory_manager:
                memory_manager.remember("user", query)
                memory_manager.remember("assistant", answer[:500])

            self.logger.info(
                f"RAG agent complete | "
                f"sources={sources} | docs={num_docs}"
            )

            return {
                "answer"  : answer,
                "sources" : sources,
                "context" : context,
                "num_docs": num_docs,
                "success" : True,
                "agent"   : self.name
            }

        except Exception as e:
            self.logger.error(f"RAG agent failed: {e}")
            raise AgentException(f"RAG agent failed: {e}", agent_name=self.name)
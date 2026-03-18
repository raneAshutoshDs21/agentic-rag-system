"""
Advanced RAG pipeline combining retrieval, reranking, and compression.
"""

from typing import List, Optional
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from core.logger import get_logger
from core.exceptions import RAGException
from rag.retriever import FAISSRetriever, faiss_retriever
from rag.reranker import LLMReranker
from rag.compressor import ContextCompressor
from config.settings import settings

logger = get_logger(__name__)

RAG_PROMPT = ChatPromptTemplate.from_template("""
You are an expert AI assistant. Answer the question using ONLY the provided context.
If the context does not contain enough information, say so clearly.
Always cite which source you used.

Context:
{context}

Conversation History:
{history}

Question: {question}

Answer:
""")


class RAGPipeline:
    """
    Advanced RAG pipeline with retrieval, reranking, and compression.
    """

    def __init__(
        self,
        llm,
        retriever : FAISSRetriever = None,
        use_rerank: bool           = True,
        use_compress: bool         = True,
        top_k     : int            = 3
    ):
        """
        Initialize RAG pipeline.

        Args:
            llm         : LangChain LLM instance
            retriever   : Document retriever
            use_rerank  : Whether to use LLM reranker
            use_compress: Whether to use context compression
            top_k       : Final number of docs to use
        """
        self.llm          = llm
        self.retriever    = retriever or faiss_retriever
        self.use_rerank   = use_rerank
        self.use_compress = use_compress
        self.top_k        = top_k

        self.reranker   = LLMReranker(llm, top_k=top_k)   if use_rerank   else None
        self.compressor = ContextCompressor(llm)            if use_compress else None

        self.chain = RAG_PROMPT | llm | StrOutputParser()

        logger.info(
            f"RAGPipeline initialized | "
            f"rerank={use_rerank} | compress={use_compress}"
        )

    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents into context string."""
        if not docs:
            return "No relevant context found."
        return "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'unknown')}]\n"
            f"{doc.page_content}"
            for doc in docs
        )

    def retrieve(self, query: str) -> List[Document]:
        """
        Full retrieval pipeline with optional reranking and compression.

        Args:
            query: Search query

        Returns:
            List of processed Document objects
        """
        try:
            # Step 1 — Base retrieval
            docs = self.retriever.retrieve(query)
            logger.info(f"Base retrieval: {len(docs)} docs")

            # Step 2 — Reranking
            if self.use_rerank and self.reranker and docs:
                docs = self.reranker.rerank_and_return_docs(query, docs)
                logger.info(f"After reranking: {len(docs)} docs")

            # Step 3 — Compression
            if self.use_compress and self.compressor and docs:
                docs = self.compressor.compress(query, docs)
                logger.info(f"After compression: {len(docs)} docs")

            return docs

        except Exception as e:
            logger.error(f"Retrieval pipeline failed: {e}")
            return []

    def run(
        self,
        query  : str,
        history: str = ""
    ) -> dict:
        """
        Run the full RAG pipeline on a query.

        Args:
            query  : User query
            history: Conversation history string

        Returns:
            Dict with answer, sources, and metadata

        Raises:
            RAGException: If pipeline fails
        """
        try:
            logger.info(f"RAG pipeline running | query={query[:60]}...")

            # Retrieve and process documents
            docs    = self.retrieve(query)
            context = self._format_docs(docs)
            sources = [d.metadata.get("source", "unknown") for d in docs]

            # Generate answer
            answer = self.chain.invoke({
                "context" : context,
                "history" : history or "No previous conversation",
                "question": query
            })

            logger.info(f"RAG pipeline complete | sources={sources}")

            return {
                "answer"    : answer,
                "sources"   : sources,
                "num_docs"  : len(docs),
                "context"   : context,
                "success"   : True
            }

        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            raise RAGException(f"Pipeline failed: {e}")


# ── Factory function ──────────────────────────────────────
def create_rag_pipeline(llm, **kwargs) -> RAGPipeline:
    """
    Factory function to create a RAG pipeline instance.

    Args:
        llm   : LangChain LLM instance
        kwargs: Additional RAGPipeline arguments

    Returns:
        Configured RAGPipeline instance
    """
    return RAGPipeline(llm=llm, **kwargs)
"""
RAG retriever module.
Wraps FAISS store with the BaseRetriever interface.
"""

from typing import List, Optional
from langchain.schema import Document
from core.base_retriever import BaseRetriever
from core.exceptions import RetrieverException
from core.logger import get_logger
from vectorstore.faiss_store import FAISSStore, faiss_store
from config.settings import settings

logger = get_logger(__name__)


class FAISSRetriever(BaseRetriever):
    """
    FAISS-based document retriever.
    Supports similarity search and MMR retrieval.
    """

    def __init__(
        self,
        store      : FAISSStore = None,
        k          : int        = None,
        search_type: str        = "mmr"
    ):
        """
        Initialize FAISS retriever.

        Args:
            store      : FAISSStore instance
            k          : Number of documents to retrieve
            search_type: Search type (mmr or similarity)
        """
        super().__init__(
            name = "faiss_retriever",
            k    = k or settings.retriever_k
        )
        self.store       = store or faiss_store
        self.search_type = search_type
        logger.info(
            f"FAISSRetriever ready | "
            f"k={self.k} | search_type={self.search_type}"
        )

    def retrieve(
        self,
        query: str,
        k    : Optional[int] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents from FAISS index.

        Args:
            query: Search query string
            k    : Number of documents (overrides default)

        Returns:
            List of relevant Document objects

        Raises:
            RetrieverException: If retrieval fails
        """
        k = k or self.k

        try:
            # Auto-load FAISS index if not initialized
            if self.store._vectorstore is None:
                self.logger.info("FAISS not loaded — auto-loading...")
                self.store.load()

            if self.search_type == "mmr":
                retriever = self.store.as_retriever(
                    search_type = "mmr",
                    k           = k,
                    fetch_k     = settings.retriever_fetch_k,
                    lambda_mult = 0.7
                )
                docs = retriever.invoke(query)
            else:
                docs = self.store.similarity_search(query, k=k)

            self.logger.info(
                f"Retrieved {len(docs)} docs | "
                f"type={self.search_type}"
            )
            return docs

        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            raise RetrieverException(f"FAISS retrieval failed: {e}")

    def retrieve_with_scores(
        self,
        query: str,
        k    : Optional[int] = None
    ) -> List[tuple]:
        """
        Retrieve documents with relevance scores.

        Args:
            query: Search query string
            k    : Number of results

        Returns:
            List of (Document, score) tuples
        """
        k = k or self.k
        try:
            # Auto-load if needed
            if self.store._vectorstore is None:
                self.logger.info("FAISS not loaded — auto-loading...")
                self.store.load()

            results = self.store.similarity_search_with_score(query, k=k)
            logger.info(f"Retrieved {len(results)} scored docs")
            return results

        except Exception as e:
            logger.error(f"Scored retrieval failed: {e}")
            raise RetrieverException(f"Scored retrieval failed: {e}")


# ── Singleton instance ────────────────────────────────────
faiss_retriever = FAISSRetriever()
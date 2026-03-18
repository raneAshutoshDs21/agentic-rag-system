"""
Abstract base class for all retrievers in the system.
All retrievers must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from langchain.schema import Document
from core.logger import get_logger
from core.exceptions import RetrieverException


class BaseRetriever(ABC):
    """
    Abstract base class for all document retrievers.
    Provides common interface for retrieval operations.
    """

    def __init__(self, name: str, k: int = 4):
        """
        Initialize base retriever.

        Args:
            name: Retriever name for logging
            k   : Number of documents to retrieve
        """
        self.name        = name
        self.k           = k
        self.logger      = get_logger(f"retriever.{name}")
        self._call_count  = 0
        self._error_count = 0

        self.logger.info(f"Retriever initialized: {self.name} | k={self.k}")

    @abstractmethod
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query string
            k    : Number of documents (overrides default)

        Returns:
            List of relevant Document objects
        """
        pass

    def __call__(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Make retriever callable. Wraps retrieve() with error handling.

        Args:
            query: Search query
            k    : Number of documents

        Returns:
            List of Document objects
        """
        self._call_count += 1
        self.logger.info(
            f"[{self.name}] Retrieving | query: {query[:60]}..."
        )

        try:
            docs = self.retrieve(query, k)
            self.logger.info(
                f"[{self.name}] Retrieved {len(docs)} documents"
            )
            return docs

        except RetrieverException as e:
            self._error_count += 1
            self.logger.error(f"[{self.name}] RetrieverException: {e}")
            return []

        except Exception as e:
            self._error_count += 1
            self.logger.error(f"[{self.name}] Unexpected error: {e}")
            return []

    def format_docs(self, docs: List[Document]) -> str:
        """
        Format list of documents into a single context string.

        Args:
            docs: List of Document objects

        Returns:
            Formatted string with all document contents
        """
        if not docs:
            return "No relevant documents found."

        return "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'unknown')}]\n"
            f"{doc.page_content}"
            for doc in docs
        )

    def get_sources(self, docs: List[Document]) -> List[str]:
        """
        Extract source names from documents.

        Args:
            docs: List of Document objects

        Returns:
            List of source name strings
        """
        return [
            doc.metadata.get("source", "unknown")
            for doc in docs
        ]

    def get_stats(self) -> dict:
        """Get retriever execution statistics."""
        return {
            "retriever"  : self.name,
            "calls"      : self._call_count,
            "errors"     : self._error_count,
            "error_rate" : (
                self._error_count / self._call_count
                if self._call_count > 0 else 0.0
            )
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, k={self.k})"
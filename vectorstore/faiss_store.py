"""
FAISS vector store management.
Handles creation, persistence, loading, and retrieval.
"""

from pathlib import Path
from typing import List, Optional, Tuple
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from core.logger import get_logger
from core.exceptions import FAISSException
from config.settings import settings
from vectorstore.embeddings import embedding_manager

logger = get_logger(__name__)


class FAISSStore:
    """
    Manages a FAISS vector store for document retrieval.
    Supports creation, persistence, loading, and search.
    """

    def __init__(self, index_path: str = None):
        """
        Initialize FAISS store.

        Args:
            index_path: Path to save/load FAISS index
        """
        self.index_path  = Path(index_path or settings.faiss_index_path)
        self.embeddings  = embedding_manager.get_model()
        self._vectorstore: Optional[FAISS] = None
        logger.info(f"FAISSStore initialized | path={self.index_path}")

    def build(self, documents: List[Document]) -> FAISS:
        """
        Build FAISS index from a list of documents.

        Args:
            documents: List of Document objects to index

        Returns:
            Built FAISS vectorstore

        Raises:
            FAISSException: If index building fails
        """
        if not documents:
            raise FAISSException("Cannot build index from empty document list")

        try:
            logger.info(f"Building FAISS index from {len(documents)} documents")
            self._vectorstore = FAISS.from_documents(
                documents = documents,
                embedding = self.embeddings
            )
            logger.info(
                f"FAISS index built | "
                f"vectors={self._vectorstore.index.ntotal}"
            )
            return self._vectorstore

        except Exception as e:
            logger.error(f"FAISS build failed: {e}")
            raise FAISSException(f"Index build failed: {e}")

    def save(self):
        """
        Persist FAISS index to disk.

        Raises:
            FAISSException: If save fails or store not built
        """
        if self._vectorstore is None:
            raise FAISSException("No vectorstore to save — build first")

        try:
            self.index_path.mkdir(parents=True, exist_ok=True)
            self._vectorstore.save_local(str(self.index_path))
            logger.info(f"FAISS index saved to: {self.index_path}")

        except Exception as e:
            logger.error(f"FAISS save failed: {e}")
            raise FAISSException(f"Index save failed: {e}")

    def load(self) -> FAISS:
        """
        Load FAISS index from disk.

        Returns:
            Loaded FAISS vectorstore

        Raises:
            FAISSException: If load fails or index not found
        """
        if not self.index_path.exists():
            raise FAISSException(
                f"FAISS index not found at: {self.index_path}. "
                f"Run build() first."
            )

        try:
            logger.info(f"Loading FAISS index from: {self.index_path}")
            self._vectorstore = FAISS.load_local(
                folder_path            = str(self.index_path),
                embeddings             = self.embeddings,
                allow_dangerous_deserialization = True
            )
            logger.info(
                f"FAISS index loaded | "
                f"vectors={self._vectorstore.index.ntotal}"
            )
            return self._vectorstore

        except Exception as e:
            logger.error(f"FAISS load failed: {e}")
            raise FAISSException(f"Index load failed: {e}")

    def get_or_build(self, documents: List[Document] = None) -> FAISS:
        """
        Load existing index or build from documents.

        Args:
            documents: Documents to build from if index not found

        Returns:
            FAISS vectorstore instance

        Raises:
            FAISSException: If neither load nor build succeeds
        """
        if self._vectorstore is not None:
            return self._vectorstore

        if self.index_path.exists():
            return self.load()

        if documents:
            self.build(documents)
            self.save()
            return self._vectorstore

        raise FAISSException(
            "No existing index found and no documents provided to build one"
        )

    def similarity_search(
        self,
        query: str,
        k    : int = None
    ) -> List[Document]:
        """
        Search for similar documents.

        Args:
            query: Search query string
            k    : Number of results

        Returns:
            List of relevant Document objects

        Raises:
            FAISSException: If search fails
        """
        if self._vectorstore is None:
            raise FAISSException("Vectorstore not initialized — call load() or build() first")

        try:
            k = k or settings.retriever_k
            docs = self._vectorstore.similarity_search(query, k=k)
            logger.info(f"Similarity search returned {len(docs)} docs")
            return docs

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise FAISSException(f"Search failed: {e}")

    def similarity_search_with_score(
        self,
        query: str,
        k    : int = None
    ) -> List[Tuple[Document, float]]:
        """
        Search with relevance scores.

        Args:
            query: Search query string
            k    : Number of results

        Returns:
            List of (Document, score) tuples

        Raises:
            FAISSException: If search fails
        """
        if self._vectorstore is None:
            raise FAISSException("Vectorstore not initialized")

        try:
            k = k or settings.retriever_k
            results = self._vectorstore.similarity_search_with_score(query, k=k)
            logger.info(f"Scored search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Scored search failed: {e}")
            raise FAISSException(f"Scored search failed: {e}")

    def as_retriever(
        self,
        search_type  : str = "mmr",
        k            : int = None,
        fetch_k      : int = None,
        lambda_mult  : float = 0.7
    ):
        """
        Return a LangChain retriever interface.

        Args:
            search_type : mmr or similarity
            k           : Number of results
            fetch_k     : Candidates to fetch for MMR
            lambda_mult : MMR diversity parameter

        Returns:
            LangChain VectorStoreRetriever
        """
        if self._vectorstore is None:
            raise FAISSException("Vectorstore not initialized")

        k       = k       or settings.retriever_k
        fetch_k = fetch_k or settings.retriever_fetch_k

        return self._vectorstore.as_retriever(
            search_type   = search_type,
            search_kwargs = {
                "k"           : k,
                "fetch_k"     : fetch_k,
                "lambda_mult" : lambda_mult
            }
        )

    def add_documents(self, documents: List[Document]):
        """
        Add new documents to existing index.

        Args:
            documents: New documents to add

        Raises:
            FAISSException: If addition fails
        """
        if self._vectorstore is None:
            raise FAISSException("Vectorstore not initialized")

        try:
            self._vectorstore.add_documents(documents)
            logger.info(
                f"Added {len(documents)} docs | "
                f"total={self._vectorstore.index.ntotal}"
            )
        except Exception as e:
            logger.error(f"Document addition failed: {e}")
            raise FAISSException(f"Add documents failed: {e}")

    @property
    def total_vectors(self) -> int:
        """Get total number of vectors in the index."""
        if self._vectorstore is None:
            return 0
        return self._vectorstore.index.ntotal


# ── Singleton instance ────────────────────────────────────
faiss_store = FAISSStore()
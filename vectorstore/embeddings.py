"""
Embedding model initialization and management.
Uses BAAI/bge-small-en-v1.5 running locally via HuggingFace.
"""

from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from core.logger import get_logger
from core.exceptions import EmbeddingException
from config.settings import settings

logger = get_logger(__name__)


class EmbeddingManager:
    """
    Manages the embedding model lifecycle.
    Provides a singleton pattern to avoid reloading the model.
    """

    _instance = None

    def __new__(cls):
        """Singleton — only one embedding model loaded at a time."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._model       = None
        self.model_name   = settings.embedding_model
        self.device       = settings.embedding_device
        logger.info(f"EmbeddingManager created | model={self.model_name}")

    def load(self) -> HuggingFaceEmbeddings:
        """
        Load embedding model. Downloads on first run (~130MB).

        Returns:
            HuggingFaceEmbeddings instance

        Raises:
            EmbeddingException: If model loading fails
        """
        if self._model is not None:
            logger.info("Embedding model already loaded — reusing")
            return self._model

        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = HuggingFaceEmbeddings(
                model_name    = self.model_name,
                model_kwargs  = {"device": self.device},
                encode_kwargs = {"normalize_embeddings": True},
            )
            logger.info("Embedding model loaded successfully")
            return self._model

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise EmbeddingException(f"Model load failed: {e}")

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query string.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            EmbeddingException: If embedding fails
        """
        try:
            model = self.load()
            vector = model.embed_query(text)
            logger.debug(f"Embedded query | dim={len(vector)}")
            return vector

        except EmbeddingException:
            raise
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise EmbeddingException(f"Query embedding failed: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingException: If embedding fails
        """
        try:
            model = self.load()
            vectors = model.embed_documents(texts)
            logger.info(f"Embedded {len(texts)} documents | dim={len(vectors[0])}")
            return vectors

        except EmbeddingException:
            raise
        except Exception as e:
            logger.error(f"Document embedding failed: {e}")
            raise EmbeddingException(f"Document embedding failed: {e}")

    def get_model(self) -> HuggingFaceEmbeddings:
        """
        Get the raw HuggingFaceEmbeddings model instance.

        Returns:
            HuggingFaceEmbeddings instance
        """
        return self.load()

    def get_embedding_dim(self) -> int:
        """
        Get embedding dimension by running a test query.

        Returns:
            Integer dimension of embedding vectors
        """
        vector = self.embed_query("test")
        return len(vector)


# ── Singleton instance ────────────────────────────────────
embedding_manager = EmbeddingManager()
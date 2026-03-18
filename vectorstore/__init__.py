"""Vectorstore package — exports FAISS store and embedding manager."""

from vectorstore.embeddings import embedding_manager, EmbeddingManager
from vectorstore.faiss_store import faiss_store, FAISSStore

__all__ = [
    "embedding_manager",
    "EmbeddingManager",
    "faiss_store",
    "FAISSStore",
]
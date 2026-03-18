"""
Document ingestion script.
Supports local files, directories, PDFs, and URLs.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from core.logger import get_logger
from vectorstore.faiss_store import faiss_store
from vectorstore.embeddings  import embedding_manager
from config.settings import settings

logger = get_logger(__name__)


def load_text_file(file_path: str) -> Document:
    """
    Load a single text file as a Document.

    Args:
        file_path: Path to text file

    Returns:
        Document object
    """
    path    = Path(file_path)
    content = path.read_text(encoding="utf-8", errors="ignore")
    return Document(
        page_content = content,
        metadata     = {
            "source"  : path.name,
            "type"    : "text",
            "path"    : str(path)
        }
    )


def load_directory(directory: str) -> List[Document]:
    """
    Load all text files from a directory.

    Args:
        directory: Path to directory

    Returns:
        List of Document objects
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        logger.warning(f"Directory not found: {directory}")
        return []

    docs       = []
    extensions = {".txt", ".md", ".rst", ".csv"}

    for file_path in dir_path.rglob("*"):
        if file_path.suffix.lower() in extensions:
            try:
                doc = load_text_file(str(file_path))
                docs.append(doc)
                logger.info(f"Loaded: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to load {file_path.name}: {e}")

    logger.info(f"Loaded {len(docs)} documents from {directory}")
    return docs


def chunk_documents(
    documents    : List[Document],
    chunk_size   : int = None,
    chunk_overlap: int = None
) -> List[Document]:
    """
    Split documents into chunks.

    Args:
        documents    : List of Document objects
        chunk_size   : Characters per chunk
        chunk_overlap: Overlap between chunks

    Returns:
        List of chunked Document objects
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = chunk_size    or settings.chunk_size,
        chunk_overlap = chunk_overlap or settings.chunk_overlap,
        length_function = len,
        separators    = ["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    logger.info(
        f"Chunked {len(documents)} docs → {len(chunks)} chunks"
    )
    return chunks


def ingest_documents(documents: List[Document]) -> dict:
    """
    Ingest documents into FAISS vector store.

    Args:
        documents: List of Document objects to ingest

    Returns:
        Dict with ingestion statistics
    """
    if not documents:
        logger.warning("No documents to ingest")
        return {"docs": 0, "chunks": 0, "vectors": 0}

    # Chunk documents
    chunks = chunk_documents(documents)

    # Build or update FAISS index
    if faiss_store._vectorstore is not None:
        faiss_store.add_documents(chunks)
        logger.info(f"Added {len(chunks)} chunks to existing index")
    else:
        faiss_store.build(chunks)
        logger.info(f"Built new index from {len(chunks)} chunks")

    # Save to disk
    faiss_store.save()

    total_vectors = faiss_store.total_vectors
    logger.info(
        f"Ingestion complete | "
        f"docs={len(documents)} | "
        f"chunks={len(chunks)} | "
        f"total_vectors={total_vectors}"
    )

    return {
        "docs"   : len(documents),
        "chunks" : len(chunks),
        "vectors": total_vectors
    }


def ingest_from_directory(directory: str) -> dict:
    """
    Full pipeline: load directory → chunk → ingest.

    Args:
        directory: Path to documents directory

    Returns:
        Dict with ingestion statistics
    """
    logger.info(f"Ingesting from directory: {directory}")
    docs = load_directory(directory)
    return ingest_documents(docs)


def ingest_from_texts(
    texts      : List[str],
    source_name: str = "manual"
) -> dict:
    """
    Ingest raw text strings directly.

    Args:
        texts      : List of text strings
        source_name: Source label for metadata

    Returns:
        Dict with ingestion statistics
    """
    docs = [
        Document(
            page_content = text,
            metadata     = {
                "source": source_name,
                "index" : i
            }
        )
        for i, text in enumerate(texts)
    ]
    return ingest_documents(docs)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest documents into FAISS vector store"
    )
    parser.add_argument(
        "--dir",
        default = "data/raw",
        help    = "Directory to ingest (default: data/raw)"
    )
    args = parser.parse_args()

    print(f"Starting ingestion from: {args.dir}")
    result = ingest_from_directory(args.dir)
    print(f"✅ Done | {result}")
"""
Context compression module for RAG pipeline.
Extracts only the most relevant parts from retrieved documents.
"""

from typing import List
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from core.logger import get_logger
from core.exceptions import CompressorException

logger = get_logger(__name__)

COMPRESS_PROMPT = ChatPromptTemplate.from_template("""
Extract ONLY the parts of the document that are directly relevant to the query.
If nothing is relevant, respond with: NOT_RELEVANT
Keep extracted text concise but complete.

Query   : {query}
Document: {document}

Relevant extract:
""")


class ContextCompressor:
    """
    Compresses retrieved documents by extracting relevant content.
    Reduces noise and improves answer quality.
    """

    def __init__(self, llm, min_length: int = 20):
        """
        Initialize compressor.

        Args:
            llm       : LangChain LLM instance
            min_length: Minimum length for extracted content
        """
        self.llm        = llm
        self.min_length = min_length
        self.chain      = COMPRESS_PROMPT | llm | StrOutputParser()
        logger.info("ContextCompressor initialized")

    def compress_document(
        self,
        query   : str,
        document: Document
    ) -> str:
        """
        Extract relevant content from a single document.

        Args:
            query   : Search query
            document: Document to compress

        Returns:
            Compressed relevant content string
        """
        try:
            compressed = self.chain.invoke({
                "query"   : query,
                "document": document.page_content[:800]
            })

            compressed = compressed.strip()

            if "NOT_RELEVANT" in compressed:
                logger.debug(
                    f"Doc not relevant | "
                    f"source={document.metadata.get('source', 'unknown')}"
                )
                return ""

            if len(compressed) < self.min_length:
                return document.page_content

            return compressed

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return document.page_content

    def compress(
        self,
        query    : str,
        documents: List[Document]
    ) -> List[Document]:
        """
        Compress a list of documents.

        Args:
            query    : Search query
            documents: Documents to compress

        Returns:
            List of compressed Document objects (irrelevant docs removed)

        Raises:
            CompressorException: If compression fails
        """
        if not documents:
            logger.warning("No documents to compress")
            return []

        try:
            logger.info(f"Compressing {len(documents)} documents")
            compressed_docs = []

            for doc in documents:
                content = self.compress_document(query, doc)
                if content:
                    compressed_doc = Document(
                        page_content = content,
                        metadata     = doc.metadata
                    )
                    compressed_docs.append(compressed_doc)

            logger.info(
                f"Compression complete | "
                f"{len(documents)} → {len(compressed_docs)} docs"
            )
            return compressed_docs

        except Exception as e:
            logger.error(f"Compression pipeline failed: {e}")
            raise CompressorException(f"Compression failed: {e}")
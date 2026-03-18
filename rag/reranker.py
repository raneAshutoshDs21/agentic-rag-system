"""
Reranker module for improving retrieval quality.
Scores retrieved documents by relevance and reorders them.
"""

from typing import List, Tuple
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from core.logger import get_logger
from core.exceptions import RerankerException

logger = get_logger(__name__)

RERANK_PROMPT = ChatPromptTemplate.from_template("""
You are a relevance scoring assistant.
Score how relevant the document is to the query on a scale of 0-10.
Respond with ONLY a number between 0 and 10. Nothing else.

Query   : {query}
Document: {document}

Score:
""")


class LLMReranker:
    """
    LLM-based reranker for retrieved documents.
    Scores each document for relevance and returns sorted results.
    """

    def __init__(self, llm, top_k: int = 3):
        """
        Initialize reranker.

        Args:
            llm  : LangChain LLM instance
            top_k: Number of top documents to return after reranking
        """
        self.llm   = llm
        self.top_k = top_k
        self.chain = RERANK_PROMPT | llm | StrOutputParser()
        logger.info(f"LLMReranker initialized | top_k={top_k}")

    def score_document(self, query: str, document: str) -> float:
        """
        Score a single document for relevance to query.

        Args:
            query   : Search query
            document: Document content to score

        Returns:
            Float relevance score between 0 and 10
        """
        try:
            raw_score = self.chain.invoke({
                "query"   : query,
                "document": document[:500]
            })
            score = float(raw_score.strip())
            return max(0.0, min(10.0, score))

        except (ValueError, TypeError):
            logger.warning(f"Could not parse score — defaulting to 5.0")
            return 5.0
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return 5.0

    def rerank(
        self,
        query    : str,
        documents: List[Document]
    ) -> List[Tuple[Document, float]]:
        """
        Rerank documents by relevance score.

        Args:
            query    : Search query
            documents: List of retrieved documents

        Returns:
            List of (Document, score) sorted by score descending

        Raises:
            RerankerException: If reranking fails
        """
        if not documents:
            logger.warning("No documents to rerank")
            return []

        try:
            logger.info(f"Reranking {len(documents)} documents")
            scored = []

            for doc in documents:
                score = self.score_document(query, doc.page_content)
                scored.append((doc, score))
                logger.debug(
                    f"Doc score={score:.1f} | "
                    f"source={doc.metadata.get('source', 'unknown')}"
                )

            # Sort by score descending
            scored.sort(key=lambda x: x[1], reverse=True)

            # Return top_k
            top_results = scored[:self.top_k]
            logger.info(
                f"Reranking complete | "
                f"top score={top_results[0][1]:.1f} if top_results else 0"
            )
            return top_results

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            raise RerankerException(f"Reranking failed: {e}")

    def rerank_and_return_docs(
        self,
        query    : str,
        documents: List[Document]
    ) -> List[Document]:
        """
        Rerank and return only documents without scores.

        Args:
            query    : Search query
            documents: Documents to rerank

        Returns:
            Reranked list of Document objects
        """
        scored = self.rerank(query, documents)
        return [doc for doc, _ in scored]
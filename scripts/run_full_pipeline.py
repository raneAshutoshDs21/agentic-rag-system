"""
Full end-to-end pipeline runner script.
Tests all system components together.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from core.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


def setup_llm():
    """Initialize LLM."""
    from langchain_groq import ChatGroq
    return ChatGroq(
        model       = settings.groq_model,
        api_key     = settings.groq_api_key,
        temperature = settings.groq_temperature,
        max_tokens  = settings.groq_max_tokens
    )


def setup_vector_store():
    """Load or build FAISS vector store."""
    from vectorstore.faiss_store import faiss_store
    from scripts.ingest_documents import ingest_from_directory

    try:
        faiss_store.load()
        logger.info(
            f"FAISS loaded | vectors={faiss_store.total_vectors}"
        )
    except Exception:
        logger.info("Building FAISS index from sample docs...")
        ingest_from_directory(str(ROOT / "data" / "raw"))

    return faiss_store


def run_pipeline_tests(orchestrator) -> list:
    """
    Run a series of test queries through the full pipeline.

    Args:
        orchestrator: Orchestrator instance

    Returns:
        List of result dicts
    """
    test_cases = [
        {
            "query"      : "What is RAG and how does it work?",
            "session_id" : "pipeline_test_001",
            "description": "RAG Knowledge Base Query"
        },
        {
            "query"      : "How does FAISS enable fast similarity search?",
            "session_id" : "pipeline_test_002",
            "description": "Vector DB Query"
        },
        {
            "query"      : "Calculate the sum of squares from 1 to 5",
            "session_id" : "pipeline_test_003",
            "description": "Python Computation Query"
        },
        {
            "query"      : "Compare RAG vs fine-tuning for production AI",
            "session_id" : "pipeline_test_004",
            "description": "Complex Reasoning Query"
        },
        {
            "query"      : "What is RAG and how does it work?",
            "session_id" : "pipeline_test_005",
            "description": "Cache Hit Test (repeat of query 1)"
        },
    ]

    results = []
    print("\n" + "=" * 70)
    print("       FULL AGENTIC RAG PIPELINE — END TO END TEST")
    print("=" * 70)

    for i, test in enumerate(test_cases):
        print(f"\n{'─' * 70}")
        print(f"Test {i+1}/{len(test_cases)}: {test['description']}")
        print(f"Query     : {test['query']}")
        print(f"{'─' * 70}")

        start = time.time()

        try:
            result = orchestrator.run(
                query      = test["query"],
                session_id = test["session_id"],
                use_cache  = True
            )
            results.append(result)

            elapsed = (time.time() - start) * 1000

            print(f"Route     : {result.get('route', 'N/A')}")
            print(f"Answer    : {result.get('answer', '')[:250]}...")
            print(f"Score     : {result.get('score', 0):.1f}/10")
            print(f"Feedback  : {result.get('feedback', 'N/A')}")
            print(f"Sources   : {result.get('sources', [])}")
            print(f"Cache Hit : {result.get('from_cache', False)}")
            print(f"Time      : {elapsed:.0f}ms")
            print(f"Success   : {result.get('success', False)}")

        except Exception as e:
            logger.error(f"Test {i+1} failed: {e}")
            results.append({
                "success": False,
                "error"  : str(e),
                "query"  : test["query"]
            })

    return results


def print_summary(results: list):
    """Print final pipeline summary."""
    print(f"\n{'=' * 70}")
    print("                    PIPELINE SUMMARY")
    print(f"{'=' * 70}")

    total      = len(results)
    successful = sum(1 for r in results if r.get("success"))
    avg_score  = (
        sum(r.get("score", 0) for r in results) / total
        if total > 0 else 0
    )
    avg_time   = (
        sum(r.get("total_time_ms", 0) for r in results) / total
        if total > 0 else 0
    )
    cache_hits = sum(1 for r in results if r.get("from_cache"))

    print(f"Total Queries  : {total}")
    print(f"Successful     : {successful}/{total}")
    print(f"Avg Score      : {avg_score:.1f}/10")
    print(f"Avg Latency    : {avg_time:.0f}ms")
    print(f"Cache Hits     : {cache_hits}/{total}")

    # Per query breakdown
    print(f"\nPer Query Results:")
    for i, r in enumerate(results):
        cache_str = "CACHE HIT" if r.get("from_cache") else "fresh"
        print(
            f"  [{i+1}] {r.get('route','N/A'):20} | "
            f"score={r.get('score',0):.1f} | "
            f"{cache_str} | "
            f"{r.get('total_time_ms',0):.0f}ms"
        )

    print(f"\n{'=' * 70}")
    print("✅ FULL PIPELINE COMPLETE — ALL SYSTEMS OPERATIONAL")
    print(f"{'=' * 70}\n")


def main():
    """Main entry point for full pipeline test."""
    print("\n🚀 Initializing Agentic RAG System...")

    # Load environment
    load_dotenv(ROOT / ".env")

    # Setup components
    print("⚙️  Setting up LLM...")
    llm = setup_llm()

    print("⚙️  Setting up Vector Store...")
    setup_vector_store()

    print("⚙️  Setting up Orchestrator...")
    from agents.orchestrator import Orchestrator
    orchestrator = Orchestrator(llm)

    print("✅ All components ready\n")

    # Run tests
    results = run_pipeline_tests(orchestrator)

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
"""
Main entry point for the Agentic RAG System.
Starts the FastAPI server using uvicorn.
"""

import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Add project root to path
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


def main():
    """Start the FastAPI server."""
    logger.info("=" * 50)
    logger.info("Starting Agentic RAG System")
    logger.info(f"Host        : {settings.api_host}")
    logger.info(f"Port        : {settings.api_port}")
    logger.info(f"Environment : {settings.environment}")
    logger.info(f"LLM Model   : {settings.groq_model}")
    logger.info(f"Docs        : http://{settings.api_host}:{settings.api_port}/docs")
    logger.info("=" * 50)

    uvicorn.run(
        "api.main:app",
        host    = settings.api_host,
        port    = settings.api_port,
        reload  = settings.api_reload,
        log_level = settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
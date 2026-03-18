"""
Centralized logging configuration for the agentic RAG system.
Provides a consistent logger across all modules.
"""

import logging
import sys
from pathlib import Path
from config.constants import LOG_FORMAT, LOG_DATE_FORMAT, LOGS_DIR


def setup_logger(
    name      : str,
    level     : str = "INFO",
    log_file  : str = None,
) -> logging.Logger:
    """
    Create and configure a logger with console and file handlers.

    Args:
        name    : Logger name (usually __name__)
        level   : Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on re-import
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt     = LOG_FORMAT,
        datefmt = LOG_DATE_FORMAT
    )

    # ── Console handler ───────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ── File handler ──────────────────────────────────────
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create one with default settings.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    from config.settings import settings

    log_file = settings.log_file if settings.log_file else None

    return setup_logger(
        name     = name,
        level    = settings.log_level,
        log_file = log_file
    )
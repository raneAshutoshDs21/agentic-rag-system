"""
Input guardrails for validating and sanitizing user queries.
Blocks harmful, unsafe, or malformed inputs before processing.
"""

import re
from typing import Tuple
from core.logger import get_logger
from core.exceptions import InputGuardrailException
from config.constants import (
    BLOCKED_INPUT_PATTERNS,
    MAX_INPUT_LENGTH,
    MIN_OUTPUT_LENGTH,
)

logger = get_logger(__name__)


class InputGuard:
    """
    Validates and sanitizes user input before pipeline processing.
    Blocks unsafe patterns, enforces length limits, and cleans text.
    """

    def __init__(
        self,
        max_length      : int  = MAX_INPUT_LENGTH,
        blocked_patterns: list = None,
    ):
        """
        Initialize input guard.

        Args:
            max_length      : Maximum allowed input length
            blocked_patterns: List of regex patterns to block
        """
        self.max_length       = max_length
        self.blocked_patterns = blocked_patterns or BLOCKED_INPUT_PATTERNS
        logger.info(
            f"InputGuard initialized | "
            f"max_length={max_length} | "
            f"patterns={len(self.blocked_patterns)}"
        )

    def check(self, query: str) -> dict:
        """
        Run all guardrail checks on input query.

        Args:
            query: Raw user input string

        Returns:
            Dict with is_safe, reason, and clean_query fields
        """
        # Check empty
        is_safe, reason = self._check_empty(query)
        if not is_safe:
            return self._blocked_result(reason)

        # Check length
        is_safe, reason = self._check_length(query)
        if not is_safe:
            return self._blocked_result(reason)

        # Check blocked patterns
        is_safe, reason = self._check_patterns(query)
        if not is_safe:
            return self._blocked_result(reason)

        # Sanitize
        clean_query = self._sanitize(query)

        logger.info(f"Input passed guardrails: {clean_query[:50]}...")
        return {
            "is_safe"    : True,
            "reason"     : "Input is safe",
            "clean_query": clean_query,
            "original"   : query
        }

    def _check_empty(self, query: str) -> Tuple[bool, str]:
        """Check if input is empty."""
        if not query or not query.strip():
            logger.warning("Blocked: empty input")
            return False, "Empty input provided"
        return True, ""

    def _check_length(self, query: str) -> Tuple[bool, str]:
        """Check if input exceeds maximum length."""
        if len(query) > self.max_length:
            logger.warning(
                f"Blocked: input too long ({len(query)} chars)"
            )
            return (
                False,
                f"Input too long: {len(query)} chars "
                f"(max {self.max_length})"
            )
        return True, ""

    def _check_patterns(self, query: str) -> Tuple[bool, str]:
        """Check if input matches any blocked patterns."""
        query_lower = query.lower()
        for pattern in self.blocked_patterns:
            if re.search(pattern, query_lower):
                logger.warning(
                    f"Blocked: pattern matched '{pattern}'"
                )
                return False, "Input contains blocked content"
        return True, ""

    def _sanitize(self, query: str) -> str:
        """
        Clean and normalize input text.

        Args:
            query: Raw input string

        Returns:
            Sanitized input string
        """
        # Strip leading/trailing whitespace
        clean = query.strip()

        # Normalize internal whitespace
        clean = " ".join(clean.split())

        # Remove null bytes
        clean = clean.replace("\x00", "")

        return clean

    def _blocked_result(self, reason: str) -> dict:
        """Build a blocked result dict."""
        return {
            "is_safe"    : False,
            "reason"     : reason,
            "clean_query": "",
            "original"   : ""
        }

    def add_pattern(self, pattern: str):
        """
        Add a new blocked pattern at runtime.

        Args:
            pattern: Regex pattern to block
        """
        self.blocked_patterns.append(pattern)
        logger.info(f"Added blocked pattern: {pattern}")

    def validate_batch(self, queries: list) -> list:
        """
        Validate multiple queries at once.

        Args:
            queries: List of query strings

        Returns:
            List of check result dicts
        """
        return [self.check(q) for q in queries]
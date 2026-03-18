"""
Output guardrails for validating and cleaning LLM responses.
Ensures responses meet quality and safety standards.
"""

import re
from typing import Tuple
from core.logger import get_logger
from core.exceptions import OutputGuardrailException
from config.constants import (
    BLOCKED_OUTPUT_PATTERNS,
    MAX_OUTPUT_LENGTH,
    MIN_OUTPUT_LENGTH,
)

logger = get_logger(__name__)


class OutputGuard:
    """
    Validates and cleans LLM output before returning to user.
    Enforces length limits, removes problematic patterns, and normalizes text.
    """

    def __init__(
        self,
        max_length      : int  = MAX_OUTPUT_LENGTH,
        min_length      : int  = MIN_OUTPUT_LENGTH,
        blocked_patterns: list = None,
    ):
        """
        Initialize output guard.

        Args:
            max_length      : Maximum allowed output length
            min_length      : Minimum required output length
            blocked_patterns: Patterns to remove from output
        """
        self.max_length       = max_length
        self.min_length       = min_length
        self.blocked_patterns = blocked_patterns or BLOCKED_OUTPUT_PATTERNS
        logger.info(
            f"OutputGuard initialized | "
            f"min={min_length} | max={max_length}"
        )

    def check(self, output: str) -> dict:
        """
        Run all guardrail checks on LLM output.

        Args:
            output: Raw LLM output string

        Returns:
            Dict with is_valid, reason, and clean_output fields
        """
        # Check empty
        is_valid, reason = self._check_empty(output)
        if not is_valid:
            return self._invalid_result(reason)

        # Check minimum length
        is_valid, reason = self._check_min_length(output)
        if not is_valid:
            return self._invalid_result(reason)

        # Truncate if too long
        output = self._truncate(output)

        # Clean blocked patterns
        clean_output = self._clean_patterns(output)

        # Normalize whitespace
        clean_output = self._normalize(clean_output)

        logger.info("Output passed guardrails")
        return {
            "is_valid"    : True,
            "reason"      : "Output is valid",
            "clean_output": clean_output,
            "original_len": len(output),
            "clean_len"   : len(clean_output)
        }

    def _check_empty(self, output: str) -> Tuple[bool, str]:
        """Check if output is empty."""
        if not output or not output.strip():
            logger.warning("Output guardrail: empty output")
            return False, "Empty output from LLM"
        return True, ""

    def _check_min_length(self, output: str) -> Tuple[bool, str]:
        """Check if output meets minimum length."""
        if len(output.strip()) < self.min_length:
            logger.warning(
                f"Output guardrail: too short ({len(output)} chars)"
            )
            return (
                False,
                f"Output too short: {len(output)} chars "
                f"(min {self.min_length})"
            )
        return True, ""

    def _truncate(self, output: str) -> str:
        """Truncate output if it exceeds maximum length."""
        if len(output) > self.max_length:
            logger.warning(
                f"Output truncated: {len(output)} → {self.max_length}"
            )
            return output[:self.max_length] + "...[truncated]"
        return output

    def _clean_patterns(self, output: str) -> str:
        """Remove blocked patterns from output."""
        clean = output
        for pattern in self.blocked_patterns:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)
        return clean

    def _normalize(self, output: str) -> str:
        """Normalize whitespace and formatting."""
        # Remove excessive newlines
        clean = re.sub(r"\n{3,}", "\n\n", output)
        # Strip leading/trailing whitespace
        clean = clean.strip()
        return clean

    def _invalid_result(self, reason: str) -> dict:
        """Build an invalid result dict."""
        return {
            "is_valid"    : False,
            "reason"      : reason,
            "clean_output": "Unable to generate a valid response.",
            "original_len": 0,
            "clean_len"   : 0
        }

    def validate_pair(self, query: str, output: str) -> dict:
        """
        Validate an input-output pair together.

        Args:
            query : Original user query
            output: LLM generated output

        Returns:
            Combined validation result dict
        """
        output_result = self.check(output)
        return {
            "query"       : query,
            "is_valid"    : output_result["is_valid"],
            "reason"      : output_result["reason"],
            "clean_output": output_result["clean_output"],
            "pipeline_ok" : output_result["is_valid"]
        }
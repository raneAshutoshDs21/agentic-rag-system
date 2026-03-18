"""
Abstract base class for all tools in the system.
All tools must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from core.logger import get_logger
from core.exceptions import ToolException


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    Provides common interface, error handling, and logging.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize base tool.

        Args:
            name       : Tool name for logging and identification
            description: Human readable description of tool purpose
        """
        self.name        = name
        self.description = description
        self.logger      = get_logger(f"tool.{name}")
        self._call_count  = 0
        self._error_count = 0

        self.logger.info(f"Tool initialized: {self.name}")

    @abstractmethod
    def execute(self, input_data: Any, **kwargs) -> dict:
        """
        Execute the tool with given input.

        Args:
            input_data: Tool input (query, code, etc.)
            kwargs    : Additional keyword arguments

        Returns:
            Dict with 'result', 'success', and 'error' keys
        """
        pass

    def __call__(self, input_data: Any, **kwargs) -> dict:
        """
        Make tool callable. Wraps execute() with error handling.

        Args:
            input_data: Tool input
            kwargs    : Additional arguments

        Returns:
            Dict with result and metadata
        """
        self._call_count += 1
        self.logger.info(
            f"[{self.name}] Call #{self._call_count}"
        )

        try:
            result = self.execute(input_data, **kwargs)
            success = result.get("success", False)
            self.logger.info(
                f"[{self.name}] Completed | success={success}"
            )
            if not success:
                self._error_count += 1
            return result

        except ToolException as e:
            self._error_count += 1
            self.logger.error(f"[{self.name}] ToolException: {e}")
            return self._error_response(str(e))

        except Exception as e:
            self._error_count += 1
            self.logger.error(f"[{self.name}] Unexpected error: {e}")
            return self._error_response(str(e))

    def _error_response(self, error_msg: str) -> dict:
        """
        Build a standard error response.

        Args:
            error_msg: Error message string

        Returns:
            Standard error dict
        """
        return {
            "result" : None,
            "success": False,
            "error"  : error_msg,
            "tool"   : self.name
        }

    def _success_response(self, result: Any, metadata: dict = None) -> dict:
        """
        Build a standard success response.

        Args:
            result  : Tool execution result
            metadata: Optional additional metadata

        Returns:
            Standard success dict
        """
        response = {
            "result" : result,
            "success": True,
            "error"  : None,
            "tool"   : self.name
        }
        if metadata:
            response.update(metadata)
        return response

    def get_stats(self) -> dict:
        """Get tool execution statistics."""
        return {
            "tool"      : self.name,
            "calls"     : self._call_count,
            "errors"    : self._error_count,
            "error_rate": (
                self._error_count / self._call_count
                if self._call_count > 0 else 0.0
            )
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
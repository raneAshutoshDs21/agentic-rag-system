"""
Abstract base class for all agents in the system.
All agents must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from core.logger import get_logger
from core.exceptions import AgentException


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Provides common interface and shared functionality.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize base agent.

        Args:
            name       : Agent name for logging and identification
            description: Human readable description of agent purpose
        """
        self.name        = name
        self.description = description
        self.logger      = get_logger(f"agent.{name}")
        self._call_count = 0
        self._error_count = 0

        self.logger.info(f"Agent initialized: {self.name}")

    @abstractmethod
    def run(self, query: str, **kwargs) -> dict:
        """
        Execute the agent on a query.

        Args:
            query  : Input query string
            kwargs : Additional keyword arguments

        Returns:
            Dict with at minimum 'answer' and 'success' keys
        """
        pass

    def __call__(self, query: str, **kwargs) -> dict:
        """
        Make agent callable. Wraps run() with error handling.

        Args:
            query  : Input query
            kwargs : Additional arguments

        Returns:
            Dict with answer and metadata
        """
        self._call_count += 1
        self.logger.info(
            f"[{self.name}] Call #{self._call_count} | "
            f"query: {query[:60]}..."
        )

        try:
            result = self.run(query, **kwargs)
            self.logger.info(
                f"[{self.name}] Completed | "
                f"success={result.get('success', False)}"
            )
            return result

        except AgentException as e:
            self._error_count += 1
            self.logger.error(f"[{self.name}] AgentException: {e}")
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
            "answer" : f"Agent {self.name} failed: {error_msg}",
            "success": False,
            "error"  : error_msg,
            "agent"  : self.name
        }

    def get_stats(self) -> dict:
        """
        Get agent execution statistics.

        Returns:
            Dict with call count and error count
        """
        return {
            "agent"      : self.name,
            "calls"      : self._call_count,
            "errors"     : self._error_count,
            "error_rate" : (
                self._error_count / self._call_count
                if self._call_count > 0 else 0.0
            )
        }

    def reset_stats(self):
        """Reset agent statistics."""
        self._call_count  = 0
        self._error_count = 0
        self.logger.info(f"[{self.name}] Stats reset")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
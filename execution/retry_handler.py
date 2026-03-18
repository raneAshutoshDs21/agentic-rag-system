"""
Retry handler for robust pipeline execution.
Implements exponential backoff and evaluation-based retry logic.
"""

import time
from typing import Callable, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from core.logger import get_logger
from core.exceptions import AgenticRAGException
from config.settings import settings

logger = get_logger(__name__)


def with_retry(
    func           : Callable,
    max_attempts   : int   = None,
    min_wait       : int   = None,
    max_wait       : int   = None,
    exceptions     : tuple = (Exception,)
) -> Callable:
    """
    Wrap a function with exponential backoff retry logic.

    Args:
        func        : Function to wrap
        max_attempts: Maximum retry attempts
        min_wait    : Minimum wait between retries in seconds
        max_wait    : Maximum wait between retries in seconds
        exceptions  : Exception types to retry on

    Returns:
        Wrapped function with retry logic
    """
    max_attempts = max_attempts or settings.max_retries
    min_wait     = min_wait     or settings.retry_min_wait
    max_wait     = max_wait     or settings.retry_max_wait

    @retry(
        stop              = stop_after_attempt(max_attempts),
        wait              = wait_exponential(
                                multiplier = 1,
                                min        = min_wait,
                                max        = max_wait
                            ),
        retry             = retry_if_exception_type(exceptions),
        reraise           = True
    )
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapped


class RetryHandler:
    """
    Handles retry logic for the agentic pipeline.
    Supports both exception-based and evaluation-based retries.
    """

    def __init__(
        self,
        max_retries   : int   = None,
        min_score     : float = None,
        min_wait      : int   = None,
        max_wait      : int   = None,
    ):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            min_score  : Minimum acceptable evaluation score
            min_wait   : Minimum wait between retries in seconds
            max_wait   : Maximum wait between retries in seconds
        """
        self.max_retries = max_retries or settings.max_retries
        self.min_score   = min_score   or settings.eval_min_score
        self.min_wait    = min_wait    or settings.retry_min_wait
        self.max_wait    = max_wait    or settings.retry_max_wait
        logger.info(
            f"RetryHandler initialized | "
            f"max_retries={self.max_retries} | "
            f"min_score={self.min_score}"
        )

    def run_with_retry(
        self,
        func      : Callable,
        evaluator : Optional[Callable] = None,
        *args,
        **kwargs
    ) -> dict:
        """
        Run a function with retry on failure or low eval score.

        Args:
            func     : Function to execute
            evaluator: Optional evaluation function
            args     : Positional arguments for func
            kwargs   : Keyword arguments for func

        Returns:
            Best result dict across all attempts
        """
        best_result = None
        best_score  = 0.0
        attempt     = 0

        while attempt <= self.max_retries:
            logger.info(
                f"Attempt {attempt + 1}/{self.max_retries + 1}"
            )

            try:
                result = func(*args, **kwargs)

                # Evaluate result if evaluator provided
                score = self.min_score
                if evaluator and result.get("answer"):
                    eval_out = evaluator(result.get("answer", ""))
                    score    = eval_out.get(
                        "scores", {}
                    ).get("overall", self.min_score)

                logger.info(f"Attempt {attempt + 1} score: {score:.1f}")

                # Track best result
                if score > best_score:
                    best_score  = score
                    best_result = result
                    best_result["score"]   = score
                    best_result["attempt"] = attempt + 1

                # Accept if score is good enough
                if score >= self.min_score:
                    logger.info(
                        f"Score {score:.1f} >= threshold "
                        f"{self.min_score} — accepting"
                    )
                    break

                attempt += 1
                if attempt <= self.max_retries:
                    wait_time = min(
                        self.min_wait * (2 ** attempt),
                        self.max_wait
                    )
                    logger.warning(
                        f"Score {score:.1f} below threshold — "
                        f"retrying in {wait_time}s"
                    )
                    time.sleep(wait_time)

            except AgenticRAGException as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1
                if attempt <= self.max_retries:
                    time.sleep(self.min_wait)

            except Exception as e:
                logger.error(
                    f"Unexpected error on attempt {attempt + 1}: {e}"
                )
                attempt += 1
                if attempt <= self.max_retries:
                    time.sleep(self.min_wait)

        if best_result is None:
            logger.error("All retry attempts failed")
            return {
                "answer"        : "All retry attempts failed",
                "success"       : False,
                "score"         : 0.0,
                "total_attempts": attempt
            }

        best_result["total_attempts"] = attempt
        logger.info(
            f"Retry complete | "
            f"best_score={best_score:.1f} | "
            f"attempts={attempt}"
        )
        return best_result

    def retry_on_exception(
        self,
        func      : Callable,
        exceptions: tuple = (Exception,),
        *args,
        **kwargs
    ):
        """
        Retry a function only on specific exceptions.

        Args:
            func      : Function to execute
            exceptions: Exception types that trigger retry
            args      : Positional arguments
            kwargs    : Keyword arguments

        Returns:
            Function result
        """
        wrapped = with_retry(
            func         = func,
            max_attempts = self.max_retries,
            min_wait     = self.min_wait,
            max_wait     = self.max_wait,
            exceptions   = exceptions
        )
        return wrapped(*args, **kwargs)
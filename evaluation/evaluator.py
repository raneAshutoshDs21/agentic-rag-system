"""
Main evaluator combining LLM judge and metrics tracking.
"""
from typing import List
from langchain_groq import ChatGroq
from core.logger import get_logger
from core.exceptions import EvaluationException
from evaluation.llm_judge import LLMJudge
from evaluation.metrics   import MetricsTracker
from config.settings      import settings

logger = get_logger(__name__)


class Evaluator:
    """
    Complete evaluation system combining LLM judge and metrics.
    """

    def __init__(self, llm: ChatGroq):
        """
        Initialize evaluator.

        Args:
            llm: ChatGroq LLM instance
        """
        self.llm     = llm
        self.judge   = LLMJudge(llm)
        self.metrics = MetricsTracker()
        self.enabled = settings.eval_enabled
        logger.info(
            f"Evaluator initialized | enabled={self.enabled}"
        )

    def evaluate(self, question: str, answer: str) -> dict:
        """
        Evaluate a question-answer pair.

        Args:
            question: Original question
            answer  : Generated answer

        Returns:
            Dict with scores, feedback, and metadata
        """
        if not self.enabled:
            logger.info("Evaluation disabled — skipping")
            return {
                "scores"     : {"overall": 7.0},
                "feedback"   : "Evaluation disabled",
                "needs_retry": False,
                "success"    : True
            }

        try:
            result = self.judge.judge(question, answer)

            # Track metrics
            self.metrics.add(
                question = question,
                scores   = result["scores"],
                feedback = result["feedback"]
            )

            logger.info(
                f"Evaluation complete | "
                f"overall={result['scores'].get('overall', 0):.1f} | "
                f"retry={result['needs_retry']}"
            )

            return result

        except EvaluationException:
            raise
        except Exception as e:
            logger.error(f"Evaluator failed: {e}")
            return {
                "scores"     : {"overall": 5.0},
                "feedback"   : f"Evaluation error: {str(e)}",
                "needs_retry": False,
                "success"    : False
            }

    def evaluate_batch(
        self,
        pairs: list
    ) -> List[dict]:
        """
        Evaluate multiple question-answer pairs.

        Args:
            pairs: List of (question, answer) tuples

        Returns:
            List of evaluation result dicts
        """
        results = []
        for question, answer in pairs:
            result = self.evaluate(question, answer)
            results.append(result)
        return results

    def get_metrics_summary(self) -> dict:
        """Get aggregated metrics summary."""
        return self.metrics.get_summary()

    def reset_metrics(self):
        """Reset metrics tracker."""
        self.metrics.reset()
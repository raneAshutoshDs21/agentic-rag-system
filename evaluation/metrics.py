"""
Evaluation metrics computation module.
Tracks and aggregates evaluation scores over time.
"""

from typing import List, Dict
from core.logger import get_logger
from config.constants import EVAL_CRITERIA

logger = get_logger(__name__)


class MetricsTracker:
    """
    Tracks evaluation metrics across multiple queries.
    Computes aggregates like averages and pass rates.
    """

    def __init__(self):
        """Initialize metrics tracker."""
        self.records : List[dict] = []
        self.total   : int        = 0
        self.passed  : int        = 0
        logger.info("MetricsTracker initialized")

    def add(self, question: str, scores: dict, feedback: str = ""):
        """
        Add an evaluation record.

        Args:
            question: Evaluated question
            scores  : Dict of criterion scores
            feedback: Judge feedback string
        """
        record = {
            "question": question[:100],
            "scores"  : scores,
            "feedback": feedback,
            "passed"  : scores.get("overall", 0) >= 6.0
        }
        self.records.append(record)
        self.total  += 1
        if record["passed"]:
            self.passed += 1

        logger.debug(
            f"Metrics added | overall={scores.get('overall', 0):.1f}"
        )

    def get_averages(self) -> Dict[str, float]:
        """
        Compute average scores across all records.

        Returns:
            Dict of criterion to average score
        """
        if not self.records:
            return {c: 0.0 for c in EVAL_CRITERIA + ["overall"]}

        averages = {}
        for criterion in EVAL_CRITERIA + ["overall"]:
            values = [
                r["scores"].get(criterion, 0.0)
                for r in self.records
            ]
            averages[criterion] = round(
                sum(values) / len(values), 2
            ) if values else 0.0

        return averages

    def get_pass_rate(self) -> float:
        """
        Compute percentage of responses that passed evaluation.

        Returns:
            Pass rate as float between 0 and 1
        """
        if self.total == 0:
            return 0.0
        return round(self.passed / self.total, 3)

    def get_summary(self) -> dict:
        """
        Get full metrics summary.

        Returns:
            Dict with all aggregate metrics
        """
        return {
            "total_evaluated" : self.total,
            "passed"          : self.passed,
            "failed"          : self.total - self.passed,
            "pass_rate"       : self.get_pass_rate(),
            "average_scores"  : self.get_averages(),
        }

    def get_worst_queries(self, n: int = 3) -> List[dict]:
        """
        Get the lowest scoring queries.

        Args:
            n: Number of worst queries to return

        Returns:
            List of worst scoring records
        """
        sorted_records = sorted(
            self.records,
            key=lambda r: r["scores"].get("overall", 0)
        )
        return sorted_records[:n]

    def get_best_queries(self, n: int = 3) -> List[dict]:
        """
        Get the highest scoring queries.

        Args:
            n: Number of best queries to return

        Returns:
            List of best scoring records
        """
        sorted_records = sorted(
            self.records,
            key=lambda r: r["scores"].get("overall", 0),
            reverse=True
        )
        return sorted_records[:n]

    def reset(self):
        """Reset all metrics."""
        self.records = []
        self.total   = 0
        self.passed  = 0
        logger.info("MetricsTracker reset")
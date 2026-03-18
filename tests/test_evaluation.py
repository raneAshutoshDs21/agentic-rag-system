"""
Unit tests for evaluation components.
Tests LLM judge, metrics tracker, and evaluator.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from unittest.mock import MagicMock, patch


# ── Fixtures ──────────────────────────────────────────────

MOCK_JUDGE_OUTPUT = (
    "RELEVANCE: 8\n"
    "ACCURACY: 7\n"
    "COMPLETENESS: 8\n"
    "CLARITY: 9\n"
    "OVERALL: 8.0\n"
    "FEEDBACK: Clear and accurate response\n"
    "NEEDS_RETRY: NO"
)

MOCK_JUDGE_OUTPUT_LOW = (
    "RELEVANCE: 3\n"
    "ACCURACY: 2\n"
    "COMPLETENESS: 3\n"
    "CLARITY: 3\n"
    "OVERALL: 2.75\n"
    "FEEDBACK: Poor answer\n"
    "NEEDS_RETRY: YES"
)


@pytest.fixture
def mock_llm():
    """Mock LLM that returns proper string via chain."""
    llm = MagicMock()
    return llm


# ── LLM Judge Tests ───────────────────────────────────────

class TestLLMJudge:
    """Tests for LLMJudge."""

    def test_judge_init(self, mock_llm):
        """LLMJudge should initialize correctly."""
        from evaluation.llm_judge import LLMJudge
        judge = LLMJudge(mock_llm)
        assert judge is not None

    def test_judge_returns_scores(self, mock_llm):
        """Judge should return parsed scores."""
        from evaluation.llm_judge import LLMJudge

        judge       = LLMJudge(mock_llm)
        judge.chain = MagicMock()
        judge.chain.invoke = MagicMock(return_value=MOCK_JUDGE_OUTPUT)

        result = judge.judge("What is RAG?", "RAG is Retrieval Augmented Generation.")

        assert result["success"]               == True
        assert "relevance"    in result["scores"]
        assert "accuracy"     in result["scores"]
        assert "completeness" in result["scores"]
        assert "clarity"      in result["scores"]
        assert "overall"      in result["scores"]

    def test_judge_score_range(self, mock_llm):
        """All scores should be between 0 and 10."""
        from evaluation.llm_judge import LLMJudge

        judge       = LLMJudge(mock_llm)
        judge.chain = MagicMock()
        judge.chain.invoke = MagicMock(return_value=MOCK_JUDGE_OUTPUT)

        result = judge.judge("question", "answer")

        for score in result["scores"].values():
            assert 0.0 <= score <= 10.0

    def test_judge_returns_feedback(self, mock_llm):
        """Judge should return feedback string."""
        from evaluation.llm_judge import LLMJudge

        judge       = LLMJudge(mock_llm)
        judge.chain = MagicMock()
        judge.chain.invoke = MagicMock(return_value=MOCK_JUDGE_OUTPUT)

        result = judge.judge("question", "answer")

        assert "feedback" in result
        assert isinstance(result["feedback"], str)
        assert len(result["feedback"]) > 0

    def test_judge_returns_needs_retry(self, mock_llm):
        """Judge should return needs_retry boolean."""
        from evaluation.llm_judge import LLMJudge

        judge       = LLMJudge(mock_llm)
        judge.chain = MagicMock()
        judge.chain.invoke = MagicMock(return_value=MOCK_JUDGE_OUTPUT)

        result = judge.judge("question", "answer")

        assert "needs_retry" in result
        assert isinstance(result["needs_retry"], bool)
        assert result["needs_retry"] == False

    def test_judge_empty_answer(self, mock_llm):
        """Judge should handle empty answer."""
        from evaluation.llm_judge import LLMJudge

        judge  = LLMJudge(mock_llm)
        result = judge.judge("question", "")

        assert result["success"]           == False
        assert result["needs_retry"]       == True
        assert result["scores"]["overall"] == 0.0

    def test_parse_needs_retry_yes(self, mock_llm):
        """Should parse NEEDS_RETRY: YES correctly."""
        from evaluation.llm_judge import LLMJudge

        judge       = LLMJudge(mock_llm)
        judge.chain = MagicMock()
        judge.chain.invoke = MagicMock(return_value=MOCK_JUDGE_OUTPUT_LOW)

        result = judge.judge("question", "bad answer")
        assert result["needs_retry"]       == True
        assert result["scores"]["overall"] == 2.75

    def test_judge_overall_score_value(self, mock_llm):
        """Judge should parse overall score correctly."""
        from evaluation.llm_judge import LLMJudge

        judge       = LLMJudge(mock_llm)
        judge.chain = MagicMock()
        judge.chain.invoke = MagicMock(return_value=MOCK_JUDGE_OUTPUT)

        result = judge.judge("question", "answer")
        assert result["scores"]["overall"] == 8.0


# ── Metrics Tracker Tests ─────────────────────────────────

class TestMetricsTracker:
    """Tests for MetricsTracker."""

    def test_tracker_init(self):
        """MetricsTracker should initialize with zero counts."""
        from evaluation.metrics import MetricsTracker
        tracker = MetricsTracker()
        assert tracker.total  == 0
        assert tracker.passed == 0

    def test_add_record(self):
        """Should add records and update counts."""
        from evaluation.metrics import MetricsTracker
        tracker = MetricsTracker()
        tracker.add(
            "What is RAG?",
            {"overall": 8.0, "relevance": 8.0},
            "Good answer"
        )
        assert tracker.total == 1

    def test_pass_rate_calculation(self):
        """Should calculate pass rate correctly."""
        from evaluation.metrics import MetricsTracker
        tracker = MetricsTracker()

        tracker.add("q1", {"overall": 8.0}, "good")
        tracker.add("q2", {"overall": 7.0}, "good")
        tracker.add("q3", {"overall": 4.0}, "poor")

        rate = tracker.get_pass_rate()
        assert abs(rate - 0.667) < 0.01

    def test_get_averages(self):
        """Should compute average scores."""
        from evaluation.metrics import MetricsTracker
        tracker = MetricsTracker()

        tracker.add("q1", {"overall": 8.0, "relevance": 8.0}, "")
        tracker.add("q2", {"overall": 6.0, "relevance": 6.0}, "")

        avgs = tracker.get_averages()
        assert avgs["overall"]   == 7.0
        assert avgs["relevance"] == 7.0

    def test_get_summary(self):
        """get_summary should return complete stats."""
        from evaluation.metrics import MetricsTracker
        tracker = MetricsTracker()
        tracker.add("q1", {"overall": 8.0}, "good")

        summary = tracker.get_summary()
        assert "total_evaluated" in summary
        assert "passed"          in summary
        assert "failed"          in summary
        assert "pass_rate"       in summary
        assert "average_scores"  in summary

    def test_get_worst_queries(self):
        """Should return lowest scoring queries."""
        from evaluation.metrics import MetricsTracker
        tracker = MetricsTracker()

        tracker.add("q1", {"overall": 9.0}, "")
        tracker.add("q2", {"overall": 3.0}, "")
        tracker.add("q3", {"overall": 6.0}, "")

        worst = tracker.get_worst_queries(n=1)
        assert len(worst) == 1
        assert worst[0]["scores"]["overall"] == 3.0

    def test_reset(self):
        """Reset should clear all records."""
        from evaluation.metrics import MetricsTracker
        tracker = MetricsTracker()
        tracker.add("q1", {"overall": 8.0}, "")
        tracker.reset()

        assert tracker.total        == 0
        assert tracker.passed       == 0
        assert len(tracker.records) == 0


# ── Evaluator Tests ───────────────────────────────────────

class TestEvaluator:
    """Tests for Evaluator."""

    def test_evaluator_init(self, mock_llm):
        """Evaluator should initialize correctly."""
        from evaluation.evaluator import Evaluator
        evaluator = Evaluator(mock_llm)
        assert evaluator.enabled == True

    def test_evaluate_returns_result(self, mock_llm):
        """evaluate should return result dict."""
        from evaluation.evaluator import Evaluator

        evaluator             = Evaluator(mock_llm)
        evaluator.judge.chain = MagicMock()
        evaluator.judge.chain.invoke = MagicMock(
            return_value=MOCK_JUDGE_OUTPUT
        )

        result = evaluator.evaluate(
            "What is RAG?",
            "RAG is Retrieval Augmented Generation."
        )

        assert "scores"      in result
        assert "feedback"    in result
        assert "needs_retry" in result

    def test_evaluate_updates_metrics(self, mock_llm):
        """evaluate should update metrics tracker."""
        from evaluation.evaluator import Evaluator

        evaluator             = Evaluator(mock_llm)
        evaluator.judge.chain = MagicMock()
        evaluator.judge.chain.invoke = MagicMock(
            return_value=MOCK_JUDGE_OUTPUT
        )

        evaluator.evaluate("q1", "answer 1")
        evaluator.evaluate("q2", "answer 2")

        summary = evaluator.get_metrics_summary()
        assert summary["total_evaluated"] == 2

    def test_evaluate_disabled_skips_judging(self, mock_llm):
        """Disabled evaluator should skip LLM judging."""
        from evaluation.evaluator import Evaluator

        evaluator         = Evaluator(mock_llm)
        evaluator.enabled = False

        result = evaluator.evaluate("question", "answer")
        assert result["feedback"] == "Evaluation disabled"

    def test_evaluate_batch(self, mock_llm):
        """evaluate_batch should process all pairs."""
        from evaluation.evaluator import Evaluator

        evaluator             = Evaluator(mock_llm)
        evaluator.judge.chain = MagicMock()
        evaluator.judge.chain.invoke = MagicMock(
            return_value=MOCK_JUDGE_OUTPUT
        )

        pairs = [
            ("q1", "answer 1"),
            ("q2", "answer 2"),
            ("q3", "answer 3"),
        ]
        results = evaluator.evaluate_batch(pairs)
        assert len(results) == 3

    def test_reset_metrics(self, mock_llm):
        """reset_metrics should clear all metrics."""
        from evaluation.evaluator import Evaluator

        evaluator             = Evaluator(mock_llm)
        evaluator.judge.chain = MagicMock()
        evaluator.judge.chain.invoke = MagicMock(
            return_value=MOCK_JUDGE_OUTPUT
        )

        evaluator.evaluate("q1", "answer")
        evaluator.reset_metrics()

        summary = evaluator.get_metrics_summary()
        assert summary["total_evaluated"] == 0


# ── Cache Tests ───────────────────────────────────────────

class TestResponseCache:
    """Tests for ResponseCache."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create cache with temp database."""
        from cache.response_cache import ResponseCache
        return ResponseCache(
            db_path = str(tmp_path / "test.db"),
            ttl     = 3600,
            enabled = True
        )

    def test_cache_miss_returns_none(self, cache):
        """Cache miss should return None."""
        result = cache.get("nonexistent query")
        assert result is None

    def test_set_and_get(self, cache):
        """Should set and get cached response."""
        cache.set("What is RAG?", "RAG is a technique...", score=8.0)
        result = cache.get("What is RAG?")

        assert result               is not None
        assert result["from_cache"] == True
        assert "RAG is a technique" in result["response"]

    def test_case_insensitive_keys(self, cache):
        """Cache keys should be case insensitive."""
        cache.set("What is RAG?", "answer", score=7.0)
        result = cache.get("what is rag?")
        assert result is not None

    def test_delete_removes_entry(self, cache):
        """Delete should remove cached entry."""
        cache.set("test query", "test response", score=7.0)
        cache.delete("test query")
        result = cache.get("test query")
        assert result is None

    def test_stats_returns_correct_counts(self, cache):
        """Stats should return correct entry count."""
        cache.set("q1", "r1", score=8.0)
        cache.set("q2", "r2", score=7.0)

        stats = cache.stats()
        assert stats["total_entries"] == 2

    def test_clear_all_removes_everything(self, cache):
        """clear_all should remove all entries."""
        cache.set("q1", "r1")
        cache.set("q2", "r2")
        removed = cache.clear_all()

        assert removed >= 2
        stats = cache.stats()
        assert stats["total_entries"] == 0

    def test_disabled_cache_returns_none(self, tmp_path):
        """Disabled cache should always return None."""
        from cache.response_cache import ResponseCache
        cache = ResponseCache(
            db_path = str(tmp_path / "test.db"),
            enabled = False
        )
        cache.set("query", "response")
        result = cache.get("query")
        assert result is None
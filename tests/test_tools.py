"""
Unit tests for tool components.
Tests web search, Python executor, and database tool.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from unittest.mock import MagicMock, patch


# ── Base Tool Tests ───────────────────────────────────────

class TestBaseTool:
    """Tests for BaseTool abstract class."""

    def test_base_tool_stats(self):
        """BaseTool should track execution statistics."""
        from core.base_tool import BaseTool

        class ConcreteTool(BaseTool):
            def execute(self, input_data, **kwargs):
                return self._success_response("result")

        tool = ConcreteTool("test_tool")
        tool("input 1")
        tool("input 2")

        stats = tool.get_stats()
        assert stats["calls"]  == 2
        assert stats["errors"] == 0

    def test_base_tool_error_response(self):
        """BaseTool should handle errors and return error dict."""
        from core.base_tool import BaseTool

        class FailingTool(BaseTool):
            def execute(self, input_data, **kwargs):
                raise Exception("Tool error")

        tool   = FailingTool("failing_tool")
        result = tool("input")

        assert result["success"] == False
        assert result["error"]   is not None

    def test_success_response_structure(self):
        """_success_response should return correct structure."""
        from core.base_tool import BaseTool

        class ConcreteTool(BaseTool):
            def execute(self, input_data, **kwargs):
                return self._success_response("test result")

        tool   = ConcreteTool("test")
        result = tool("input")

        assert result["success"] == True
        assert result["result"]  == "test result"
        assert result["error"]   is None


# ── Python Executor Tests ─────────────────────────────────

class TestPythonExecutorTool:
    """Tests for PythonExecutorTool."""

    def test_executor_init(self):
        """PythonExecutorTool should initialize correctly."""
        from tools.python_executor import PythonExecutorTool
        tool = PythonExecutorTool()
        assert tool.name == "python_executor"

    def test_execute_simple_code(self):
        """Executor should run simple Python code."""
        from tools.python_executor import PythonExecutorTool
        tool   = PythonExecutorTool()
        result = tool("print('hello world')")

        assert result["success"]      == True
        assert "hello world" in result["result"]

    def test_execute_math_code(self):
        """Executor should handle math computations."""
        from tools.python_executor import PythonExecutorTool
        tool   = PythonExecutorTool()
        result = tool("print(2 + 2)")

        assert result["success"] == True
        assert "4" in result["result"]

    def test_execute_handles_syntax_error(self):
        """Executor should handle syntax errors gracefully."""
        from tools.python_executor import PythonExecutorTool
        tool   = PythonExecutorTool()
        result = tool("def broken(")

        assert result["success"] == False
        assert result["error"]   is not None

    def test_execute_handles_runtime_error(self):
        """Executor should handle runtime errors gracefully."""
        from tools.python_executor import PythonExecutorTool
        tool   = PythonExecutorTool()
        result = tool("print(1/0)")

        assert result["success"] == False

    def test_extract_code_from_markdown(self):
        """Executor should extract code from markdown blocks."""
        from tools.python_executor import PythonExecutorTool
        tool = PythonExecutorTool()
        code = tool._extract_code("```python\nprint('hi')\n```")
        assert code == "print('hi')"

    def test_safety_check_blocks_dangerous(self):
        """Safety check should block dangerous operations."""
        from tools.python_executor import PythonExecutorTool
        tool   = PythonExecutorTool()
        result = tool("import os; os.system('rm -rf /')")

        assert result["success"] == False

    def test_execute_multiline_code(self):
        """Executor should handle multiline code."""
        from tools.python_executor import PythonExecutorTool
        tool = PythonExecutorTool()
        code = """
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f'Sum: {total}')
"""
        result = tool(code)
        assert result["success"] == True
        assert "15" in result["result"]


# ── Database Tool Tests ───────────────────────────────────

class TestDatabaseTool:
    """Tests for DatabaseTool."""

    @pytest.fixture
    def db_tool(self, tmp_path):
        """Create database tool with temp database."""
        from tools.database_tool import DatabaseTool
        db_path = str(tmp_path / "test.db")
        return DatabaseTool(db_path=db_path)

    def test_db_tool_init(self, db_tool):
        """DatabaseTool should initialize correctly."""
        assert db_tool.name == "database"

    def test_save_and_retrieve_tool_result(self, db_tool):
        """Should save and retrieve tool results."""
        db_tool.save_tool_result(
            tool_name = "web_search",
            query     = "test query",
            result    = "test result",
            success   = True
        )
        results = db_tool.get_recent_queries(limit=5)
        assert isinstance(results, list)

    def test_blocks_non_select_queries(self, db_tool):
        """Should block non-SELECT SQL queries."""
        result = db_tool.execute("DROP TABLE tool_results")
        assert result["success"] == False

    def test_select_query_works(self, db_tool):
        """Should execute SELECT queries."""
        result = db_tool.execute(
            "SELECT COUNT(*) as count FROM tool_results"
        )
        assert result["success"] == True

    def test_get_stats(self, db_tool):
        """Should return database statistics."""
        stats = db_tool.get_stats()
        assert "tool_results"  in stats
        assert "query_history" in stats


# ── Guardrails Tests ──────────────────────────────────────

class TestInputGuard:
    """Tests for InputGuard."""

    @pytest.fixture
    def guard(self):
        from guardrails.input_guard import InputGuard
        return InputGuard()

    def test_safe_query_passes(self, guard):
        """Safe query should pass guardrails."""
        result = guard.check("What is RAG?")
        assert result["is_safe"] == True

    def test_empty_query_blocked(self, guard):
        """Empty query should be blocked."""
        result = guard.check("")
        assert result["is_safe"] == False

    def test_too_long_query_blocked(self, guard):
        """Too long query should be blocked."""
        result = guard.check("A" * 3000)
        assert result["is_safe"] == False

    def test_harmful_query_blocked(self, guard):
        """Harmful query should be blocked."""
        result = guard.check("how to hack a system")
        assert result["is_safe"] == False

    def test_sanitization_normalizes_whitespace(self, guard):
        """Sanitization should normalize whitespace."""
        result = guard.check("  what   is   RAG?  ")
        assert result["is_safe"]     == True
        assert result["clean_query"] == "what is RAG?"


class TestOutputGuard:
    """Tests for OutputGuard."""

    @pytest.fixture
    def guard(self):
        from guardrails.output_guard import OutputGuard
        return OutputGuard()

    def test_valid_output_passes(self, guard):
        """Valid output should pass guardrails."""
        result = guard.check("RAG is a technique for improving LLMs.")
        assert result["is_valid"] == True

    def test_empty_output_blocked(self, guard):
        """Empty output should be blocked."""
        result = guard.check("")
        assert result["is_valid"] == False

    def test_too_short_output_blocked(self, guard):
        """Too short output should be blocked."""
        result = guard.check("OK")
        assert result["is_valid"] == False

    def test_long_output_truncated(self, guard):
        """Long output should be truncated."""
        long_output = "A" * 5000
        result      = guard.check(long_output)
        assert result["is_valid"]         == True
        assert len(result["clean_output"]) < 5000
        assert "truncated" in result["clean_output"]
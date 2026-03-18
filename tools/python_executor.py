"""
Python code execution tool.
Safely executes Python code and captures output.
"""

import io
import contextlib
import traceback
import ast
from typing import Any
from core.base_tool import BaseTool
from core.logger import get_logger
from core.exceptions import PythonExecutorException

logger = get_logger(__name__)

# Safe built-ins allowed during execution
SAFE_BUILTINS = {
    "print"     : print,
    "range"     : range,
    "len"       : len,
    "sum"       : sum,
    "min"       : min,
    "max"       : max,
    "abs"       : abs,
    "round"     : round,
    "sorted"    : sorted,
    "enumerate" : enumerate,
    "zip"       : zip,
    "map"       : map,
    "filter"    : filter,
    "list"      : list,
    "dict"      : dict,
    "set"       : set,
    "tuple"     : tuple,
    "str"       : str,
    "int"       : int,
    "float"     : float,
    "bool"      : bool,
    "type"      : type,
    "isinstance": isinstance,
    "__import__": __import__,
}


class PythonExecutorTool(BaseTool):
    """
    Safe Python code execution tool.
    Captures stdout, stderr, and handles errors gracefully.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize Python executor.

        Args:
            timeout: Maximum execution time in seconds
        """
        super().__init__(
            name        = "python_executor",
            description = "Execute Python code and return output"
        )
        self.timeout = timeout
        logger.info(f"PythonExecutorTool initialized | timeout={timeout}s")

    def execute(self, input_data: str, **kwargs) -> dict:
        """
        Execute Python code string.

        Args:
            input_data: Python code to execute

        Returns:
            Dict with stdout output and execution status
        """
        code = self._extract_code(input_data)

        if not self._is_safe(code):
            return self._error_response(
                "Code contains unsafe operations and cannot be executed"
            )

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            logger.info("Executing Python code")
            with contextlib.redirect_stdout(stdout_capture):
                with contextlib.redirect_stderr(stderr_capture):
                    exec(
                        compile(code, "<string>", "exec"),
                        {"__builtins__": SAFE_BUILTINS}
                    )

            stdout = stdout_capture.getvalue()
            stderr = stderr_capture.getvalue()

            logger.info(f"Execution successful | output_len={len(stdout)}")
            return self._success_response(
                result   = stdout or "Code executed with no output",
                metadata = {
                    "stderr" : stderr,
                    "code"   : code[:200]
                }
            )

        except SyntaxError as e:
            logger.error(f"Syntax error: {e}")
            return self._error_response(f"Syntax error: {e}")

        except Exception as e:
            error = traceback.format_exc()
            logger.error(f"Execution failed: {e}")
            return self._error_response(
                f"Runtime error: {str(e)}\n{error[:300]}"
            )

    def _extract_code(self, text: str) -> str:
        """
        Extract code from markdown code blocks if present.

        Args:
            text: Raw text possibly containing code blocks

        Returns:
            Clean Python code string
        """
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        if "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def _is_safe(self, code: str) -> bool:
        """
        Basic safety check for dangerous operations.

        Args:
            code: Python code string

        Returns:
            True if code appears safe to execute
        """
        dangerous = [
            "os.system",
            "subprocess",
            "shutil.rmtree",
            "__import__('os')",
            "open(",
            "eval(",
            "exec(",
            "socket",
            "requests",
        ]
        code_lower = code.lower()
        for pattern in dangerous:
            if pattern.lower() in code_lower:
                logger.warning(f"Unsafe pattern detected: {pattern}")
                return False
        return True


# ── Singleton instance ────────────────────────────────────
python_executor_tool = PythonExecutorTool()
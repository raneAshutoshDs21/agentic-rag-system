"""
LLM-as-a-judge evaluation module.
Scores responses on relevance, accuracy, completeness, and clarity.
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from core.logger import get_logger
from core.exceptions import EvaluationException
from config.constants import EVAL_CRITERIA, EVAL_MAX_SCORE

logger = get_logger(__name__)

JUDGE_PROMPT = ChatPromptTemplate.from_template("""
You are an expert AI evaluator. Score the answer on these criteria.
Respond in EXACTLY this format with no extra text:

RELEVANCE: <0-10>
ACCURACY: <0-10>
COMPLETENESS: <0-10>
CLARITY: <0-10>
OVERALL: <average of above>
FEEDBACK: <one sentence of constructive feedback>
NEEDS_RETRY: <YES or NO>

Question : {question}
Answer   : {answer}

Evaluation:
""")


class LLMJudge:
    """
    LLM-based evaluation judge.
    Scores question-answer pairs across multiple quality dimensions.
    """

    def __init__(self, llm: ChatGroq):
        """
        Initialize LLM judge.

        Args:
            llm: ChatGroq LLM instance
        """
        self.llm   = llm
        self.chain = JUDGE_PROMPT | llm | StrOutputParser()
        logger.info("LLMJudge initialized")

    def judge(self, question: str, answer: str) -> dict:
        """
        Judge a question-answer pair.

        Args:
            question: Original question
            answer  : Generated answer to evaluate

        Returns:
            Dict with scores, feedback, and retry recommendation

        Raises:
            EvaluationException: If evaluation fails
        """
        if not answer or not answer.strip():
            return self._empty_answer_result()

        try:
            logger.info(f"Judging response for: {question[:50]}...")

            raw_output = self.chain.invoke({
                "question": question,
                "answer"  : answer[:1000]
            })

            result = self._parse_output(raw_output)
            logger.info(
                f"Judge complete | overall={result['scores'].get('overall', 0):.1f}"
            )
            return result

        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            raise EvaluationException(f"Judge failed: {e}")

    def _parse_output(self, raw_output: str) -> dict:
        """
        Parse judge output into structured dict.

        Args:
            raw_output: Raw LLM judge output string

        Returns:
            Dict with scores and feedback
        """
        scores      = {}
        feedback    = ""
        needs_retry = False

        for line in raw_output.strip().split("\n"):
            line = line.strip()
            try:
                if line.startswith("RELEVANCE:"):
                    scores["relevance"] = float(
                        line.split(":")[1].strip()
                    )
                elif line.startswith("ACCURACY:"):
                    scores["accuracy"] = float(
                        line.split(":")[1].strip()
                    )
                elif line.startswith("COMPLETENESS:"):
                    scores["completeness"] = float(
                        line.split(":")[1].strip()
                    )
                elif line.startswith("CLARITY:"):
                    scores["clarity"] = float(
                        line.split(":")[1].strip()
                    )
                elif line.startswith("OVERALL:"):
                    scores["overall"] = float(
                        line.split(":")[1].strip()
                    )
                elif line.startswith("FEEDBACK:"):
                    feedback = line.split(":", 1)[1].strip()
                elif line.startswith("NEEDS_RETRY:"):
                    needs_retry = "YES" in line.upper()
            except (ValueError, IndexError):
                continue

        # Compute overall if not parsed
        if "overall" not in scores and scores:
            scores["overall"] = round(
                sum(scores.values()) / len(scores), 2
            )

        # Default scores if parsing completely failed
        if not scores:
            scores = {c: 5.0 for c in EVAL_CRITERIA}
            scores["overall"] = 5.0

        return {
            "scores"     : scores,
            "feedback"   : feedback or "No feedback provided",
            "needs_retry": needs_retry,
            "raw_output" : raw_output,
            "success"    : True
        }

    def _empty_answer_result(self) -> dict:
        """Return result for empty answer."""
        return {
            "scores"     : {c: 0.0 for c in EVAL_CRITERIA + ["overall"]},
            "feedback"   : "Empty answer provided",
            "needs_retry": True,
            "raw_output" : "",
            "success"    : False
        }
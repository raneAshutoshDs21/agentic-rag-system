"""
Evaluation agent prompt templates.
"""

from langchain.prompts import ChatPromptTemplate

JUDGE_PROMPT = ChatPromptTemplate.from_template("""
You are an expert AI evaluator. Score the answer strictly.
Respond in EXACTLY this format with no extra text:

RELEVANCE: <0-10>
ACCURACY: <0-10>
COMPLETENESS: <0-10>
CLARITY: <0-10>
OVERALL: <average of above>
FEEDBACK: <one sentence of constructive feedback>
NEEDS_RETRY: <YES or NO>

Scoring guide:
- 9-10: Excellent, comprehensive, accurate
- 7-8 : Good, mostly accurate with minor gaps
- 5-6 : Average, partially correct
- 3-4 : Poor, significant errors or gaps
- 0-2 : Very poor or completely wrong

Question : {question}
Answer   : {answer}

Evaluation:
""")

FACTUAL_CHECK_PROMPT = ChatPromptTemplate.from_template("""
You are a fact-checking agent. Verify if the answer is
factually consistent with the provided context.

Context: {context}
Answer : {answer}

Is the answer factually consistent with the context?
Respond with: CONSISTENT or INCONSISTENT
Then explain why in one sentence.

Verdict:
""")

HALLUCINATION_CHECK_PROMPT = ChatPromptTemplate.from_template("""
Check if the answer contains any hallucinations or
information not supported by the context.

Context: {context}
Answer : {answer}

Does the answer contain hallucinations?
Respond with: YES or NO
Then list any unsupported claims.

Result:
""")
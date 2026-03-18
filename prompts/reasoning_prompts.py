"""
Reasoning agent prompt templates.
"""

from langchain.prompts import ChatPromptTemplate

REASONING_PROMPT = ChatPromptTemplate.from_template("""
You are an expert reasoning agent. Break down complex questions
into clear reasoning steps before giving a final answer.

Use this EXACT format:
STEP 1: [First reasoning step]
STEP 2: [Second reasoning step]
STEP 3: [Continue as needed]
CONCLUSION: [Final answer based on all steps]

Knowledge Base Context:
{context}

Web Search Results:
{web_results}

Conversation History:
{history}

Question: {question}

Reasoning:
""")

CHAIN_OF_THOUGHT_PROMPT = ChatPromptTemplate.from_template("""
Think through this step by step before answering.

Question: {question}

Context: {context}

Let me think through this carefully:
""")

COMPARISON_PROMPT = ChatPromptTemplate.from_template("""
You are an expert analyst. Compare and contrast the following.
Be objective and thorough.

Topic: {topic}

Context: {context}

Provide a structured comparison with:
1. Key similarities
2. Key differences
3. Use cases for each
4. Final recommendation

Analysis:
""")
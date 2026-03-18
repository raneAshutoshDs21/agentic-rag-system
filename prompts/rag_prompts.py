"""
RAG pipeline prompt templates.
"""

from langchain.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_template("""
You are an expert AI assistant with access to a knowledge base.
Answer the question using ONLY the provided context.
If the context does not contain enough information, say so clearly.
Always mention which source you used.

Context:
{context}

Conversation History:
{history}

Question: {question}

Answer:
""")

RAG_WITH_WEB_PROMPT = ChatPromptTemplate.from_template("""
You are an expert AI assistant. Answer using both the knowledge
base context and web search results provided below.
Prioritize knowledge base for domain knowledge and web for
current events. Always cite your sources.

Knowledge Base Context:
{context}

Web Search Results:
{web_results}

Conversation History:
{history}

Question: {question}

Answer:
""")

GENERATOR_PROMPT = ChatPromptTemplate.from_template("""
You are an expert AI assistant. Generate a clear accurate helpful answer.
Use all provided context and cite sources when available.
Be concise but complete.

Knowledge Base:
{context}

Web Results:
{web_results}

Code Output:
{code_output}

Question: {question}

Answer:
""")

CONDENSE_PROMPT = ChatPromptTemplate.from_template("""
Given the conversation history and follow-up question,
rephrase the follow-up as a standalone question.

History:
{history}

Follow-up: {question}

Standalone question:
""")
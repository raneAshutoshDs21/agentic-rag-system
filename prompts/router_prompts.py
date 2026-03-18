"""
Router agent prompt templates.
"""

from langchain.prompts import ChatPromptTemplate

ROUTER_PROMPT = ChatPromptTemplate.from_template("""
You are a routing agent for an advanced AI system.
Analyze the user query and decide which agent should handle it.
Choose EXACTLY ONE of these options:

- RAG_AGENT      : Query needs information from the knowledge base
- WEB_SEARCH     : Query needs current or live information from internet
- PYTHON_AGENT   : Query needs code execution or mathematical computation
- REASONING_AGENT: Query needs multi-step reasoning or complex analysis
- DIRECT_ANSWER  : Query is simple and can be answered directly

Rules:
- If query asks about recent events or news → WEB_SEARCH
- If query asks to calculate, compute, or code → PYTHON_AGENT
- If query is about documents, concepts, or stored knowledge → RAG_AGENT
- If query is complex with multiple parts → REASONING_AGENT
- If query is a simple greeting or factual → DIRECT_ANSWER

Respond with ONLY the agent name. Nothing else.

Query: {query}

Agent:
""")

ROUTER_WITH_HISTORY_PROMPT = ChatPromptTemplate.from_template("""
You are a routing agent for an advanced AI system.
Consider the conversation history when routing.
Choose EXACTLY ONE option:

- RAG_AGENT
- WEB_SEARCH
- PYTHON_AGENT
- REASONING_AGENT
- DIRECT_ANSWER

Conversation History:
{history}

Current Query: {query}

Agent:
""")
"""
Global constants used throughout the agentic RAG system.
These are fixed values that do not change with environment.
"""

# ── Agent Routes ──────────────────────────────────────────
ROUTE_RAG_AGENT       = "RAG_AGENT"
ROUTE_WEB_SEARCH      = "WEB_SEARCH"
ROUTE_PYTHON_AGENT    = "PYTHON_AGENT"
ROUTE_REASONING_AGENT = "REASONING_AGENT"
ROUTE_DIRECT_ANSWER   = "DIRECT_ANSWER"
ROUTE_BLOCKED         = "BLOCKED"

VALID_ROUTES = [
    ROUTE_RAG_AGENT,
    ROUTE_WEB_SEARCH,
    ROUTE_PYTHON_AGENT,
    ROUTE_REASONING_AGENT,
    ROUTE_DIRECT_ANSWER,
]

# ── Node Names ────────────────────────────────────────────
NODE_INPUT_GUARD   = "input_guard_node"
NODE_ROUTER        = "router_node"
NODE_RETRIEVER     = "retriever_node"
NODE_WEB_SEARCH    = "web_search_node"
NODE_PYTHON        = "python_node"
NODE_REASONING     = "reasoning_node"
NODE_GENERATOR     = "generator_node"
NODE_OUTPUT_GUARD  = "output_guard_node"

# ── Memory ────────────────────────────────────────────────
MEMORY_SHORT_TERM  = "short_term_memory"
MEMORY_LONG_TERM   = "long_term_memory"
MEMORY_CACHE       = "response_cache"
MEMORY_TOOL_DB     = "tool_results"

# ── Evaluation ────────────────────────────────────────────
EVAL_CRITERIA = [
    "relevance",
    "accuracy",
    "completeness",
    "clarity"
]
EVAL_MAX_SCORE     = 10.0
EVAL_MIN_SCORE     = 6.0
EVAL_PASSING_GRADE = 7.0

# ── Guardrails ────────────────────────────────────────────
MAX_INPUT_LENGTH   = 2000
MAX_OUTPUT_LENGTH  = 4000
MIN_OUTPUT_LENGTH  = 10

BLOCKED_INPUT_PATTERNS = [
    r"\b(hack|exploit|malware|virus|ransomware)\b",
    r"\b(bomb|weapon|explosive|poison)\b",
    r"\b(suicide|self.harm|kill yourself)\b",
    r"\b(password|credit.card|ssn|social.security)\b",
]

BLOCKED_OUTPUT_PATTERNS = [
    r"\b(as an AI|I am an AI|I'm an AI)\b",
]

# ── RAG ───────────────────────────────────────────────────
DEFAULT_CHUNK_SIZE    = 300
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_K             = 4
DEFAULT_FETCH_K       = 8
MMR_LAMBDA            = 0.7

# ── Cache ─────────────────────────────────────────────────
DEFAULT_TTL           = 3600
CACHE_KEY_PREFIX      = "rag_cache"

# ── Observability ─────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Tools ─────────────────────────────────────────────────
TOOL_WEB_SEARCH      = "web_search"
TOOL_PYTHON_EXECUTOR = "python_executor"
TOOL_DATABASE        = "database"

# ── File Paths ────────────────────────────────────────────
SAMPLE_DOCS_DIR  = "data/sample_docs"
PROCESSED_DIR    = "data/processed"
RAW_DIR          = "data/raw"
LOGS_DIR         = "logs"
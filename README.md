# 🤖 Agentic RAG System

> Production-ready Agentic AI system with advanced RAG, multi-agent orchestration,
> glassmorphism React UI, and full observability — powered by LLaMA 3.3 70B via Groq.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.25-green?style=flat-square)](https://langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4.1-purple?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2-blue?style=flat-square&logo=react)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## 🏗️ System Architecture

<img width="2811" height="2811" alt="Agentic RAG System Architecture" src="https://github.com/user-attachments/assets/1ae3686c-e98f-47d2-bbe9-4e8f3514121f" />

---

## 🖥️ Frontend Screenshots
<img width="1905" height="1021" alt="Screenshot 2026-03-19 111916" src="https://github.com/user-attachments/assets/13f56829-36c4-4fc0-9a76-950fa10cc407" />

-->

---

## 🎬 Demo Video

> 📹 Full demo video coming soon!

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 Multi-Agent System | Router, RAG, Reasoning, Python, Web Search agents |
| 📚 Advanced RAG | FAISS + BGE embeddings with MMR retrieval |
| 🔄 LangGraph Workflow | 8-node stateful pipeline with conditional routing |
| 💾 Dual Memory | Short-term (session) + Long-term (cross-session) SQLite |
| ⚡ Response Cache | MD5-keyed SQLite cache with TTL, 0ms on hits |
| 🛡️ Guardrails | Input/output validation and safety checks |
| ⚖️ LLM Judge | Automated evaluation scoring 0-10 on 4 criteria |
| 🔍 Observability | Full request tracing with span-level latency |
| 🎨 React UI | Dark glassmorphism interface with real-time metrics |
| 🌐 FastAPI | REST API with Swagger docs at /docs |
| 💻 CLI | Interactive terminal interface with Rich UI |
| 🐳 Docker | Containerized deployment ready |

---

## 🚀 Quick Start

### Backend Setup

#### 1. Clone and setup
```bash
git clone https://github.com/raneAshutoshDs21/agentic-rag-system.git
cd agentic-rag-system
```

#### 2. Create virtual environment
```bash
uv venv .venv
source .venv/Scripts/activate  # Windows Git Bash
source .venv/bin/activate       # Mac/Linux
```

#### 3. Install dependencies
```bash
uv pip install -r requirements.txt
```

#### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

#### 5. Ingest documents
```bash
python scripts/ingest_documents.py --dir data/raw
```

#### 6. Run full pipeline test
```bash
python scripts/run_full_pipeline.py
```

#### 7. Start API server
```bash
python run.py
```

---

### Frontend Setup

#### 1. Navigate to frontend
```bash
cd frontend
```

#### 2. Install dependencies
```bash
npm install
```

#### 3. Start development server
```bash
npm start
```

#### 4. Open browser
```
http://localhost:3000
```

> ⚠️ Make sure backend is running on port 8000 before starting frontend

---

## 💻 CLI Usage
```bash
# Interactive chat
python -m cli.main chat

# Single question
python -m cli.main ask "What is RAG?"

# Show system stats
python -m cli.main stats

# Ingest documents
python -m cli.main ingest data/raw

# Clear response cache
python -m cli.main clear-cache
```

---

## 📁 Project Structure
```
agentic-rag-system/
├── frontend/                     # React glassmorphism UI
│   ├── src/
│   │   ├── App.js                # Main app with session management
│   │   ├── index.js              # React entry point
│   │   ├── index.css             # Global styles and design system
│   │   ├── components/
│   │   │   ├── Sidebar.js        # Conversation history sidebar
│   │   │   ├── Message.js        # Message with badges and sources
│   │   │   ├── ChatInput.js      # Input with suggestion chips
│   │   │   ├── RightPanel.js     # Metrics, memory, ingest tabs
│   │   │   └── LoadingMessage.js # Animated 6-step loading
│   │   └── utils/
│   │       └── api.js            # FastAPI connection layer
│   └── package.json
│
├── config/                       # Settings and constants
│   ├── settings.py               # Pydantic settings from .env
│   └── constants.py              # System-wide constants
│
├── core/                         # Base classes and utilities
│   ├── base_agent.py             # Abstract agent class
│   ├── base_tool.py              # Abstract tool class
│   ├── base_retriever.py         # Abstract retriever class
│   ├── exceptions.py             # Custom exception hierarchy
│   └── logger.py                 # Centralized logging
│
├── agents/                       # All agent implementations
│   ├── router_agent.py           # LLM-based query router
│   ├── reasoning_agent.py        # Chain-of-thought reasoning
│   ├── rag_agent.py              # Knowledge base QA agent
│   └── orchestrator.py           # Master pipeline coordinator
│
├── rag/                          # RAG pipeline components
│   ├── retriever.py              # FAISS retriever with MMR
│   ├── reranker.py               # LLM-based reranker
│   ├── compressor.py             # Context compressor
│   └── pipeline.py               # Full RAG pipeline
│
├── tools/                        # Agent tools
│   ├── web_search.py             # Tavily web search
│   ├── python_executor.py        # Safe Python execution
│   └── database_tool.py          # SQLite CRUD operations
│
├── memory/                       # Memory system
│   ├── short_term.py             # Session-scoped memory
│   ├── long_term.py              # Cross-session memory
│   └── memory_manager.py         # Unified memory interface
│
├── evaluation/                   # Quality evaluation
│   ├── llm_judge.py              # LLM-as-a-judge scorer
│   ├── metrics.py                # Metrics tracker
│   └── evaluator.py              # Main evaluator
│
├── vectorstore/                  # Vector store
│   ├── embeddings.py             # BGE embedding manager
│   └── faiss_store.py            # FAISS index manager
│
├── database/                     # Database layer
│   ├── models.py                 # SQLAlchemy ORM models
│   └── sqlite_db.py              # Raw SQLite manager
│
├── graph/                        # LangGraph workflow
│   ├── state.py                  # AgentState TypedDict
│   ├── nodes.py                  # 8 pipeline nodes
│   └── workflow.py               # Graph compilation
│
├── prompts/                      # Prompt templates
│   ├── router_prompts.py
│   ├── reasoning_prompts.py
│   ├── rag_prompts.py
│   └── evaluation_prompts.py
│
├── guardrails/                   # Safety layer
│   ├── input_guard.py            # Input validation
│   └── output_guard.py           # Output validation
│
├── cache/                        # Caching layer
│   └── response_cache.py         # SQLite cache with TTL
│
├── observability/                # Monitoring
│   ├── tracer.py                 # Span-based tracer
│   └── metrics_collector.py      # System metrics
│
├── execution/                    # Execution utilities
│   └── retry_handler.py          # Tenacity retry logic
│
├── api/                          # FastAPI application
│   ├── main.py                   # App factory and lifespan
│   ├── routes/
│   │   ├── query.py              # Query and ingest routes
│   │   └── health.py             # Health and metrics routes
│   └── schemas/
│       └── request_response.py   # Pydantic schemas
│
├── cli/                          # CLI interface
│   └── main.py                   # Click commands
│
├── notebooks/                    # Development notebooks
│   └── 01_agentic_rag_prototype.ipynb
│
├── scripts/                      # Utility scripts
│   ├── ingest_documents.py       # Document ingestion pipeline
│   └── run_full_pipeline.py      # End-to-end test runner
│
├── tests/                        # Test suite
│   ├── test_rag.py               # RAG component tests
│   ├── test_agents.py            # Agent tests
│   ├── test_tools.py             # Tool tests
│   ├── test_memory.py            # Memory tests
│   └── test_evaluation.py        # Evaluation tests
│
├── data/                         # Data directory
│   ├── raw/                      # Source documents
│   ├── processed/                # FAISS index + SQLite DB
│   └── sample_docs/              # Sample documents
│
├── logs/                         # Application logs
├── run.py                        # API server entry point
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project configuration
├── .env.example                  # Environment template
└── README.md                     # This file
```

---

## 🔧 Tech Stack

| Component | Technology |
|---|---|
| LLM | Groq — LLaMA 3.3 70B (500+ tokens/sec) |
| Embeddings | BAAI/bge-small-en-v1.5 (local, 384 dims) |
| Vector DB | FAISS with MMR search |
| Framework | LangChain + LangGraph |
| Memory | SQLite (short + long term) |
| API | FastAPI + Uvicorn |
| Frontend | React 18 + Glassmorphism CSS |
| CLI | Click + Rich |
| Observability | Custom tracer + OpenTelemetry |
| Package Mgr | uv |
| Container | Docker |
| Cloud | Azure Container Apps |

---

## 🔄 Request Flow
```
User Query (UI / API / CLI)
        ↓
Input Guardrails (safety + sanitization)
        ↓
Response Cache (0ms if hit)
        ↓
Router Agent — LLaMA 3.3 70B decides:
        ↓
┌───────────────────────────────────┐
│  RAG Agent   │ Web Search │ Python │ Reasoning │
│  FAISS+BGE   │  Tavily    │  Exec  │  CoT      │
└───────────────────────────────────┘
        ↓
LangGraph Workflow (8 nodes)
        ↓
Output Guardrails (quality check)
        ↓
LLM Evaluation Judge (0-10 score)
        ↓
Save to Memory + Database + Cache
        ↓
Response with metadata
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Root info |
| GET | /health | Health check |
| GET | /health/metrics | System metrics |
| GET | /health/ready | Component readiness |
| POST | /query | Process a query |
| POST | /query/ingest | Ingest documents |
| GET | /query/history | Query history |
| GET | /docs | Swagger UI |

---

## 📊 Performance Results

| Metric | Value |
|---|---|
| Avg Quality Score | 8.8 / 10 |
| Cache Hit Latency | 0ms |
| Fresh Response Latency | ~1000ms |
| Unit Tests | 111 / 111 passing ✅ |
| Specialized Agents | 5 |
| LangGraph Nodes | 8 |
| Memory Layers | 3 (STM + LTM + Cache) |
| Vector Dimensions | 384 (BGE) |

---

## 📝 Environment Variables
```env
# LLM
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=1024

# Embeddings
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# Vector Store
FAISS_INDEX_PATH=data/processed/faiss_index

# Database
SQLITE_DB_PATH=data/processed/memory.db

# Tools
TAVILY_API_KEY=your_tavily_key
TAVILY_MAX_RESULTS=3

# Cache
CACHE_TTL=3600
CACHE_ENABLED=True

# Evaluation
EVAL_MIN_SCORE=6.0
EVAL_ENABLED=True

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
ENVIRONMENT=development
```

---

## 🧪 Running Tests
```bash
pytest tests/ -v
```

Expected output:
```
111 passed in 43.98s ✅
```

---

## 🐳 Docker
```bash
# Build and run everything
docker-compose up --build

# Backend API
http://localhost:8000

# Frontend UI
http://localhost:3000

# API Documentation
http://localhost:8000/docs
```

---

## 🙏 Acknowledgements

Built with:
- [Groq](https://groq.com) — Ultra-fast LLM inference
- [LangChain](https://langchain.com) — LLM orchestration framework
- [LangGraph](https://langchain-ai.github.io/langgraph) — Stateful agent workflows
- [FAISS](https://github.com/facebookresearch/faiss) — Vector similarity search
- [Tavily](https://tavily.com) — Real-time web search API
- [HuggingFace](https://huggingface.co) — BGE embedding models

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

<div align="center">
  <strong>Built with ❤️ by <a href="https://github.com/raneAshutoshDs21">Ashutosh Rane</a></strong>
  <br/><br/>
  <a href="https://github.com/raneAshutoshDs21/agentic-rag-system">⭐ Star this repo if you found it useful!</a>
</div>

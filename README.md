# 🤖 Agentic RAG System

Production-ready Agentic AI system using open-source models with
advanced RAG, tools, memory, evaluation, and observability.

---

## 🏗️ Architecture
```
User Query
    ↓
Input Guardrails
    ↓
Router Agent (LLM-based)
    ↓
┌───────────────────────────────────┐
│  RAG Agent   │ Web Search │ Python │
│  (FAISS+BGE) │  (Tavily)  │  Exec  │
└───────────────────────────────────┘
    ↓
Generator Node
    ↓
Output Guardrails
    ↓
LLM Evaluation (Judge)
    ↓
Cache + Memory Save
    ↓
Response
```

---

## 🚀 Quick Start

### 1. Clone and setup
```bash
git clone <your-repo>
cd agentic-rag-system
```

### 2. Create virtual environment
```bash
uv venv .venv
source .venv/Scripts/activate  # Windows Git Bash
source .venv/bin/activate       # Mac/Linux
```

### 3. Install dependencies
```bash
uv pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 5. Ingest documents
```bash
python scripts/ingest_documents.py --dir data/raw
```

### 6. Run full pipeline test
```bash
python scripts/run_full_pipeline.py
```

### 7. Start API server
```bash
python run.py
```

### 8. Use CLI
```bash
# Interactive chat
python -m cli.main chat

# Single question
python -m cli.main ask "What is RAG?"

# Show stats
python -m cli.main stats

# Ingest documents
python -m cli.main ingest data/raw
```

---

## 📁 Project Structure
```
agentic-rag-system/
├── config/          # Settings and constants
├── core/            # Base classes and utilities
├── agents/          # Router, RAG, Reasoning, Orchestrator
├── rag/             # Retriever, Reranker, Compressor, Pipeline
├── tools/           # Web search, Python executor, Database
├── memory/          # Short-term and long-term memory
├── evaluation/      # LLM judge and metrics
├── vectorstore/     # FAISS and embeddings
├── database/        # SQLite models and manager
├── graph/           # LangGraph state, nodes, workflow
├── prompts/         # All prompt templates
├── guardrails/      # Input and output validation
├── cache/           # Response cache
├── observability/   # Tracing and metrics
├── execution/       # Retry handler
├── api/             # FastAPI routes and schemas
├── cli/             # Command-line interface
├── notebooks/       # Jupyter prototype notebook
├── scripts/         # Ingestion and pipeline scripts
├── tests/           # Unit tests
└── data/            # Raw and processed data
```

---

## 🔧 Tech Stack

| Component    | Technology                    |
|-------------|-------------------------------|
| LLM         | Groq (LLaMA 3.3 70B)         |
| Embeddings  | BAAI/bge-small-en-v1.5 (local)|
| Vector DB   | FAISS                         |
| Framework   | LangChain + LangGraph         |
| Memory      | SQLite                        |
| API         | FastAPI                       |
| CLI         | Click + Rich                  |
| Observability| Custom tracer + OpenTelemetry |
| Package Mgr | uv                            |

---

## 🌐 API Endpoints

| Method | Endpoint        | Description              |
|--------|----------------|--------------------------|
| GET    | /               | Root info                |
| GET    | /health         | Health check             |
| GET    | /health/metrics | System metrics           |
| GET    | /health/ready   | Component readiness      |
| POST   | /query          | Process a query          |
| POST   | /query/ingest   | Ingest documents         |
| GET    | /query/history  | Query history            |
| GET    | /docs           | Swagger UI               |

---

## 📝 Environment Variables
```env
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.3-70b-versatile
TAVILY_API_KEY=your_key
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
FAISS_INDEX_PATH=data/processed/faiss_index
SQLITE_DB_PATH=data/processed/memory.db
LOG_LEVEL=INFO
ENVIRONMENT=development
```

---

## 🧪 Running Tests
```bash
pytest tests/ -v
```

---

## 📄 License

MIT License
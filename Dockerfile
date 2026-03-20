# ── Base image ────────────────────────────────────────────
FROM python:3.11-slim

# ── Set working directory ─────────────────────────────────
WORKDIR /app

# ── Install system dependencies ───────────────────────────
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Install uv ────────────────────────────────────────────
RUN pip install uv

# ── Copy requirements first (layer caching) ───────────────
COPY requirements.txt .

# ── Install Python dependencies ───────────────────────────
RUN uv pip install --system -r requirements.txt

# ── Copy project files ────────────────────────────────────
COPY . .

# ── Create necessary directories ──────────────────────────
RUN mkdir -p data/raw data/processed logs

# ── Expose API port ───────────────────────────────────────
EXPOSE 8000

# ── Start FastAPI server ──────────────────────────────────
CMD ["python", "run.py"]
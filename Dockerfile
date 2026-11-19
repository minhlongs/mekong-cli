FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and runtime engine package
COPY src/ ./src/
COPY engine/ ./engine/
COPY pyproject.toml ./

# Create persistent data directory for SQLite and Pilot A tenants
RUN mkdir -p /data/pilot_a_tenants
ENV MEKONG_PILOT_A_DB_DIR=/data/pilot_a_tenants

# Health check (Python gateway is now a local-dev / fallback target;
# production runs on Cloudflare Workers via packages/mekong-engine).
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.gateway:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

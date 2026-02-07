# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry or use pip with requirements.txt
# Since we have requirements.txt in root, let's copy that.
# Note: In docker-compose context, we will likely set context to root.
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runner
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime libs
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY api ./api
COPY .env .env

# Expose port
EXPOSE 8000

# Command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

---
name: Docker Compose Setup
description: Containerize applications with Docker Compose for multi-service development and deployment
author: Mekong CLI
tags: docker,devops,containers,compose,deployment
difficulty: intermediate
estimated_time: 25min
---

# Docker Compose Setup

Learn to containerize applications using Docker and orchestrate multi-service deployments with Docker Compose.

## Prerequisites

- Docker Desktop installed (or Docker Engine + Compose)
- Basic command line knowledge
- Understanding of containers concepts

## Step 1: Project Setup

```bash
# Create project directory
mkdir docker-compose-app && cd docker-compose-app

# Create directory structure
mkdir -p src nginx db
```

## Step 2: Create Dockerfile for API

Create `src/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `src/requirements.txt`:

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
psycopg2-binary>=2.9.0
```

Create `src/main.py`:

```python
from fastapi import FastAPI
import os

app = FastAPI(title="Docker Compose Demo")

@app.get("/")
def read_root():
    return {"message": "Hello from Docker Compose!", "service": os.getenv("SERVICE_NAME", "api")}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

## Step 3: Create Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /health {
            proxy_pass http://api/health;
        }
    }
}
```

Create `nginx/Dockerfile`:

```dockerfile
FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## Step 4: Create PostgreSQL Setup

Create `db/init.sql`:

```sql
-- Initialize database
CREATE DATABASE IF NOT EXISTS app_db;

-- Create user
CREATE USER app_user WITH PASSWORD 'app_password';
GRANT ALL PRIVILEGES ON DATABASE app_db TO app_user;

-- Create sample table
\c app_db;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (username, email) VALUES
    ('admin', 'admin@example.com'),
    ('user1', 'user1@example.com'),
    ('user2', 'user2@example.com');
```

## Step 5: Create Docker Compose File

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - api
    networks:
      - app-network
    restart: unless-stopped

  # FastAPI Application
  api:
    build:
      context: ./src
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://app_user:app_password@db:5432/app_db
      - SERVICE_NAME=fastapi-app
    depends_on:
      - db
    networks:
      - app-network
    restart: unless-stopped
    volumes:
      - ./src:/app  # Hot reload for development
    command: >
      sh -c "pip install -r requirements.txt &&
             uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=app_user
      - POSTGRES_PASSWORD=app_password
      - POSTGRES_DB=app_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d app_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache (optional)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network
    restart: unless-stopped
    volumes:
      - redis_data:/data

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

## Step 6: Create .dockerignore

Create `src/.dockerignore`:

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.venv/
venv/
.git
.gitignore
.dockerignore
Dockerfile
*.md
.pytest_cache/
.coverage
htmlcov/
```

## Step 7: Docker Compose Commands

```bash
# Start all services (detached mode)
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs -f api  # Specific service

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build

# Run one-off command
docker-compose run api python main.py

# Scale services
docker-compose up -d --scale api=3

# View running containers
docker-compose ps

# Execute command in running container
docker-compose exec api bash
docker-compose exec db psql -U app_user -d app_db
```

## Step 8: Create Tests

Create `test_api.py`:

```python
import requests
import pytest

BASE_URL = "http://localhost"

def test_root_endpoint():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Docker Compose" in data["message"]

def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_nginx_proxy():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
```

## Step 9: Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: always

  api:
    build:
      context: ./src
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
```

## Verification Criteria

- [ ] All services start without errors
- [ ] Nginx proxies requests to API
- [ ] Database initializes correctly
- [ ] Health endpoints respond
- [ ] Data persists after restart

## Next Steps

- Add SSL/TLS with Let's Encrypt
- Configure log aggregation
- Add monitoring with Prometheus/Grafana
- Set up CI/CD pipeline
- Add secrets management

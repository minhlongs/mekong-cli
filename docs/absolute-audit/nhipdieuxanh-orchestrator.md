# Subsystem Audit: apps/nhipdieuxanh-orchestrator

## 1. Purpose
- **Business Role**: Coordinates and operates the deployment, integration, and monitoring of 20 modules within the **Nhịp Điệu Xanh** Proptech ecosystem, targeting the Can Tho real estate market.
- **Technical Role**: Serves as the central repository for Infrastructure as Code (IaC), API gateway routing, end-to-end integration tests, load tests, and system-wide monitoring configurations.

## 2. Entry Points
- **Local Development**: `docker-compose.yml` launches the entire stack (Gateway, Frontend, Backend, AI, Database, Kafka, Zookeeper, Local Blockchain, Prometheus, Grafana).
- **Production Deployment**: Kubernetes Helm Chart under `helm/nhipdieuxanh` (`values.yaml`, `Chart.yaml`, templates).
- **FastAPI AI Microservice**: `mock-services/ai-service/main.py`.
- **E2E Testing**: Playwright test suite `tests/e2e/lead-flow.spec.ts`.
- **Performance Load Testing**: k6 load test script `tests/performance/load-test.js`.

## 3. Runtime Lifecycle
- **Initialization**:
  1. Local: Docker Compose mounts volumes and brings up containers.
  2. Nginx API Gateway establishes routing and proxy rules.
  3. AI service FastAPI spins up, establishing database connectivity and launching a background asynchronous Kafka consumer loop.
- **Event-Driven Lead Processing**:
  1. API Gateway routes `/api/leads` traffic to Backend.
  2. Backend inserts the lead into PostgreSQL and publishes a `lead` created event on Kafka's `nhipdieuxanh-leads` topic.
  3. AI microservice Kafka consumer detects the event, performs heuristic analysis, and updates the SQL database (`leads` table).
- **Observability & Monitoring**: Prometheus scrapes metrics every 15 seconds from registered service endpoints; Promtail forwards container logs to Loki.

## 4. State Management
- **Relational Data**: PostgreSQL database (`nhipdieuxanh_db`), persistable via Docker volume `pgdata`.
- **Event Bus Stream**: Apache Kafka events.
- **RAG Content**: SQLite database (`~/.mekong/ask/ask.db`) containing text chunks and vectors.
- **Ledger/DAO state**: Local Geth private node database (`ndx-blockchain` container).

## 5. Dependencies
- **Internal Sibling Workspaces**: `../nhipdieuxanh` (Next.js frontend and Node.js backend).
- **External Libraries**: `fastapi`, `uvicorn`, `pydantic`, `aiokafka`, `asyncpg`, `numpy` (Python AI Service); Nginx, Postgres, Kafka/Zookeeper, Geth (Docker/Helm); Playwright (E2E); k6 (load tests).

## 6. Failure Modes
- **Kafka Unavailability**: The AI service's background consumer fails to connect on startup. It retries 10 times and then exits, leaving the consumer inactive.
- **Database Connection Failure**: Relational database downtime or connection pool exhaustion.
- **SQLite FTS5 Support Gaps**: The trigram retriever falls back to dense-only or throws if sqlite3 does not support FTS5 virtual tables.
- **Local LLM Endpoint Offline**: Fallback to remote OpenAI API fails if no `OPENAI_API_KEY` is set.

## 7. Recovery Behavior
- **Nginx Gateways**: Returns Nginx custom `50x.html` error pages.
- **AI Service Fallbacks**: If the local LLM completions endpoint (`localhost:11437`) fails, it attempts the remote OpenAI API. If that fails too, it falls back to a heuristic regex/snippet generator from the SQL retrieved chunks.
- **Retry Mechanism**: Kafka connection loop attempts 10 connections separated by 3 seconds.

## 8. Scale Limits
- **Nginx connections**: The API Gateway is configured with `worker_connections 1024`, limiting concurrent traffic handling.
- **No Read Replicas**: The PostgreSQL service runs on a single main instance.
- **AI Service Bottleneck**: `values.yaml` specifies `replicaCount.ai: 1` by default.

## 9. Security Surface
- **Exposed Ports**: Gateway (80), Postgres (5432) on localhost, Blockchain RPC (8545/8546) on localhost.
- **Weak Default Credentials**: `postgres/postgres` for database user/pass.
- **Secrets Leaks**: Hardcoded SMTP password placeholder (`secret_password_here`) in `alertmanager.yml`.

## 10. Observability
- **Prometheus Scrapes**: Configured for `nginx-gateway`, `nextjs-frontend`, `nodejs-backend`, `fastapi-ai`.
- **Log Aggregation**: Promtail scraper configured for `/var/run/docker.sock` and Nginx log files.
- **Alertmanager**: Routes Slack webhooks and email alerts for critical alerts.

## 11. Technical Debt
- **DRY Violation**: Sentiment analysis heuristics and classification logic are duplicated in both `main.py` (FastAPI route) and the async event processor (`process_lead_event`).
- **No Unit Tests**: The AI service python codebase does not include unit/integration tests.
- **Placeholder Values**: Webhooks and mail server setups contain template/fake values.

## 12. Missing Knowledge
- **Blockchain Integration**: A Geth development node is containerized, but details on how the backend writes synchronized events to the ledger are missing.

# Security & Reliability Gap Analysis & Remediation Roadmap

This report consolidates security and reliability gaps discovered across the `mekong-cli` codebase, categorized by severity, along with actionable remediation roadmaps.

---

## 1. Risk Categorization and Findings

### 🔴 P0 — Existential Risks
Existential risks represent critical vulnerabilities that directly threaten data integrity, compliance (Decree 13/2023/NĐ-CP), or service survival through resource leaks and access control failures.

#### Gap P0.1: Python SQLite Connection Leaks
- **Location**: `src/raas/tenant.py` (Lines 94-234) and `src/raas/credits.py` (Lines 231-265).
- **Finding**: The `with self._connect() as conn:` block handles transactions but does not close the connection. File descriptors grow linearly with each connection made, eventually causing file descriptor exhaustion, locking the database, and crashing the backend under load.
- **Remediation**: Use a context manager that guarantees `conn.close()` is called in a `finally` block (similar to the pattern used in `packages/agent-core/src/agent_core/memory.py`).

#### Gap P0.2: Broken Access Control (Public Leads API & Updates)
- **Location**: `apps/nhipdieuxanh/app/api/leads/route.ts` and `apps/nhipdieuxanh/app/api/leads/update-status/route.ts`.
- **Finding**: The endpoints `GET /api/leads` and `POST/PATCH /api/leads/update-status` are completely public. Anyone can query all lead details in plaintext (names, emails, phone numbers for consenting leads) or mutate pipeline statuses to `'won'` without credentials.
- **Remediation**: Implement a robust session/token check (e.g., JWT verification or auth middleware) on all sensitive backend API endpoints.

#### Gap P0.3: Decree 13 PII Plaintext Exposure & Leakage
- **Location**: PostgreSQL `Lead` schema (`schema.prisma`), Kafka event payload (`leads/route.ts`), AI service stdout logs (`main.py`).
- **Finding**: 
  1. Consenting leads have their Name, Phone, and Email stored in plaintext, presenting a data leak risk.
  2. Kafka messages carry plaintext PII without transit encryption.
  3. AI service consumer logs the entire Kafka payload containing plaintext PII directly to console stdout (`print(f"Received event: {event}")`).
  4. There is no API route/mechanism to process consent revocation requests.
- **Remediation**:
  - Implement application-level AES-256 field encryption for `name`, `phone`, and `email` columns in PostgreSQL.
  - Sanitize stdout logging to strip or mask PII fields.
  - Secure Kafka brokers via TLS/SASL.
  - Implement a `/api/leads/revoke-consent` route to erase or anonymize PII records upon request.

#### Gap P0.4: Hardcoded Active Credentials & Keys
- **Location**: Root `.env` and `apps/nhipdieuxanh-orchestrator/helm/nhipdieuxanh/values.yaml`.
- **Finding**: Active third-party tokens `POLAR_API_KEY` and `POLAR_WEBHOOK_SECRET` are checked into `.env`. Default production database passwords (`postgres/postgres`) are hardcoded in the Helm values configuration.
- **Remediation**: Remove sensitive keys from git immediately. Transition Helm configuration to resolve secrets via Kubernetes Secrets or external secret engines (e.g., Vault, AWS Secrets Manager).

---

### 🟡 P1 — Scale Blockers
Scale blockers prevent the monorepo from handling real-world production concurrency or 10x traffic bursts.

#### Gap P1.1: Gateway Connection Limits
- **Location**: API Gateway Nginx configuration (`apps/nhipdieuxanh-orchestrator`).
- **Finding**: `worker_connections` is capped at `1024`. Highly concurrent client and webhook spikes will exceed this limit, leading to dropped gateway requests.
- **Remediation**: Boost `worker_connections` to at least `4096` or `8192` in Nginx, and optimize system `ulimit` settings.

#### Gap P1.2: Synchronous JS Loops in Cosine Similarity
- **Location**: `packages/ask-core/src/retriever.ts` (Lines 117-128).
- **Finding**: RAG dense searches load all vector records into memory and compute cosine similarity synchronously in a JS loop. This blocks the single-threaded Node/Bun event loop during large index queries.
- **Remediation**: Migrate to a native vector search solution (e.g. SQLite extension `sqlite-vec` or PgVector for Postgres).

#### Gap P1.3: Dynamic DDL Statements Locking Database Reads
- **Location**: `apps/nhipdieuxanh-orchestrator/mock-services/ai-service/retriever.py`.
- **Finding**: `init_db()` runs schema migration DDL queries (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`) for *every search request*. This acquires exclusive database write locks, causing concurrent searches to fail with `sqlite3.OperationalError: database is locked`.
- **Remediation**: Execute schema initialization once on startup, rather than during the request lifecycle.

#### Gap P1.4: Non-Pooled Connection Exhaustion (FastAPI Kafka Consumer)
- **Location**: `apps/nhipdieuxanh-orchestrator/mock-services/ai-service/main.py`.
- **Finding**: The consumer establishes a raw TCP connection (`asyncpg.connect`) to PostgreSQL for every message processed and immediately closes it. Under high load, this causes TCP socket exhaustion.
- **Remediation**: Initialize an `asyncpg.create_pool` database connection pool once at startup and reuse connection instances from the pool.

---

### 🔵 P2 — Velocity Killers
Velocity killers are issues that slow down development cycles, cause regressions, or lead to hard-to-debug behaviors.

#### Gap P2.1: Code Duplication in AI Service Heuristics
- **Location**: `apps/nhipdieuxanh-orchestrator/mock-services/ai-service/main.py`.
- **Finding**: Sentiment analysis logic and persona heuristics are duplicated between the FastAPI REST route and the async Kafka consumer handler `process_lead_event`.
- **Remediation**: Extract classification logic into a shared helper module in the AI service.

#### Gap P2.2: Lack of Python Unit Testing
- **Location**: `apps/nhipdieuxanh-orchestrator/mock-services/ai-service/`.
- **Finding**: The AI service contains zero unit or integration tests, risking regression on code updates.
- **Remediation**: Introduce a test suite using `pytest` and mock external Kafka/Postgre services.

#### Gap P2.3: Unauthenticated Route Changes
- **Location**: Next.js pipeline navigation and page transitions.
- **Finding**: Users can transition routes or toggle view states on CRM boards without verification checks, allowing clients to access restricted UI flows.
- **Remediation**: Add client-side route guards and server-side middleware validation.

#### Gap P2.4: Lack of Transaction Hash Tracking for Blockchain Notarization
- **Location**: `apps/nhipdieuxanh/app/api/leads/route.ts` (Lines 245-249).
- **Finding**: The returned transaction hash `txHash` from geth notarization is printed to stdout but never saved to PostgreSQL. If proof is needed, it cannot be verified, violating the audit integrity of the system.
- **Remediation**: Add a `blockchainTxHash` string field to the Prisma Lead schema and update it once Geth returns success.

---

### 🟢 P3 — Optimization
Optimization issues represent minor technical debt and configuration rigidities.

#### Gap P3.1: Unused Packages/Dependencies
- **Location**: `packages/ask-core/package.json`.
- **Finding**: `zod` is declared in dependencies but never used in `@mekong/ask-core`.
- **Remediation**: Remove `zod` from `package.json` to keep build artifacts lightweight.

#### Gap P3.2: Configuration Endpoint Rigidity
- **Location**: `main.py`, `retriever.py`, and `blockchain.ts`.
- **Finding**: AI completions (`localhost:11437`) and Geth RPC endpoints (`blockchain-node:8545`) are hardcoded, preventing easy port changes.
- **Remediation**: Load these connection parameters from environment variables (e.g. `BLOCKCHAIN_RPC_URL`, `OLLAMA_API_URL`).

---

## 2. Remediation Roadmap

The following schedule breaks down implementation phases for resolving these findings:

| Phase | Priority | Gaps Covered | Focus Area |
|---|---|---|---|
| **Phase 1** | **Immediate** | P0.1, P0.2, P0.4 | **Critical Security & Connection Fixes**: Close leaks, secure APIs, remove secrets |
| **Phase 2** | **Short-term** | P0.3, P1.3, P1.4 | **Decree 13 Compliance & Concurrency**: Cryptography layer, pool db connections, decouple DDL migrations |
| **Phase 3** | **Medium-term**| P1.2, P2.4, P3.2 | **Scaling & Traceability**: PgVector integration, blockchain Tx tracking, configure endpoints dynamically |
| **Phase 4** | **Long-term** | P2.1, P2.2, P3.1 | **Clean Code & Testing**: Deduplicate scripts, set up pytest suites, clean dependencies |

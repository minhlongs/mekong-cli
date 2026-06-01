# Handoff Report — Subsystem Analysis

## 1. Observation
The following file paths, code blocks, and execution results were observed during investigation:
- **`packages/ask-core/package.json`**: Explicitly configures `"main": "./src/index.ts"` (Line 6) and `"test": "bun test"` (Line 9).
- **`packages/ask-core/src/db.ts`**: SQLite schema and FTS5 virtual table initialization (Lines 55-93):
  ```typescript
  CREATE TABLE IF NOT EXISTS chunks (...);
  CREATE VIRTUAL TABLE IF NOT EXISTS fts_index USING fts5(...);
  CREATE TABLE IF NOT EXISTS chunk_vectors (...);
  ```
- **`packages/ask-core/src/retriever.ts`**: In-memory dense similarity computation (Lines 117-128) pulling all vectors via `db.getAllVectors()`, and Reciprocal Rank Fusion (Lines 130-149) using `k = 60`.
- **`apps/nhipdieuxanh/package.json`**: Shows mekong workspace reference `"@mekong/ask-core": "workspace:*"` (Line 16) and test script `"test": "vitest run"` (Line 10).
- **`apps/nhipdieuxanh/lib/prisma.ts`**: Implements `$transactionWithRetry` (Lines 47-89) wrapping transient code checking (Line 11: `['P2034', 'P2028', 'P1001', 'P1008', 'P1017']`) and using random jitter backoff.
- **`apps/nhipdieuxanh/app/api/leads/route.ts`**: dynamic lead scoring logic (Lines 80-138) grading leads, Decree 13 PII masking (Lines 172-183) overriding values if `consent === false`, and manual duplicate updates (Lines 185-228).
- **`apps/nhipdieuxanh/app/api/payments/sepay/route.ts`**: payment webhook logic using `crypto.timingSafeEqual` in `timingSafeCompare` (Lines 28-36), checking webhook signature headers (Lines 63-91), checking amount matches 10,000,000 VND (Lines 115-121), and updating lead status to `won`.
- **`apps/nhipdieuxanh/app/api/faq/query/route.ts`**: require override hook (Lines 7-17) overriding Node's global `require` to return `tests/bun-sqlite-mock` when requesting `bun:sqlite`. The SQLite connection is closed in the `finally` block (Lines 183-191).
- **Tests Execution**:
  - `bun test` inside `packages/ask-core` successfully ran 12 tests across 4 files.
  - `pnpm test` inside `apps/nhipdieuxanh` successfully ran 35 tests across 4 files.

## 2. Logic Chain
- **LC-1**: By checking `packages/ask-core/package.json` and `src/index.ts`, we see that the package is designed as a TypeScript module exposing retrieval services (`AskRetriever`, `AskDatabase`).
- **LC-2**: Examining `packages/ask-core/src/retriever.ts` reveals that dense vector similarity checks iterate over all vectors from the database synchronously. Under 10x load, this causes a major CPU/memory bottleneck scaling at $O(N)$ where $N$ is the total chunks.
- **LC-3**: Investigating `apps/nhipdieuxanh/app/api/faq/query/route.ts` shows the require override which hooks module loading. This indicates a high level of coupling to the Bun runtime that had to be polyfilled to work inside Node.js (which runs Next.js server actions).
- **LC-4**: Observing `apps/nhipdieuxanh/lib/prisma.ts` indicates transient database failures are handled cleanly using custom middleware retries, which improves reliability under high concurrency.
- **LC-5**: Reading `apps/nhipdieuxanh/app/api/payments/sepay/route.ts` shows strict validation of amount (10M VND) and transfer type, coupled with timing safe compares, mitigating transaction spoofing and timing attacks.

## 3. Caveats
- The external API endpoints (e.g. `MODEL_SERVER_URL` chat completions, Geth JSON-RPC node accounts) are mocked/simulated in test environments; actual network latency or gateway timeouts could diverge from local test behaviors.
- Evaluated performance of the trigram hashing fallback under large datasets has not been analyzed.

## 4. Conclusion
- **`packages/ask-core`** is a functional document search & RAG indexer engine that works natively in Bun. Its main structural bottleneck is the in-memory cosine similarity loop. It should be refactored to use native database vector indices (like `sqlite-vec`).
- **`apps/nhipdieuxanh`** is a feature-rich Next.js real-estate landing page and CRM backend. It includes robust security (timing safe compares, strict webhook amounts, PII masking under Decree 13) and recovery patterns (Prisma transaction retries). However, it relies on a global `require` override hook to run Bun dependencies in Node, which poses a reliability concern.

## 5. Verification Method
- **`packages/ask-core` Unit Tests**:
  - Command: `bun test` in `/Users/macbook/mekong-cli/packages/ask-core`.
  - Verification: 12 tests pass successfully.
- **`apps/nhipdieuxanh` Integration Tests**:
  - Command: `pnpm test` in `/Users/macbook/mekong-cli/apps/nhipdieuxanh`.
  - Verification: 35 tests pass successfully.
- **Invalidation Condition**: If the database schema changes without running Prisma generate (`prisma generate`), the integration tests will fail due to missing TypeScript types.

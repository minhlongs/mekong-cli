# Subsystem Audit: apps/nhipdieuxanh

## 1. Purpose
- **Business Role**: Landing page and AI-powered CRM for the "Nhịp Điệu Xanh" (Green Rhythm) eco-residential development in Cái Răng, Cần Thơ. Governs lead registration, dynamic lead scoring, buyer segmentation, Decree 13/2023/NĐ-CP compliance for PII data masking, automated real estate social media marketing generator, RAG legal FAQ assistant, and deposit payment notarization.
- **Technical Role**: Next.js App Router application connecting to PostgreSQL (via Prisma client), Kafka (kafkajs) for message queuing, Geth blockchain nodes via JSON-RPC, and utilizing `@mekong/ask-core` for vector searching.

## 2. Entry Points
- **Client Pages**: Home Page (`app/page.tsx`) and CRM Kanban board (`app/pipeline/page.tsx` with dynamic hydration `ssr: false`).
- **REST APIs**:
  - `/api/leads` (POST/GET) - lead ingestion and retrieval.
  - `/api/leads/status` (GET) - PII-protected status checking.
  - `/api/leads/update-status` (POST/PATCH) - pipeline status modification.
  - `/api/payments/sepay` (POST) - payment webhook.
  - `/api/posts` (POST) - local LLM social post creator.
  - `/api/faq/query` (POST) - legal/FAQ RAG query processor.
- **Verification Scripts**: `scripts/verify_leads.ts`.
- **Integration Tests**: `tests/crm.test.ts`, `tests/sepay.test.ts`, `tests/prisma-retry.test.ts`, `tests/stress.test.ts` (Vitest-based).

## 3. Runtime Lifecycle
- **Lead Ingestion Flow (`/api/leads` POST at `app/api/leads/route.ts:57`)**:
  1. Validation: Inspects mandatory fields and Vietnamese phone formats (`/^(0|84|\+84)[3-9][0-9]{8}$/`).
  2. Scoring: Dynamically grades lead quality (Phone validation: +20, valid email: +10, Cái Răng area: +30, Mekong area: +20, investor intent keywords: +10, budget >= 2 billion: +10). Allocates level: Hot (score >= 70), Warm (score >= 40), Cold (score < 40).
  3. Segmentation: Identifies buyer personas based on keywords ("Phụ huynh học sinh", "Nhà đầu tư", "Người mua nhà định cư").
  4. Compliance Checks (Decree 13): If `consent === false`, masks Name, Phone, and Email using asterisk masking (e.g. `TEST_LEAD` -> `T*** L***`), and assigns a random UUID as `leadHash`. If `consent === true`, hashes the phone number (SHA-256) as `leadHash`.
  5. DB Upsert: Checks duplicates (only if consent granted). Inserts or updates Lead status.
  6. Event Dispatch: Dispatches non-blocking Kafka event (`lead_ingested`) to the topic `nhipdieuxanh-leads`.
  7. Blockchain Notarization: If consent is true, asynchronously sends JSON-RPC transaction to Geth node.
- **Deposit Payment Flow**:
  1. User registers successfully, receiving a booking modal with MB Bank transfer details, amount `10,000,000` VND, memo `NDX<leadId>`, and a polling script checking `/api/leads/status?id=<leadId>` every 3s.
  2. The webhook `/api/payments/sepay` POST catches transaction alerts from SePay.
  3. Signature validation (HMAC SHA-256) checks matching headers via `timingSafeCompare` to prevent timing attacks.
  4. Webhook strictly enforces: `transferType === 'in'` and amount is exactly `10,000,000` VND.
  5. Extracts lead ID matching `NDX-<uuid>` (formatted with or without hyphens).
  6. Idempotency: Returns success if lead is already `won`. Updates lead status to `won` in PostgreSQL.
  7. Polling script detects status transition, closing the modal.
- **RAG FAQ Assistant Flow (`/api/faq/query` POST at `app/api/faq/query/route.ts:111`)**:
  1. Client sends a question.
  2. The Node.js require polyfill runs at startup to dynamically intercept `bun:sqlite` and return a mock wrapping `better-sqlite3` or a dummy fallback database.
  3. RAG Search: Queries `@mekong/ask-core` retriever. If matching chunks exist, returns compiled responses and citations.
  4. Keyword Fallback: Scans predefined static `faqDatabase` based on keyword occurrences.
  5. Mail Notification Alert: If no keywords match, calls `triggerEmailMockAlert` and returns a default fallback.

## 4. State Management
- **Database**: PostgreSQL (Prisma Client).
- **Messaging State**: Dispatched out to Kafka.
- **Client Board State**: React Context (`PipelineProvider` at `app/pipeline/context.tsx`). Drag-and-drop operations trigger optimistic column updates on the card, with automated rollback to the database state on HTTP request rejections.

## 5. Dependencies
- **Internal**: `@mekong/ask-core` (Workspace reference).
- **External**: `next`, `react`, `react-dom`, `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`, `@prisma/client`, `kafkajs`, `lucide-react`.
- **Dev**: `prisma`, `vitest`, `eslint`, `tailwindcss`, `@tailwindcss/postcss`.

## 6. Failure Modes
- **Kafka Outage**: Lead ingestion logs Kafka warnings but runs without failing.
- **Geth Notarization Outage**: RPC connection error triggers warning logs, returns null, but lets API complete.
- **Postgres Pool Saturation**: Dynamic transactions can exhaust pool connections under high load.
- **No SQLite Mock Library**: In Node environments where `better-sqlite3` is absent, the require polyfill reverts to a dummy mock that returns empty results, breaking RAG searches silently.
- **SePay Amount/Type Mismatch**: Webhook ignores incorrect amounts (non 10M VND) or non-incoming transactions.

## 7. Recovery Behavior
- **Prisma Retry Policy (`lib/prisma.ts:47`)**: Overrides `$transaction` with `$transactionWithRetry`. Automatically detects transient SQL errors (codes `P2034`, `P2028`, `P1001`, `P1008`, `P1017` or messages like `deadlock`, `write conflict`, `timeout`) and retries up to 5 times using exponential backoff with random jitter.
- **Non-blocking Operations**: Async calls (`publishLeadEvent`, `notarizeLeadOnBlockchain`) are isolated inside catch blocks to prevent REST failures.
- **Bank-Friendly Webhook Handlers**: Webhooks catch errors and return HTTP 200 with `{ success: false }` for business logic issues, preventing the gateway from spamming retry requests.

## 8. Scale Limits
- **Connection Pool Exhaustion**: High concurrent REST requests can exhaust Postgres connection limits if PgBouncer is omitted.
- **Single-Host Kafka Producer**: A single producer checks `isConnected = false` on every request. High concurrent triggers can cause racing connect requests or timeout errors.
- **Thread Blocking Polyfill**: The synchronous Node polyfill hijack blocks module caching during load.

## 9. Security Surface
- **Exposed APIs**: Leads, Status, Update-Status, Webhook, Chat Completions, FAQ RAG.
- **Decree 13 Compliance**: Restricts PII leaks. GET `/api/leads/status` strictly queries and returns `{ status: lead.status }` without checking/leaking patient names, phones, or emails. Consent bypass sanitizes values before database insertions.
- **Timing attack defenses**: `timingSafeCompare` is explicitly used for webhook validation.
- **Signature Bypass**: Allowed in non-production environments when webhook secret is set to `insecure_dev`. Strictly blocked in production.

## 10. Observability
- **Gaps**: Lacks centralized APM tools (e.g. OpenTelemetry, Jaeger, Prometheus). All diagnostics depend on raw `console.warn` and `console.error` logs.

## 11. Technical Debt
- **Require Hijacking Polyfill**: Overriding standard module requirements is risky and violates framework guidelines.
- **Dev/Prod Configuration Mismatch**: Dev utilizes SQLite mocks while Prod relies on PostgreSQL and Kafka, increasing staging integration drift risks.
- **Mock Geth Accounts**: Relies on a dev node having unlocked accounts without credentials.

## 12. Missing Knowledge
- Why lead notarizations are persisted to a Geth block instead of standard immutable DB hashes remains unstated.
- No transaction log outbox is provided to guarantee event delivery if Kafka is offline.

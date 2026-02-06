# Project Overview & Product Development Requirements (PDR)

**Version:** 2.0.0
**Derived From:** `MASTER_PRD.md`

## 1. Project Overview
**AgencyOS (Mekong CLI)** is a Robot-as-a-Service (RaaS) platform designed to transform the agency model from service-based to outcome-based. It employs a Hub-and-Spoke architecture to orchestrate AI agents that deliver tangible results (leads, content, reports) rather than just tools.

### Core Philosophy
> "We don't sell tools. We sell Deliverables."

### Key Components
1.  **Money Layer (Spoke 1)**: A Next.js web platform for non-technical agency owners to purchase credits and order results.
2.  **Viral Layer (Spoke 2)**: An Open Source Developer Kit (CLI + Recipes) for developers to build and share agent workflows.
3.  **Engine Layer (Hub)**: The centralized backend infrastructure (OpenClaw, BullMQ, PostgreSQL) that orchestrates the execution of tasks.

## 2. Product Development Requirements (PDR)

### 2.1 Functional Requirements

#### A. Authentication & User Management
- **FR-AUTH-01**: System must support API Key authentication for the CLI.
- **FR-AUTH-02**: Web platform must support user signup/login via Supabase Auth.
- **FR-AUTH-03**: Users must have a credit balance (AgencyCoin).

#### B. Job Execution (Engine)
- **FR-JOB-01**: System must accept job requests via REST API (`POST /v1/chat/completions`).
- **FR-JOB-02**: Jobs must be validated against defined schemas (Zod).
- **FR-JOB-03**: Jobs must be persisted to the database before queuing (Reliability).
- **FR-JOB-04**: Jobs must be executed asynchronously via a worker queue (Redis/BullMQ).
- **FR-JOB-05**: System must support "Compensation Transactions" to handle failures gracefully.
- **FR-JOB-06**: System must handle concurrency issues (SQLite busy states) with retry logic.

#### C. CLI & Recipes
- **FR-CLI-01**: CLI must allow users to list, search, and run recipes.
- **FR-CLI-02**: Recipes must be defined in a standard format (Markdown/JSON).
- **FR-CLI-03**: CLI must provide an interactive UI for module selection.

### 2.2 Non-Functional Requirements

#### A. Performance
- **NFR-PERF-01**: API response time for job submission < 200ms.
- **NFR-PERF-02**: Worker must process jobs within 5 seconds of queuing (assuming available capacity).

#### B. Reliability & Resilience
- **NFR-REL-01**: System must implement retry logic for transient failures (e.g., DB locks).
- **NFR-REL-02**: System must clean up "Zombie Jobs" (stuck in PROCESSING) on startup.
- **NFR-REL-03**: Critical data (credits, job status) must be stored in a durable database (PostgreSQL in Prod).

#### C. Scalability
- **NFR-SCALE-01**: Architecture must support horizontal scaling of Worker nodes.
- **NFR-SCALE-02**: Queue system must handle high throughput without data loss.

#### D. Security
- **NFR-SEC-01**: API Keys must be rotated and secured.
- **NFR-SEC-02**: Database access must be restricted to internal services.
- **NFR-SEC-03**: Inputs must be sanitized to prevent injection attacks.

## 3. Architecture Summary
- **Frontend**: Next.js 14, Tailwind CSS.
- **Backend API**: Node.js, Fastify.
- **Worker**: Node.js, BullMQ.
- **Database**: PostgreSQL (Prod), SQLite (Dev).
- **Queue**: Redis.
- **Gateway**: Cloudflare Workers.

## 4. Success Metrics
- **Stability**: Zero "Ghost Jobs" (jobs lost in transit).
- **Availability**: 99.9% uptime for the Engine API.
- **Performance**: Average job turnaround time < target SLA per recipe type.

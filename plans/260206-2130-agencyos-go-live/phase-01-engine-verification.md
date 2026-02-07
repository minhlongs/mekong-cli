# Phase 1: Engine Verification

## Context
The Engine layer is the core processing unit. We need to verify that the API correctly queues jobs and the Worker correctly processes them, updating the database state at each step.

## Verification Checklist

### 1. Infrastructure Setup
- [ ] Ensure `infrastructure/docker-compose.yml` is valid.
- [ ] Start services: `docker-compose up -d redis postgres`.
- [ ] Run Prisma migrations: `cd apps/engine && npx prisma db push`.

### 2. Service Startup
- [ ] Start Engine API: `cd apps/engine && npm run dev`.
- [ ] Start Worker: `cd apps/worker && npm run dev`.
- [ ] Verify both connect to Redis successfully (check logs for "🚀 Job Queue initialized").

### 3. Job Flow Verification
- [ ] **Step 1: Submit Job**
    - Send POST to `http://localhost:3000/v1/chat/completions`.
    - Payload: `{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}`.
    - Expected: HTTP 200, JSON response with `id` and `status: queued`.
- [ ] **Step 2: Database Check (Queued)**
    - Query Postgres: `SELECT * FROM "Job" WHERE id = <id>`.
    - Verify `status` is `QUEUED`.
- [ ] **Step 3: Worker Pickup**
    - Check Worker logs: "📥 Processing job <id>".
    - Verify Worker updates DB `status` to `PROCESSING`.
- [ ] **Step 4: Completion**
    - Check Worker logs: "✅ Job <id> completed".
    - Query Postgres: Verify `status` is `COMPLETED` and `output` contains result.
- [ ] **Step 5: API Retrieval**
    - GET `http://localhost:3000/v1/jobs/<id>`.
    - Expected: JSON response with `status: completed` and `result`.

## Failure Scenarios
- [ ] **Redis Down:** Verify API handles queue failure gracefully (DB rollback or error).
- [ ] **Worker Crash:** Verify stale jobs are reset on Worker restart (`cleanupStaleJobs` in `index.js`).

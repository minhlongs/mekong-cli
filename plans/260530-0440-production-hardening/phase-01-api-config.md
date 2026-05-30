# Phase 1: API Configuration Hardening

## Tasks
1. Refactor `packages/ask-core/src/retriever.ts` to fetch embeddings using environment variables `MODEL_SERVER_URL`, `MODEL_NAME`, and `MODEL_SERVER_TOKEN` instead of hardcoded strings.
2. Refactor `apps/nhipdieuxanh/app/api/posts/route.ts` to call completion endpoints dynamically utilizing the same environment variables.

## Verification
- Code builds cleanly.
- Tests pass when mocking environment.

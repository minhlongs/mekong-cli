# Phase 2: Database Transaction Retry

## Tasks
1. Extend Prisma Client in `apps/nhipdieuxanh/lib/prisma.ts` with custom client method `$transactionWithRetry`.
2. Ensure the method retries on transient errors (like P2034) using an exponential backoff with jitter.

## Verification
- Connection compiles cleanly.
- Export matches existing usage.

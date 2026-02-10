# AgencyOS Worker — Background Job Processing

> **第八篇 九變 (Jiu Bian)** — Adaptations: handle varied terrain and conditions
>
> This file governs CC CLI behavior ONLY when working inside `apps/worker/`.
> Inherits from root `CLAUDE.md` (Constitution) and `~/.claude/CLAUDE.md` (Global).

## Identity

**Role:** Background worker service for async jobs, scheduled tasks, event processing
**Pattern:** Queue consumer with retry logic

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Node.js |
| Language | JavaScript |

## Development Rules (Domain-Specific)

### Job Processing
- All jobs MUST be idempotent (safe to retry)
- Implement proper retry logic with exponential backoff
- Log all job outcomes (success, failure, retry count)
- Dead letter queue for permanently failed jobs

### Error Handling
- Never swallow errors silently
- Structured logging: `{ jobId, status, duration, error? }`
- Alert on consecutive failures (>3 retries)

### Code Standards
- Each job handler in its own file
- kebab-case file naming
- Job handlers < 100 lines
- Shared utilities in `lib/` directory

## Quality Gates

- All jobs must handle timeout gracefully
- No unhandled promise rejections
- Retry logic must be tested
- Log every job start and completion

---
description: "Deploy to production — build, push, verify CI/CD, confirm green. Engineering deploy command."
argument-hint: "[environment or version]"
allowed-tools: Read, Write, Bash, Task
---

# /raas:deploy — Production Deployment

**Core engineering command** — Full deployment pipeline with verification.

## Pipeline

```
SEQUENTIAL: Build → Push → CI/CD → Verify          (~20 min)
    |
OUTPUT: reports/raas/deploy/
```

## Estimated: 10 credits, 20 minutes

## Execution

Load recipe: `recipes/raas/deploy.json`

Execute DAG workflow following binh-phap-cicd.md:

### Deployment Cycle (sequential)
1. `build` — Build project, verify 0 errors
2. `push` — Git push to trigger CI/CD
3. `ci-cd` — Poll GitHub Actions until GREEN
4. `verify` — Production HTTP check + smoke test

## CRITICAL: GREEN PRODUCTION RULE

After `git push`, MUST verify:
1. CI/CD status = GREEN (poll max 5 min)
2. Production HTTP = 200 OK
3. Smoke test passes

**Report format:**
```
## Verification Report
- Build: ✅ exit code 0
- Tests: ✅ [N] tests passed
- Git Push: ✅ [commit_hash] → main
- CI/CD: ✅ GitHub Actions [status] [conclusion]
- Deploy: ✅ [URL] [ready_state]
- Production: ✅ HTTP [status_code]
- Timestamp: [actual_time]
```

## Instructions

1. Read recipe DAG definition
2. Execute steps in order
3. NEVER use vercel --prod (BANNED)
4. Only use git push for deployment
5. Write outputs to `reports/raas/deploy/`

## Usage

```
/raas:deploy [production|staging]
/raas:deploy --version [x.y.z]
```

## Goal context

<goal>$ARGUMENTS</goal>

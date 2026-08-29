# Super Command #4 — Next 10 Tasks (approved by user "go")

> Source: §23 STOP report delivered at end of Super Command #3 (Runtime v0.2, PR #9 merged as 0d08762c7).
> User approved execution of exactly these 10 tasks via the /orchestrate pipeline.

## Security constraints (verbatim, MUST be preserved)

- No private keys, seed phrases, wallet creation, custody, real transactions in tests.
- Must not break protected flows (NOWPayments IPN, license gate, payment flow).
- Must not touch .github/workflows/* (owned by concurrent PR #7).

## Repo constraints

- No console statements in production.
- Tests must pass before push.
- Use `python3` not `python`; pytest-timeout NOT installed.
- Parity gate: `grep -E "^FAILED" <output> | sed 's/ - .*//' | sort -u` then `comm -13 .orchestrate/latest/failset_baseline.txt <new>` must be EMPTY. Baseline keep the "FAILED " prefix.

## The 10 tasks

1. **Merge PR #7 (CI-runnable gates)** → core-dna-gate + Quality Gates green in CI.
   - NOTE: PR #7 is CONFLICTING (mergeable: CONFLICTING, mergeStateStatus: DIRTY) because main advanced past it with PR #9. Requires rebase/conflict resolution. .github/workflows/* is owned by PR #7 so conflict resolution must be handled carefully.

2. **E10 Buzz live** — wire `run_from_payload` to a real Buzz workspace once credentials available.
   - Verify if blocked on Buzz workspace/credentials first.

3. **NOWPayments IPN remount behind `PaymentProvider`** (dedicated reviewed lane; protected flow).

4. **Harness verifier `explain()`/quality-gate merge into `src/core/verifier.py`** (2-stack convergence).

5. **Real network enforcement** — replace deny-all placeholder struct across all three runtimes.

6. **MemoryStore conformant implementation** — known gap in core-contract.md.

7. **GoalEngine conformant implementation** — known gap (live engine in `src/mekongcli/`).

8. **MCP adapter ↔ capability bus integration test** against a real MCP server.

9. **Resolve `llm_client` transitional exception** — move remaining HTTP to `src/providers/` per DEPRECATION.md resolution target.

10. **Replace deleted tracing stubs (E3) with a real telemetry emitter** carrying `mission_id` correlation (invariant 5).
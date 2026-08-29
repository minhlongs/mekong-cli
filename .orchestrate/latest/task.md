# Super Command #5 — Economic Bus + Capability Bus + Agent Registry

> Source: §24 STOP report delivered at end of Super Command #4 (Runtime v0.3, PR #10 merged as 7c5f64093).
> User approved execution of exactly these tasks via the /orchestrate pipeline.
> Branch: `feat/sc5-economic-capability-buses` based on `7c5f64093`.

## Mission

Transform Mekong CLI into an open-source autonomous runtime for Solo Companies /
Solo Vibe Coders: **Autonomous Agent Runtime + Capability Bus + Economic Bus**.
Build the *smallest correct foundation* for that architecture — not the whole
future vision.

## Security constraints (verbatim, MUST be preserved)

- No private keys, seed phrases, wallet creation, custody, real transactions in tests.
- Must not break protected flows (NOWPayments IPN, license gate, payment flow).
- Must not touch `.github/workflows/*` (owned by concurrent PR #7).
- No speculative marketplace implementation.
- No tokenomics. No custody of user funds. No autonomous financial transactions
  without explicit policy/approval boundaries.
- Do not hard-code Claude / Cloudflare / Buzz / USDT / x402 as the only protocol.
- Preserve working functionality. Do not rewrite the entire repository.
- Every architectural change must have tests.

## The tasks

1. **Clean CORE / ADAPTERS boundary** — `src/core/` must not import vendor SDKs or
   adapter implementations at module level. One import site binds core to CF
   runtime; isolate it.
2. **Canonical LLM provider interface** — `generate()` / `stream()` /
   `structured_output()` / `tool_call()` / `health()` behind one port.
   Prove two providers satisfy the same interface.
3. **Single-source agent registry** — YAML is the source of truth; Python
   discovery and CLI are adapters. Each agent declares id/name/role/description/
   capabilities/allowed_tools/risk_level/model_preference/max_budget/
   max_iterations/approval_policy.
4. **Capability bus abstraction** — `Capability` (id/description/input_schema/
   output_schema/risk_level/cost/authorization/execute) + `CapabilityBus`.
   Agents request `capability.execute(...)` rather than reaching for providers.
5. **MCP adapter → capability bus bridge** — MCP tools become Capabilities;
   `mcp:<tool_name>` ids. Prefer the official MCP SDK; do not reimplement MCP.
6. **Payment abstraction (x402 + MPP, neither hard-coded)** — one
   `PaymentProvider` protocol, two scheme providers, fail-closed config, no
   custody, no autonomous transactions.
7. **Buzz adapter** — canonical Buzz transport, hermetic-by-injection, fail-loud
   `BuzzConfigError` at call time (not import time).
8. **Cloudflare adapter isolation** — `CloudflareTransport(Protocol)` with
   `.dispatch(payload) -> dict`; the single import site that binds core to CF
   runtime.
9. **Agent-loop E2E test** — hermetic end-to-end proof of the canonical
   lifecycle (GOAL → CONTEXT → PLAN → DELEGATE → EXECUTE → OBSERVE → VERIFY →
   REPAIR → REMEMBER → COMMIT).
10. **Quality gates green** — ruff + pyright (CI's actual type gate) + pytest
    parity vs `.orchestrate/latest/failset_baseline.txt` (277 entries) must be
    EMPTY. Zero `: any` without explicit approval.

## Repo constraints

- No console statements in production. Tests must pass before push.
- Use `python3` not `python`; pytest-timeout NOT installed.
- Parity gate: `comm -13 .orchestrate/latest/failset_baseline.txt <new-failures>`
  must be EMPTY. Baseline keeps the "FAILED " prefix.
- New files ≤ 200 LOC.
- pyright is the authoritative type gate (CI gate; continue-on-error: true).
  mypy only in `deploy-cf.yml`, which is owned by PR #7 and must not be touched.
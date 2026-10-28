# CLI Product Promise — Implementation Status

**Scope source:** the public promise at <https://www.mekongmind.com/cli> (frozen snapshot in
`src/registry/capability_ledger.json`).
**Denominator:** 197 advertised command groups, 10 departments, 6 layers (L0–L5), 7 milestone
gates, 121 advertised aliases. The denominator is fixed: claims are never deleted, merged or
re-worded to improve a ratio.
**Per-claim binding matrix:** [`CLAIM_LEDGER.md`](./CLAIM_LEDGER.md) (generated —
`python scripts/generate_claim_ledger_doc.py`).

This document states what is *measured*, not what is intended. A command is not "done" because it
returns HTTP 200, because a test count went up, or because a gate artifact was written; it is done
when a real handler produced a business result that an independent verifier recomputed from
statute, and a test asserts that result.

---

## 1. The shared execution path (implemented)

```
CLI / HTTP  →  identity + authorization  →  schema validation  →  job row (QUEUED)
            →  runtime (handler resolution, timeout, budget reservation)
            →  real engine / handler      →  postcondition verifiers
            →  evidence rows (facts)      →  signed receipt (v2)  →  run status
```

* **Transport:** `POST /v1/cli/runs`, `GET /v1/cli/runs[/{id}]`, `POST /v1/cli/runs/{id}/approval`,
  `…/approval/decision`, `…/cancel`, `POST /v1/cli/receipts/verify`, `GET /v1/cli/capabilities`,
  `GET /v1/cli/gates`, `POST /v1/cli/gates/{gate_id}/reconcile` — all in
  `src/api/cli_promise_routes.py`, mounted in `src/gateway.py`. Every endpoint requires a
  principal: an HTTP caller without a credential gets **403 `MISSING_CREDENTIAL`** (local
  single-operator mode is opt-in via `MEKONG_PROMISE_LOCAL_MODE=1`).
* **Authorization** (`src/core/promise/identity.py`): role → permission
  (`promise:execute`, `promise:execute:irreversible`, `promise:approve`, `promise:read`,
  `gates:reconcile`, `registry:read`, `promise:cancel`), plus per-workspace cluster allowlist and
  per-command denylist. Checks run **before** anything is persisted.
* **Validation** (`src/core/promise/schema.py`): each operation declares a JSON Schema;
  `additionalProperties: false`, enums, patterns and ranges are enforced. Invalid input ⇒
  `FAILED` + `INPUT_INVALID`, never an exception and never a partial write.
* **Runtime** (`src/core/promise/runtime.py`, `service.py`): job lifecycle
  `QUEUED → RUNNING → COMPLETED|FAILED|CANCELLED|NEEDS_RECONCILIATION|NOT_IMPLEMENTED|REJECTED`,
  `AWAITING_APPROVAL → QUEUED` on resume. Per-workspace engine databases
  (`.mekong/workspaces/{workspace_id}/…`, root follows `MEKONG_PROMISE_STATE_DIR` /
  `MEKONG_PROMISE_WORKSPACE_ROOT`).
* **Approvals**: bound to a payload digest (`src/opc/approval.py`), consumed atomically
  (`expires_at >= now`, `consumed = 0`, `revoked = 0`), bound to one run, and re-checked on
  resume. Tampered payload ⇒ `APPROVAL_PAYLOAD_MISMATCH`; reuse ⇒ `APPROVAL_REPLAY_OR_EXPIRED`;
  wrong run ⇒ `APPROVAL_TOKEN_UNKNOWN`.
* **Idempotency**: an operation that declares `idempotency_fields` derives a replay key, so a
  double submission returns the persisted job (`idempotent_replay: true`) instead of executing
  twice; engine UNIQUE constraints remain the second line of defence.
* **Restart recovery**: `recover_after_restart()` turns in-flight runs into
  `NEEDS_RECONCILIATION` when the external effect is uncertain (`PROVIDER_CALL`, `SEND_MESSAGE`,
  `MOVE_MONEY`, `FILE_SUBMISSION`, `DEPLOY`) and into `FAILED / INTERRUPTED_BY_RESTART` otherwise.
  Closing a reconciliation requires provider proof (`provider` + `reference`); usage that cannot be
  known is recorded as `UNKNOWN`, never coerced to zero.
* **Evidence & receipts** (`src/core/promise/evidence.py`, `signing.py`): run evidence, revenue
  facts, deployment proofs, client acceptances, attestations, channel metrics and SOP exports live
  in separate tables with an allowlisted query surface. Receipts are HMAC-SHA256 signed over a
  canonical (RFC 8785-style) JSON body that **includes the signer identity**, and separate
  `handler_ran` / `artifact_integrity` / `business_conditions_met`. With no key configured the
  receipt degrades to an explicit `UNSIGNED` mark — it never pretends to be signed.
* **Gates** (`src/core/promise/gates.py`): 7 gates, 17 conditions, each condition a function that
  measures persisted facts. Missing evidence ⇒ `LOCKED`; partial ⇒ `PARTIAL_EVIDENCE`; all
  conditions met ⇒ `SEALED_VERIFIED`. Sealing is a *result* of measurement, never an input:
  `CliEvidenceStore.unlock_gate_with_reconciliation()` refuses to seal without an all-true
  condition map.

## 2. Statutory engine (Vietnam) — period-aware

`src/core/vn_statutory_rules.py` holds versioned rules with citation + effective dates, and the
engines resolve the version in force for the period the caller states (`as_of`, `tax_period`,
`contribution_period`, `payroll_period`; CLI `--ky-thue`):

| domain | rule versions encoded |
| --- | --- |
| PIT (TNCN) | 7 brackets + 11M/4.4M relief until 31/12/2025 (NQ 954/2020/UBTVQH14); 5 brackets + 15.5M/6.2M from 01/01/2026 (Luật 109/2025/QH15, NQ 110/2025/UBTVQH15) |
| CIT (TNDN) | 20% only until 30/09/2025; 20% / 15% (revenue ≤ 3B) / 17% (3B–50B) from 01/10/2025 (Luật 67/2025/QH15 Điều 10) |
| VAT (GTGT) | 0/5/10; 10%→8% reduction 01/07/2025–31/12/2026 with sector exclusions (NQ 204/2025/QH15, NĐ 174/2025/NĐ-CP); 7% is always illegal |
| BHXH/BHYT/BHTN | ceiling 20 × reference salary: 46.8M until 30/06/2026, 50.6M from 01/07/2026 (NĐ 161/2026/NĐ-CP); regional minimum wages from 01/01/2026 (NĐ 293/2025/NĐ-CP) ⇒ BHTN ceiling 106.2M (vùng I) |
| Tax code (MST) | modulus-11 checksum, weights `[31,29,23,19,17,13,7,5,3]` (TT 105/2020/TT-BTC Điều 5) |
| Late payment | 0.03%/day on the unpaid amount (Điều 59 Luật Quản lý thuế) |
| Admin sanctions | fine frame arithmetic (Điều 23.4 NĐ 118/2021/NĐ-CP), 1-year / 2-year limitation periods (Điều 6 Luật XLVPHC), leap-safe expiry |

The independent verifiers in `src/core/statutory_verifiers.py` recompute PIT (shortcut formula of
Phụ lục 01/PL-TNCN), CIT, VAT, BHXH caps, VAS double entry, VietQR EMVCo CRC-16 and
administrative-fine bounds **from the rule table for the stated period**, and report
`rule_version` / `rule_effective_from` / `statutory_citation` with every verdict.

## 3. Measured state (wave 1)

| measure | value | how it is measured |
| --- | --- | --- |
| advertised command groups (denominator) | **197** | `CapabilityLedger.validate_integrity()` |
| commands bound to the promise execution path | **7** (`thue`, `ke-toan`, `bhxh`, `payroll`, `vietqr`, `adminsanction`, `taxadmin`) | `GET /v1/cli/capabilities` → `execution_status` |
| bound operations (`OperationSpec`) | **20**, each with schema, handler, effects, postconditions and an acceptance test | `load_default_registry()` |
| advertised commands answered `NOT_IMPLEMENTED` by the promise path | **190** | same endpoint |
| advertised commands dispatched in-process by the legacy dispatcher | **197 / 197 COMPLETED**, 0 reaching a synthetic fallback | `tests/test_product_promise_fullstack.py::…without_a_synthetic_success` |
| milestone gates defined / sealed by default | **7 / 0** | `GET /v1/cli/gates` |
| gates sealable end-to-end today | **1** (`first-revenue`: reconciled bank transfer + issued TT78 invoice + tax record) | `tests/test_promise_spine_wave1.py` |
| promise acceptance tests | **93 passing** (26 finance ops + 38 spine + 29 fullstack contract) | `pytest tests/test_promise_finance_ops.py tests/test_promise_spine_wave1.py tests/test_product_promise_fullstack.py` |
| CLI named entries vs advertised names | 217 CLI entries; **9 advertised names missing** (`bootstrap`, `cell`, `cook`, `csuite`, `graph`, `recipe`, `system`, `workflow`, `zenpay`); **101 of 121 advertised aliases missing** | `build_app()` enumeration |

Reproduce:

```bash
python -m pytest tests/test_promise_finance_ops.py tests/test_promise_spine_wave1.py \
                 tests/test_product_promise_fullstack.py -q
python -m pytest tests/test_antigravity_thue.py tests/test_antigravity_payroll.py \
                 tests/commands/test_thue_dnvn.py tests/zenos/test_vietnam_feature_regression.py -q
python scripts/generate_claim_ledger_doc.py --check
ruff check src/core/promise src/api/cli_promise_routes.py src/core/vn_statutory_rules.py \
           tests/test_promise_finance_ops.py tests/test_promise_spine_wave1.py
```

## 4. What was fixed in this wave (fake-success removal)

1. **Dispatcher fail-open fallback removed.** Step 10 of
   `CliCommandDispatcher._execute_in_process` used to answer every unmapped command with
   `{"status": "EXECUTED", "deliverable": "Artifact generated …"}` and a `PASSED` verifier.
   It now returns `NOT_IMPLEMENTED` + verifier `NO_HANDLER_BOUND` with the next step to take.
2. **Gate sealing required measured conditions.** `unlock_gate_with_reconciliation()` accepted any
   two strings (a transaction id and a URL) and stamped `SEALED_VERIFIED`. It now refuses without
   an all-true `verified_conditions` map, and the HTTP route returns **409
   `EVIDENCE_REFERENCE_UNKNOWN` / `GATE_CONDITIONS_UNMET`** instead of sealing.
3. **Statutory constants were pinned to expired law.** PIT/CIT/BHXH verifiers and engines now
   derive rates, brackets, deductions and ceilings from the rule version in force; the CLI states
   the period (`--ky-thue`) and refuses illegal rates/sectors with a citation.
4. **Silent coercions removed** in the patched engines: unknown VAT rate → error (not 10%),
   invalid region → error (not 1), negative salary → error (not clamped), `add_employee` returns
   the stored row id, D02-LT refuses unknown employees, `net_to_gross` keeps `as_of`.
5. **Receipt signing bug:** the HMAC was computed *before* the `signing` block was attached, so no
   verifier could reproduce it — every v2 receipt failed its own verification. Fixed, and now
   covered by tests (valid / tampered output / downgraded result / re-attributed key / stripped
   signature / unsigned degradation).
6. **Approval TTL was ignored:** `request_approval(ttl_seconds=…)` issued a token with the engine
   default expiry. Now bound to the requested window.
7. **Idempotency keys were only derived for provider-side effects**, so every workspace-write
   operation (bank transfer, taxpayer registration, invoice issuance, employee registration) could
   be applied twice by a retry. Declarations are now honoured.
8. **Authorization ordering:** capability checks now run before the `NOT_IMPLEMENTED` record is
   persisted, so a denied caller leaves no run row.
9. **Per-request service instantiation** in the HTTP routes rebuilt the whole service (and its
   stores) on every call; the routes now use the process-wide service.
10. **Test-harness defect that hid two advertised commands:** `tests/conftest.py` replaced
    `src.api.raas_router.router` with a bare `MagicMock`, which trips FastAPI's `include_router`
    assertion when the gateway module is imported a second time inside a test session. `mekong
    gateway` and `mekong system` therefore "failed" only under pytest. The stub now behaves like an
    empty router, and both commands dispatch `COMPLETED`.

## 5. Outstanding promise list (not complete — do not treat any section above as final)

Ordered by what blocks the public promise the most. Each item keeps the 197 denominator intact.

1. **Bind the remaining 190 advertised commands to the promise path.** Waves are grouped by
   department so each is independently reviewable: `quality-compliance` (47 remaining),
   `engineering-factory` (32), `platform-operations` (24), `product-strategy` (24),
   `sales-revenue` (17), `customer-success` (13), `growth-marketing` (13), `ceo-command` (10),
   `knowledge-memory` (5), `market-intelligence` (5). Each binding needs: input schema, real
   handler, declared effects, postconditions that measure the business result, an acceptance test,
   and — where the claim is legal/tax — jurisdiction, rule version and effective date.
2. **One execution path, not two.** The legacy `CliCommandDispatcher` still serves most commands.
   It reaches real engines (123 `*_ENGINE_CALLED` verifiers) but has weaker guarantees than the
   promise path: engines default to `<repo>/.mekong/*.db` (no tenant isolation), params are not
   schema-validated, receipts are the legacy v1 shape, and approval policy is not enforced.
   Migration means moving each command's dispatch onto `OperationSpec`s and deleting the legacy
   branch — not wrapping it.
3. **Gates L0/L1/L2/L4/L5 cannot be sealed yet.** Their 14 conditions are implemented as
   measurements, but the operations that would produce the facts (blueprint attestation, offer
   validation criteria with research provenance, production health/build+test digests/compliance
   scan, channel metrics across ≥2 periods, client acceptance, SOP packaging) are not bound. Until
   they are, those gates correctly stay `LOCKED`.
4. **CLI surface:** 9 advertised command names and 101 advertised aliases are not reachable from
   `mekong …`. They must resolve to the same contract as their canonical command (alias parity is
   an acceptance criterion, not cosmetics).
5. **Ledger maturity tiers are overstated.** All 197 claims carry `maturity_tier: REAL_VERIFIED`
   from the snapshot. The honest tier for an unbound claim is `NOT_IMPLEMENTED`; the measured value
   is exposed today as `execution_status` in `GET /v1/cli/capabilities` and must be written back
   into the ledger with `BLOCKED` for claims waiting on credentials/providers.
6. **Signing is symmetric.** Receipts/evidence use HMAC-SHA256 with a key from
   `MEKONG_EVIDENCE_SIGNING_KEY` / `MEKONG_EVIDENCE_KEY_FILE`. A verifier holding the key can forge
   a receipt, so this proves integrity + attribution inside one trust domain, not third-party
   non-repudiation. Asymmetric signing (key pair, public verifier, signer identity) is still owed.
7. **Website alignment (`minhlongs/mekongmind`).** The `/cli` page
   (`mvp/src/app/(landing)/cli/page.tsx`, data in `mvp/src/data/cli-full-registry.ts`) still shows
   fabricated success ("cfo dispatched to business-analyst … gate evidence sealed",
   "✓ Gate Artifact Sealed", `SHA-256 VERIFIED` / `GATE_PASSED_SHA256` badges, sample output
   presented as a real run) and its TypeScript bridge (`mvp/src/lib/cli-execution-bridge.ts`) and
   proxies (`mvp/src/app/api/cli/*/route.ts`) call the backend without an authenticated transport.
   That repository is outside this working branch, so it is a separate deliverable: point the
   bridge at the authenticated endpoints, render backend status/loading/denied/empty states, and
   mark samples as samples.
8. **Engine hardening beyond the 8 patched engines.** The fail-open patterns found in
   `thue`/`bhxh`/`payroll`/`adminsanction` (silent coercion of invalid input, fabricated seed
   rows, dropped period parameters) are likely present in the ~128 remaining `src/core/*_engine.py`
   modules and must be removed as each is bound.
9. **SOP/department mismatches in the snapshot.** e.g. `audit` (SOX 404/ITGC/COSO) is advertised
   under `sales-revenue` with the `first-revenue` gate and a checkout SOP; legal commands are tied
   to `mvp-live`. The SOP chain must fit the work rather than being forced through a revenue gate.
10. **CI reconciliation.** `scripts/generate_claim_ledger_doc.py --check` keeps the claim matrix
    honest, but CI does not yet fail when an advertised command loses its binding, when a gate is
    sealed without measured conditions, or when a receipt cannot be verified.

## 6. Whole-suite measurement and blockers

Full suite on this branch (`pytest tests/ --ignore=tests/test_antigravity_init.py`, 5,521 collected
tests, 32 min):

```
123 failed, 12,788 passed, 110 skipped, 59 errors
```

Every one of those failures was reproduced at the base commit `ab41c25` in a separate worktree, so
none is a regression from this work. Measured on the 46 files that fail:

| | base `ab41c25` | this branch |
| --- | --- | --- |
| failed | 117 | 118 |
| passed | 727 | **759** |
| collection errors | 60 | **59** |

The single additional "failure" is `tests/test_antigravity_gateway.py::TestMCPGatewayTools::
test_mcp_tool_parity_schemas`: at base that whole file was a *collection error* (the mocked RaaS
router aborted the gateway import), so none of its tests ran. With the file collecting again, its 32
tests pass once the MCP SDK is installed at the version the code targets (`mcp<2` — `mcp` 2.x
renamed `FastMCP` to `MCPServer`, and `mcp` is not declared in `requirements.txt` at all).

Pre-existing causes of the remaining red tests, none of them touched by this work: missing
`.agents/skills` assets (`tests/test_antigravity_init.py` cannot even be collected,
`tests/test_antigravity_e2e.py`, `tests/test_ak_init_bridge.py`, `tests/test_antigravity_subagents.py`),
no `mekong` binary on `PATH`, command-fabric packaging tests that expect built IDE/npm artifacts,
and payment/tier route tests that need services this sandbox does not have.

Blockers:

* **No access to the website repository from this branch.** The session works in
  `minhlongs/mekong-cli`; changes to `minhlongs/mekongmind` (the app serving
  `www.mekongmind.com`) are out of scope here and are listed as deliverable 7 above.
* **No production credentials or provider accounts** are configured in this environment, so
  provider-facing operations are exercised against their adapters with labelled mocks only, and no
  filing, payment, message or deployment side effect has been triggered.
* **Undeclared dependency:** `src/core/mcp_server.py` needs `mcp<2`; `requirements.txt` does not
  mention `mcp`, so a fresh environment installs 2.x and the MCP server reports "SDK not installed".
* **Tests mutate tracked runtime state.** The payment/webhook tests append revenue events to
  `.mekong/company.json`, which is committed, and an inheritance engine drops `inheritance.db` in
  the current working directory. Those files should be untracked or redirected to a temp dir; both
  mutations were deliberately kept out of these commits.
* **Demo rows seeded by engines.** `BhxhEngine` seeds `CANONICAL_EMPLOYEES` and `ThueEngine` seeds
  `CANONICAL_TAX_PROFILES` unless constructed with `seed_canonical=False`. The promise path always
  passes `seed_canonical=False`, but a default-constructed engine still shows fabricated employees
  in a compliance ledger — the default should change once the CLI surfaces that depend on it are
  updated.

## 7. Rules this work follows

* Never replace real execution with a synthetic success payload; errors stay errors.
* Never accept browser-sent state as authority: only allowlisted command ids and schema-validated
  params are accepted, and status/approval/quota/evidence come from the backend.
* A SHA-256 digest proves integrity only. A gate needs a business fact, and missing evidence stays
  `NOT-MET`.
* The denominator never shrinks, and completion is never self-declared after one group.

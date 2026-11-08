---
title: "Phase 01 — HMAC Approval Binding & Pack Manifest Hygiene"
status: completed
---

# Phase 01 — HMAC Approval Binding & Pack Manifest Hygiene

## Context

`src/opc/approval.py` binds an `ApprovalToken` to an `ActionPayload` with a plain
SHA-256 `action_digest`. That protects against tampering with the payload after
the token is minted, which is why `tests/test_opc_approval_security.py` passes
today. What it does **not** protect against is a forged or mutated token: anyone
who can construct an `ApprovalToken` in memory or update a row in `opc_approvals`
can flip `decision` to `approve`, extend `expires_at`, or swap `run_id` while
keeping the original `action_digest`, and `verify_and_consume()` will accept it.

Separately, `src/opc/packs/vn-sme-ops/pack.json` points at
`"entrypoint": "src.opc.packs.vn:VnSmePack"`, a module that does not exist in
the repository, and its `legal_references` block cites Circular 78/2021 and
Decree 123/2020 as an operational tax-compliance pack without the draft-only
caveat established in PR #139.

## Requirements

1. Add `signature: str = ""` to `ApprovalToken` (`src/opc/models.py`) and persist
   it in `StateStore.opc_approvals` (`src/opc/state.py`, additive column migration
   when opening an older DB).
2. In `src/opc/approval.py`:
   - Accept `secret_key: str | bytes | None = None` on `PayloadBoundApprovalEngine`,
     defaulting to `os.environ.get("MEKONG_APPROVAL_SECRET")` and falling back to
     a deterministic local key when unset so offline tests stay reproducible.
   - Compute `compute_token_hmac(token, payload, secret_key)` with `hmac.new(..., hashlib.sha256)`
     over canonical JSON binding `token_id`, `run_id`, `principal`, `capability`,
     `connector`, `action_digest`, `decision`, `created_at`, and `expires_at`.
   - Verify the HMAC with `hmac.compare_digest` inside `verify_and_consume()`
     before marking the token consumed; raise `ApprovalSecurityError("HMAC signature mismatch...")`
     on any discrepancy or empty signature, or when verified under a different secret.
3. Update `src/opc/packs/vn-sme-ops/pack.json` so `entrypoint` resolves to
   `"src.opc.engine:OPCEngine"`, capabilities and connectors match the engine's
   draft-preparation contract, and `legal_references` states explicitly that
   outputs are pre-accounting drafts pending licensed TVAN submission. Add sample
   fixtures under `src/opc/packs/vn-sme-ops/fixtures/` so both packs under
   `src/opc/packs/` load cleanly.

## Files

- `src/opc/models.py`
- `src/opc/approval.py`
- `src/opc/state.py`
- `src/opc/packs/vn-sme-ops/pack.json`
- `src/opc/packs/vn-sme-ops/fixtures/sample_business_profile.json`
- `src/opc/packs/vn-sme-ops/fixtures/sample_client_request.json`
- `tests/test_opc_approval_security.py`

## Validation

- `python3 -m pytest tests/test_opc_approval_security.py -v`

## Risks & Rollback

- Existing callers construct `ApprovalToken` via `issue_token()`, so giving
  `signature: str = ""` a default keeps dataclass construction backwards-compatible
  while `verify_and_consume()` rejects unsigned tokens.

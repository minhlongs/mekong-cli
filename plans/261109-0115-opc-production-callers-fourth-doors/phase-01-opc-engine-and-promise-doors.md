# Phase 01 — Enforce QuarantineFloor in OPCEngine & HMAC Verification in PromiseService

## Context
- `OPCEngine.generate_draft` (`src/opc/engine.py`) is currently 184 LOC (ceiling is 185 LOC) and does not call `QuarantineFloor`.
- `PromiseService._require_approval` (`src/core/promise/service.py`) checks `compute_action_digest(payload) != token.action_digest` and `consume_approval_atomic`, skipping `self.approvals.verify_and_consume(token, payload, now=now_ts)`. Furthermore, `decide_approval` resumes approved jobs without calling `_require_approval` to verify HMAC or atomically consume the token.

## Requirements
1. In `src/opc/engine.py`:
   - Import `QuarantineFloor` from `src.opc.quarantine`.
   - Initialize `self.quarantine = QuarantineFloor()` in `OPCEngine.__init__`.
   - In `OPCEngine.generate_draft`, run `self.quarantine.enforce_before_tool(self.quarantine.guard_proposal_input(intake))` right after `self._assert_manifest_allows("proposal.generate_draft")` before any draft creation, state persistence, or usage recording.
   - Keep `src/opc/engine.py` strictly `<= 185 LOC`.
2. In `src/core/promise/service.py`:
   - In `_require_approval`, after verifying `compute_action_digest(payload) != token.action_digest` (`APPROVAL_PAYLOAD_MISMATCH`) and checking `token.revoked or token.consumed or now_ts > token.expires_at` (`APPROVAL_REPLAY_OR_EXPIRED`), invoke `self.approvals.verify_and_consume(token, payload, now=now_ts)` and map `ApprovalSecurityError` to `PromiseError("APPROVAL_SECURITY_VIOLATION", str(exc), http_status=409)` before `consume_approval_atomic`.
   - In `decide_approval`, when `decision == "approve"`, invoke `_require_approval(approver, job, spec, dict(job.get("params") or {}), token_id)` so the token's digest, expiry, HMAC-SHA256 signature, and atomic single-use lock are enforced before resuming execution.

## Files
- Modify: `src/opc/engine.py`
- Modify: `src/core/promise/service.py`
- Test: `tests/test_opc_production_callers.py`, `tests/test_promise_spine_wave1.py`

## Validation
- `python3 -m pytest tests/test_opc_platform_contract.py tests/test_opc_approval_security.py tests/test_promise_spine_wave1.py tests/test_promise_finance_ops.py -v`

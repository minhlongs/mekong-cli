# Phase 03: Fail-Closed Governance & Payload-Bound Approvals (`G3`)

- **Status:** pending
- **Priority:** P1
- **Dependencies:** Phase 02

## Context & Requirements

Eliminate the default-allow risk classification defect in `Governance.classify_risk()` (`src/core/governance.py:206`), standardize the `PolicyDecision` contract, enforce untrusted content separation (`untrusted_context=True`), and bind high-risk approvals to single-use payload digests via `PayloadBoundApprovalEngine` (`src/opc/approval.py:35`).

<!-- Updated: Validation Session 1 - RT-02 applied -->

## Affected Files

- `/Users/macbook/mekong-cli-autonomous-worktree/src/core/governance.py` (modify) — Fix `classify_risk()` at line 206 so unknown/missing risk levels return `ActionClass.FORBIDDEN` instead of `ActionClass.SAFE`; add `PolicyDecision` dataclass and `evaluate_ticket_action()` enforcing mandate boundaries, untrusted content separation, and payload-bound single-use approval tokens.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/core/runtime_adapter.py` (modify) — Ensure `MekongCoreRuntimeImpl._effective_risk()` (`lines 400-410`) and delegate/execute hooks honor fail-closed governance and `evaluate_ticket_action()`.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/opc/approval.py` (modify) — Expose helper methods if needed to bind `(ticket_id, task_id, capability, command_hash, resource_scope, mandate_hash)` into single-use approval tokens.

## Implementation Steps

1. In `src/core/governance.py:206`, change `self.RISK_LEVEL_MAP.get(risk_upper, ActionClass.SAFE)` so unknown, empty, or malformed `risk_level` values return `ActionClass.FORBIDDEN`.
2. Define `PolicyDecision` (`decision: Literal["ALLOW", "APPROVAL_REQUIRED", "DENY"]`, `actor`, `capability`, `resource_scope`, `risk_level`, `policy_version`, `decision_reason`, `audit_correlation_id`, `payload_digest`) in `src/core/governance.py`.
3. Implement `Governance.evaluate_ticket_action()` verifying:
   - `capability` is in `mandate.permitted_capabilities` and `resource_scope` matches `mandate.resource_boundaries` (otherwise `DENY`).
   - If `untrusted_context=True`, any attempt to escalate capabilities, mutate mandate fields, or bypass approval returns `DENY`.
   - Destructive/privileged capabilities (`deploy_prod`, `git_push_main`, `payment_transfer`, `credential_rotate`, `shell_global_mutate`) or `HIGH`/`CRITICAL` risk require a valid, unconsumed payload-bound approval token from `PayloadBoundApprovalEngine` (returning `APPROVAL_REQUIRED` when absent, `DENY` when mismatched or replayed, and `ALLOW` only on exact first-use match).

## Validation & Gate

```bash
python3 -m pytest tests/test_governance.py tests/core/test_re_governance.py tests/test_opc_approval_security.py -q
```

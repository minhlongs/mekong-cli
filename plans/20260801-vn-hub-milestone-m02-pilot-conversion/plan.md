# Mission Block M02 — VN Hub Pilot Conversion

> Status: COMPOSED — needs human approval before execution.
> Scope: billing, auth, checkout, and pilot enrollment flows only.
> Hard-stop rule: No PingOne manifest generation, no credential writes, no checkout URL mutations until explicit consent is granted.

## Objectives
1. Lock down VietQR pilot billing + renew paths in gateway.
2. Separate pilot enrollment from production checkout states.
3. Wire org invite / multi-tenant admin primitive.
4. Enable audit-log deltas between staging and main.

## Execution Constraints (Non-Negotiable)
- No writes to:
  - PingOne tenants / applications
  - Checkout / Polar / SePay production configurations
  - Auth secret stores or signing keys
- All environment mutations must be gated by:
  - explicit `go` / `consent` confirmation per run
  - sandbox / staging targets only
- Read-only research / git operations are pre-approved.

## Work Items
- [ ] Expand test matrix for VietQR pilot billing (current: 15/15 green)
- [ ] Audit PilotCreditGateMiddleware against renew + invite paths
- [ ] Add orchestrator hooks for staging→main promotion with audit diff
- [ ] Freeze checkout URL schema in `src/schemas/checkout.json`
- [ ] Publish conversion KPI runbook in `docs/`

## Rollout Sequence
1. Rehearse in sandbox only.
2. Validate with `ruff check`, `pytest`, smoke tests.
3. Produce a pass/fail report in `docs/reports/`.
4. Request explicit merge + deploy consent.


# Review Tickets — M02 Bounded Patch

## RT-01: PilotCreditGateMiddleware renew-path coverage
- File: `src/middleware/pilot_credit_gate.py`
- Issue: renew endpoint bypasses credit gate in some state transitions
- Fix: add `renew` to `_SKIP_PATHS` guard + test
- Trust gate: no prod writes, no auth/secret mutation

## RT-02: VietQR billing test matrix expansion
- File: `tests/test_vietqr_billing.py` (or nearest billing test module)
- Issue: renew+overdue+expire state transitions lack combined coverage
- Fix: add parametrized tests for renew→overdue→expire chain
- Trust gate: test-only, no prod writes

## RT-03: Audit diff hook for staging→main
- File: `src/services/audit_logger.py`
- Issue: no diff export for staging vs main audit events
- Fix: add `export_diff(target_scope)` read-only method
- Trust gate: read-only on audit log, no schema change


---
title: "Phase 02 — Untrusted Input Quarantine Floor"
status: completed
---

# Phase 02 — Untrusted Input Quarantine Floor

## Context

Customer messages arriving from Zalo OA, proposal notes, attachment names, and
client-supplied titles are untrusted text. Passing them straight into an agent or
tool dispatcher lets a prompt injection rewrite pricing, swap the recipient bank
account, forge an approval instruction, or invoke an undeclared capability.

## Requirements

1. Create `src/opc/quarantine.py` with:
   - `QuarantineViolationError(PermissionError)` raised when a caller demands
     strict blocking on an unsafe input.
   - `QuarantinedInput` (frozen dataclass): `source`, `raw_text`, `wrapped_text`
     enclosed in `<untrusted_customer_input source="...">...</untrusted_customer_input>`
     with any embedded closing/opening boundary tags neutralized, `is_safe: bool`,
     `risk_score: float`, `matched_rules: tuple[str, ...]`, and
     `tool_invocation_allowed: bool` (always `False` for the untrusted segment
     itself, and `is_safe=False` whenever any injection pattern matches).
   - `QuarantineFloor`:
     - `inspect(text: str, source: str = "zalo_message") -> QuarantinedInput`
     - `guard_proposal_input(intake: ProposalInput) -> QuarantinedInput`
     - `enforce_before_tool(quarantined: QuarantinedInput) -> None` — raises
       `QuarantineViolationError` if `not quarantined.is_safe`, guaranteeing zero
       downstream tool executions on flagged inputs.
   - Detection rules covering Vietnamese and English injection classes:
     instruction override (`ignore previous`, `bỏ qua hướng dẫn`, `quên hết quy tắc`),
     system/developer role spoofing (`[system]`, `<|im_start|>`, `system prompt:`),
     approval bypass (`auto-approve`, `tự động duyệt`, `bypass approval`, `issue_token`),
     payment/recipient hijacking (`chuyển khoản vào stk`, `đổi số tài khoản`,
     `wire to account`, `override price to 0`, `giảm giá 100% miễn phí hoàn toàn`),
     boundary tag breakout (`</untrusted_customer_input>`), and shell/SQL/tool
     execution directives (`exec(`, `os.system`, `DROP TABLE`, `call_tool(`).
2. Create `tests/test_quarantine_floor.py` with a 50-sample corpus (25 Vietnamese +
   25 English/mixed injection payloads) plus legitimate Vietnamese SME customer
   inquiries, proving:
   - 50/50 malicious samples are flagged (`is_safe is False`) and
     `enforce_before_tool` blocks 100% of them with `0` tool calls dispatched.
   - All legitimate customer quote inquiries pass (`is_safe is True`) and preserve
     their wrapped boundary tags.

## Files

- `src/opc/quarantine.py`
- `tests/test_quarantine_floor.py`

## Validation

- `python3 -m pytest tests/test_quarantine_floor.py -v`

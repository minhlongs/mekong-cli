---
title: "Phase 03 — Pilot A End-to-End Vertical Slice"
status: completed
---

# Phase 03 — Pilot A End-to-End Vertical Slice

## Context

The strategic research identifies Pilot A (`client-proposal-followup` over Zalo OA
with deterministic Python pricing, dynamic VietQR EMVCo payment generation, and a
one-tap owner Approval Card) as the single commercial wedge. `OPCEngine`,
`VietQrEngine`, and `PayloadBoundApprovalEngine` all exist in the repo, but they
are not wired into a single verifiable workflow with Zalo 48-hour interaction
window enforcement and quarantine protection.

## Requirements

1. Create `src/opc/pilot_a.py` containing:
   - `ZaloWebhookEvent` (dataclass): `event_id`, `oa_id`, `sender_id`,
     `sender_name`, `message_text`, `timestamp`, `last_user_interaction_ts`,
     `requested_services`, `estimated_hours`, `project_title`.
   - `ApprovalCard` (frozen dataclass): `run_id`, `event_id`, `client_name`,
     `client_contact`, `project_title`, `total_amount_vnd`, `currency`,
     `vietqr_emvco`, `vietqr_quicklink`, `approval_token`, `action_payload`,
     `quarantine_report`, `rendered_card_vi`.
   - `ZaloSandboxConnector` implementing `ConnectorProtocol` (`connector_id = "zalo_oa_sandbox"`),
     recording outbound messages idempotently and enforcing the 48-hour
     (`172800` second) Zalo OA customer-service interaction window.
   - `PilotAWorkflow`:
     - `handle_webhook(event: ZaloWebhookEvent) -> ApprovalCard`
       1. Checks 48-hour interaction window (`event.timestamp - event.last_user_interaction_ts <= 172800`).
       2. Runs `QuarantineFloor.inspect(event.message_text)` and `enforce_before_tool`.
       3. Runs deterministic `Decimal` quote calculation via `OPCEngine.generate_draft`.
       4. Generates real EMVCo QR payload via `VietQrEngine.generate_qr`.
       5. Binds the quote + VietQR payload into an `ActionPayload` for `zalo_oa_sandbox`,
          issues an HMAC-signed `ApprovalToken`, persists state, and returns the
          rendered Vietnamese `ApprovalCard`.
     - `approve_and_send(card: ApprovalCard, token: ApprovalToken | None = None, idempotency_key: str | None = None) -> dict[str, Any]`
       Verifies the HMAC approval token and dispatches the message + VietQR to
       `ZaloSandboxConnector`.
2. Create `tests/test_pilot_a_e2e.py` covering:
   - Full happy path: Zalo message → quarantine pass → deterministic VND quote →
     valid EMVCo VietQR (starts with `000201` and passes CRC) → owner approval →
     single outbound Zalo message recorded.
   - Quarantine rejection: prompt-injected Zalo message is blocked before quote
     or connector dispatch (`0` messages sent).
   - 48-hour window expiration: message outside the 48h window is rejected cleanly.
   - Approval tampering / replay / expiration / rejection block outbound send.

## Files

- `src/opc/pilot_a.py`
- `src/opc/packs/client-proposal-followup/pack.json`
- `tests/test_pilot_a_e2e.py`

## Validation

- `python3 -m pytest tests/test_pilot_a_e2e.py -v`

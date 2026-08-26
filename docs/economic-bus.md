# Economic Bus

> Refreshed: 2026-08-26 · Code: `src/core/protocols.py` (`PaymentProvider`,
> `Quote`, `PaymentRequest`, `PaymentReceipt`),
> `src/core/adapters/payment_mock.py`,
> `src/core/adapters/payment_x402_shape.py`, `src/core/billing_adapter.py`

The economic bus abstracts money movement behind one interface so the core
runtime never talks to a payment vendor directly.

## PaymentProvider protocol

Legacy methods (unchanged): `record_usage / check_quota / settle_payment`.
Extended v0.1 methods:

| Method | Signature | Notes |
|--------|-----------|-------|
| `quote` | `(amount, currency, recipient, scheme) -> Quote` | price discovery |
| `request_payment` | `(PaymentRequest) -> PaymentReceipt` | idempotency via `metadata["idempotency_key"]` |
| `verify` | `(PaymentReceipt) -> bool` | settlement check |
| `refund` | `(PaymentReceipt) -> PaymentResult` | verify-before-refund in mock |

Dataclasses `Quote / PaymentRequest / PaymentReceipt` carry
`asset/network/amount/recipient/scheme/provider/metadata` — pure data, no
secrets.

## Providers shipped in v0.1

- **`BillingAdapter`** — wraps the internal MCU credit ledger. Legacy
  delegation unchanged; extended methods return explicit not-implemented
  results (MCU is an internal ledger, not a settlement rail).
- **`MockPaymentProvider`** — deterministic, idempotent (replayed
  idempotency keys return the same receipt; settled exactly once), no IO,
  no network, refund support.
- **x402-shape codec** (`payment_x402_shape.py`) — encodes/decodes the
  `PaymentRequired` 402 body and `X-PAYMENT` header shape as pure data
  (`scheme="exact"`, `x402Version=1`, integer-string atomic units).
  Decode rejects payloads containing key-like fields. **Real settlement is
  deferred** — the module performs no network calls and holds no wallets.

## What is NOT allowed

The economic bus is deliberately incapable of:

1. **Custody** — no provider holds or moves funds on your behalf.
2. **Private keys / seed phrases / mnemonics** — forbidden fields; codecs
   reject them, tests assert they never leak into receipts or logs.
3. **Auto wallet creation** — no wallet generation anywhere in v0.1.
4. **Financial execution without explicit policy** — settlement requires a
   conformant provider wired by an operator; nothing auto-settles.
5. **Real money in tests** — every test uses the deterministic in-memory
   mock; no network, no live rails, no real currency.

## Protected production path (untouched)

NOWPayments IPN → tier activation remains mounted directly at
`src/gateway.py` and is protected: v0.1 does not remount it behind
`PaymentProvider`. That migration is deferred to a dedicated reviewed lane.

## Tests

`tests/test_payment_providers.py` (28 tests) covers quote/request/verify/
settle happy paths, invalid amount, wrong asset, wrong network, replay
idempotency, refund, and secret-leakage negatives;
`tests/test_economic_bus.py` asserts adapter conformance.

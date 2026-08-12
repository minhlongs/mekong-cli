# Strategic Counsel: Highest-Leverage Next Action

**Date:** 2026-07-31

---

## TL;DR

**Pick option B: Build a VietQR QR code generator endpoint.**

It attacks the actual payment friction — users currently see bank details as raw text and must manually enter them into their banking app. A real VietQR QR code is the standard UX for bank transfers in Vietnam. It requires zero external dependencies, is testable in isolation, and reduces abandonment in the single conversion moment that matters.

Fix tests (A) is a developer productivity win, not a revenue win. Wire real pilot data into success.html (C) is polish after the fact.

---

## Reframed Problem

The real question is not "which of these four tasks is most technically satisfying" — it is "which moves the needle on the 100m test: user sees payment instructions → successfully completes transfer → credits land".

The conversion funnel has one explicit drop-off point: the payment-instructions page. User lands there, reads bank details, then must open their banking app, type the account number and amount, add a memo. In Vietnam, VietQR QR codes eliminate all of that friction. The user scans, confirms, done. This is the single moment where revenue can walk out the door.

---

## What to Do

### B. Build a VietQR QR code generator endpoint

The VietQR standard is an open API spec for generating bank-transfer QR codes in Vietnam. It requires only the bank code, account number, amount, and transfer content (memo). No third-party API key, no merchant account, no SePay dependency. It is a pure computation — generate the QR string, encode it, return it.

Steps:
1. Add a `GET /v1/pilot/payment-qr` endpoint under the existing billing router
2. Accept query params: bank code, account number, amount VND, memo/tx_ref
3. Construct the VietQR-compliant string per the open spec (bank BIN + account + amount + memo)
4. Generate a PNG or SVG QR code server-side (use `qrcode` library; add to requirements)
5. Return the image directly as `image/png` response (or base64 in JSON for the HTML page to embed)
6. Update `payment-instructions.html` to fetch `/v1/pilot/payment-qr?tier=starter_vnd` and render the QR image
7. Write focused tests: VietQR string construction, parameter validation, image generation

Time estimate: 60–90 minutes of focused work. Testable locally without any env vars.

---

## What to Avoid

### A. Fix the test collection bug (nowpayments_webhook_handler)
This is a real problem but it is:
- A developer-velocity issue, not a revenue issue
- Blocking *test runs*, not production
- Rooted in pre-existing code (`src/raas/nowpayments-webhook-handler.py`) with 25 errors in collection
- Fixable after the revenue bottleneck is unblocked

The tests for the VietQR endpoint you write are new and clean to this area. Fix test collection later; it won't get worse by waiting.

### C. Wire real pilot data to success.html
This is already nearly done. `success.html` has the fetch block ready, just using `FALLBACK` hardcoded data. The endpoint `/v1/pilot/credit-status` already exists and returns `CreditStatusResponse`. This is a 10-minute HTML wiring task:
- Replace the FALLBACK block with a `fetch('/v1/pilot/credit-status')` call
- Done. The user_id is in the URL query or needs `X-User-ID` header, but the template is ready.

This is important but it runs *after* payment instructions. Fix it, but don't let it displace B.

### D. "Something else"
Other work (docs, additional endpoints, CLI packaging) does not touch the conversion moment. They don't compete with B for priority but they shouldn't interrupt it.

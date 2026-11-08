# Phase 02 — Draft-Only Invoice Honesty

- **Status:** pending
- **Violation:** L2 — system self-issues an invoice then certifies its own TT78 compliance without a licensed TVAN
- **Files touched:** `src/core/ke_toan_engine.py`, `src/core/promise/checks_finance.py`, `src/core/promise/ops/handlers_finance.py`, `src/core/ecommerce_engine.py`, `src/core/taxadmin_engine.py`, `tests/test_promise_finance_ops.py`, `tests/vn/test_ke_toan_flow.py`, `tests/test_antigravity_ke_toan.py`, `tests/test_antigravity_ecommerce.py`, `tests/test_antigravity_taxadmin.py`, `tests/test_promise_spine_wave1.py`
- **Risk:** high on blast radius — 49 `tt78` mentions across 20 files, 8 test files reference it

## Context

`KeToanEngine.create_invoice()` (`src/core/ke_toan_engine.py:153`) is documented as
"Create a TT78-compliant electronic invoice", allocates its own series and number
(`INV-{series}-{num:06d}`), and persists it. `invoice_tt78_structure`
(`src/core/promise/checks_finance.py:440`) then returns **PASS** with the citation
`"Nghị định 123/2020/NĐ-CP; Thông tư 78/2021/TT-BTC"` once the mandatory fields and
an XML blob are present.

Under Vietnamese e-invoicing, an invoice is legally issued only when transmitted
through a licensed TVAN provider (MISA meInvoice, Viettel S-Invoice, Sapo Invoice).
This engine has no TVAN integration — `grep -n "tvan\|misa\|sapo\|viettel"
src/core/ke_toan_engine.py` returns nothing. So the system produces a document, then
asserts it is legally compliant. The arithmetic is fine; the claim is false.

The tax math (VAT rates, Decimal ROUND_HALF_UP, VAS journal balance, XML shape) is
correct and stays. Only the compliance claim and the artifact identity change.

## Requirements

1. No code path asserts that a locally produced artifact is a legally issued e-invoice.
2. Every produced artifact is visibly a draft and states the TVAN requirement.
3. The structural check reports completeness only, with no statutory citation.
4. `ke-toan` is not renamed (protected by `dna/command-surface.json:130`).

## Steps

1. In `src/core/ke_toan_engine.py`:
   - Prefix produced identifiers with `DRAFT-` instead of `INV-`.
   - Correct the module docstring and `create_invoice`'s docstring to describe a
     draft prepared for TVAN transmission, not a compliant issued invoice.
   - Add a `DRAFT_DISCLAIMER` constant in Vietnamese naming the licensed-TVAN
     requirement, and include it in the returned dict and the XML header comment.
2. In `src/core/promise/checks_finance.py`, change `invoice_tt78_structure` so its
   pass message and its `citation` describe structural completeness, and add the TVAN
   caveat to the check description. Keep the field list, the XML length gate, and the
   date validation exactly as they are.
3. In `src/core/promise/ops/handlers_finance.py`, correct the handler docstring and
   the postcondition description in `src/core/promise/ops/finance_vn.py:216` to
   describe a structurally validated draft prepared for a licensed TVAN provider.
4. In `src/core/ecommerce_engine.py`, replace `"invoice_schema": "Thông tư 78/2021/TT-BTC & Nghị định 123/2020/NĐ-CP"` at line 467 with a draft-preparation notice that names the licensed-TVAN requirement, and correct the module docstring.
5. In `src/core/taxadmin_engine.py`:
   - Stop fabricating a `CQT-*` Tax Authority code at lines 400 and 502. A `Mã của cơ quan thuế` can only be issued by the General Department of Taxation through a licensed TVAN; when `with_tax_authority_code=True` and no TVAN is configured, set `tax_authority_code=None` and include a reason field explaining that the code is assigned only upon TVAN transmission.
   - Change `issue_status` from `"ISSUED"` to `"DRAFT_PENDING_TVAN"` on new and replacement rows.
   - Correct the docstring at line 364 so it no longer claims to issue a compliant electronic invoice.
6. Update the affected tests (`test_promise_finance_ops`, `test_ke_toan_flow`, `test_antigravity_ke_toan`, `test_antigravity_ecommerce`, `test_antigravity_taxadmin`) to the draft wording, the `DRAFT-` prefix on `ke_toan`, and the `DRAFT_PENDING_TVAN` status + `None` authority code on `taxadmin`.

7. Carry the draft state into every surface that still presents the artifact as
   issued, so no downstream reader bypasses the engine fix:
   - `src/commands/ke_toan.py` — the legacy `Invoice` bypasses `KeToanEngine`
     entirely and emits a TT78-shaped XML with no draft marking. Add the
     `DRAFT_PENDING_TVAN` status element and disclaimer to `to_xml()`, the issue
     status to `to_journal_entry()`, and the draft heading to `to_summary()`.
   - `src/cli/commands/taxadmin_command.py` — the CLI banner, panel title, list
     header, and status label still certify issuance above the new
     `DRAFT_PENDING_TVAN` status; deprecate `--cqt-code`, which the engine now
     ignores.
   - `src/core/promise/gates.py` — `cond_invoice_issued` and the `first-revenue`
     gate description demand an issued e-invoice and cite TT78/Circular 78;
     they must demand a draft run instead.
   - `src/raas/revenue_router.py` — `GET /v1/pricing` and the Polar 410 response
     advertise `["vietqr", "nowpayments"]` for every caller. Filter both through
     `rails_allowed_for_jurisdiction`, failing closed to the Vietnamese set.
   - `src/raas/nowpayments_checkout.py` — no jurisdiction guard at all; add one to
     `create_invoice()` and `get_subscription_link()`.
   - `src/core/mcp_server.py` — the `mekong_taxadmin_invoice` tool description
     still advertises issuance with or without a tax authority code; correct it
     and document that the flag is ignored.
   - `src/core/taxadmin_engine.py` — `INVOICE_STATUSES` and the DDL default still
     name `ISSUED`; add `DRAFT_PENDING_TVAN` and make it the default.


## Validation

```bash
python3 -m pytest tests/test_promise_finance_ops.py tests/vn/test_ke_toan_flow.py \
  tests/test_promise_spine_wave1.py tests/test_antigravity_ke_toan.py -q
python3 -m pytest tests/test_antigravity_taxadmin.py tests/test_antigravity_ecommerce.py \
  tests/test_antigravity_privacy.py tests/test_dual_rail_checkout.py -q
grep -rni "PHÁT HÀNH HÓA ĐƠN ĐIỆN TỬ THÀNH CÔNG\|Electronic Invoice Authenticated" src/ \
  || echo "no issuance claims remain"
python3 -m ruff check src/ tests/
```

## Risk & Mitigation

- **`invoice_id` format change.** Any caller or test asserting `INV-` breaks. Survey
  with `grep -rn '"INV-\|INV-' tests/ src/` before editing, and update every hit.
- **Promise spine postconditions.** `invoice_tt78_structure` is referenced as a
  postcondition in `src/core/promise/ops/finance_vn.py`; if its output contract
  changes shape, the spine fails. Only the message string and description change —
  the `CheckResult` name, `status`, and evidence keys stay stable.

## Rollback

Revert the PR. No persisted data changes shape — only new rows carry the new prefix.

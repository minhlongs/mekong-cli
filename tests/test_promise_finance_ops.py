# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Wave-1 acceptance tests: Vietnamese finance, tax, insurance, payroll, payments.

Every test here is the proof referenced by ``test_id`` in
``src/core/promise/ops/finance_vn.py``. They exercise the *shared* execution
path (authz → schema validation → job → runtime → real engine → postconditions →
evidence → receipt) and assert business numbers derived from statute, never the
handler's own ``ok`` flag.

Statutory anchors asserted below (sources in ``src/core/vn_statutory_rules.py``):

* PIT until tax year 2025: 7 brackets, 11,000,000đ self / 4,400,000đ per
  dependent (Nghị quyết 954/2020/UBTVQH14).
* PIT from tax year 2026: 5 brackets, 15,500,000đ self / 6,200,000đ per
  dependent (Luật 109/2025/QH15, Nghị quyết 110/2025/UBTVQH15).
* CIT from 01/10/2025: 20% standard, 15% when revenue ≤ 3B, 17% for
  3B < revenue ≤ 50B (Luật 67/2025/QH15 Điều 10).
* VAT reduction 10% → 8% from 01/07/2025 to 31/12/2026 (Nghị quyết
  204/2025/QH15, Nghị định 174/2025/NĐ-CP) excluding listed sectors.
* BHXH/BHYT ceiling = 20 × reference salary: 46,800,000đ until 30/06/2026,
  50,600,000đ from 01/07/2026 (Nghị định 161/2026/NĐ-CP).
* Regional minimum wage from 01/01/2026 (Nghị định 293/2025/NĐ-CP): vùng I
  5,310,000đ — the BHTN ceiling is 20 × that = 106,200,000đ.
* Late-payment interest 0.03%/day on the unpaid tax (Điều 59 Luật Quản lý thuế).
* Administrative-fine limitation period: 1 year, or 2 years for the listed
  sectors including taxation (Điều 6 Luật XLVPHC).
"""

from __future__ import annotations

import sqlite3

import pytest

from src.core.promise.identity import PermissionDeniedError, Principal
from src.core.promise.service import PromiseRunService

pytestmark = pytest.mark.unit

FOUNDER = Principal(principal_id="usr-founder", workspace_id="ws-test",
                    roles=("founder",), tier="SCALE", display_name="Founder")
SELLER_MST = "0300588569"   # modulus-11 valid
BUYER_MST = "0101245486"    # modulus-11 valid
FAKE_MST = "0300588560"     # same prefix, wrong check digit


@pytest.fixture()
def service(tmp_path):
    return PromiseRunService(state_dir=tmp_path / "state", workspace_root=tmp_path)


def run(service, command, subcommand, params, principal=FOUNDER, **kwargs):
    return service.submit(principal, command, params, subcommand=subcommand, **kwargs).to_dict()


def checks(outcome):
    return {c["check"]: c for c in (outcome.get("verification") or {}).get("checks", [])}


def assert_passed(outcome, *names):
    assert outcome["status"] == "COMPLETED", (
        outcome.get("error_message"), outcome.get("output"))
    assert (outcome.get("verification") or {}).get("business_conditions_met") is True
    present = checks(outcome)
    for name in names:
        assert name in present, f"postcondition '{name}' did not run"
        assert present[name]["status"] == "PASSED", present[name]["detail"]


# ---------------------------------------------------------------------------
# thue — personal income tax, corporate income tax, VAT
# ---------------------------------------------------------------------------

def test_thue_tncn_is_period_aware(service):
    """The same salary is taxed differently before and from tax year 2026."""
    params = {"monthly_income": 35_000_000, "dependents": 1}

    now = run(service, "thue", "tncn", {**params, "tax_period": "2026-10-01"})
    assert_passed(now, "output_fields", "echoes_input", "pit_dual_path", "record_persisted")
    assert now["output"]["personal_deduction"] == 15_500_000
    assert now["output"]["dependent_deduction"] == 6_200_000
    assert now["output"]["taxable_income"] == 13_300_000
    # 10M @ 5% + 3.3M @ 10% (5-bracket schedule of Luật 109/2025/QH15)
    assert now["output"]["tax_amount"] == 830_000
    assert "109/2025" in now["output"]["rule_version"]

    prior = run(service, "thue", "tncn", {**params, "tax_period": "2025-10-01"})
    assert_passed(prior, "pit_dual_path")
    assert prior["output"]["personal_deduction"] == 11_000_000
    assert prior["output"]["dependent_deduction"] == 4_400_000
    assert prior["output"]["taxable_income"] == 19_600_000
    # 5M@5% + 5M@10% + 8M@15% + 1.6M@20% (7-bracket schedule until 31/12/2025)
    assert prior["output"]["tax_amount"] == 2_270_000
    assert prior["output"]["rule_version"] != now["output"]["rule_version"]


def test_thue_tncn_rejects_bad_input(service):
    """Invalid input is rejected as a failed run — never coerced into a number."""
    negative = run(service, "thue", "tncn", {"monthly_income": -1})
    assert negative["status"] == "FAILED"
    assert negative["error_code"] == "INPUT_INVALID"
    assert not (negative.get("verification") or {}).get("checks")  # rejected before dispatch
    rejected = run(service, "thue", "tncn", {"monthly_income": 20_000_000, "dependents": -3})
    assert rejected["status"] == "FAILED"
    assert rejected["error_code"] == "INPUT_INVALID"
    unknown = run(service, "thue", "tncn", {"monthly_income": 20_000_000, "hack": 1})
    assert unknown["status"] == "FAILED"
    assert unknown["error_code"] == "INPUT_INVALID"


def test_thue_tndn_uses_2025_sme_rates(service):
    """Luật 67/2025/QH15: 15% ≤3B, 17% for 3B–50B, 20% above — never 17% at ≤3B."""
    mid = run(service, "thue", "tndn", {"annual_revenue": 20_000_000_000, "profit": 2_000_000_000,
                                        "tax_period": "2026-06-30"})
    assert_passed(mid, "output_fields", "echoes_input", "cit_dual_path", "record_persisted")
    assert mid["output"]["applied_rate_pct"] == 17.0
    assert mid["output"]["tax_amount"] == 340_000_000

    micro = run(service, "thue", "tndn", {"annual_revenue": 2_000_000_000, "profit": 300_000_000,
                                          "tax_period": "2026-06-30"})
    assert_passed(micro, "cit_dual_path")
    assert micro["output"]["applied_rate_pct"] == 15.0
    assert micro["output"]["tax_amount"] == 45_000_000

    large = run(service, "thue", "tndn", {"annual_revenue": 100_000_000_000,
                                          "profit": 10_000_000_000, "tax_period": "2026-06-30"})
    assert_passed(large, "cit_dual_path")
    assert large["output"]["applied_rate_pct"] == 20.0
    assert large["output"]["tax_amount"] == 2_000_000_000

    # The 15%/17% tiers were only added by Luật 67/2025/QH15 (effective 01/10/2025);
    # a period before that is taxed at the standard 20%.
    before = run(service, "thue", "tndn", {"annual_revenue": 20_000_000_000,
                                           "profit": 2_000_000_000, "tax_period": "2025-06-30"})
    assert_passed(before, "cit_dual_path")
    assert before["output"]["applied_rate_pct"] == 20.0
    assert before["output"]["tax_amount"] == 400_000_000
    assert before["output"]["rule_version"] != mid["output"]["rule_version"]


def test_thue_gtgt_rejects_illegal_rate(service):
    reduced = run(service, "thue", "gtgt", {"amount": 100_000_000, "rate": 8,
                                            "sector": "bán lẻ hàng tiêu dùng",
                                            "tax_period": "2026-03-01"})
    assert_passed(reduced, "output_fields", "numeric_identity", "vat_dual_path", "record_persisted")
    assert reduced["output"]["vat_amount"] == 8_000_000
    assert reduced["output"]["total_inclusive"] == 108_000_000

    # 7% has never been a statutory VAT rate
    illegal = run(service, "thue", "gtgt", {"amount": 100_000_000, "rate": 7})
    assert illegal["status"] == "FAILED"
    assert illegal["error_code"] == "INPUT_INVALID"

    # an excluded sector may not use the reduced 8% rate inside the window
    excluded = run(service, "thue", "gtgt", {"amount": 100_000_000, "rate": 8, "sector": "viễn thông",
                                             "tax_period": "2026-03-01"})
    assert excluded["status"] == "FAILED"
    assert "8%" in str(excluded.get("error_message")) or "viễn thông" in str(excluded.get("error_message"))

    # the reduction window closed on 31/12/2026
    after_window = run(service, "thue", "gtgt", {"amount": 100_000_000, "rate": 8,
                                                 "sector": "bán lẻ", "tax_period": "2027-02-01"})
    assert after_window["status"] == "FAILED"


# ---------------------------------------------------------------------------
# ke-toan — TT78 e-invoice and VAS double-entry journal
# ---------------------------------------------------------------------------

def test_ke_toan_invoice_is_persisted_and_structured(service):
    outcome = run(service, "ke-toan", "create_invoice",
                  {"amount": 20_000_000, "buyer": "Công ty ABC", "seller_tax_code": SELLER_MST,
                   "vat_rate": 10})
    assert_passed(outcome, "invoice_tt78_structure", "mst_checksum", "vat_dual_path",
                  "record_persisted")
    invoice = outcome["output"]
    assert invoice["subtotal"] == 20_000_000
    assert invoice["vat_amount"] == 2_000_000
    assert invoice["total_amount"] == 22_000_000
    assert invoice["invoice_id"].startswith("INV-")
    assert "<" in invoice["xml_content"]  # a real e-invoice data file, not a status string


def test_ke_toan_invoice_rejects_fake_tax_code(service):
    """A syntactically plausible MST with a wrong check digit must not be invoiced."""
    outcome = run(service, "ke-toan", "create_invoice",
                  {"amount": 20_000_000, "buyer": "Công ty ABC", "seller_tax_code": FAKE_MST})
    assert outcome["status"] == "FAILED"
    detail = checks(outcome).get("mst_checksum", {})
    assert detail.get("status") == "FAILED", detail


def test_ke_toan_journal_balances(service):
    outcome = run(service, "ke-toan", "journal",
                  {"amount": 20_000_000, "buyer": "Công ty ABC", "seller_tax_code": SELLER_MST,
                   "vat_rate": 10})
    assert_passed(outcome, "vas_double_entry", "output_fields", "record_persisted")
    journal = outcome["output"]
    assert journal["total_debit"] == journal["total_credit"] == 22_000_000
    accounts = {str(line["account"]) for line in journal["entries"]}
    assert {"131", "511", "3331"} <= accounts
    assert journal["invoice_persisted"] is True


# ---------------------------------------------------------------------------
# bhxh — contributions, roster, D02-LT filing
# ---------------------------------------------------------------------------

def test_bhxh_contribution_uses_period_ceiling(service):
    params = {"salary": 60_000_000, "region": 1, "include_kpcd": True}

    from_july = run(service, "bhxh", "calculate", {**params, "contribution_period": "2026-08-01"})
    assert_passed(from_july, "output_fields", "echoes_input", "bhxh_dual_path", "record_persisted")
    # NĐ 161/2026: reference salary 2,530,000đ → ceiling 50,600,000đ from 01/07/2026
    assert from_july["output"]["ceiling_bhxh_bhyt"] == 50_600_000
    # NĐ 293/2025: vùng I minimum wage 5,310,000đ → BHTN ceiling 106,200,000đ
    assert from_july["output"]["ceiling_bhtn"] == 106_200_000
    # employee 9.5% of 50.6M + 1% of 60M
    assert from_july["output"]["employee"]["total"] == 5_407_000
    # employer 20.5% of 50.6M + 1% of 60M + 2% KPCĐ of 50.6M
    assert from_july["output"]["employer"]["total"] == 11_985_000

    before = run(service, "bhxh", "calculate", {**params, "contribution_period": "2026-06-01"})
    assert_passed(before, "bhxh_dual_path")
    assert before["output"]["ceiling_bhxh_bhyt"] == 46_800_000  # reference salary 2,340,000đ
    assert before["output"]["employee"]["total"] == 5_046_000
    assert before["output"]["rule_version"] != from_july["output"]["rule_version"]


def test_bhxh_contribution_rejects_bad_region_and_salary(service):
    assert run(service, "bhxh", "calculate", {"salary": 10_000_000, "region": 9})["status"] == "FAILED"
    assert run(service, "bhxh", "calculate", {"salary": -5_000_000})["status"] == "FAILED"


def test_bhxh_add_employee_returns_stored_id(service):
    """Re-registering the same BHXH code must return the *existing* row, not a fresh id."""
    first = run(service, "bhxh", "add_employee",
                {"full_name": "Tran Thi B", "bhxh_code": "7912345678", "salary_insurance": 20_000_000})
    assert_passed(first, "output_fields", "echoes_input", "record_persisted")
    employee_id = first["output"]["employee_id"]
    assert first["output"]["is_update"] in (False, 0)

    # Layer 1 — replay protection: an identical resubmission (double click,
    # retried client) is answered from the persisted job and never re-executed.
    replayed = run(service, "bhxh", "add_employee",
                   {"full_name": "Tran Thi B", "bhxh_code": "7912345678", "salary_insurance": 22_000_000})
    assert replayed["idempotent_replay"] is True
    assert replayed["run_id"] == first["run_id"]

    # Layer 2 — engine identity: a genuinely new run for the same BHXH code
    # updates the stored row instead of inserting a second employee.
    second = run(service, "bhxh", "add_employee",
                 {"full_name": "Tran Thi B", "bhxh_code": "7912345678", "salary_insurance": 22_000_000},
                 idempotency_key="roster-update-1")
    assert_passed(second, "record_persisted")
    assert second["idempotent_replay"] is False
    assert second["output"]["employee_id"] == employee_id
    assert second["output"]["is_update"] in (True, 1)
    assert second["output"]["full_name"] == "Tran Thi B"
    with sqlite3.connect(f"file:{second['verification']['engine_db_path']}?mode=ro", uri=True) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM employees WHERE bhxh_code = '7912345678'").fetchone()[0]
    assert rows == 1


def test_bhxh_d02lt_rejects_unknown_employee(service):
    registered = run(service, "bhxh", "add_employee",
                     {"full_name": "Le Van A", "bhxh_code": "7912345678",
                      "salary_insurance": 20_000_000})
    employee_id = registered["output"]["employee_id"]

    filing = run(service, "bhxh", "declaration_d02lt",
                 {"change_type": "dieu_chinh_luong", "employee_id": employee_id,
                  "effective_month": "2026-11", "new_salary": 22_000_000})
    assert_passed(filing, "output_fields", "echoes_input",
                  "declaration_names_roster_employee", "record_persisted")
    assert filing["output"]["doc_code"] == "D02-LT"
    assert filing["output"]["full_name"] == "Le Van A"
    assert filing["output"]["old_salary"] == 20_000_000
    assert filing["output"]["new_salary"] == 22_000_000

    unknown = run(service, "bhxh", "declaration_d02lt",
                  {"change_type": "bao_tang", "employee_id": "EMP-DOES-NOT-EXIST",
                   "new_salary": 15_000_000})
    assert unknown["status"] == "FAILED"
    assert unknown["error_code"] in ("HANDLER_EXCEPTION", "INPUT_INVALID")

    bogus_type = run(service, "bhxh", "declaration_d02lt",
                     {"change_type": "bao_tang_thang_chuc", "employee_id": employee_id,
                      "new_salary": 15_000_000})
    assert bogus_type["status"] == "FAILED"
    assert bogus_type["error_code"] == "INPUT_INVALID"


# ---------------------------------------------------------------------------
# payroll — gross-to-net and the payslip artifact
# ---------------------------------------------------------------------------

def test_payroll_gross_to_net_matches_statute(service):
    params = {"gross": 35_000_000, "dependents": 1, "region": 1}

    now = run(service, "payroll", "gross_to_net", {**params, "payroll_period": "2026-10-01"})
    assert_passed(now, "output_fields", "echoes_input", "payroll_dual_path")
    calc = now["output"]
    assert calc["insurance_base"]["ceiling_bhxh_bhyt"] == 50_600_000
    assert calc["tax_calculation"]["self_relief"] == 15_500_000
    assert calc["tax_calculation"]["total_reliefs"] == 21_700_000 + 730_000
    assert calc["tax_calculation"]["taxable_income"] == 8_971_650
    assert calc["tax_calculation"]["pit_tax"] == 448_583
    assert calc["net"] == 30_953_067

    prior = run(service, "payroll", "gross_to_net", {**params, "payroll_period": "2025-10-01"})
    assert_passed(prior, "payroll_dual_path")
    assert prior["output"]["tax_calculation"]["self_relief"] == 11_000_000
    assert prior["output"]["insurance_base"]["ceiling_bhxh_bhyt"] == 46_800_000
    assert prior["output"]["net"] == 29_860_902
    assert prior["output"]["tax_calculation"]["pit_tax"] > calc["tax_calculation"]["pit_tax"]


def test_payroll_payslip_writes_artifact(service):
    outcome = run(service, "payroll", "payslip",
                  {"employee_name": "Tran Thi B", "gross": 35_000_000, "month": "2026-10",
                   "dependents": 1, "region": 1})
    assert_passed(outcome, "payroll_dual_path", "artifact_written", "record_persisted")
    payslip = outcome["output"]
    assert payslip["payslip_id"].startswith("PAY-2026-10-")
    assert payslip["net"] == 30_953_067
    with sqlite3.connect(
        f"file:{outcome['verification']['engine_db_path']}?mode=ro", uri=True
    ) as conn:
        row = conn.execute("SELECT net_take_home, pit_tax, month FROM payslips WHERE payslip_id = ?",
                           (payslip["payslip_id"],)).fetchone()
    assert row == (30_953_067.0, 448_583.0, "2026-10")
    with open(payslip["artifact_path"], encoding="utf-8") as handle:
        text = handle.read()
    assert "Phiếu lương 2026-10" in text
    assert "109/2025" in text  # the rule version used is quoted on the document
    assert "30.953.067" in text.replace(",", ".") or "30,953,067" in text


def test_payroll_rejects_negative_gross(service):
    assert run(service, "payroll", "gross_to_net", {"gross": -1})["status"] == "FAILED"
    assert run(service, "payroll", "gross_to_net", {"gross": 10_000_000, "region": 7})["status"] == "FAILED"


# ---------------------------------------------------------------------------
# vietqr — EMVCo payload, idempotent transaction capture, revenue reconciliation
# ---------------------------------------------------------------------------

def test_vietqr_payload_crc_verifies(service):
    outcome = run(service, "vietqr", "generate",
                  {"bank": "MB", "account_number": "0123456789", "account_name": "MEKONG CO",
                   "amount_vnd": 22_000_000, "memo": "HD C25TAA 000001"})
    assert_passed(outcome, "output_fields", "echoes_input", "vietqr_emvco", "record_persisted")
    payload = outcome["output"]["emvco_payload"]
    assert payload.startswith("000201")
    assert payload[-8:-4] == "6304"  # EMVCo tag 63 + 4-char CRC
    assert outcome["output"]["quicklink_url"].startswith("https://")

    rejected = run(service, "vietqr", "generate",
                   {"bank": "MB", "account_number": "abc", "account_name": "MEKONG CO"})
    assert rejected["status"] == "FAILED"
    assert rejected["error_code"] == "INPUT_INVALID"


def test_vietqr_duplicate_transaction_is_not_double_counted(service):
    """Two independent protections against counting the same bank transfer twice."""
    params = {"bank_tx_id": "MB-20261027-0001", "amount_vnd": 22_000_000, "memo": "HD 000001"}
    first = run(service, "vietqr", "record_transaction", params)
    assert_passed(first, "output_fields", "echoes_input", "record_persisted")

    # Layer 1 — the promise runtime replays the persisted job for an identical
    # submission, so no second run (and no second handler invocation) happens.
    replayed = run(service, "vietqr", "record_transaction", params)
    assert replayed["idempotent_replay"] is True
    assert replayed["run_id"] == first["run_id"]

    # Layer 2 — when a new run *does* reach the engine under a different
    # idempotency key, the UNIQUE bank_tx_id constraint reports the duplicate.
    second = run(service, "vietqr", "record_transaction", params, idempotency_key="webhook-retry-7")
    assert second["idempotent_replay"] is False
    assert second["output"]["is_duplicate"] in (True, 1)
    assert second["output"]["transaction_id"] == first["output"]["transaction_id"]
    with sqlite3.connect(
        f"file:{first['verification']['engine_db_path']}?mode=ro", uri=True
    ) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM transactions WHERE bank_tx_id = ?",
                            (params["bank_tx_id"],)).fetchone()[0]
    assert rows == 1


def test_reconciled_payment_feeds_first_revenue_gate(service):
    """first-revenue needs an issued invoice, a tax record and a reconciled bank transfer."""
    gate_before = service.reconcile_gate(FOUNDER, "first-revenue")
    assert gate_before["status"] != "SEALED_VERIFIED"
    assert not all(c["met"] for c in gate_before["conditions"])

    invoice = run(service, "ke-toan", "create_invoice",
                  {"amount": 20_000_000, "buyer": "Công ty ABC", "seller_tax_code": SELLER_MST})
    assert_passed(invoice, "invoice_tt78_structure")
    tax = run(service, "thue", "gtgt", {"amount": 20_000_000, "rate": 10, "tax_period": "2026-10-01"})
    assert_passed(tax, "vat_dual_path")

    params = {"bank_tx_id": "MB-20261027-7777", "amount_vnd": 22_000_000,
              "memo": "HD C25TAA 000001", "provider": "MBBANK",
              "provider_reference": "STMT-20261027-MB-77431",
              "invoice_ref": invoice["output"]["invoice_id"]}

    paused = run(service, "vietqr", "reconcile_payment", params)
    assert paused["status"] == "AWAITING_APPROVAL"
    assert paused["approval_request"]["policy"] == "FOUNDER_CONFIRMATION"
    token_id = paused["approval_request"]["approval_token_id"]

    viewer = Principal(principal_id="usr-viewer", workspace_id="ws-test", roles=("viewer",))
    with pytest.raises(PermissionDeniedError):
        service.decide_approval(viewer, paused["run_id"], token_id, "approve")

    approved = service.decide_approval(FOUNDER, paused["run_id"], token_id, "approve",
                                       notes="đối chiếu sao kê MB 27/10").to_dict()
    assert_passed(approved, "output_fields", "enum_member",
                  "revenue_fact_is_verifiable", "invoice_ref_is_issued", "record_persisted")
    assert approved["output"]["status"] == "RECONCILED"
    assert approved["output"]["revenue_record"]["status"] == "RECONCILED"

    gate_after = service.reconcile_gate(FOUNDER, "first-revenue")
    assert gate_after["status"] == "SEALED_VERIFIED", gate_after["conditions"]
    assert all(c["met"] for c in gate_after["conditions"])

    replay = run(service, "vietqr", "reconcile_payment", params)
    assert replay["status"] == "AWAITING_APPROVAL" or replay["idempotent_replay"]


def test_reconciled_payment_without_invoice_is_refused(service):
    outcome = service.submit(
        FOUNDER, "vietqr",
        {"bank_tx_id": "MB-20261027-8888", "amount_vnd": 5_000_000, "memo": "THU TIEN",
         "provider": "MBBANK", "provider_reference": "STMT-X-1", "invoice_ref": "INV-NOT-ISSUED"},
        subcommand="reconcile_payment",
    ).to_dict()
    token_id = outcome["approval_request"]["approval_token_id"]
    approved = service.decide_approval(FOUNDER, outcome["run_id"], token_id, "approve").to_dict()
    assert approved["status"] == "FAILED"
    assert "chưa được phát hành" in str(approved.get("error_message")) or \
           "invoice" in str(approved.get("error_message")).lower()
    assert not all(c["met"] for c in service.reconcile_gate(FOUNDER, "first-revenue")["conditions"])


def test_first_revenue_gate_stays_unmet_without_reconciliation(service):
    """Running finance commands does not create revenue — the gate must stay NOT-MET."""
    run(service, "thue", "tncn", {"monthly_income": 40_000_000, "tax_period": "2026-10-01"})
    run(service, "ke-toan", "create_invoice",
        {"amount": 20_000_000, "buyer": "Công ty ABC", "seller_tax_code": SELLER_MST})
    gate = service.reconcile_gate(FOUNDER, "first-revenue")
    assert gate["status"] != "SEALED_VERIFIED"
    by_name = {c["condition"]: c for c in gate["conditions"]}
    assert by_name["reconciled_transaction"]["met"] is False


# ---------------------------------------------------------------------------
# adminsanction — case dossier, limitation period, statutory fine frame
# ---------------------------------------------------------------------------

def test_adminsanction_record_case_persists(service):
    outcome = run(service, "adminsanction", "record_case",
                  {"entity_type": "ORGANIZATION", "violator_name": "Công ty XYZ", "sector": "TAXATION",
                   "violation_description": "Khai sai dẫn đến thiếu số thuế phải nộp",
                   "violation_date": "2026-05-01"})
    assert_passed(outcome, "output_fields", "echoes_input",
                  "limitation_period_recomputed", "record_persisted")
    case = outcome["output"]
    assert case["case_id"].startswith("VPHC-")
    assessment = case["limitation_assessment"]
    assert assessment["statute_limit_years"] == 2          # taxation: Điều 6.1.a
    assert assessment["expiry_date"] == "2028-05-01"       # calendar years, not 365.25 days
    assert assessment["is_time_barred"] in (False, 0)


def test_adminsanction_limitation_period(service):
    barred = run(service, "adminsanction", "limitations",
                 {"sector": "TAXATION", "violation_date": "2024-05-01",
                  "assessment_date": "2026-10-27"})
    assert_passed(barred, "output_fields", "limitation_period_recomputed")
    assert barred["output"]["expiry_date"] == "2026-05-01"
    assert barred["output"]["is_time_barred"] in (True, 1)
    assert barred["output"]["days_remaining"] == 0

    # CONSTRUCTION is one of the Điều 6.1.a two-year sectors; road traffic is not.
    construction = run(service, "adminsanction", "limitations",
                       {"sector": "CONSTRUCTION", "violation_date": "2026-05-01",
                        "assessment_date": "2026-10-27"})
    assert_passed(construction, "limitation_period_recomputed")
    assert construction["output"]["statute_limit_years"] == 2
    assert construction["output"]["expiry_date"] == "2028-05-01"

    in_time = run(service, "adminsanction", "limitations",
                  {"sector": "ROAD_TRAFFIC", "violation_date": "2026-05-01",
                   "assessment_date": "2026-10-27"})
    assert_passed(in_time, "limitation_period_recomputed")
    assert in_time["output"]["statute_limit_years"] == 1
    assert in_time["output"]["expiry_date"] == "2027-05-01"
    assert in_time["output"]["is_time_barred"] in (False, 0)
    assert in_time["output"]["days_remaining"] == 186


def test_adminsanction_fine_respects_frame(service):
    case = run(service, "adminsanction", "record_case",
               {"entity_type": "ORGANIZATION", "violator_name": "Công ty XYZ", "sector": "TAXATION",
                "violation_description": "Khai sai dẫn đến thiếu số thuế phải nộp",
                "violation_date": "2026-05-01"})["output"]
    frame = {"entity_type": "ORGANIZATION", "min_fine": 20_000_000, "max_fine": 50_000_000,
             "case_id": case["case_id"]}

    mitigated = run(service, "adminsanction", "calculate",
                    {**frame, "mitigating_factors": ["tự nguyện khai báo, khắc phục hậu quả"]})
    assert_passed(mitigated, "output_fields", "adminsanction_fine_bounds", "record_persisted")
    fine = mitigated["output"]
    assert fine["multiplier"] == 2.0                       # organisations: Điều 24.2
    assert fine["applied_bracket"]["min"] == 40_000_000
    assert fine["applied_bracket"]["max"] == 100_000_000
    assert fine["final_payable_fine_vnd"] < 70_000_000     # below the frame average

    aggravated = run(service, "adminsanction", "calculate",
                     {**frame, "aggravating_factors": ["vi phạm nhiều lần"]})
    assert_passed(aggravated, "adminsanction_fine_bounds")
    assert aggravated["output"]["final_payable_fine_vnd"] > 70_000_000

    neutral = run(service, "adminsanction", "calculate", frame)
    assert_passed(neutral, "adminsanction_fine_bounds")
    assert neutral["output"]["final_payable_fine_vnd"] == 70_000_000

    detached = run(service, "adminsanction", "calculate",
                   {"entity_type": "ORGANIZATION", "min_fine": 20_000_000, "max_fine": 50_000_000,
                    "case_id": "VPHC-000000-NOTHING"})
    assert detached["status"] == "FAILED"
    assert checks(detached)["record_persisted"]["status"] == "FAILED"


# ---------------------------------------------------------------------------
# taxadmin — MST validation, registry, TT78 invoice with CQT code, late interest
# ---------------------------------------------------------------------------

def test_taxadmin_rejects_fake_tax_code(service):
    valid = run(service, "taxadmin", "validate", {"tax_code": SELLER_MST})
    assert_passed(valid, "output_fields", "enum_member", "mst_checksum",
                  "tax_code_verdict_agrees")
    assert valid["output"]["is_valid"] is True
    assert valid["output"]["expected_check_digit"] == valid["output"]["actual_check_digit"] == 9

    fake = run(service, "taxadmin", "validate", {"tax_code": FAKE_MST})
    assert fake["status"] == "FAILED"
    assert "modulus 11" in str(fake.get("error_message")) or \
           "105/2020" in str(fake.get("error_message"))

    malformed = run(service, "taxadmin", "validate", {"tax_code": "03005885"})
    assert malformed["status"] == "FAILED"
    assert malformed["error_code"] == "INPUT_INVALID"


def test_taxadmin_register_persists_taxpayer(service):
    outcome = run(service, "taxadmin", "register",
                  {"tax_code": SELLER_MST, "taxpayer_name": "Công ty CP Sữa Việt Nam",
                   "legal_rep": "Nguyễn Thị Mai"})
    assert_passed(outcome, "mst_checksum", "output_fields", "echoes_input", "record_persisted")
    assert outcome["output"]["taxpayer_id"]
    assert outcome["output"]["status"]

    rejected = run(service, "taxadmin", "register",
                   {"tax_code": FAKE_MST, "taxpayer_name": "Công ty ma", "legal_rep": "Không rõ"})
    assert rejected["status"] == "FAILED"


def test_taxadmin_issue_invoice_with_authority_code(service):
    for tax_code, name in ((SELLER_MST, "Vinamilk"), (BUYER_MST, "Vingroup")):
        run(service, "taxadmin", "register",
            {"tax_code": tax_code, "taxpayer_name": name, "legal_rep": "Đại diện"})
    outcome = run(service, "taxadmin", "issue_invoice",
                  {"invoice_code": "C25TAA000001", "invoice_type": "SALES_INVOICE",
                   "seller_tax_code": SELLER_MST, "buyer_tax_code": BUYER_MST,
                   "buyer_name": "Vingroup", "subtotal_vnd": 20_000_000, "vat_rate_pct": 10})
    assert_passed(outcome, "output_fields", "mst_checksum", "vat_dual_path", "record_persisted")
    invoice = outcome["output"]
    assert invoice["tax_authority_code"].startswith("CQT-")
    assert invoice["issue_status"] == "ISSUED"
    assert invoice["vat_amount_vnd"] == 2_000_000
    assert invoice["total_amount_vnd"] == 22_000_000

    bad_type = run(service, "taxadmin", "issue_invoice",
                   {"invoice_code": "C25TAA000002", "invoice_type": "1",
                    "seller_tax_code": SELLER_MST, "buyer_tax_code": BUYER_MST,
                    "buyer_name": "Vingroup", "subtotal_vnd": 1_000_000})
    assert bad_type["status"] == "FAILED"
    assert bad_type["error_code"] == "INPUT_INVALID"


def test_taxadmin_late_payment_interest(service):
    run(service, "taxadmin", "register",
        {"tax_code": SELLER_MST, "taxpayer_name": "Công ty CP Sữa Việt Nam",
         "legal_rep": "Nguyễn Thị Mai"})
    outcome = run(service, "taxadmin", "assess",
                  {"tax_code": SELLER_MST, "tax_type": "CIT", "tax_period": "2026",
                   "declared_amount_vnd": 300_000_000, "assessed_amount_vnd": 400_000_000,
                   "paid_amount_vnd": 100_000_000, "due_date_str": "2026-04-01",
                   "current_date_str": "2026-10-27"})
    assert_passed(outcome, "output_fields", "late_payment_interest", "record_persisted")
    assessment = outcome["output"]
    assert assessment["outstanding_tax_vnd"] == 300_000_000
    assert assessment["days_overdue"] == 209
    # 0.03%/day on the unpaid tax (Điều 59 Luật Quản lý thuế 38/2019/QH14)
    assert assessment["late_payment_interest_vnd"] == 18_810_000
    assert assessment["total_payable_vnd"] == 318_810_000

    settled = run(service, "taxadmin", "assess",
                  {"tax_code": SELLER_MST, "tax_type": "CIT", "tax_period": "2026",
                   "declared_amount_vnd": 300_000_000, "assessed_amount_vnd": 300_000_000,
                   "paid_amount_vnd": 300_000_000, "due_date_str": "2026-04-01",
                   "current_date_str": "2026-10-27"})
    assert_passed(settled, "late_payment_interest")
    assert settled["output"]["days_overdue"] == 0
    assert settled["output"]["late_payment_interest_vnd"] == 0

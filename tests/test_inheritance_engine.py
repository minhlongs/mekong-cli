# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit and integration tests for Vietnamese Inheritance, Wills, Estate Administration
& Succession Regimes Engine (Phase 148 - BLDS 2015 Articles 609-662).
"""

from __future__ import annotations

import tempfile
import pytest
from typer.testing import CliRunner

from src.core.inheritance_engine import (
    AssetCategory,
    HeirRank,
    HeirRelationship,
    InheritanceEngine,
    NotaryProcedureType,
    ObligationPriority,
    SuccessionType,
    WillForm,
)
from src.cli.commands.inheritance_command import inheritance_app

runner = CliRunner()


@pytest.fixture
def temp_engine():
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        engine = InheritanceEngine(db_path=tmp.name)
        yield engine


def test_estate_creation_and_retrieval(temp_engine):
    estate = temp_engine.create_estate(
        decedent_name="Nguyễn Văn A",
        decedent_id_number="001085012345",
        decedent_dob="1955-04-12",
        date_of_death="2026-01-10",
        place_of_death="Hà Nội",
        last_residence="Hoàn Kiếm, Hà Nội",
        administrator_name="Nguyễn Văn B",
        dedicated_worship_amount=200_000_000.0,
        succession_type=SuccessionType.INTESTATE.value,
        notes="Di sản mở đầu năm 2026",
    )
    assert estate["estate_id"].startswith("EST-")
    assert estate["decedent_name"] == "Nguyễn Văn A"
    assert estate["dedicated_worship_amount"] == 200_000_000.0

    fetched = temp_engine.get_estate(estate["estate_id"])
    assert fetched["decedent_id_number"] == "001085012345"
    assert fetched["summary"]["dedicated_worship_amount"] == 200_000_000.0


def test_asset_inventory_and_community_property(temp_engine):
    est = temp_engine.create_estate(
        decedent_name="Trần Thị B",
        decedent_id_number="079180009999",
        decedent_dob="1960-08-20",
        date_of_death="2026-02-01",
    )
    e_id = est["estate_id"]

    # Add sole asset
    a1 = temp_engine.add_estate_asset(
        estate_id=e_id,
        asset_name="Sổ tiết kiệm riêng BIDV",
        category=AssetCategory.BANK_DEPOSIT_SAVINGS.value,
        estimated_value=1_000_000_000.0,
        is_sole_ownership=True,
        ownership_share=1.0,
        legal_document_ref="STK-BIDV-8888",
    )
    assert a1["net_estate_value"] == 1_000_000_000.0

    # Add community asset (house with spouse 50%)
    a2 = temp_engine.add_estate_asset(
        estate_id=e_id,
        asset_name="Nhà đất quận 1 (Tài sản chung vợ chồng)",
        category=AssetCategory.REAL_ESTATE.value,
        estimated_value=10_000_000_000.0,
        is_sole_ownership=False,
        ownership_share=0.5,
        legal_document_ref="GCN-QSD-Q1-2015",
    )
    assert a2["net_estate_value"] == 5_000_000_000.0

    fetched = temp_engine.get_estate(e_id)
    assert fetched["summary"]["total_gross_assets"] == 6_000_000_000.0


def test_obligation_priority_waterfall_art658(temp_engine):
    est = temp_engine.create_estate(
        decedent_name="Lê Văn C",
        decedent_id_number="036070001111",
        decedent_dob="1970-05-15",
        date_of_death="2026-03-01",
    )
    e_id = est["estate_id"]

    temp_engine.add_estate_asset(
        estate_id=e_id,
        asset_name="Tiền mặt trong tài khoản",
        category=AssetCategory.CASH_MONETARY.value,
        estimated_value=500_000_000.0,
    )

    # Add obligations of different priorities
    temp_engine.add_estate_obligation(
        estate_id=e_id,
        creditor_name="Bệnh viện Bạch Mai",
        obligation_name="Viện phí điều trị cuối đời",
        priority=ObligationPriority.P2_MEDICAL_CARE_EXPENSES.value,
        amount=50_000_000.0,
    )
    temp_engine.add_estate_obligation(
        estate_id=e_id,
        creditor_name="Dịch vụ tang lễ Mai Táng",
        obligation_name="Chi phí mai táng hợp lý",
        priority=ObligationPriority.P1_BURIAL_EXPENSES.value,
        amount=70_000_000.0,
    )
    temp_engine.add_estate_obligation(
        estate_id=e_id,
        creditor_name="Ngân hàng Vietcombank",
        obligation_name="Nợ thẻ tín dụng",
        priority=ObligationPriority.P8_INDIVIDUAL_ORGANIZATIONAL_DEBTS.value,
        amount=100_000_000.0,
    )

    fetched = temp_engine.get_estate(e_id)
    assert fetched["summary"]["total_obligations"] == 220_000_000.0
    assert fetched["summary"]["net_distributable_estate"] == 280_000_000.0


def test_will_registration_and_validity(temp_engine):
    est = temp_engine.create_estate(
        decedent_name="Phạm Văn D",
        decedent_id_number="001065004444",
        decedent_dob="1965-01-01",
        date_of_death="2026-03-10",
        succession_type=SuccessionType.TESTAMENTARY.value,
    )
    e_id = est["estate_id"]

    # Register a valid notarized will
    will = temp_engine.register_will(
        estate_id=e_id,
        will_form=WillForm.WRITTEN_NOTARIZED.value,
        date_created="2025-11-20",
        place_created="Văn phòng Công chứng Thăng Long",
        notary_office_or_ubnd="VPCC Thăng Long",
        notary_number="1234/2025/TP-CC",
        executor_name="Phạm Văn E (Con trai trưởng)",
        contents_summary="Để lại toàn bộ nhà đất cho con trai Phạm Văn E",
    )
    assert will["will_status"] == "VALID"
    assert will["is_valid"] == 1


def test_heir_registration_and_disqualification_art621(temp_engine):
    est = temp_engine.create_estate(
        decedent_name="Hoàng Thị M",
        decedent_id_number="001168007777",
        decedent_dob="1968-10-10",
        date_of_death="2026-03-15",
    )
    e_id = est["estate_id"]

    # Register eligible spouse
    h1 = temp_engine.register_heir(
        estate_id=e_id,
        full_name="Nguyễn Văn N (Chồng)",
        id_number="001064003333",
        dob="1964-02-02",
        relationship=HeirRelationship.SPOUSE.value,
    )
    assert h1["heir_rank"] == HeirRank.FIRST_RANK.value
    assert h1["eligibility_status"] == "ELIGIBLE"

    # Register disqualified child under Art 621 (e.g. convicted of ill-treatment)
    h2 = temp_engine.register_heir(
        estate_id=e_id,
        full_name="Nguyễn Văn P (Con bị kết án ngược đãi)",
        id_number="001095006666",
        dob="1995-03-03",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
        is_disqualified_art621=True,
        is_forgiven_in_will=False,
    )
    assert h2["eligibility_status"] == "DISQUALIFIED_ART621"

    # Register forgiven disqualified child under Art 621 clause 2
    h3 = temp_engine.register_heir(
        estate_id=e_id,
        full_name="Nguyễn Thị Q (Con được tha thứ trong di chúc)",
        id_number="001098007777",
        dob="1998-04-04",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
        is_disqualified_art621=True,
        is_forgiven_in_will=True,
    )
    assert h3["eligibility_status"] == "ELIGIBLE"


def test_intestate_succession_equal_per_capita_art651(temp_engine):
    """Test intestate succession: Gross 6 tỷ, No debt, 3 heirs in rank 1 -> 2 tỷ each."""
    est = temp_engine.create_estate(
        decedent_name="Đặng Văn T",
        decedent_id_number="024060001234",
        decedent_dob="1960-06-06",
        date_of_death="2026-01-01",
        succession_type=SuccessionType.INTESTATE.value,
    )
    e_id = est["estate_id"]

    temp_engine.add_estate_asset(
        estate_id=e_id,
        asset_name="Biệt thự Ecopark",
        category=AssetCategory.REAL_ESTATE.value,
        estimated_value=6_000_000_000.0,
    )

    # 3 heirs in 1st rank: Spouse + 2 Children
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Trần Thị U (Vợ)",
        id_number="024162002345",
        dob="1962-07-07",
        relationship=HeirRelationship.SPOUSE.value,
    )
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Đặng Văn V (Con trai 1)",
        id_number="024090003456",
        dob="1990-08-08",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
    )
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Đặng Thị X (Con gái 2)",
        id_number="024094004567",
        dob="1994-09-09",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
    )

    calc = temp_engine.calculate_statutory_shares(e_id)
    assert calc["net_distributable_estate"] == 6_000_000_000.0
    assert calc["one_statutory_share_reference"] == 2_000_000_000.0
    assert len(calc["allocations"]) == 3
    for alloc in calc["allocations"]:
        assert alloc["allocated_amount"] == 2_000_000_000.0
        assert alloc["allocated_percentage"] == pytest.approx(33.333, 0.01)


def test_substitutional_inheritance_art652(temp_engine):
    """Test Article 652: Grandchild substitutes for deceased parent."""
    est = temp_engine.create_estate(
        decedent_name="Cụ Nguyễn Văn Ông",
        decedent_id_number="001040000001",
        decedent_dob="1940-01-01",
        date_of_death="2026-02-15",
        succession_type=SuccessionType.INTESTATE.value,
    )
    e_id = est["estate_id"]

    temp_engine.add_estate_asset(
        estate_id=e_id,
        asset_name="Sổ tiết kiệm 4 tỷ",
        category=AssetCategory.BANK_DEPOSIT_SAVINGS.value,
        estimated_value=4_000_000_000.0,
    )

    # 1 living child
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Bác Nguyễn Văn Con Cả (Sống)",
        id_number="001070000002",
        dob="1970-02-02",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
    )

    # 2 grandchildren substituting for deceased child 2
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Cháu Nguyễn Văn Cháu 1 (Thế vị)",
        id_number="001200000003",
        dob="2000-03-03",
        relationship=HeirRelationship.GRANDCHILD.value,
        is_substitutional_art652=True,
        substituting_for_name="Nguyễn Văn Con Thứ (Đã mất 2024)",
    )
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Cháu Nguyễn Thị Cháu 2 (Thế vị)",
        id_number="001203000004",
        dob="2003-04-04",
        relationship=HeirRelationship.GRANDCHILD.value,
        is_substitutional_art652=True,
        substituting_for_name="Nguyễn Văn Con Thứ (Đã mất 2024)",
    )

    calc = temp_engine.calculate_statutory_shares(e_id)
    assert calc["net_distributable_estate"] == 4_000_000_000.0

    allocs = {a["full_name"]: a["allocated_amount"] for a in calc["allocations"]}
    assert allocs["Bác Nguyễn Văn Con Cả (Sống)"] == 2_000_000_000.0
    # Each grandchild gets 1/2 of their deceased parent's 2 tỷ branch = 1 tỷ
    assert allocs["Cháu Nguyễn Văn Cháu 1 (Thế vị)"] == 1_000_000_000.0
    assert allocs["Cháu Nguyễn Thị Cháu 2 (Thế vị)"] == 1_000_000_000.0


def test_forced_heirship_art644_with_disinheritance_will(temp_engine):
    """Test Article 644: Decedent leaves 100% of 9 tỷ estate to charity/friend in Will,
    excluding wife and minor son.
    Statutory share reference = 9 tỷ / 2 (Wife + Son) = 4.5 tỷ each.
    Each forced heir must receive 2/3 of 4.5 tỷ = 3 tỷ.
    Total forced heir deductions = 6 tỷ. Remaining 3 tỷ goes to testamentary beneficiary.
    """
    est = temp_engine.create_estate(
        decedent_name="Võ Văn K",
        decedent_id_number="079075008888",
        decedent_dob="1975-05-20",
        date_of_death="2026-03-01",
        succession_type=SuccessionType.TESTAMENTARY.value,
    )
    e_id = est["estate_id"]

    temp_engine.add_estate_asset(
        estate_id=e_id,
        asset_name="Tài sản ròng ngân hàng & cổ phiếu",
        category=AssetCategory.CORPORATE_SHARES_EQUITY.value,
        estimated_value=9_000_000_000.0,
    )

    # Valid will registered
    temp_engine.register_will(
        estate_id=e_id,
        will_form=WillForm.WRITTEN_NOTARIZED.value,
        date_created="2025-12-01",
        place_created="VPCC Sài Gòn",
        notary_office_or_ubnd="VPCC Sài Gòn",
        notary_number="999/2025",
        contents_summary="Để lại 100% tài sản cho bạn thân Lê Văn Bạn",
    )

    # Forced heir 1: Wife (excluded in will)
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Bà Nguyễn Thị Vợ (Vợ hợp pháp)",
        id_number="079178001111",
        dob="1978-01-01",
        relationship=HeirRelationship.SPOUSE.value,
        is_minor_or_disabled=False,
        testamentary_share_percent=0.0,
    )

    # Forced heir 2: Minor son (12 years old)
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Cháu Võ Văn Con (12 tuổi, chưa thành niên)",
        id_number="079214002222",
        dob="2014-06-01",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
        is_minor_or_disabled=True,
        testamentary_share_percent=0.0,
    )

    # Testamentary heir: Friend receiving 100%
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Lê Văn Bạn (Người hưởng di chúc 100%)",
        id_number="079075003333",
        dob="1975-09-09",
        relationship=HeirRelationship.NON_RELATIVE_BENEFICIARY.value,
        heir_rank=HeirRank.TESTAMENTARY_ONLY.value,
        testamentary_share_percent=100.0,
    )

    calc = temp_engine.calculate_statutory_shares(e_id)
    assert calc["net_distributable_estate"] == 9_000_000_000.0
    assert calc["one_statutory_share_reference"] == 4_500_000_000.0
    assert calc["forced_heir_2_3_share_reference"] == 3_000_000_000.0

    allocs = {a["full_name"]: a["allocated_amount"] for a in calc["allocations"]}
    assert allocs["Bà Nguyễn Thị Vợ (Vợ hợp pháp)"] == 3_000_000_000.0
    assert allocs["Cháu Võ Văn Con (12 tuổi, chưa thành niên)"] == 3_000_000_000.0
    assert allocs["Lê Văn Bạn (Người hưởng di chúc 100%)"] == 3_000_000_000.0


def test_disclaimer_of_inheritance_art620(temp_engine):
    est = temp_engine.create_estate(
        decedent_name="Phan Văn H",
        decedent_id_number="001070005555",
        decedent_dob="1970-01-01",
        date_of_death="2026-02-01",
    )
    e_id = est["estate_id"]

    h = temp_engine.register_heir(
        estate_id=e_id,
        full_name="Phan Văn K (Con trai cả)",
        id_number="001095006666",
        dob="1995-05-05",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
    )
    h_id = h["heir_id"]

    # Legitimate disclaimer
    disc = temp_engine.record_disclaimer(
        estate_id=e_id,
        heir_id=h_id,
        declaration_date="2026-02-20",
        notary_or_ubnd_office="VPCC Hà Nội",
        notary_document_number="555/2026/CC-TC",
        reason="Nhường toàn bộ phần di sản cho mẹ",
        is_for_debt_evasion=False,
    )
    assert disc["is_valid"] is True
    assert disc["status"] == "RECORDED"

    # Test fraudulent debt evasion disclaimer
    disc_fraud = temp_engine.record_disclaimer(
        estate_id=e_id,
        heir_id=h_id,
        declaration_date="2026-02-20",
        notary_or_ubnd_office="VPCC Hà Nội",
        notary_document_number="556/2026/CC-TC",
        reason="Trốn nợ thi hành án",
        is_for_debt_evasion=True,
    )
    assert disc_fraud["is_valid"] is False
    assert disc_fraud["status"] == "VOID_DEBT_EVASION"


def test_statute_of_limitations_art623(temp_engine):
    res = temp_engine.check_statute_of_limitations("2000-01-01", "2026-01-01")
    # 26 years passed: Real estate (30y) is still WITHIN_LIMITATION (4y left). Movable property (10y) is EXPIRED. Obligations (3y) EXPIRED.
    assert res["real_estate_claim"]["status"] == "WITHIN_LIMITATION"
    assert res["real_estate_claim"]["remaining_years"] == 4
    assert res["movable_property_claim"]["status"] == "EXPIRED"
    assert res["creditor_obligation_claim"]["status"] == "EXPIRED"

    res2 = temp_engine.check_statute_of_limitations("1990-01-01", "2026-01-01")
    # 36 years passed: All claims EXPIRED
    assert res2["real_estate_claim"]["status"] == "EXPIRED"


def test_division_agreement_and_public_posting(temp_engine):
    est = temp_engine.create_estate(
        decedent_name="Lâm Văn G",
        decedent_id_number="001060007777",
        decedent_dob="1960-01-01",
        date_of_death="2026-01-15",
    )
    e_id = est["estate_id"]

    temp_engine.add_estate_asset(
        estate_id=e_id,
        asset_name="Nhà phố Hoàn Kiếm",
        category=AssetCategory.REAL_ESTATE.value,
        estimated_value=12_000_000_000.0,
    )
    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Lâm Văn H1",
        id_number="001090001111",
        dob="1990-01-01",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
    )

    agr = temp_engine.execute_division_agreement(
        estate_id=e_id,
        procedure_type=NotaryProcedureType.DIVISION_AGREEMENT.value,
        notary_office="VPCC Hoàn Kiếm",
        division_date="2026-03-01",
        public_posting_ubnd="UBND Phường Hàng Trống",
    )
    assert agr["procedure_type"] == NotaryProcedureType.DIVISION_AGREEMENT.value
    assert agr["public_posting"]["notice_duration_days"] == 15
    assert agr["is_compliant"] is True


def test_compliance_audit_and_dossier(temp_engine):
    est = temp_engine.create_estate(
        decedent_name="Bùi Văn T",
        decedent_id_number="001050008888",
        decedent_dob="1950-01-01",
        date_of_death="2026-01-10",
    )
    e_id = est["estate_id"]

    temp_engine.add_estate_asset(
        estate_id=e_id,
        asset_name="Căn hộ chung cư cao cấp",
        category=AssetCategory.REAL_ESTATE.value,
        estimated_value=5_000_000_000.0,
    )

    temp_engine.register_heir(
        estate_id=e_id,
        full_name="Bùi Thị Con",
        id_number="001080009999",
        dob="1980-01-01",
        relationship=HeirRelationship.BIOLOGICAL_CHILD.value,
    )

    audit = temp_engine.audit_compliance(e_id)
    assert audit["is_compliant"] is True
    assert audit["compliance_rating"] == "EXCELLENT"

    dossier = temp_engine.generate_inheritance_dossier(e_id)
    assert dossier["dossier_id"].startswith("DOS-")
    assert len(dossier["notary_requirements"]) >= 6


def test_cli_inheritance_commands():
    # Test main dashboard output
    result = runner.invoke(inheritance_app, ["--json"])
    assert result.exit_code == 0

    # Test estate-create command
    create_res = runner.invoke(
        inheritance_app,
        [
            "estate-create",
            "--name", "Lý Thái Tổ",
            "--id-number", "001000000001",
            "--dob", "1950-01-01",
            "--dod", "2026-01-01",
            "--json",
        ],
    )
    assert create_res.exit_code == 0
    import json
    est_data = json.loads(create_res.output)
    e_id = est_data["estate_id"]

    # Test asset-add command
    asset_res = runner.invoke(
        inheritance_app,
        [
            "asset-add",
            "-e", e_id,
            "-n", "Sổ đỏ 500m2",
            "-c", "REAL_ESTATE",
            "-v", "5000000000",
            "--json",
        ],
    )
    assert asset_res.exit_code == 0

    # Test heir-add command
    heir_res = runner.invoke(
        inheritance_app,
        [
            "heir-add",
            "-e", e_id,
            "-n", "Lý Thái Tông",
            "-i", "001000000002",
            "--dob", "1980-01-01",
            "-r", "BIOLOGICAL_CHILD",
            "--json",
        ],
    )
    assert heir_res.exit_code == 0

    # Test calculate command
    calc_res = runner.invoke(
        inheritance_app,
        ["calculate", "-e", e_id, "--json"],
    )
    assert calc_res.exit_code == 0

    # Test statute-check command
    stat_res = runner.invoke(
        inheritance_app,
        ["statute-check", "--dod", "2000-01-01", "--json"],
    )
    assert stat_res.exit_code == 0

    # Test audit command
    audit_res = runner.invoke(
        inheritance_app,
        ["audit", "-e", e_id, "--json"],
    )
    assert audit_res.exit_code == 0

    # Test dossier command
    dos_res = runner.invoke(
        inheritance_app,
        ["dossier", "-e", e_id, "--json"],
    )
    assert dos_res.exit_code == 0

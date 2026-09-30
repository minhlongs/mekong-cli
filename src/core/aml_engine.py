# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Anti-Money Laundering, Counter-Terrorist Financing & Sanctions Engine.

Operating with pure Python standard library and SQLite WAL persistence, this engine
codifies statutory compliance under:
1. Law on Anti-Money Laundering 2022 (Luật Phòng, chống rửa tiền số 14/2022/QH15,
   có hiệu lực từ ngày 01/03/2023).
2. Decree No. 19/2023/NĐ-CP detailing implementation of the Law on AML.
3. Decision No. 11/2023/QĐ-TTg establishing large cash transaction reporting
   threshold at 400,000,000 VND.
4. Circular No. 09/2023/TT-NHNN guiding AML/CTF/CPF implementation by the State
   Bank of Vietnam (SBV).
5. FATF (Financial Action Task Force) 40 Recommendations & Grey List remediation.

Adheres strictly to ``tests/test_core_boundary.py`` (zero external HTTP, zero vendor SDKs).
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import os
import pathlib
import sqlite3
import typing
import uuid

# Statutory threshold for Large Cash Transaction Reporting (Decision 11/2023/QĐ-TTg)
STATUTORY_LCTR_THRESHOLD_VND: float = 400_000_000.0

# Statutory UBO ownership threshold under Article 10 Law 14/2022/QH15
STATUTORY_UBO_THRESHOLD_PCT: float = 25.0

# Canonical Sanctions & Designated Terrorist Entities List
CANONICAL_SANCTIONS_LIST: list[dict[str, typing.Any]] = [
    {
        "entity_id": "SANCT-UNSC-001",
        "name": "ISIL (DA'ESH)",
        "entity_type": "ORGANIZATION",
        "list_name": "UNSC_1267_ISIL_ALQAEDA",
        "program": "UNSC Resolution 1267/1989/2253",
        "sanction_type": "ASSET_FREEZE_TRAVEL_BAN",
    },
    {
        "entity_id": "SANCT-UNSC-002",
        "name": "AL-QAIDA",
        "entity_type": "ORGANIZATION",
        "list_name": "UNSC_1267_ISIL_ALQAEDA",
        "program": "UNSC Resolution 1267/1989/2253",
        "sanction_type": "ASSET_FREEZE_TRAVEL_BAN",
    },
    {
        "entity_id": "SANCT-UNSC-003",
        "name": "KOREA MINING DEVELOPMENT TRADING CORPORATION",
        "entity_type": "ORGANIZATION",
        "list_name": "UNSC_1718_DPRK",
        "program": "UNSC Resolution 1718 (DPRK WMD)",
        "sanction_type": "ASSET_FREEZE",
    },
    {
        "entity_id": "SANCT-UNSC-004",
        "name": "RECONNAISSANCE GENERAL BUREAU",
        "entity_type": "ORGANIZATION",
        "list_name": "UNSC_1718_DPRK",
        "program": "UNSC Resolution 1718 (DPRK WMD)",
        "sanction_type": "ASSET_FREEZE",
    },
    {
        "entity_id": "SANCT-MPS-001",
        "name": "TỔ CHỨC KHỦNG BỐ VIỆT TÂN",
        "entity_type": "ORGANIZATION",
        "list_name": "VIETNAM_MPS_TERRORIST_LIST",
        "program": "Bộ Công an Việt Nam Thông báo số 01/2016",
        "sanction_type": "ASSET_FREEZE_PROSECUTION",
    },
    {
        "entity_id": "SANCT-MPS-002",
        "name": "CHÍNH PHỦ QUỐC GIA VIỆT NAM LÂM THỜI",
        "entity_type": "ORGANIZATION",
        "list_name": "VIETNAM_MPS_TERRORIST_LIST",
        "program": "Bộ Công an Việt Nam Thông báo số 01/2018",
        "sanction_type": "ASSET_FREEZE_PROSECUTION",
    },
    {
        "entity_id": "SANCT-PEP-001",
        "name": "NGUYEN VAN A",
        "entity_type": "INDIVIDUAL",
        "list_name": "DOMESTIC_PEP_REGISTRY",
        "program": "High-Risk Domestic Politically Exposed Person (PEP)",
        "sanction_type": "ENHANCED_DUE_DILIGENCE",
    },
]


@dataclasses.dataclass
class CddProfile:
    profile_id: str
    customer_name: str
    customer_type: str
    identifier: str
    nationality: str
    industry: str
    risk_level: str
    risk_score: float
    ubo_name: str | None
    ubo_ownership_pct: float
    is_pep: bool
    source_of_wealth: str
    edd_applied: bool
    senior_mgmt_approved: bool
    status: str
    created_at: str


@dataclasses.dataclass
class LctrReport:
    report_id: str
    customer_name: str
    transaction_amount: float
    currency: str
    threshold_exceeded: bool
    transaction_type: str
    channel: str
    reporting_date: str
    report_status: str
    sbv_reference_no: str
    notes: str
    filing_deadline: str


@dataclasses.dataclass
class StrReport:
    str_id: str
    customer_name: str
    suspicion_type: str
    amount: float
    indicators: list[str]
    urgency: str
    filing_deadline: str
    status: str
    rationale: str
    created_at: str


@dataclasses.dataclass
class SanctionsScreening:
    screening_id: str
    target_name: str
    target_type: str
    match_status: str
    matched_list: str | None
    matched_entity: str | None
    similarity_score: float
    asset_freeze_triggered: bool
    freeze_duration_days: int
    police_notification_required: bool
    screened_at: str


@dataclasses.dataclass
class InstitutionalAssessment:
    assessment_id: str
    institution_name: str
    institution_type: str
    compliance_officer_appointed: bool
    internal_rules_updated: bool
    annual_training_conducted: bool
    independent_internal_audit: bool
    risk_assessment_period: str
    compliance_score: float
    fatf_readiness_tier: str
    assessed_at: str


class AmlEngine:
    """Core autonomous engine for Vietnamese AML, CTF and TFS compliance."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            mekong_dir = pathlib.Path.home() / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "aml.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS aml_cdd_profiles (
                    profile_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    customer_type TEXT NOT NULL,
                    identifier TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    ubo_name TEXT,
                    ubo_ownership_pct REAL NOT NULL,
                    is_pep INTEGER NOT NULL,
                    source_of_wealth TEXT,
                    edd_applied INTEGER NOT NULL,
                    senior_mgmt_approved INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS aml_lctr_reports (
                    report_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    transaction_amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    threshold_exceeded INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    reporting_date TEXT NOT NULL,
                    report_status TEXT NOT NULL,
                    sbv_reference_no TEXT NOT NULL,
                    notes TEXT,
                    filing_deadline TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS aml_str_reports (
                    str_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    suspicion_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    indicators TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    filing_deadline TEXT NOT NULL,
                    status TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS aml_sanctions_screenings (
                    screening_id TEXT PRIMARY KEY,
                    target_name TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    match_status TEXT NOT NULL,
                    matched_list TEXT,
                    matched_entity TEXT,
                    similarity_score REAL NOT NULL,
                    asset_freeze_triggered INTEGER NOT NULL,
                    freeze_duration_days INTEGER NOT NULL,
                    police_notification_required INTEGER NOT NULL,
                    screened_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS aml_institutional_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    institution_name TEXT NOT NULL,
                    institution_type TEXT NOT NULL,
                    compliance_officer_appointed INTEGER NOT NULL,
                    internal_rules_updated INTEGER NOT NULL,
                    annual_training_conducted INTEGER NOT NULL,
                    independent_internal_audit INTEGER NOT NULL,
                    risk_assessment_period TEXT NOT NULL,
                    compliance_score REAL NOT NULL,
                    fatf_readiness_tier TEXT NOT NULL,
                    assessed_at TEXT NOT NULL
                );
                """
            )

    # ---------------------------------------------------------------------------
    # 1. Customer Due Diligence (CDD / KYC & UBO)
    # ---------------------------------------------------------------------------

    def perform_cdd(
        self,
        customer_name: str,
        customer_type: str = "INDIVIDUAL",
        identifier: str = "",
        industry: str = "BANKING",
        nationality: str = "VN",
        ubo_name: str | None = None,
        ubo_ownership_pct: float = 0.0,
        is_pep: bool = False,
        source_of_wealth: str = "",
        senior_mgmt_approved: bool = False,
    ) -> dict[str, typing.Any]:
        """Perform Customer Due Diligence, risk profiling & UBO verification (Articles 9-14)."""
        clean_name = customer_name.strip()
        c_type = customer_type.upper().strip()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        profile_id = f"cdd_{uuid.uuid4().hex[:10]}"

        # Calculate risk score (0 to 100)
        risk_score = 15.0  # Base line

        # Sector risk
        high_risk_sectors = {"CASINO", "PRECIOUS_METALS", "REAL_ESTATE", "VIRTUAL_ASSETS", "FOREIGN_EXCHANGE"}
        medium_risk_sectors = {"PAYMENT_INTERMEDIARY", "SECURITIES", "NOTARY_LEGAL", "ACCOUNTING"}
        if industry.upper() in high_risk_sectors:
            risk_score += 30.0
        elif industry.upper() in medium_risk_sectors:
            risk_score += 15.0

        # Nationality risk
        if nationality.upper() not in {"VN", "VNM"}:
            risk_score += 20.0

        # PEP risk (Article 17 Law 14/2022/QH15)
        if is_pep:
            risk_score += 35.0

        # UBO verification for organizations (Article 10 Law 14/2022/QH15)
        ubo_identified = True
        if c_type in {"ORGANIZATION", "ENTERPRISE", "CORPORATE"}:
            if not ubo_name or ubo_ownership_pct < STATUTORY_UBO_THRESHOLD_PCT:
                # UBO not identified or below statutory 25% threshold
                risk_score += 35.0
                ubo_identified = False
            else:
                risk_score -= 10.0  # Proper verified UBO lowers ambiguity

        risk_score = max(5.0, min(100.0, risk_score))

        # Risk level determination
        if is_pep or risk_score >= 70.0:
            risk_level = "HIGH"
        elif risk_score >= 40.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Enhanced Due Diligence (EDD) triggers
        edd_applied = (risk_level == "HIGH" or is_pep or (ubo_ownership_pct >= 50.0))

        # Status
        if risk_level == "HIGH" and not senior_mgmt_approved:
            status = "PENDING_SENIOR_APPROVAL"
        elif not ubo_identified and c_type in {"ORGANIZATION", "ENTERPRISE", "CORPORATE"}:
            status = "UBO_VERIFICATION_REQUIRED"
        else:
            status = "APPROVED"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO aml_cdd_profiles (
                    profile_id, customer_name, customer_type, identifier, nationality,
                    industry, risk_level, risk_score, ubo_name, ubo_ownership_pct,
                    is_pep, source_of_wealth, edd_applied, senior_mgmt_approved,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    clean_name,
                    c_type,
                    identifier,
                    nationality.upper(),
                    industry.upper(),
                    risk_level,
                    round(risk_score, 1),
                    ubo_name,
                    round(ubo_ownership_pct, 2),
                    1 if is_pep else 0,
                    source_of_wealth,
                    1 if edd_applied else 0,
                    1 if senior_mgmt_approved else 0,
                    status,
                    now,
                ),
            )

        return {
            "profile_id": profile_id,
            "customer_name": clean_name,
            "customer_type": c_type,
            "identifier": identifier,
            "nationality": nationality.upper(),
            "industry": industry.upper(),
            "risk_level": risk_level,
            "risk_score": round(risk_score, 1),
            "ubo_name": ubo_name,
            "ubo_ownership_pct": round(ubo_ownership_pct, 2),
            "ubo_statutory_threshold_met": ubo_ownership_pct >= STATUTORY_UBO_THRESHOLD_PCT,
            "is_pep": is_pep,
            "edd_applied": edd_applied,
            "senior_mgmt_approved": senior_mgmt_approved,
            "status": status,
            "created_at": now,
        }

    # ---------------------------------------------------------------------------
    # 2. Large Cash Transaction Reporting (LCTR)
    # ---------------------------------------------------------------------------

    def record_lctr(
        self,
        customer_name: str,
        transaction_amount: float,
        currency: str = "VND",
        transaction_type: str = "CASH_DEPOSIT",
        channel: str = "OVER_THE_COUNTER",
        notes: str = "",
        customer_id: str | None = None,
    ) -> dict[str, typing.Any]:
        """Record cash transaction and evaluate LCTR reporting threshold (Article 25)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        report_id = f"lctr_{uuid.uuid4().hex[:10]}"
        sbv_ref = f"SBV-AMLD-LCTR-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        threshold_exceeded = transaction_amount >= STATUTORY_LCTR_THRESHOLD_VND
        filing_deadline = (now + datetime.timedelta(days=1)).isoformat()
        report_status = "READY_FOR_SBV_SUBMISSION" if threshold_exceeded else "EXEMPT_BELOW_THRESHOLD"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO aml_lctr_reports (
                    report_id, customer_name, transaction_amount, currency,
                    threshold_exceeded, transaction_type, channel, reporting_date,
                    report_status, sbv_reference_no, notes, filing_deadline
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    customer_name.strip(),
                    transaction_amount,
                    currency.upper(),
                    1 if threshold_exceeded else 0,
                    transaction_type.upper(),
                    channel.upper(),
                    now_iso,
                    report_status,
                    sbv_ref,
                    notes,
                    filing_deadline,
                ),
            )

        return {
            "report_id": report_id,
            "customer_name": customer_name.strip(),
            "transaction_amount": transaction_amount,
            "currency": currency.upper(),
            "threshold_exceeded": threshold_exceeded,
            "statutory_threshold_vnd": STATUTORY_LCTR_THRESHOLD_VND,
            "transaction_type": transaction_type.upper(),
            "channel": channel.upper(),
            "reporting_date": now_iso,
            "report_status": report_status,
            "sbv_reference_no": sbv_ref,
            "notes": notes,
            "filing_deadline": filing_deadline,
        }

    # ---------------------------------------------------------------------------
    # 3. Suspicious Transaction Detection & Reporting (STR)
    # ---------------------------------------------------------------------------

    def file_str(
        self,
        customer_name: str,
        suspicion_type: str,
        amount: float,
        indicators: list[str] | None = None,
        rationale: str = "",
        urgency: str = "NORMAL",
    ) -> dict[str, typing.Any]:
        """Evaluate indicators and file Suspicious Transaction Report (Articles 26-33)."""
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        str_id = f"str_{uuid.uuid4().hex[:10]}"
        inds = indicators or []
        urg = urgency.upper().strip()

        # Filing deadline: 48h for normal, 24h for urgent/intercept (Article 37)
        if urg in {"URGENT", "CRITICAL_INTERCEPT"}:
            filing_deadline = (now + datetime.timedelta(hours=24)).isoformat()
            status = "CRITICAL_DISPATCH_REQUIRED"
        else:
            filing_deadline = (now + datetime.timedelta(hours=48)).isoformat()
            status = "SUBMITTED_TO_COMPLIANCE"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO aml_str_reports (
                    str_id, customer_name, suspicion_type, amount,
                    indicators, urgency, filing_deadline, status,
                    rationale, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str_id,
                    customer_name.strip(),
                    suspicion_type.upper(),
                    amount,
                    json.dumps(inds, ensure_ascii=False),
                    urg,
                    filing_deadline,
                    status,
                    rationale,
                    now_iso,
                ),
            )

        return {
            "str_id": str_id,
            "customer_name": customer_name.strip(),
            "suspicion_type": suspicion_type.upper(),
            "amount": amount,
            "indicators": inds,
            "urgency": urg,
            "filing_deadline": filing_deadline,
            "status": status,
            "rationale": rationale,
            "created_at": now_iso,
        }

    # ---------------------------------------------------------------------------
    # 4. Targeted Financial Sanctions & Blacklist Screening (TFS)
    # ---------------------------------------------------------------------------

    def screen_sanctions(
        self,
        target_name: str,
        target_type: str = "INDIVIDUAL",
        date_of_birth: str | None = None,
        nationality: str = "VN",
    ) -> dict[str, typing.Any]:
        """Screen entity against UNSC & MPS designated sanctions blacklists (Articles 34-37)."""
        clean_target = target_name.strip().upper()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        screening_id = f"tfs_{uuid.uuid4().hex[:10]}"

        # Token set for comparison
        target_tokens = set(clean_target.split())

        best_score = 0.0
        best_match: dict[str, typing.Any] | None = None

        for sanct in CANONICAL_SANCTIONS_LIST:
            sanct_name = sanct["name"].upper()
            sanct_tokens = set(sanct_name.split())

            # Exact match
            if clean_target == sanct_name:
                best_score = 1.0
                best_match = sanct
                break

            # If screening an INDIVIDUAL, prevent false positives when given name (last token) differs
            if target_type.upper() == "INDIVIDUAL" and sanct.get("entity_type") == "INDIVIDUAL":
                t_parts = clean_target.split()
                s_parts = sanct_name.split()
                if t_parts and s_parts and t_parts[-1] != s_parts[-1]:
                    continue

            # Jaccard token overlap
            intersection = target_tokens.intersection(sanct_tokens)
            union = target_tokens.union(sanct_tokens)
            if union:
                score = len(intersection) / len(union)
                if score > best_score:
                    best_score = score
                    best_match = sanct

        # Match status determination
        if best_score >= 0.80 and best_match:
            match_status = "CONFIRMED_MATCH"
            matched_list = best_match["list_name"]
            matched_entity = best_match["name"]
            # Immediate asset freeze without notice required (Article 34)
            asset_freeze_triggered = "ASSET_FREEZE" in best_match.get("sanction_type", "")
            freeze_duration_days = 3
            police_notification_required = True
        elif best_score >= 0.60 and best_match:
            match_status = "POTENTIAL_MATCH"
            matched_list = best_match["list_name"]
            matched_entity = best_match["name"]
            asset_freeze_triggered = False
            freeze_duration_days = 0
            police_notification_required = False
        else:
            match_status = "NO_MATCH"
            matched_list = None
            matched_entity = None
            asset_freeze_triggered = False
            freeze_duration_days = 0
            police_notification_required = False

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO aml_sanctions_screenings (
                    screening_id, target_name, target_type, match_status,
                    matched_list, matched_entity, similarity_score,
                    asset_freeze_triggered, freeze_duration_days,
                    police_notification_required, screened_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    screening_id,
                    clean_target,
                    target_type.upper(),
                    match_status,
                    matched_list,
                    matched_entity,
                    round(best_score, 2),
                    1 if asset_freeze_triggered else 0,
                    freeze_duration_days,
                    1 if police_notification_required else 0,
                    now_iso,
                ),
            )

        return {
            "screening_id": screening_id,
            "target_name": clean_target,
            "target_type": target_type.upper(),
            "match_status": match_status,
            "matched_list": matched_list,
            "matched_entity": matched_entity,
            "similarity_score": round(best_score, 2),
            "asset_freeze_triggered": asset_freeze_triggered,
            "freeze_duration_days": freeze_duration_days,
            "police_notification_required": police_notification_required,
            "statutory_safe_harbor_applies": True,
            "screened_at": now_iso,
        }

    # ---------------------------------------------------------------------------
    # 5. Institutional AML Risk Assessment & FATF Readiness
    # ---------------------------------------------------------------------------

    def assess_institution(
        self,
        institution_name: str,
        institution_type: str,
        compliance_officer_appointed: bool = True,
        internal_rules_updated: bool = True,
        annual_training_conducted: bool = True,
        independent_internal_audit: bool = True,
        risk_assessment_period: str = "2024-2025",
    ) -> dict[str, typing.Any]:
        """Audit institutional internal AML controls & FATF readiness (Articles 15, 20-24)."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        assessment_id = f"asm_{uuid.uuid4().hex[:10]}"

        score = 0.0
        if compliance_officer_appointed:
            score += 25.0
        if internal_rules_updated:
            score += 25.0
        if annual_training_conducted:
            score += 20.0
        if independent_internal_audit:
            score += 15.0
        if risk_assessment_period:
            score += 15.0

        if score >= 90.0:
            fatf_tier = "COMPLIANT"
        elif score >= 75.0:
            fatf_tier = "LARGELY_COMPLIANT"
        elif score >= 50.0:
            fatf_tier = "PARTIALLY_COMPLIANT"
        else:
            fatf_tier = "NON_COMPLIANT"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO aml_institutional_assessments (
                    assessment_id, institution_name, institution_type,
                    compliance_officer_appointed, internal_rules_updated,
                    annual_training_conducted, independent_internal_audit,
                    risk_assessment_period, compliance_score,
                    fatf_readiness_tier, assessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment_id,
                    institution_name.strip(),
                    institution_type.upper(),
                    1 if compliance_officer_appointed else 0,
                    1 if internal_rules_updated else 0,
                    1 if annual_training_conducted else 0,
                    1 if independent_internal_audit else 0,
                    risk_assessment_period,
                    round(score, 1),
                    fatf_tier,
                    now_iso,
                ),
            )

        return {
            "assessment_id": assessment_id,
            "institution_name": institution_name.strip(),
            "institution_type": institution_type.upper(),
            "compliance_officer_appointed": compliance_officer_appointed,
            "internal_rules_updated": internal_rules_updated,
            "annual_training_conducted": annual_training_conducted,
            "independent_internal_audit": independent_internal_audit,
            "risk_assessment_period": risk_assessment_period,
            "compliance_score": round(score, 1),
            "fatf_readiness_tier": fatf_tier,
            "assessed_at": now_iso,
        }

    # ---------------------------------------------------------------------------
    # 6. Listing & Telemetry Query Surface
    # ---------------------------------------------------------------------------

    def list_records(self, category: str = "all", limit: int = 50) -> list[dict[str, typing.Any]]:
        """List AML records across categories: cdd, lctr, str, screenings, assessments, all."""
        cat = category.lower().strip()
        results: list[dict[str, typing.Any]] = []

        with self._get_connection() as conn:
            if cat in {"cdd", "all"}:
                rows = conn.execute(
                    "SELECT * FROM aml_cdd_profiles ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    results.append({"category": "cdd", **dict(r)})

            if cat in {"lctr", "all"}:
                rows = conn.execute(
                    "SELECT * FROM aml_lctr_reports ORDER BY reporting_date DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    results.append({"category": "lctr", **dict(r)})

            if cat in {"str", "all"}:
                rows = conn.execute(
                    "SELECT * FROM aml_str_reports ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["indicators"] = json.loads(d.get("indicators", "[]"))
                    results.append({"category": "str", **d})

            if cat in {"screenings", "screening", "all"}:
                rows = conn.execute(
                    "SELECT * FROM aml_sanctions_screenings ORDER BY screened_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    results.append({"category": "screening", **dict(r)})

            if cat in {"assessments", "assessment", "all"}:
                rows = conn.execute(
                    "SELECT * FROM aml_institutional_assessments ORDER BY assessed_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    results.append({"category": "assessment", **dict(r)})

        return results

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate national AML/CTF/TFS compliance telemetry and FATF grey list posture."""
        with self._get_connection() as conn:
            total_cdd = conn.execute("SELECT COUNT(*) FROM aml_cdd_profiles").fetchone()[0]
            high_risk_cdd = conn.execute(
                "SELECT COUNT(*) FROM aml_cdd_profiles WHERE risk_level = 'HIGH'"
            ).fetchone()[0]
            total_ubo_verified = conn.execute(
                "SELECT COUNT(*) FROM aml_cdd_profiles WHERE ubo_ownership_pct >= ?",
                (STATUTORY_UBO_THRESHOLD_PCT,),
            ).fetchone()[0]

            total_lctr = conn.execute("SELECT COUNT(*) FROM aml_lctr_reports").fetchone()[0]
            exceeded_lctr = conn.execute(
                "SELECT COUNT(*) FROM aml_lctr_reports WHERE threshold_exceeded = 1"
            ).fetchone()[0]
            total_lctr_amount = conn.execute(
                "SELECT COALESCE(SUM(transaction_amount), 0) FROM aml_lctr_reports"
            ).fetchone()[0]

            total_str = conn.execute("SELECT COUNT(*) FROM aml_str_reports").fetchone()[0]
            critical_str = conn.execute(
                "SELECT COUNT(*) FROM aml_str_reports WHERE urgency = 'CRITICAL_INTERCEPT'"
            ).fetchone()[0]

            total_screenings = conn.execute("SELECT COUNT(*) FROM aml_sanctions_screenings").fetchone()[0]
            confirmed_sanctions = conn.execute(
                "SELECT COUNT(*) FROM aml_sanctions_screenings WHERE match_status = 'CONFIRMED_MATCH'"
            ).fetchone()[0]
            asset_freezes = conn.execute(
                "SELECT COUNT(*) FROM aml_sanctions_screenings WHERE asset_freeze_triggered = 1"
            ).fetchone()[0]

            total_assessments = conn.execute(
                "SELECT COUNT(*) FROM aml_institutional_assessments"
            ).fetchone()[0]
            avg_score = conn.execute(
                "SELECT COALESCE(AVG(compliance_score), 0.0) FROM aml_institutional_assessments"
            ).fetchone()[0]

        return {
            "status": "active",
            "statute": "Law No. 14/2022/QH15 & Decree 19/2023/ND-CP",
            "statutory_lctr_threshold_vnd": STATUTORY_LCTR_THRESHOLD_VND,
            "statutory_ubo_threshold_pct": STATUTORY_UBO_THRESHOLD_PCT,
            "cdd": {
                "total_profiles": total_cdd,
                "high_risk_profiles": high_risk_cdd,
                "ubo_verified_profiles": total_ubo_verified,
            },
            "lctr": {
                "total_reports": total_lctr,
                "threshold_exceeded_reports": exceeded_lctr,
                "total_reported_cash_volume_vnd": float(total_lctr_amount),
            },
            "str": {
                "total_reports": total_str,
                "critical_intercepts": critical_str,
            },
            "sanctions": {
                "total_screenings": total_screenings,
                "confirmed_matches": confirmed_sanctions,
                "asset_freezes_enacted": asset_freezes,
            },
            "institutions": {
                "total_assessed": total_assessments,
                "average_compliance_score": round(float(avg_score), 1),
            },
        }

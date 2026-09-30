"""
Vietnamese Competition, Antitrust, Anti-Monopoly & Economic Concentration Engine.
Governed by:
- Law on Competition 2018 (Law No. 23/2018/QH14)
- Decree No. 35/2020/ND-CP detailing provisions of the Law on Competition
- National Competition Commission (NCC - Ủy ban Cạnh tranh Quốc gia) enforcement regulations

Enforces standard-library-only pure Python constraints (zero external HTTP, zero vendor SDKs).
Uses SQLite WAL persistence at ~/.mekong/competition.db.
"""

import os
import json
import uuid
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class CompetitionEngine:
    """
    Core engine for Vietnamese Competition Law compliance, M&A economic concentration appraisal,
    market dominance & monopoly evaluation, anti-competitive cartel review, and leniency management.
    """

    # Statutory Thresholds under Decree 35/2020/ND-CP Art 13 (VND)
    THRESHOLD_ASSETS_STANDARD = 3_000_000_000_000.0  # 3,000 billion VND
    THRESHOLD_ASSETS_CREDIT = 12_000_000_000_000.0   # 12,000 billion VND
    THRESHOLD_REVENUE_STANDARD = 3_000_000_000_000.0 # 3,000 billion VND
    THRESHOLD_REVENUE_CREDIT = 10_000_000_000_000.0  # 10,000 billion VND
    THRESHOLD_TRANSACTION_STANDARD = 1_000_000_000_000.0 # 1,000 billion VND
    THRESHOLD_TRANSACTION_CREDIT = 3_000_000_000_000.0   # 3,000 billion VND
    THRESHOLD_MARKET_SHARE_PCT = 20.0  # 20% combined market share

    # Fine ceiling under Law on Competition 2018 Art 111 (5% annual turnover)
    MAX_FINE_TURNOVER_RATE = 0.05

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path.home() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "competition.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cur = conn.execute("PRAGMA table_info(economic_concentrations);")
            columns = [row["name"] for row in cur.fetchall()]
            if columns and "id" not in columns:
                conn.executescript("""
                    DROP TABLE IF EXISTS economic_concentrations;
                    DROP TABLE IF EXISTS market_dominance_assessments;
                    DROP TABLE IF EXISTS anti_competitive_agreements;
                    DROP TABLE IF EXISTS leniency_applications;
                """)

            conn.executescript("""
                CREATE TABLE IF NOT EXISTS economic_concentrations (
                    id TEXT PRIMARY KEY,
                    merger_name TEXT NOT NULL,
                    acquiring_entity TEXT NOT NULL,
                    target_entity TEXT NOT NULL,
                    total_assets_vnd REAL NOT NULL,
                    total_revenue_vnd REAL NOT NULL,
                    transaction_value_vnd REAL NOT NULL,
                    combined_market_share_pct REAL NOT NULL,
                    pre_hhi REAL NOT NULL,
                    post_hhi REAL NOT NULL,
                    delta_hhi REAL NOT NULL,
                    is_credit_institution INTEGER DEFAULT 0,
                    notification_required INTEGER NOT NULL,
                    notification_reasons TEXT NOT NULL,
                    market_concentration_level TEXT NOT NULL,
                    competition_impact_assessment TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS market_dominance_assessments (
                    id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    market_share_pct REAL NOT NULL,
                    cr_group_shares TEXT NOT NULL,
                    has_essential_facility INTEGER DEFAULT 0,
                    financial_superiority INTEGER DEFAULT 0,
                    dominance_type TEXT NOT NULL,
                    significant_market_power INTEGER NOT NULL,
                    statutory_basis TEXT NOT NULL,
                    prohibited_abuses TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS anti_competitive_agreements (
                    id TEXT PRIMARY KEY,
                    agreement_title TEXT NOT NULL,
                    parties_count INTEGER NOT NULL,
                    agreement_type TEXT NOT NULL,
                    is_horizontal INTEGER NOT NULL,
                    annual_revenue_vnd REAL NOT NULL,
                    per_se_illegal INTEGER NOT NULL,
                    max_fine_pct REAL NOT NULL,
                    max_fine_vnd REAL NOT NULL,
                    legal_risk_level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS leniency_applications (
                    id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    violation_id TEXT NOT NULL,
                    submission_order INTEGER NOT NULL,
                    self_confessed INTEGER NOT NULL,
                    submitted_evidence INTEGER NOT NULL,
                    exemption_rate_pct REAL NOT NULL,
                    leniency_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

    def assess_economic_concentration(
        self,
        merger_name: str,
        acquiring_entity: str,
        target_entity: str,
        total_assets_vnd: float,
        total_revenue_vnd: float,
        transaction_value_vnd: float,
        combined_market_share_pct: float,
        pre_hhi: float,
        post_hhi: float,
        is_credit_institution: bool = False,
    ) -> Dict[str, Any]:
        """
        Assesses merger / economic concentration notification thresholds and post-merger HHI impact
        under Law on Competition 2018 (Arts 29-43) & Decree 35/2020/ND-CP (Arts 13-15).
        """
        if total_assets_vnd < 0 or total_revenue_vnd < 0 or transaction_value_vnd < 0:
            raise ValueError("Financial figures (assets, revenue, transaction value) cannot be negative.")
        if combined_market_share_pct < 0 or combined_market_share_pct > 100:
            raise ValueError("Combined market share percentage must be between 0 and 100.")
        if pre_hhi < 0 or pre_hhi > 10000 or post_hhi < 0 or post_hhi > 10000:
            raise ValueError("HHI indices must be between 0 and 10,000.")
        if post_hhi < pre_hhi:
            raise ValueError("Post-merger HHI cannot be less than pre-merger HHI.")

        delta_hhi = round(post_hhi - pre_hhi, 2)

        # Thresholds based on industry
        asset_threshold = self.THRESHOLD_ASSETS_CREDIT if is_credit_institution else self.THRESHOLD_ASSETS_STANDARD
        revenue_threshold = self.THRESHOLD_REVENUE_CREDIT if is_credit_institution else self.THRESHOLD_REVENUE_STANDARD
        transaction_threshold = self.THRESHOLD_TRANSACTION_CREDIT if is_credit_institution else self.THRESHOLD_TRANSACTION_STANDARD

        notification_reasons = []
        if total_assets_vnd >= asset_threshold:
            notification_reasons.append(
                f"Assets threshold met: {total_assets_vnd:,.0f} VND >= {asset_threshold:,.0f} VND"
            )
        if total_revenue_vnd >= revenue_threshold:
            notification_reasons.append(
                f"Revenue threshold met: {total_revenue_vnd:,.0f} VND >= {revenue_threshold:,.0f} VND"
            )
        if transaction_value_vnd >= transaction_threshold:
            notification_reasons.append(
                f"Transaction value threshold met: {transaction_value_vnd:,.0f} VND >= {transaction_threshold:,.0f} VND"
            )
        if combined_market_share_pct >= self.THRESHOLD_MARKET_SHARE_PCT:
            notification_reasons.append(
                f"Combined market share threshold met: {combined_market_share_pct:.1f}% >= {self.THRESHOLD_MARKET_SHARE_PCT:.1f}%"
            )

        notification_required = len(notification_reasons) > 0

        # Market concentration level
        if post_hhi < 1000:
            market_concentration_level = "UNCONCENTRATED"
        elif 1000 <= post_hhi <= 1800:
            market_concentration_level = "MODERATELY_CONCENTRATED"
        else:
            market_concentration_level = "HIGHLY_CONCENTRATED"

        # Competition impact assessment under Decree 35/2020 Arts 14 & 15
        if combined_market_share_pct >= 50.0:
            competition_impact_assessment = "PROHIBITED_CONCENTRATION_RISK"
            status = "APPRAISAL_STRICT_PROHIBITION_RISK"
        elif post_hhi > 1800 and delta_hhi > 200:
            competition_impact_assessment = "STRICT_SCRUTINY_HIGH_RISK"
            status = "APPRAISAL_OFFICIAL_SCRUTINY"
        elif (1000 <= post_hhi <= 1800 and delta_hhi >= 100) or (post_hhi > 1800 and 100 <= delta_hhi <= 200):
            competition_impact_assessment = "FORMAL_APPRAISAL_REQUIRED"
            status = "APPRAISAL_FORMAL_REQUIRED"
        else:
            competition_impact_assessment = "SAFE_HARBOR_APPROVED"
            status = "NOTIFICATION_CLEARED_SAFE_HARBOR" if notification_required else "EXEMPT_NO_NOTIFICATION"

        now_str = datetime.now(timezone.utc).isoformat()
        record_id = f"CONC-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO economic_concentrations (
                    id, merger_name, acquiring_entity, target_entity,
                    total_assets_vnd, total_revenue_vnd, transaction_value_vnd,
                    combined_market_share_pct, pre_hhi, post_hhi, delta_hhi,
                    is_credit_institution, notification_required, notification_reasons,
                    market_concentration_level, competition_impact_assessment, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    merger_name,
                    acquiring_entity,
                    target_entity,
                    float(total_assets_vnd),
                    float(total_revenue_vnd),
                    float(transaction_value_vnd),
                    float(combined_market_share_pct),
                    float(pre_hhi),
                    float(post_hhi),
                    float(delta_hhi),
                    1 if is_credit_institution else 0,
                    1 if notification_required else 0,
                    json.dumps(notification_reasons, ensure_ascii=False),
                    market_concentration_level,
                    competition_impact_assessment,
                    status,
                    now_str,
                ),
            )

        return {
            "id": record_id,
            "merger_name": merger_name,
            "acquiring_entity": acquiring_entity,
            "target_entity": target_entity,
            "total_assets_vnd": total_assets_vnd,
            "total_revenue_vnd": total_revenue_vnd,
            "transaction_value_vnd": transaction_value_vnd,
            "combined_market_share_pct": combined_market_share_pct,
            "pre_hhi": pre_hhi,
            "post_hhi": post_hhi,
            "delta_hhi": delta_hhi,
            "is_credit_institution": is_credit_institution,
            "notification_required": notification_required,
            "notification_reasons": notification_reasons,
            "market_concentration_level": market_concentration_level,
            "competition_impact_assessment": competition_impact_assessment,
            "status": status,
            "created_at": now_str,
        }

    def assess_market_dominance(
        self,
        enterprise_name: str,
        market_share_pct: float,
        cr_group_shares: Optional[List[float]] = None,
        has_essential_facility: bool = False,
        financial_superiority: bool = False,
    ) -> Dict[str, Any]:
        """
        Assesses single enterprise or group market dominance under Law on Competition 2018 (Arts 24-27).
        Thresholds:
        - Single firm (CR1) >= 30% or Significant Market Power (SMP)
        - Group of 2 firms (CR2) >= 50%
        - Group of 3 firms (CR3) >= 65%
        - Group of 4 firms (CR4) >= 75%
        - Monopoly: 100% / No competitor
        """
        if market_share_pct < 0 or market_share_pct > 100:
            raise ValueError("Market share percentage must be between 0 and 100.")

        shares = sorted(cr_group_shares or [market_share_pct], reverse=True)
        if any(s < 0 or s > 100 for s in shares):
            raise ValueError("All concentration ratio shares must be between 0 and 100.")

        significant_market_power = False
        statutory_basis = []
        dominance_type = "NON_DOMINANT"

        # Check Monopoly (Art 25)
        if market_share_pct >= 99.0 or (len(shares) == 1 and market_share_pct >= 90.0 and has_essential_facility):
            dominance_type = "MONOPOLY"
            significant_market_power = True
            statutory_basis.append("Art 25 Law on Competition 2018 (Monopoly - No effective competition)")
        # Check Single Enterprise Dominance (Art 24 Clause 1)
        elif market_share_pct >= 30.0:
            dominance_type = "SINGLE_ENTERPRISE_DOMINANT"
            significant_market_power = True
            statutory_basis.append(f"Art 24 Clause 1 (Market share {market_share_pct:.1f}% >= 30%)")
        elif has_essential_facility or financial_superiority:
            dominance_type = "SINGLE_ENTERPRISE_DOMINANT"
            significant_market_power = True
            reasons = []
            if has_essential_facility:
                reasons.append("Essential Facility Control")
            if financial_superiority:
                reasons.append("Superior Financial Power")
            statutory_basis.append(f"Art 24 Clause 1 & Art 26 (Significant Market Power via {', '.join(reasons)})")

        # Group dominance check (Art 24 Clause 2)
        cr2 = sum(shares[:2]) if len(shares) >= 2 else 0.0
        cr3 = sum(shares[:3]) if len(shares) >= 3 else 0.0
        cr4 = sum(shares[:4]) if len(shares) >= 4 else 0.0

        if dominance_type == "NON_DOMINANT":
            if len(shares) >= 2 and cr2 >= 50.0 and market_share_pct in shares[:2]:
                dominance_type = "GROUP_CR2_DOMINANT"
                significant_market_power = True
                statutory_basis.append(f"Art 24 Clause 2(a) (Group CR2 {cr2:.1f}% >= 50%)")
            elif len(shares) >= 3 and cr3 >= 65.0 and market_share_pct in shares[:3]:
                dominance_type = "GROUP_CR3_DOMINANT"
                significant_market_power = True
                statutory_basis.append(f"Art 24 Clause 2(b) (Group CR3 {cr3:.1f}% >= 65%)")
            elif len(shares) >= 4 and cr4 >= 75.0 and market_share_pct in shares[:4]:
                dominance_type = "GROUP_CR4_DOMINANT"
                significant_market_power = True
                statutory_basis.append(f"Art 24 Clause 2(c) (Group CR4 {cr4:.1f}% >= 75%)")

        if not statutory_basis:
            statutory_basis.append("Market share and concentration below statutory dominance thresholds")

        # Prohibited abuses under Art 27
        prohibited_abuses = [
            "Predatory Pricing (Selling below cost to exclude competitors)",
            "Imposing unfair purchase or selling prices",
            "Limiting production, distribution, or hindering technical development",
            "Applying discriminatory commercial conditions",
            "Imposing tying conditions or forced acceptance of unrelated obligations",
            "Preventing market entry or expansion of competitors",
        ] if significant_market_power else []

        now_str = datetime.now(timezone.utc).isoformat()
        record_id = f"DOM-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO market_dominance_assessments (
                    id, enterprise_name, market_share_pct, cr_group_shares,
                    has_essential_facility, financial_superiority, dominance_type,
                    significant_market_power, statutory_basis, prohibited_abuses, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    enterprise_name,
                    float(market_share_pct),
                    json.dumps(shares),
                    1 if has_essential_facility else 0,
                    1 if financial_superiority else 0,
                    dominance_type,
                    1 if significant_market_power else 0,
                    " | ".join(statutory_basis),
                    json.dumps(prohibited_abuses, ensure_ascii=False),
                    now_str,
                ),
            )

        return {
            "id": record_id,
            "enterprise_name": enterprise_name,
            "market_share_pct": market_share_pct,
            "cr_group_shares": shares,
            "has_essential_facility": has_essential_facility,
            "financial_superiority": financial_superiority,
            "dominance_type": dominance_type,
            "significant_market_power": significant_market_power,
            "statutory_basis": " | ".join(statutory_basis),
            "prohibited_abuses": prohibited_abuses,
            "created_at": now_str,
        }

    def review_anti_competitive_agreement(
        self,
        agreement_title: str,
        parties_count: int,
        agreement_type: str,
        is_horizontal: bool,
        annual_revenue_vnd: float,
    ) -> Dict[str, Any]:
        """
        Reviews horizontal/vertical agreements, cartels, per-se illegal violations,
        and estimates maximum statutory fine under Law on Competition 2018 (Arts 11, 12, 111).
        """
        if parties_count < 2:
            raise ValueError("Agreement must involve at least 2 parties.")
        if annual_revenue_vnd < 0:
            raise ValueError("Annual revenue cannot be negative.")

        norm_type = agreement_type.strip().upper()
        valid_types = {
            "PRICE_FIXING",
            "MARKET_SHARING",
            "OUTPUT_RESTRICTION",
            "BID_RIGGING",
            "INPUT_PREVENTION",
            "VERTICAL_RPM",
            "EXCLUSIVE_DISTRIBUTION",
            "CUSTOMER_DISCRIMINATION",
        }
        if norm_type not in valid_types:
            raise ValueError(f"Invalid agreement type: '{agreement_type}'. Must be one of {sorted(valid_types)}")

        # Under Art 12 Clause 1: Horizontal agreements in price fixing, market sharing, output restriction,
        # and bid rigging are per se prohibited (cấm tuyệt đối).
        per_se_types = {"PRICE_FIXING", "MARKET_SHARING", "OUTPUT_RESTRICTION", "BID_RIGGING"}
        per_se_illegal = is_horizontal and (norm_type in per_se_types)

        if per_se_illegal:
            legal_risk_level = "CRITICAL_PER_SE_PROHIBITED"
            status = "INVESTIGATION_WARRANTED"
        elif is_horizontal:
            legal_risk_level = "HIGH_EFFECT_BASED_SCRUTINY"
            status = "UNDER_MARKET_IMPACT_REVIEW"
        else:
            legal_risk_level = "MEDIUM_VERTICAL_RULE_OF_REASON"
            status = "VERTICAL_COMPLIANCE_MONITORING"

        max_fine_pct = 5.0  # 5% of turnover under Art 111
        max_fine_vnd = round(annual_revenue_vnd * (max_fine_pct / 100.0), 2)

        now_str = datetime.now(timezone.utc).isoformat()
        record_id = f"AGR-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO anti_competitive_agreements (
                    id, agreement_title, parties_count, agreement_type,
                    is_horizontal, annual_revenue_vnd, per_se_illegal,
                    max_fine_pct, max_fine_vnd, legal_risk_level, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    agreement_title,
                    int(parties_count),
                    norm_type,
                    1 if is_horizontal else 0,
                    float(annual_revenue_vnd),
                    1 if per_se_illegal else 0,
                    float(max_fine_pct),
                    float(max_fine_vnd),
                    legal_risk_level,
                    status,
                    now_str,
                ),
            )

        return {
            "id": record_id,
            "agreement_title": agreement_title,
            "parties_count": parties_count,
            "agreement_type": norm_type,
            "is_horizontal": is_horizontal,
            "annual_revenue_vnd": annual_revenue_vnd,
            "per_se_illegal": per_se_illegal,
            "max_fine_pct": max_fine_pct,
            "max_fine_vnd": max_fine_vnd,
            "legal_risk_level": legal_risk_level,
            "status": status,
            "created_at": now_str,
        }

    def apply_leniency(
        self,
        enterprise_name: str,
        violation_id: str,
        submission_order: int,
        self_confessed: bool,
        submitted_evidence: bool,
    ) -> Dict[str, Any]:
        """
        Evaluates leniency application under Law on Competition 2018 (Art 112).
        Order 1: 100% fine immunity
        Order 2: 60% fine reduction
        Order 3: 40% fine reduction
        Order >= 4: 0% (Ineligible)
        Requires self_confessed and submitted_evidence to qualify.
        """
        if submission_order < 1:
            raise ValueError("Submission order must be 1 or greater.")

        if not self_confessed or not submitted_evidence:
            exemption_rate_pct = 0.0
            leniency_status = "REJECTED_NO_CONFESSION_OR_EVIDENCE"
        elif submission_order == 1:
            exemption_rate_pct = 100.0
            leniency_status = "FULL_IMMUNITY_GRANTED"
        elif submission_order == 2:
            exemption_rate_pct = 60.0
            leniency_status = "PARTIAL_60_GRANTED"
        elif submission_order == 3:
            exemption_rate_pct = 40.0
            leniency_status = "PARTIAL_40_GRANTED"
        else:
            exemption_rate_pct = 0.0
            leniency_status = "INELIGIBLE_ORDER_EXCEEDED"

        now_str = datetime.now(timezone.utc).isoformat()
        record_id = f"LEN-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO leniency_applications (
                    id, enterprise_name, violation_id, submission_order,
                    self_confessed, submitted_evidence, exemption_rate_pct,
                    leniency_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    enterprise_name,
                    violation_id,
                    int(submission_order),
                    1 if self_confessed else 0,
                    1 if submitted_evidence else 0,
                    float(exemption_rate_pct),
                    leniency_status,
                    now_str,
                ),
            )

        return {
            "id": record_id,
            "enterprise_name": enterprise_name,
            "violation_id": violation_id,
            "submission_order": submission_order,
            "self_confessed": self_confessed,
            "submitted_evidence": submitted_evidence,
            "exemption_rate_pct": exemption_rate_pct,
            "leniency_status": leniency_status,
            "created_at": now_str,
        }

    def list_competition_records(
        self, category: str = "all", limit: int = 50
    ) -> Dict[str, Any]:
        """
        Lists competition records across categories (all, concentrations, dominance, agreements, leniency).
        """
        norm_cat = category.strip().lower()
        res: Dict[str, Any] = {}

        with self._get_connection() as conn:
            if norm_cat in ("all", "concentrations", "mergers"):
                rows = conn.execute(
                    "SELECT * FROM economic_concentrations ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["concentrations"] = [
                    {
                        **dict(r),
                        "notification_reasons": json.loads(r["notification_reasons"]),
                    }
                    for r in rows
                ]

            if norm_cat in ("all", "dominance"):
                rows = conn.execute(
                    "SELECT * FROM market_dominance_assessments ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["dominance"] = [
                    {
                        **dict(r),
                        "cr_group_shares": json.loads(r["cr_group_shares"]),
                        "prohibited_abuses": json.loads(r["prohibited_abuses"]),
                    }
                    for r in rows
                ]

            if norm_cat in ("all", "agreements", "cartels"):
                rows = conn.execute(
                    "SELECT * FROM anti_competitive_agreements ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["agreements"] = [dict(r) for r in rows]

            if norm_cat in ("all", "leniency"):
                rows = conn.execute(
                    "SELECT * FROM leniency_applications ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["leniency"] = [dict(r) for r in rows]

        return res

    def get_competition_telemetry(self) -> Dict[str, Any]:
        """
        Aggregates operational telemetry for National Competition Commission oversight.
        """
        with self._get_connection() as conn:
            total_mergers = conn.execute("SELECT COUNT(*) FROM economic_concentrations").fetchone()[0]
            notifiable_mergers = conn.execute(
                "SELECT COUNT(*) FROM economic_concentrations WHERE notification_required = 1"
            ).fetchone()[0]
            high_risk_mergers = conn.execute(
                "SELECT COUNT(*) FROM economic_concentrations WHERE competition_impact_assessment IN ('STRICT_SCRUTINY_HIGH_RISK', 'PROHIBITED_CONCENTRATION_RISK')"
            ).fetchone()[0]

            total_dominance_checks = conn.execute("SELECT COUNT(*) FROM market_dominance_assessments").fetchone()[0]
            dominant_firms_count = conn.execute(
                "SELECT COUNT(*) FROM market_dominance_assessments WHERE significant_market_power = 1"
            ).fetchone()[0]

            total_agreements = conn.execute("SELECT COUNT(*) FROM anti_competitive_agreements").fetchone()[0]
            per_se_cartels = conn.execute(
                "SELECT COUNT(*) FROM anti_competitive_agreements WHERE per_se_illegal = 1"
            ).fetchone()[0]
            total_potential_fines_vnd = conn.execute(
                "SELECT COALESCE(SUM(max_fine_vnd), 0.0) FROM anti_competitive_agreements"
            ).fetchone()[0]

            total_leniency_apps = conn.execute("SELECT COUNT(*) FROM leniency_applications").fetchone()[0]
            full_immunity_granted = conn.execute(
                "SELECT COUNT(*) FROM leniency_applications WHERE leniency_status = 'FULL_IMMUNITY_GRANTED'"
            ).fetchone()[0]

        return {
            "status": "HEALTHY",
            "enforcement_body": "National Competition Commission (Ủy ban Cạnh tranh Quốc gia - NCC)",
            "statutory_framework": "Law on Competition 2018 (Law 23/2018/QH14) & Decree 35/2020/ND-CP",
            "economic_concentrations": {
                "total_assessed": total_mergers,
                "notification_required_count": notifiable_mergers,
                "high_risk_or_prohibited_count": high_risk_mergers,
            },
            "market_dominance": {
                "total_assessed": total_dominance_checks,
                "dominant_or_monopoly_count": dominant_firms_count,
            },
            "anti_competitive_agreements": {
                "total_reviewed": total_agreements,
                "per_se_cartels_prohibited": per_se_cartels,
                "total_potential_fines_vnd": total_potential_fines_vnd,
            },
            "leniency_program": {
                "total_applications": total_leniency_apps,
                "full_immunity_granted": full_immunity_granted,
            },
            "database_path": self.db_path,
        }

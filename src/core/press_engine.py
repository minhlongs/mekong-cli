# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Press, Mass Media, Online Journalism & OTT Broadcasting Engine.

Operating with pure Python standard library and SQLite WAL persistence, this engine
codifies statutory compliance under:
1. Law on Press 2016 (Luật Báo chí số 103/2016/QH13, có hiệu lực từ 01/01/2017).
2. Decree No. 119/2020/NĐ-CP & Decree No. 14/2022/NĐ-CP on administrative penalties
   in press and publishing activities.
3. Decree No. 71/2022/NĐ-CP amending Decree No. 06/2016/NĐ-CP on the management,
   provision, and use of radio and television services (OTT TV, VOD).
4. Decree No. 72/2013/NĐ-CP & Decree No. 27/2018/NĐ-CP on management of Internet
   services and general information websites (ICP licenses).
5. Circulars of Ministry of Information and Communications (MIC - Bộ TT&TT).

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

# Maximum statutory correction deadline for online press in hours (Article 42)
STATUTORY_ONLINE_CORRECTION_DEADLINE_HOURS: int = 24

# Mandatory homepage retention duration for correction notices in days
STATUTORY_CORRECTION_RETENTION_DAYS: int = 7

# Maximum allowed self-produced non-internal content ratio for ICP sites (%)
MAX_ICP_SELF_PRODUCED_RATIO_PCT: float = 10.0

# Mandatory SLA for taking down unlawful/violating articles on ICP sites in hours
STATUTORY_ICP_TAKEDOWN_SLA_HOURS: int = 3


@dataclasses.dataclass
class PressCredential:
    credential_id: str
    holder_name: str
    credential_type: str  # PRESS_CARD, EDITOR_IN_CHIEF, REP_OFFICE_HEAD
    press_agency: str
    education_degree: str
    experience_years: float
    disciplinary_clean: bool
    political_theory_advanced: bool
    status: str
    notes: str
    issued_at: str


@dataclasses.dataclass
class IcpAudit:
    audit_id: str
    website_domain: str
    organization_name: str
    server_located_in_vietnam: bool
    has_source_copyright_agreement: bool
    exact_source_attribution: bool
    self_produced_ratio_pct: float
    takedown_sla_hours: int
    is_commercialized_journalism: bool
    compliance_status: str
    deficiencies: list[str]
    audited_at: str


@dataclasses.dataclass
class OttVodLicense:
    license_id: str
    service_name: str
    provider_name: str
    service_type: str  # SVOD, TVOD, AVOD, OTT_INTERNET_TV
    age_rating_system_active: bool
    content_editing_committee_approved: bool
    essential_national_channels_carried: bool
    copyright_clearance_confirmed: bool
    status: str
    deficiencies: list[str]
    licensed_at: str


@dataclasses.dataclass
class PressCorrection:
    correction_id: str
    press_agency: str
    article_title: str
    publication_date: str
    medium_type: str  # ONLINE, PRINT, RADIO, TELEVISION
    violation_nature: str
    correction_text: str
    public_apology_included: bool
    within_statutory_deadline: bool
    retention_days: int
    right_of_reply_granted: bool
    status: str
    filed_at: str


class PressEngine:
    """Core autonomous engine for Vietnamese press, online journalism and OTT broadcasting compliance."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            mekong_dir = pathlib.Path.home() / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "press.db"
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
                CREATE TABLE IF NOT EXISTS press_credentials (
                    credential_id TEXT PRIMARY KEY,
                    holder_name TEXT NOT NULL,
                    credential_type TEXT NOT NULL,
                    press_agency TEXT NOT NULL,
                    education_degree TEXT NOT NULL,
                    experience_years REAL NOT NULL,
                    disciplinary_clean INTEGER NOT NULL,
                    political_theory_advanced INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    issued_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS press_icp_audits (
                    audit_id TEXT PRIMARY KEY,
                    website_domain TEXT NOT NULL,
                    organization_name TEXT NOT NULL,
                    server_located_in_vietnam INTEGER NOT NULL,
                    has_source_copyright_agreement INTEGER NOT NULL,
                    exact_source_attribution INTEGER NOT NULL,
                    self_produced_ratio_pct REAL NOT NULL,
                    takedown_sla_hours INTEGER NOT NULL,
                    is_commercialized_journalism INTEGER NOT NULL,
                    compliance_status TEXT NOT NULL,
                    deficiencies TEXT NOT NULL,
                    audited_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS press_ott_vod_licenses (
                    license_id TEXT PRIMARY KEY,
                    service_name TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    age_rating_system_active INTEGER NOT NULL,
                    content_editing_committee_approved INTEGER NOT NULL,
                    essential_national_channels_carried INTEGER NOT NULL,
                    copyright_clearance_confirmed INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    deficiencies TEXT NOT NULL,
                    licensed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS press_corrections (
                    correction_id TEXT PRIMARY KEY,
                    press_agency TEXT NOT NULL,
                    article_title TEXT NOT NULL,
                    publication_date TEXT NOT NULL,
                    medium_type TEXT NOT NULL,
                    violation_nature TEXT NOT NULL,
                    correction_text TEXT NOT NULL,
                    public_apology_included INTEGER NOT NULL,
                    within_statutory_deadline INTEGER NOT NULL,
                    retention_days INTEGER NOT NULL,
                    right_of_reply_granted INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    filed_at TEXT NOT NULL
                );
                """
            )

    # ---------------------------------------------------------------------------
    # 1. Press Credentialing & Leadership Eligibility (Articles 24-27)
    # ---------------------------------------------------------------------------

    def verify_credential(
        self,
        holder_name: str,
        credential_type: str = "PRESS_CARD",
        press_agency: str = "Báo Nhân Dân",
        education_degree: str = "BACHELOR_JOURNALISM",
        experience_years: float = 3.0,
        disciplinary_clean: bool = True,
        political_theory_advanced: bool = True,
    ) -> dict[str, typing.Any]:
        """Verify eligibility for Press Card, Editor-in-Chief, or Rep Office Head."""
        cred_id = f"crd_{uuid.uuid4().hex[:10]}"
        c_type = credential_type.upper().strip()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        deficiencies: list[str] = []

        if not disciplinary_clean:
            deficiencies.append("Đang trong thời gian xem xét kỷ luật hoặc bị kỷ luật trong 12 tháng qua")

        # Press card rules (Article 26)
        if c_type == "PRESS_CARD":
            if experience_years < 2.0:
                deficiencies.append("Thời gian công tác liên tục tại cơ quan báo chí dưới 02 năm")
            if education_degree.upper() not in {"BACHELOR_JOURNALISM", "MASTER_JOURNALISM", "BACHELOR_OTHER_WITH_JOURNALISM_CERT"}:
                deficiencies.append("Thiếu bằng tốt nghiệp đại học chuyên ngành báo chí hoặc chứng chỉ bồi dưỡng nghiệp vụ")

        # Editor-in-chief rules (Article 24)
        elif c_type == "EDITOR_IN_CHIEF":
            if not political_theory_advanced:
                deficiencies.append("Bắt buộc phải có bằng lý luận chính trị cao cấp hoặc cử nhân chính trị")
            if experience_years < 5.0:
                deficiencies.append("Thời gian hoạt động báo chí tích lũy dưới 05 năm")

        # Representative office head (Article 22)
        elif c_type == "REP_OFFICE_HEAD":
            if experience_years < 3.0:
                deficiencies.append("Thời gian công tác báo chí dưới 03 năm")

        status = "ELIGIBLE" if not deficiencies else "DISQUALIFIED"
        notes = "Đủ điều kiện cấp/bổ nhiệm chức danh theo Luật Báo chí 2016" if not deficiencies else "; ".join(deficiencies)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO press_credentials (
                    credential_id, holder_name, credential_type, press_agency,
                    education_degree, experience_years, disciplinary_clean,
                    political_theory_advanced, status, notes, issued_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cred_id,
                    holder_name.strip(),
                    c_type,
                    press_agency.strip(),
                    education_degree.upper(),
                    experience_years,
                    1 if disciplinary_clean else 0,
                    1 if political_theory_advanced else 0,
                    status,
                    notes,
                    now_iso,
                ),
            )

        return {
            "credential_id": cred_id,
            "holder_name": holder_name.strip(),
            "credential_type": c_type,
            "press_agency": press_agency.strip(),
            "education_degree": education_degree.upper(),
            "experience_years": experience_years,
            "disciplinary_clean": disciplinary_clean,
            "political_theory_advanced": political_theory_advanced,
            "status": status,
            "deficiencies": deficiencies,
            "notes": notes,
            "issued_at": now_iso,
        }

    # ---------------------------------------------------------------------------
    # 2. General Information Website (ICP) & Attribution Compliance (Decree 72 & 27)
    # ---------------------------------------------------------------------------

    def audit_icp_compliance(
        self,
        website_domain: str,
        organization_name: str,
        server_located_in_vietnam: bool = True,
        has_source_copyright_agreement: bool = True,
        exact_source_attribution: bool = True,
        self_produced_ratio_pct: float = 5.0,
        takedown_sla_hours: int = 3,
    ) -> dict[str, typing.Any]:
        """Audit general info website (ICP) for source attribution & anti-commercialized journalism."""
        audit_id = f"icp_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        deficiencies: list[str] = []

        if not server_located_in_vietnam:
            deficiencies.append("Máy chủ phục vụ trang thông tin điện tử tổng hợp không đặt tại Việt Nam")

        if not has_source_copyright_agreement:
            deficiencies.append("Thiếu văn bản thỏa thuận bản quyền trích dẫn nguồn tin với cơ quan báo chí")

        if not exact_source_attribution:
            deficiencies.append("Vi phạm quy định trích dẫn nguồn: Không ghi rõ tên cơ quan báo chí, tác giả, ngày giờ xuất bản")

        # Anti-journalization check: self-produced news exceeding 10%
        is_commercialized = False
        if self_produced_ratio_pct > MAX_ICP_SELF_PRODUCED_RATIO_PCT:
            is_commercialized = True
            deficiencies.append(
                f"Có dấu hiệu 'báo hóa' trang thông tin: Tỷ lệ tin bài tự sản xuất đạt {self_produced_ratio_pct:.1f}% (vượt ngưỡng {MAX_ICP_SELF_PRODUCED_RATIO_PCT:.1f}%)"
            )

        if takedown_sla_hours > STATUTORY_ICP_TAKEDOWN_SLA_HOURS:
            deficiencies.append(
                f"Quy trình gỡ bỏ tin bài vi phạm vượt quá SLA luật định ({takedown_sla_hours}h > {STATUTORY_ICP_TAKEDOWN_SLA_HOURS}h)"
            )

        status = "COMPLIANT" if not deficiencies else "NON_COMPLIANT_WARNING"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO press_icp_audits (
                    audit_id, website_domain, organization_name, server_located_in_vietnam,
                    has_source_copyright_agreement, exact_source_attribution, self_produced_ratio_pct,
                    takedown_sla_hours, is_commercialized_journalism, compliance_status,
                    deficiencies, audited_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    website_domain.strip().lower(),
                    organization_name.strip(),
                    1 if server_located_in_vietnam else 0,
                    1 if has_source_copyright_agreement else 0,
                    1 if exact_source_attribution else 0,
                    self_produced_ratio_pct,
                    takedown_sla_hours,
                    1 if is_commercialized else 0,
                    status,
                    json.dumps(deficiencies, ensure_ascii=False),
                    now_iso,
                ),
            )

        return {
            "audit_id": audit_id,
            "website_domain": website_domain.strip().lower(),
            "organization_name": organization_name.strip(),
            "server_located_in_vietnam": server_located_in_vietnam,
            "has_source_copyright_agreement": has_source_copyright_agreement,
            "exact_source_attribution": exact_source_attribution,
            "self_produced_ratio_pct": self_produced_ratio_pct,
            "max_allowed_self_produced_pct": MAX_ICP_SELF_PRODUCED_RATIO_PCT,
            "takedown_sla_hours": takedown_sla_hours,
            "is_commercialized_journalism": is_commercialized,
            "compliance_status": status,
            "deficiencies": deficiencies,
            "audited_at": now_iso,
        }

    # ---------------------------------------------------------------------------
    # 3. OTT Radio, TV & VOD Broadcasting Licensing (Decree 71/2022/NĐ-CP)
    # ---------------------------------------------------------------------------

    def license_ott_vod(
        self,
        service_name: str,
        provider_name: str,
        service_type: str = "SVOD",
        age_rating_system_active: bool = True,
        content_editing_committee_approved: bool = True,
        essential_national_channels_carried: bool = True,
        copyright_clearance_confirmed: bool = True,
    ) -> dict[str, typing.Any]:
        """License and audit OTT television, radio and VOD services under Decree 71/2022."""
        lic_id = f"ott_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        s_type = service_type.upper().strip()
        deficiencies: list[str] = []

        if not age_rating_system_active:
            deficiencies.append("Chưa thiết lập hệ thống cảnh báo và phân loại độ tuổi nội dung theo quy định Luật Điện ảnh")

        if not content_editing_committee_approved:
            deficiencies.append("Nội dung chương trình chưa được Ban biên tập có chứng chỉ nghiệp vụ kiểm duyệt trước khi phổ biến")

        if not essential_national_channels_carried:
            deficiencies.append("Không truyền dẫn đầy đủ các kênh phát thanh, truyền hình thiết yếu quốc gia và địa phương")

        if not copyright_clearance_confirmed:
            deficiencies.append("Thiếu chứng từ chứng minh bản quyền sở hữu trí tuệ hợp pháp đối với toàn bộ kho phim/chương trình")

        status = "LICENSED_APPROVED" if not deficiencies else "LICENSE_REJECTED"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO press_ott_vod_licenses (
                    license_id, service_name, provider_name, service_type,
                    age_rating_system_active, content_editing_committee_approved,
                    essential_national_channels_carried, copyright_clearance_confirmed,
                    status, deficiencies, licensed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lic_id,
                    service_name.strip(),
                    provider_name.strip(),
                    s_type,
                    1 if age_rating_system_active else 0,
                    1 if content_editing_committee_approved else 0,
                    1 if essential_national_channels_carried else 0,
                    1 if copyright_clearance_confirmed else 0,
                    status,
                    json.dumps(deficiencies, ensure_ascii=False),
                    now_iso,
                ),
            )

        return {
            "license_id": lic_id,
            "service_name": service_name.strip(),
            "provider_name": provider_name.strip(),
            "service_type": s_type,
            "age_rating_system_active": age_rating_system_active,
            "content_editing_committee_approved": content_editing_committee_approved,
            "essential_national_channels_carried": essential_national_channels_carried,
            "copyright_clearance_confirmed": copyright_clearance_confirmed,
            "status": status,
            "deficiencies": deficiencies,
            "licensed_at": now_iso,
        }

    # ---------------------------------------------------------------------------
    # 4. Press Correction & Public Apology Enforcement (Article 42 Law 103/2016)
    # ---------------------------------------------------------------------------

    def file_correction(
        self,
        press_agency: str,
        article_title: str,
        publication_date: str,
        medium_type: str = "ONLINE",
        violation_nature: str = "THÔNG TIN SAI SỰ THẬT VỀ DOANH NGHIỆP",
        correction_text: str = "",
        public_apology_included: bool = True,
        published_hours_after_request: int = 12,
        retention_days: int = 7,
        right_of_reply_granted: bool = True,
    ) -> dict[str, typing.Any]:
        """Record and verify statutory press correction and public apology (Article 42)."""
        corr_id = f"cor_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        m_type = medium_type.upper().strip()

        # Check deadline: 24h for online press (Article 42 Clause 2)
        within_deadline = published_hours_after_request <= STATUTORY_ONLINE_CORRECTION_DEADLINE_HOURS
        retention_compliant = retention_days >= STATUTORY_CORRECTION_RETENTION_DAYS

        if within_deadline and public_apology_included and retention_compliant:
            status = "CORRECTION_COMPLIANT"
        elif not within_deadline:
            status = "DELAYED_CORRECTION_VIOLATION"
        else:
            status = "INCOMPLETE_CORRECTION_NOTICE"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO press_corrections (
                    correction_id, press_agency, article_title, publication_date,
                    medium_type, violation_nature, correction_text, public_apology_included,
                    within_statutory_deadline, retention_days, right_of_reply_granted,
                    status, filed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    corr_id,
                    press_agency.strip(),
                    article_title.strip(),
                    publication_date,
                    m_type,
                    violation_nature.strip(),
                    correction_text.strip(),
                    1 if public_apology_included else 0,
                    1 if within_deadline else 0,
                    retention_days,
                    1 if right_of_reply_granted else 0,
                    status,
                    now_iso,
                ),
            )

        return {
            "correction_id": corr_id,
            "press_agency": press_agency.strip(),
            "article_title": article_title.strip(),
            "publication_date": publication_date,
            "medium_type": m_type,
            "violation_nature": violation_nature.strip(),
            "correction_text": correction_text.strip(),
            "public_apology_included": public_apology_included,
            "within_statutory_deadline": within_deadline,
            "published_hours_after_request": published_hours_after_request,
            "statutory_deadline_hours": STATUTORY_ONLINE_CORRECTION_DEADLINE_HOURS,
            "retention_days": retention_days,
            "retention_compliant": retention_compliant,
            "right_of_reply_granted": right_of_reply_granted,
            "status": status,
            "filed_at": now_iso,
        }

    # ---------------------------------------------------------------------------
    # 5. Listing & Status Telemetry Surface
    # ---------------------------------------------------------------------------

    def list_records(self, category: str = "all", limit: int = 50) -> list[dict[str, typing.Any]]:
        """List press records across categories: credentials, icp, ott, corrections, all."""
        cat = category.lower().strip()
        results: list[dict[str, typing.Any]] = []

        with self._get_connection() as conn:
            if cat in {"credentials", "credential", "card", "all"}:
                rows = conn.execute(
                    "SELECT * FROM press_credentials ORDER BY issued_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    results.append({"category": "credential", **dict(r)})

            if cat in {"icp", "websites", "all"}:
                rows = conn.execute(
                    "SELECT * FROM press_icp_audits ORDER BY audited_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["deficiencies"] = json.loads(d.get("deficiencies", "[]"))
                    results.append({"category": "icp", **d})

            if cat in {"ott", "vod", "all"}:
                rows = conn.execute(
                    "SELECT * FROM press_ott_vod_licenses ORDER BY licensed_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["deficiencies"] = json.loads(d.get("deficiencies", "[]"))
                    results.append({"category": "ott", **d})

            if cat in {"corrections", "correction", "all"}:
                rows = conn.execute(
                    "SELECT * FROM press_corrections ORDER BY filed_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    results.append({"category": "correction", **dict(r)})

        return results

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate national press, mass media, ICP & OTT broadcasting telemetry."""
        with self._get_connection() as conn:
            total_creds = conn.execute("SELECT COUNT(*) FROM press_credentials").fetchone()[0]
            eligible_creds = conn.execute(
                "SELECT COUNT(*) FROM press_credentials WHERE status = 'ELIGIBLE'"
            ).fetchone()[0]

            total_icp = conn.execute("SELECT COUNT(*) FROM press_icp_audits").fetchone()[0]
            compliant_icp = conn.execute(
                "SELECT COUNT(*) FROM press_icp_audits WHERE compliance_status = 'COMPLIANT'"
            ).fetchone()[0]
            commercialized_icp = conn.execute(
                "SELECT COUNT(*) FROM press_icp_audits WHERE is_commercialized_journalism = 1"
            ).fetchone()[0]

            total_ott = conn.execute("SELECT COUNT(*) FROM press_ott_vod_licenses").fetchone()[0]
            approved_ott = conn.execute(
                "SELECT COUNT(*) FROM press_ott_vod_licenses WHERE status = 'LICENSED_APPROVED'"
            ).fetchone()[0]

            total_corrections = conn.execute("SELECT COUNT(*) FROM press_corrections").fetchone()[0]
            compliant_corrections = conn.execute(
                "SELECT COUNT(*) FROM press_corrections WHERE status = 'CORRECTION_COMPLIANT'"
            ).fetchone()[0]

        return {
            "status": "active",
            "statute": "Law on Press 2016 (Law No. 103/2016/QH13) & Decree 71/2022/ND-CP",
            "competent_authority": "Ministry of Information and Communications (Cục Phát thanh, truyền hình và thông tin điện tử & Cục Báo chí - Bộ TT&TT)",
            "credentials": {
                "total_assessed": total_creds,
                "eligible_credentials": eligible_creds,
            },
            "icp": {
                "total_audited": total_icp,
                "compliant_websites": compliant_icp,
                "commercialized_journalism_warnings": commercialized_icp,
            },
            "ott_vod": {
                "total_services": total_ott,
                "approved_licenses": approved_ott,
            },
            "corrections": {
                "total_corrections": total_corrections,
                "statutory_compliant_corrections": compliant_corrections,
            },
        }

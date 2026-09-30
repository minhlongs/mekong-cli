"""
Mekong Cultural Heritage, Antiquities & National Treasures Engine (src/core/heritage_engine.py).

Statutory Framework:
- Law on Cultural Heritage 2024 (Luật Di sản văn hóa số 45/2024/QH15, passed Nov 27, 2024, effective July 1, 2025).
- Decree No. 98/2010/ND-CP detailing provisions of the Law on Cultural Heritage.
- Circular No. 09/2013/TT-BVHTTDL on management of antiquities, relics and national treasures.
- Prime Minister's Decisions on recognition of National Treasures (Bảo vật Quốc gia).

Pure Python standard-library-only implementation (AST boundary safe).
"""

from __future__ import annotations

import sqlite3
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


VALID_RELIC_CLASSIFICATIONS = {"SPECIAL_NATIONAL", "NATIONAL", "PROVINCIAL"}
VALID_ARTIFACT_CATEGORIES = {"NATIONAL_TREASURE", "ANTIQUITY", "RELIC_OBJECT"}
ARCHAEOLOGY_MAJORS = {"KHẢO CỔ", "LỊCH SỬ", "BẢO TÀNG", "ARCHAEOLOGY", "HISTORY"}


@dataclass
class RelicSiteResult:
    site_id: str
    name: str
    classification: str
    province: str
    zone1_area_sqm: float
    zone2_area_sqm: float
    construction_in_zone1: bool
    minister_approved: bool
    status: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class ArtifactRegistrationResult:
    artifact_id: str
    name: str
    category: str
    origin_period: str
    material: str
    owner_type: str
    is_unique: bool
    export_prohibited: bool
    recognized_as_treasure: bool
    registration_cert_no: str
    status: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class ExcavationPermitResult:
    permit_id: str
    project_name: str
    location: str
    lead_archaeologist: str
    degree_major: str
    experience_years: int
    permit_days: int
    artifacts_handed_over_to_museum: bool
    is_approved: bool
    status: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class MuseumExhibitionResult:
    exhibition_id: str
    museum_name: str
    artifact_id: str
    artifact_name: str
    is_national_treasure: bool
    is_overseas_tour: bool
    insurance_covered_100pct: bool
    prime_minister_approval: bool
    temp_celsius: float
    humidity_pct: float
    status: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class HeritageTelemetry:
    total_relic_sites: int
    special_national_sites: int
    national_treasures_count: int
    registered_antiquities: int
    active_excavation_permits: int
    approved_exhibitions: int


class HeritageEngine:
    """Core cultural heritage, relics, antiquities and national treasures engine."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = Path.home() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "heritage.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS heritage_relic_sites (
                    site_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    province TEXT NOT NULL,
                    zone1_area_sqm REAL NOT NULL,
                    zone2_area_sqm REAL NOT NULL,
                    construction_in_zone1 INTEGER NOT NULL,
                    minister_approved INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS heritage_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    origin_period TEXT NOT NULL,
                    material TEXT NOT NULL,
                    owner_type TEXT NOT NULL,
                    is_unique INTEGER NOT NULL,
                    export_prohibited INTEGER NOT NULL,
                    recognized_as_treasure INTEGER NOT NULL,
                    registration_cert_no TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS heritage_excavations (
                    permit_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    lead_archaeologist TEXT NOT NULL,
                    degree_major TEXT NOT NULL,
                    experience_years INTEGER NOT NULL,
                    permit_days INTEGER NOT NULL,
                    artifacts_handed_over_to_museum INTEGER NOT NULL,
                    is_approved INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS heritage_exhibitions (
                    exhibition_id TEXT PRIMARY KEY,
                    museum_name TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    artifact_name TEXT NOT NULL,
                    is_national_treasure INTEGER NOT NULL,
                    is_overseas_tour INTEGER NOT NULL,
                    insurance_covered_100pct INTEGER NOT NULL,
                    prime_minister_approval INTEGER NOT NULL,
                    temp_celsius REAL NOT NULL,
                    humidity_pct REAL NOT NULL,
                    status TEXT NOT NULL,
                    reasons TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def assess_relic_site(
        self,
        name: str,
        classification: str,
        province: str,
        zone1_area_sqm: float,
        zone2_area_sqm: float,
        construction_in_zone1: bool = False,
        minister_approved: bool = True,
    ) -> RelicSiteResult:
        """
        Assess protection zones and construction compliance for historical-cultural relics (Articles 27-32 Law 45/2024).
        """
        reasons: List[str] = []
        cls_upper = classification.strip().upper()
        if cls_upper not in VALID_RELIC_CLASSIFICATIONS:
            cls_upper = "PROVINCIAL"

        if construction_in_zone1:
            reasons.append(
                "Nghiêm cấm xây dựng công trình mới trong Khu vực bảo vệ I của di tích theo Điều 32 Luật Di sản văn hóa 2024 (phải bảo vệ nguyên trạng yếu tố gốc)."
            )

        if not minister_approved and cls_upper in ("SPECIAL_NATIONAL", "NATIONAL"):
            reasons.append(
                f"Việc xây dựng, cải tạo công trình tại vùng đệm (Khu vực II) của di tích cấp {cls_upper} bắt buộc có sự chấp thuận bằng văn bản của Bộ trưởng Bộ VHTTDL."
            )

        if zone1_area_sqm <= 0:
            reasons.append("Chưa cắm mốc giới phân định Khu vực bảo vệ I theo quy định.")

        status = "PROTECTED_COMPLIANT" if not reasons else "PROTECTION_VIOLATION"
        site_id = f"SITE-{cls_upper[:3]}-{uuid.uuid4().hex[:6].upper()}"

        result = RelicSiteResult(
            site_id=site_id,
            name=name.strip(),
            classification=cls_upper,
            province=province.strip(),
            zone1_area_sqm=zone1_area_sqm,
            zone2_area_sqm=zone2_area_sqm,
            construction_in_zone1=construction_in_zone1,
            minister_approved=minister_approved,
            status=status,
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO heritage_relic_sites
                (site_id, name, classification, province, zone1_area_sqm, zone2_area_sqm, construction_in_zone1, minister_approved, status, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.site_id,
                    result.name,
                    result.classification,
                    result.province,
                    result.zone1_area_sqm,
                    result.zone2_area_sqm,
                    1 if result.construction_in_zone1 else 0,
                    1 if result.minister_approved else 0,
                    result.status,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def register_artifact(
        self,
        name: str,
        category: str = "ANTIQUITY",
        origin_period: str = "Đông Sơn",
        material: str = "Đồng",
        owner_type: str = "STATE",
        is_unique: bool = True,
        age_years: int = 150,
        historical_scientific_value: bool = True,
    ) -> ArtifactRegistrationResult:
        """
        Register antiquity, relic object or National Treasure under Articles 39-44 Law 45/2024.
        """
        reasons: List[str] = []
        cat_upper = category.strip().upper()
        if cat_upper not in VALID_ARTIFACT_CATEGORIES:
            cat_upper = "ANTIQUITY"

        owner_upper = owner_type.strip().upper()
        recognized_as_treasure = False

        if cat_upper == "NATIONAL_TREASURE":
            if not is_unique:
                reasons.append("Bảo vật Quốc gia phải là hiện vật gốc độc bản theo Điều 41 Luật Di sản văn hóa 2024.")
            if not historical_scientific_value:
                reasons.append("Bảo vật Quốc gia phải có giá trị lịch sử, văn hóa, khoa học đặc biệt tiêu biểu của đất nước.")
            recognized_as_treasure = is_unique and historical_scientific_value

        if cat_upper == "ANTIQUITY" and age_years < 100:
            reasons.append(f"Cổ vật phải có niên đại từ 100 năm tuổi trở lên theo quy định ({age_years} < 100 năm).")

        # Commercial export prohibition
        export_prohibited = (cat_upper == "NATIONAL_TREASURE") or (owner_upper in ("STATE", "COMMUNITY"))

        status = "REGISTERED_COMPLIANT" if not reasons else "REGISTRATION_REJECTED"
        cert_no = f"DSVH-DK-{uuid.uuid4().hex[:6].upper()}" if not reasons else "N/A"
        artifact_id = f"ART-{uuid.uuid4().hex[:8].upper()}"

        result = ArtifactRegistrationResult(
            artifact_id=artifact_id,
            name=name.strip(),
            category=cat_upper,
            origin_period=origin_period.strip(),
            material=material.strip(),
            owner_type=owner_upper,
            is_unique=is_unique,
            export_prohibited=export_prohibited,
            recognized_as_treasure=recognized_as_treasure,
            registration_cert_no=cert_no,
            status=status,
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO heritage_artifacts
                (artifact_id, name, category, origin_period, material, owner_type, is_unique, export_prohibited, recognized_as_treasure, registration_cert_no, status, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.artifact_id,
                    result.name,
                    result.category,
                    result.origin_period,
                    result.material,
                    result.owner_type,
                    1 if result.is_unique else 0,
                    1 if result.export_prohibited else 0,
                    1 if result.recognized_as_treasure else 0,
                    result.registration_cert_no,
                    result.status,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def permit_excavation(
        self,
        project_name: str,
        location: str,
        lead_archaeologist: str,
        degree_major: str = "Khảo cổ học",
        experience_years: int = 4,
        permit_days: int = 60,
        artifacts_handed_over: bool = True,
    ) -> ExcavationPermitResult:
        """
        Evaluate archaeological excavation licensing under Articles 35-38 Law 45/2024.
        """
        reasons: List[str] = []
        major_upper = degree_major.strip().upper()

        if not any(kw in major_upper for kw in ARCHAEOLOGY_MAJORS):
            reasons.append(
                f"Người chủ trì khai quật phải có bằng cử nhân chuyên ngành khảo cổ học hoặc lịch sử theo Điều 37 Luật Di sản văn hóa 2024."
            )

        if experience_years < 3:
            reasons.append(
                f"Người chủ trì khai quật chưa đạt kinh nghiệm thực tế tham gia khai quật khảo cổ tối thiểu ({experience_years}/3 năm)."
            )

        if not artifacts_handed_over:
            reasons.append(
                "Vi phạm nghĩa vụ bàn giao toàn bộ di vật, cổ vật khai quật được vào bảo tàng công lập theo Điều 38."
            )

        is_approved = len(reasons) == 0
        status = "EXCAVATION_PERMITTED" if is_approved else "PERMIT_DENIED"
        permit_id = f"EXC-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:6].upper()}"

        result = ExcavationPermitResult(
            permit_id=permit_id,
            project_name=project_name.strip(),
            location=location.strip(),
            lead_archaeologist=lead_archaeologist.strip(),
            degree_major=degree_major.strip(),
            experience_years=experience_years,
            permit_days=permit_days,
            artifacts_handed_over_to_museum=artifacts_handed_over,
            is_approved=is_approved,
            status=status,
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO heritage_excavations
                (permit_id, project_name, location, lead_archaeologist, degree_major, experience_years, permit_days, artifacts_handed_over_to_museum, is_approved, status, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.permit_id,
                    result.project_name,
                    result.location,
                    result.lead_archaeologist,
                    result.degree_major,
                    result.experience_years,
                    result.permit_days,
                    1 if result.artifacts_handed_over_to_museum else 0,
                    1 if result.is_approved else 0,
                    result.status,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def audit_exhibition(
        self,
        museum_name: str,
        artifact_id: str,
        artifact_name: str,
        is_national_treasure: bool = False,
        is_overseas_tour: bool = False,
        insurance_covered_100pct: bool = True,
        prime_minister_approval: bool = True,
        temp_celsius: float = 22.0,
        humidity_pct: float = 55.0,
    ) -> MuseumExhibitionResult:
        """
        Audit museum display and overseas exhibition tour compliance (Articles 47-53 Law 45/2024).
        """
        reasons: List[str] = []

        if is_overseas_tour:
            if not insurance_covered_100pct:
                reasons.append("Triển lãm ở nước ngoài bắt buộc phải có bảo hiểm toàn diện 100% giá trị di vật, bảo vật theo Điều 50.")
            if is_national_treasure and not prime_minister_approval:
                reasons.append("Đưa Bảo vật Quốc gia ra nước ngoài trưng bày bắt buộc phải có Quyết định phê duyệt của Thủ tướng Chính phủ.")

        if not (18.0 <= temp_celsius <= 24.0):
            reasons.append(f"Nhiệt độ trưng bày ({temp_celsius}°C) ngoài dải an toàn vi khí hậu bảo quản cổ vật (18.0 - 24.0°C).")

        if not (45.0 <= humidity_pct <= 65.0):
            reasons.append(f"Độ ẩm phòng trưng bày ({humidity_pct}%) ngoài dải tiêu chuẩn chống thoái biến hiện vật (45.0 - 65.0%).")

        if not reasons:
            status = "OVERSEAS_TOUR_APPROVED" if is_overseas_tour else "APPROVED_FOR_DISPLAY"
        else:
            status = "EXHIBITION_REJECTED"

        exhibition_id = f"EXH-{uuid.uuid4().hex[:8].upper()}"

        result = MuseumExhibitionResult(
            exhibition_id=exhibition_id,
            museum_name=museum_name.strip(),
            artifact_id=artifact_id.strip(),
            artifact_name=artifact_name.strip(),
            is_national_treasure=is_national_treasure,
            is_overseas_tour=is_overseas_tour,
            insurance_covered_100pct=insurance_covered_100pct,
            prime_minister_approval=prime_minister_approval,
            temp_celsius=temp_celsius,
            humidity_pct=humidity_pct,
            status=status,
            reasons=reasons,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO heritage_exhibitions
                (exhibition_id, museum_name, artifact_id, artifact_name, is_national_treasure, is_overseas_tour, insurance_covered_100pct, prime_minister_approval, temp_celsius, humidity_pct, status, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.exhibition_id,
                    result.museum_name,
                    result.artifact_id,
                    result.artifact_name,
                    1 if result.is_national_treasure else 0,
                    1 if result.is_overseas_tour else 0,
                    1 if result.insurance_covered_100pct else 0,
                    1 if result.prime_minister_approval else 0,
                    result.temp_celsius,
                    result.humidity_pct,
                    result.status,
                    json.dumps(result.reasons, ensure_ascii=False),
                ),
            )
            conn.commit()

        return result

    def list_records(self, category: str = "all", limit: int = 50) -> Dict[str, Any]:
        """Query stored heritage records by category."""
        res: Dict[str, Any] = {}
        with self._get_connection() as conn:
            if category in ("all", "sites"):
                rows = conn.execute(
                    "SELECT * FROM heritage_relic_sites ORDER BY site_id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["relic_sites"] = [
                    {
                        "site_id": r["site_id"],
                        "name": r["name"],
                        "classification": r["classification"],
                        "province": r["province"],
                        "status": r["status"],
                    }
                    for r in rows
                ]

            if category in ("all", "artifacts"):
                rows = conn.execute(
                    "SELECT * FROM heritage_artifacts ORDER BY artifact_id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["artifacts"] = [
                    {
                        "artifact_id": r["artifact_id"],
                        "name": r["name"],
                        "category": r["category"],
                        "origin_period": r["origin_period"],
                        "material": r["material"],
                        "recognized_as_treasure": bool(r["recognized_as_treasure"]),
                        "registration_cert_no": r["registration_cert_no"],
                        "status": r["status"],
                    }
                    for r in rows
                ]

            if category in ("all", "excavations"):
                rows = conn.execute(
                    "SELECT * FROM heritage_excavations ORDER BY permit_id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["excavations"] = [
                    {
                        "permit_id": r["permit_id"],
                        "project_name": r["project_name"],
                        "location": r["location"],
                        "lead_archaeologist": r["lead_archaeologist"],
                        "is_approved": bool(r["is_approved"]),
                        "status": r["status"],
                    }
                    for r in rows
                ]

            if category in ("all", "exhibitions"):
                rows = conn.execute(
                    "SELECT * FROM heritage_exhibitions ORDER BY exhibition_id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["exhibitions"] = [
                    {
                        "exhibition_id": r["exhibition_id"],
                        "museum_name": r["museum_name"],
                        "artifact_name": r["artifact_name"],
                        "is_overseas_tour": bool(r["is_overseas_tour"]),
                        "status": r["status"],
                    }
                    for r in rows
                ]

        return res

    def get_status(self) -> HeritageTelemetry:
        """Aggregate national cultural heritage telemetry."""
        with self._get_connection() as conn:
            total_sites = conn.execute("SELECT COUNT(*) FROM heritage_relic_sites").fetchone()[0]
            special_sites = conn.execute(
                "SELECT COUNT(*) FROM heritage_relic_sites WHERE classification = 'SPECIAL_NATIONAL'"
            ).fetchone()[0]
            national_treasures = conn.execute(
                "SELECT COUNT(*) FROM heritage_artifacts WHERE recognized_as_treasure = 1"
            ).fetchone()[0]
            registered_antiquities = conn.execute(
                "SELECT COUNT(*) FROM heritage_artifacts WHERE status = 'REGISTERED_COMPLIANT'"
            ).fetchone()[0]
            active_permits = conn.execute(
                "SELECT COUNT(*) FROM heritage_excavations WHERE is_approved = 1"
            ).fetchone()[0]
            approved_exhibitions = conn.execute(
                "SELECT COUNT(*) FROM heritage_exhibitions WHERE status LIKE 'APPROVED%'"
            ).fetchone()[0]

        return HeritageTelemetry(
            total_relic_sites=total_sites,
            special_national_sites=special_sites,
            national_treasures_count=national_treasures,
            registered_antiquities=registered_antiquities,
            active_excavation_permits=active_permits,
            approved_exhibitions=approved_exhibitions,
        )

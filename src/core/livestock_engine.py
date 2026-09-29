# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Animal Husbandry, Livestock Farming, Feed Standards & Biosecurity Engine.

Implements statutory livestock unit (Đơn vị vật nuôi - ĐVN) conversion, farm scale classification,
biosecurity buffer distance compliance, regional stocking density caps, animal feed safety standards,
and agricultural waste biogas treatment under:
- Luật Chăn nuôi 2018 (Luật số 32/2018/QH14) & Nghị định 13/2020/NĐ-CP, Nghị định 46/2022/NĐ-CP:
  * Hệ số Đơn vị vật nuôi (Livestock Unit - ĐVN, Phụ lục V Nghị định 13/2020/NĐ-CP):
    - Lợn thịt (PIG_FATTENER): 0.20 ĐVN
    - Lợn nái (PIG_SOW): 0.50 ĐVN
    - Bò thịt (CATTLE_BEEF): 1.00 ĐVN
    - Bò sữa (CATTLE_DAIRY): 1.50 ĐVN
    - Trâu (BUFFALO): 1.00 ĐVN
    - Gà thịt (POULTRY_BROILER): 0.014 ĐVN
    - Gà đẻ (POULTRY_LAYER): 0.018 ĐVN
    - Vịt thịt (DUCK): 0.018 ĐVN
    - Dê, cừu (GOAT_SHEEP): 0.15 ĐVN
  * Phân loại quy mô trang trại chăn nuôi (Điều 21 Nghị định 13/2020/NĐ-CP):
    - Quy mô lớn (LARGE_SCALE): >= 300 ĐVN (Cấp Giấy chứng nhận đủ điều kiện chăn nuôi).
    - Quy mô vừa (MEDIUM_SCALE): Từ 30 đến dưới 300 ĐVN.
    - Quy mô nhỏ (SMALL_SCALE): Từ 10 đến dưới 30 ĐVN.
    - Nông hộ (HOUSEHOLD): Dưới 10 ĐVN.
  * Mật độ chăn nuôi tối đa các vùng sinh thái (Điều 53 Luật Chăn nuôi & Nghị định 13/2020/NĐ-CP):
    - Đồng bằng sông Hồng: <= 1.5 ĐVN/ha đất nông nghiệp
    - Trung du và miền núi phía Bắc: <= 1.0 ĐVN/ha
    - Bắc Trung Bộ và Duyên hải miền Trung: <= 1.0 ĐVN/ha
    - Tây Nguyên: <= 1.0 ĐVN/ha
    - Đông Nam Bộ: <= 1.5 ĐVN/ha
    - Đồng bằng sông Cửu Long: <= 1.5 ĐVN/ha
  * Khoảng cách an toàn sinh học trang trại chăn nuôi (Điều 5 Nghị định 13/2020/NĐ-CP):
    - Đến khu dân cư, trường học, bệnh viện, chợ:
      * Quy mô lớn: >= 400 m
      * Quy mô vừa: >= 300 m
      * Quy mô nhỏ: >= 200 m
    - Đến nguồn nước sinh hoạt:
      * Quy mô lớn: >= 100 m
      * Quy mô vừa & nhỏ: >= 80 m
    - Giữa 2 trang trại chăn nuôi quy mô lớn: >= 1,000 m
- Quy chuẩn Kỹ thuật Quốc gia Thức ăn Chăn nuôi (QCVN 01-183:2016/BNNPTNT & Thông tư 21/2019/TT-BNNPTNT):
  * Khống chế độc tố Aflatoxin B1 <= 20.0 ppb.
  * Kim loại nặng: Chì (Pb) <= 5.0 ppm, Asen (As) <= 2.0 ppm, Cadmi (Cd) <= 0.5 ppm.
  * Nghiêm cấm tuyệt đối hóa chất cấm nhóm Beta-agonist (Salbutamol, Clenbuterol, Ractopamine) = 0.
- Xử lý chất thải chăn nuôi và khí sinh học Biogas (Nghị định 46/2022/NĐ-CP & QCVN 62-MT:2016/BTNMT):
  * Định mức dung tích hầm Biogas: >= 0.8 m3/ĐVN đối với lợn, >= 1.2 m3/ĐVN đối với trâu bò.
- Lưu trữ SQLite WAL tại ``.mekong/livestock.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import json
import math
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Statutory Livestock Units (ĐVN) & Regional Stocking Density Baselines
# ---------------------------------------------------------------------------

LIVESTOCK_UNIT_FACTORS: dict[str, dict[str, typing.Any]] = {
    "PIG_FATTENER": {"name_vi": "Lợn thịt", "factor": 0.20},
    "PIG_SOW": {"name_vi": "Lợn nái / Đực giống", "factor": 0.50},
    "CATTLE_BEEF": {"name_vi": "Bò thịt", "factor": 1.00},
    "CATTLE_DAIRY": {"name_vi": "Bò sữa", "factor": 1.50},
    "BUFFALO": {"name_vi": "Trâu", "factor": 1.00},
    "POULTRY_BROILER": {"name_vi": "Gà thịt", "factor": 0.014},
    "POULTRY_LAYER": {"name_vi": "Gà đẻ trứng", "factor": 0.018},
    "DUCK": {"name_vi": "Vịt thịt / Vịt đẻ", "factor": 0.018},
    "GOAT_SHEEP": {"name_vi": "Dê / Cừu", "factor": 0.15},
}

REGIONAL_DENSITY_CAPS: dict[str, float] = {
    "RED_RIVER_DELTA": 1.5,
    "NORTHERN_MIDLANDS_MOUNTAINS": 1.0,
    "NORTH_CENTRAL_COASTAL": 1.0,
    "CENTRAL_HIGHLANDS": 1.0,
    "SOUTHEAST": 1.5,
    "MEKONG_DELTA": 1.5,
}

BIOSECURITY_MIN_DISTANCES: dict[str, dict[str, float]] = {
    "LARGE_SCALE": {
        "residential_distance_m": 400.0,
        "water_source_distance_m": 100.0,
        "farm_to_farm_distance_m": 1000.0,
    },
    "MEDIUM_SCALE": {
        "residential_distance_m": 300.0,
        "water_source_distance_m": 80.0,
        "farm_to_farm_distance_m": 500.0,
    },
    "SMALL_SCALE": {
        "residential_distance_m": 200.0,
        "water_source_distance_m": 80.0,
        "farm_to_farm_distance_m": 300.0,
    },
    "HOUSEHOLD": {
        "residential_distance_m": 50.0,
        "water_source_distance_m": 30.0,
        "farm_to_farm_distance_m": 50.0,
    },
}

BANNED_SUBSTANCES: set[str] = {
    "SALBUTAMOL",
    "CLENBUTEROL",
    "RACTOPAMINE",
}


class RecordList(list):
    """List with Rich table display capability for CLI output."""

    def __init__(self, items: list[dict[str, typing.Any]], key: str = "items"):
        super().__init__(items)
        self.key = key

    @property
    def data(self) -> list[dict[str, typing.Any]]:
        return list(self)

    def to_dict(self) -> dict[str, typing.Any]:
        return {self.key: list(self)}


class LivestockEngine:
    """Core engine for Vietnamese Livestock Farming, Feed Quality, Biosecurity & Waste Regulations."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "livestock.db"
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
                CREATE TABLE IF NOT EXISTS livestock_farms (
                    farm_id TEXT PRIMARY KEY,
                    farm_name TEXT NOT NULL,
                    owner_name TEXT NOT NULL,
                    province TEXT NOT NULL,
                    animal_type TEXT NOT NULL,
                    head_count INTEGER NOT NULL,
                    livestock_units REAL NOT NULL,
                    farm_scale TEXT NOT NULL,
                    agricultural_land_ha REAL NOT NULL,
                    stocking_density REAL NOT NULL,
                    is_density_compliant INTEGER NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS biosecurity_audits (
                    audit_id TEXT PRIMARY KEY,
                    farm_id TEXT NOT NULL,
                    farm_scale TEXT NOT NULL,
                    residential_distance_m REAL NOT NULL,
                    water_source_distance_m REAL NOT NULL,
                    farm_to_farm_distance_m REAL NOT NULL,
                    is_biosecurity_compliant INTEGER NOT NULL,
                    audited_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS feed_quality_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    feed_type TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    crude_protein_pct REAL NOT NULL,
                    aflatoxin_b1_ppb REAL NOT NULL,
                    lead_pb_ppm REAL NOT NULL,
                    banned_substance_detected INTEGER NOT NULL,
                    is_feed_compliant INTEGER NOT NULL,
                    inspected_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS waste_biogas_audits (
                    waste_audit_id TEXT PRIMARY KEY,
                    farm_id TEXT NOT NULL,
                    livestock_units REAL NOT NULL,
                    treatment_method TEXT NOT NULL,
                    biogas_volume_m3 REAL NOT NULL,
                    required_volume_m3 REAL NOT NULL,
                    is_biogas_sufficient INTEGER NOT NULL,
                    audited_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Livestock Unit (ĐVN) & Farm Scale Registration (Decree 13/2020)
    # -----------------------------------------------------------------------

    def register_livestock_farm(
        self,
        farm_name: str,
        owner_name: str = "Tập Đoàn Chăn Nuôi CP Việt Nam",
        province: str = "Đồng Nai",
        animal_type: str = "PIG_FATTENER",
        head_count: int = 2000,
        agricultural_land_ha: float = 30.0,
        region: str = "SOUTHEAST",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register livestock farm, compute ĐVN, farm scale, and regional stocking density."""
        atype = animal_type.upper().strip()
        factor_info = LIVESTOCK_UNIT_FACTORS.get(atype, LIVESTOCK_UNIT_FACTORS["PIG_FATTENER"])
        factor = factor_info["factor"]

        livestock_units = round(head_count * factor, 2)

        # Classify farm scale under Article 21 Decree 13/2020
        if livestock_units >= 300.0:
            scale = "LARGE_SCALE"
            scale_vi = "Trang trại quy mô lớn (Bắt buộc Giấy chứng nhận đủ điều kiện chăn nuôi)"
        elif livestock_units >= 30.0:
            scale = "MEDIUM_SCALE"
            scale_vi = "Trang trại quy mô vừa"
        elif livestock_units >= 10.0:
            scale = "SMALL_SCALE"
            scale_vi = "Trang trại quy mô nhỏ"
        else:
            scale = "HOUSEHOLD"
            scale_vi = "Chăn nuôi nông hộ"

        # Calculate stocking density (ĐVN / ha)
        land = max(0.1, agricultural_land_ha)
        density = round(livestock_units / land, 2)

        reg_key = region.upper().strip()
        cap = REGIONAL_DENSITY_CAPS.get(reg_key, 1.5)
        is_density_ok = density <= cap

        farm_id = f"LVF-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        profile = {
            "farm_name": farm_name.strip(),
            "owner_name": owner_name.strip(),
            "province": province.strip(),
            "region": reg_key,
            "animal_type": atype,
            "animal_name_vi": factor_info["name_vi"],
            "head_count": head_count,
            "dvn_factor_per_head": factor,
            "livestock_units": livestock_units,
            "farm_scale": scale,
            "farm_scale_vi": scale_vi,
            "agricultural_land_ha": land,
            "actual_stocking_density": density,
            "regional_density_cap": cap,
            "is_density_compliant": is_density_ok,
            "density_verdict": "MẬT ĐỘ CHĂN NUÔI HỢP LỆ THEO LUẬT CHĂN NUÔI" if is_density_ok else "MẬT ĐỘ VƯỢT QUY ĐỊNH VÙNG SINH THÁI (CẦN TĂNG DIỆN TÍCH HOẶC GIẢM ĐÀN)",
        }

        result = {
            "ok": True,
            "farm_id": farm_id,
            "farm_profile": profile,
            "statutory_mandates": {
                "livestock_law": "Luật Chăn nuôi 2018 (Luật số 32/2018/QH14)",
                "scale_decree": "Nghị định 13/2020/NĐ-CP và Nghị định 46/2022/NĐ-CP",
            },
            "registered_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO livestock_farms (
                        farm_id, farm_name, owner_name, province, animal_type,
                        head_count, livestock_units, farm_scale, agricultural_land_ha,
                        stocking_density, is_density_compliant, registered_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        farm_id,
                        farm_name.strip(),
                        owner_name.strip(),
                        province.strip(),
                        atype,
                        head_count,
                        livestock_units,
                        scale,
                        land,
                        density,
                        1 if is_density_ok else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Biosecurity Buffer Distances Audit (Article 5 Decree 13/2020)
    # -----------------------------------------------------------------------

    def audit_biosecurity_distance(
        self,
        farm_id: str,
        farm_scale: str = "LARGE_SCALE",
        residential_distance_m: float = 450.0,
        water_source_distance_m: float = 120.0,
        farm_to_farm_distance_m: float = 1200.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit farm buffer distances against biosecurity standards under Article 5 Decree 13/2020."""
        scale_key = farm_scale.upper().strip()
        reqs = BIOSECURITY_MIN_DISTANCES.get(scale_key, BIOSECURITY_MIN_DISTANCES["LARGE_SCALE"])

        res_ok = residential_distance_m >= reqs["residential_distance_m"]
        water_ok = water_source_distance_m >= reqs["water_source_distance_m"]
        f2f_ok = farm_to_farm_distance_m >= reqs["farm_to_farm_distance_m"]

        is_compliant = res_ok and water_ok and f2f_ok
        audit_id = f"BIO-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        audit_data = {
            "farm_id": farm_id.strip(),
            "farm_scale": scale_key,
            "residential_distance_m": residential_distance_m,
            "min_residential_distance_m": reqs["residential_distance_m"],
            "residential_distance_compliant": res_ok,
            "water_source_distance_m": water_source_distance_m,
            "min_water_source_distance_m": reqs["water_source_distance_m"],
            "water_source_distance_compliant": water_ok,
            "farm_to_farm_distance_m": farm_to_farm_distance_m,
            "min_farm_to_farm_distance_m": reqs["farm_to_farm_distance_m"],
            "farm_to_farm_distance_compliant": f2f_ok,
            "is_biosecurity_compliant": is_compliant,
            "biosecurity_verdict": "ĐẠT CHUẨN KHOẢNG CÁCH AN TOÀN SINH HỌC THEO NĐ 13/2020" if is_compliant else "VI PHẠM KHOẢNG CÁCH AN TOÀN SINH HỌC (QUÁ GẦN KHU DÂN CƯ HOẶC NGUỒN NƯỚC)",
        }

        result = {
            "ok": True,
            "audit_id": audit_id,
            "biosecurity_audit": audit_data,
            "statutory_mandate": "Điều 5 Nghị định 13/2020/NĐ-CP quy định khoảng cách an toàn trong chăn nuôi trang trại",
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO biosecurity_audits (
                        audit_id, farm_id, farm_scale, residential_distance_m,
                        water_source_distance_m, farm_to_farm_distance_m,
                        is_biosecurity_compliant, audited_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        farm_id.strip(),
                        scale_key,
                        residential_distance_m,
                        water_source_distance_m,
                        farm_to_farm_distance_m,
                        1 if is_compliant else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Animal Feed Quality & Banned Substances Inspection (QCVN 01-183)
    # -----------------------------------------------------------------------

    def inspect_feed_quality(
        self,
        product_name: str,
        feed_type: str = "PIG_FEED_COMPLETE",
        manufacturer: str = "C.P. Vietnam Corporation",
        crude_protein_pct: float = 18.5,
        aflatoxin_b1_ppb: float = 8.5,
        lead_pb_ppm: float = 1.2,
        banned_substance: str | None = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Inspect animal feed safety, mycotoxins, heavy metals, and prohibited beta-agonists."""
        # Aflatoxin B1 max 20.0 ppb
        aflatoxin_ok = aflatoxin_b1_ppb <= 20.0
        # Lead (Pb) max 5.0 ppm
        lead_ok = lead_pb_ppm <= 5.0
        # Crude protein minimum (usually >= 16.0% for pig feed)
        protein_ok = crude_protein_pct >= 14.0

        # Check banned substances (Salbutamol, Clenbuterol, Ractopamine)
        banned_detected = False
        if banned_substance:
            sub = banned_substance.upper().strip()
            if any(b in sub for b in BANNED_SUBSTANCES):
                banned_detected = True

        is_compliant = aflatoxin_ok and lead_ok and protein_ok and not banned_detected

        inspection_id = f"FEE-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        inspection_data = {
            "product_name": product_name.strip(),
            "feed_type": feed_type.strip(),
            "manufacturer": manufacturer.strip(),
            "crude_protein_pct": crude_protein_pct,
            "crude_protein_compliant": protein_ok,
            "aflatoxin_b1_ppb": aflatoxin_b1_ppb,
            "max_aflatoxin_b1_ppb": 20.0,
            "aflatoxin_compliant": aflatoxin_ok,
            "lead_pb_ppm": lead_pb_ppm,
            "max_lead_pb_ppm": 5.0,
            "lead_compliant": lead_ok,
            "banned_substance_tested": banned_substance if banned_substance else "NEGATIVE",
            "banned_substance_detected": banned_detected,
            "is_feed_compliant": is_compliant,
            "quality_verdict": "ĐẠT CHUẨN CHẤT LƯỢNG THỨC ĂN CHĂN NUÔI (QCVN 01-183:2016/BNNPTNT)" if is_compliant else "VI PHẠM TIÊU CHUẨN THỨC ĂN (NHIỄM ĐỘC TỐ HOẶC CHẤT CẤM CHĂN NUÔI)",
        }

        result = {
            "ok": True,
            "inspection_id": inspection_id,
            "feed_inspection": inspection_data,
            "statutory_mandates": {
                "feed_standard": "QCVN 01-183:2016/BNNPTNT Quy chuẩn kỹ thuật quốc gia thức ăn chăn nuôi",
                "prohibited_substances": "Thông tư 21/2019/TT-BNNPTNT cấm sử dụng kháng sinh kích thích sinh trưởng & chất cấm",
            },
            "inspected_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO feed_quality_inspections (
                        inspection_id, product_name, feed_type, manufacturer,
                        crude_protein_pct, aflatoxin_b1_ppb, lead_pb_ppm,
                        banned_substance_detected, is_feed_compliant, inspected_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inspection_id,
                        product_name.strip(),
                        feed_type.strip(),
                        manufacturer.strip(),
                        crude_protein_pct,
                        aflatoxin_b1_ppb,
                        lead_pb_ppm,
                        1 if banned_detected else 0,
                        1 if is_compliant else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Agricultural Waste & Biogas Tank Sizing (Decree 46/2022 & QCVN 62)
    # -----------------------------------------------------------------------

    def audit_waste_treatment(
        self,
        farm_id: str,
        livestock_units: float,
        treatment_method: str = "BIOGAS_DIGESTER",
        biogas_volume_m3: float = 350.0,
        is_cattle: bool = False,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit livestock manure/wastewater treatment capacity against biogas standards."""
        # Biogas sizing standard: 0.8 m3/ĐVN for pigs, 1.2 m3/ĐVN for cattle
        rate_per_dvn = 1.2 if is_cattle else 0.8
        req_vol = round(livestock_units * rate_per_dvn, 2)

        is_sufficient = biogas_volume_m3 >= req_vol
        waste_audit_id = f"WST-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        waste_data = {
            "farm_id": farm_id.strip(),
            "livestock_units": livestock_units,
            "treatment_method": treatment_method.strip(),
            "biogas_volume_m3": biogas_volume_m3,
            "required_biogas_volume_m3": req_vol,
            "rate_m3_per_dvn": rate_per_dvn,
            "is_biogas_sufficient": is_sufficient,
            "treatment_verdict": "DUNG TÍCH HẦM BIOGAS ĐẠT TIÊU CHUẨN XỬ LÝ CHẤT THẢI CHĂN NUÔI" if is_sufficient else "DUNG TÍCH BIOGAS THIẾU HỤT SO VỚI QUY MÔ ĐÀN (NGUY CƠ QUÁ TẢI Ô NHIỄM)",
        }

        result = {
            "ok": True,
            "waste_audit_id": waste_audit_id,
            "waste_treatment_audit": waste_data,
            "statutory_mandate": "Nghị định 46/2022/NĐ-CP và QCVN 62-MT:2016/BTNMT về nước thải chăn nuôi",
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO waste_biogas_audits (
                        waste_audit_id, farm_id, livestock_units, treatment_method,
                        biogas_volume_m3, required_volume_m3, is_biogas_sufficient, audited_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        waste_audit_id,
                        farm_id.strip(),
                        livestock_units,
                        treatment_method.strip(),
                        biogas_volume_m3,
                        req_vol,
                        1 if is_sufficient else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Record Listing & Telemetry Status
    # -----------------------------------------------------------------------

    def list_livestock_farms(self, limit: int = 50) -> RecordList:
        """List registered livestock farms."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM livestock_farms ORDER BY registered_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="livestock_farms")

    def list_biosecurity_audits(self, limit: int = 50) -> RecordList:
        """List biosecurity buffer distance audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM biosecurity_audits ORDER BY audited_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="biosecurity_audits")

    def list_feed_inspections(self, limit: int = 50) -> RecordList:
        """List animal feed quality inspections."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM feed_quality_inspections ORDER BY inspected_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="feed_inspections")

    def list_waste_audits(self, limit: int = 50) -> RecordList:
        """List waste and biogas treatment audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM waste_biogas_audits ORDER BY audited_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return RecordList([dict(r) for r in rows], key="waste_audits")

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate telemetry across livestock farms, biosecurity, feed, and waste."""
        with self._get_connection() as conn:
            farm_count = conn.execute("SELECT COUNT(*) FROM livestock_farms").fetchone()[0]
            total_dvn = conn.execute("SELECT COALESCE(SUM(livestock_units), 0) FROM livestock_farms").fetchone()[0]
            density_ok = conn.execute("SELECT COUNT(*) FROM livestock_farms WHERE is_density_compliant = 1").fetchone()[0]
            bio_count = conn.execute("SELECT COUNT(*) FROM biosecurity_audits").fetchone()[0]
            bio_ok = conn.execute("SELECT COUNT(*) FROM biosecurity_audits WHERE is_biosecurity_compliant = 1").fetchone()[0]
            feed_count = conn.execute("SELECT COUNT(*) FROM feed_quality_inspections").fetchone()[0]
            feed_ok = conn.execute("SELECT COUNT(*) FROM feed_quality_inspections WHERE is_feed_compliant = 1").fetchone()[0]
            waste_count = conn.execute("SELECT COUNT(*) FROM waste_biogas_audits").fetchone()[0]
            waste_ok = conn.execute("SELECT COUNT(*) FROM waste_biogas_audits WHERE is_biogas_sufficient = 1").fetchone()[0]

        return {
            "ok": True,
            "regulatory_framework": "Luật Chăn nuôi 2018 (Luật số 32/2018/QH14) & Nghị định 13/2020/NĐ-CP",
            "metrics": {
                "registered_livestock_farms": farm_count,
                "total_livestock_units_dvn": round(total_dvn, 2),
                "stocking_density_compliant_farms": density_ok,
                "biosecurity_audits_conducted": bio_count,
                "biosecurity_compliant_farms": bio_ok,
                "feed_quality_inspections_conducted": feed_count,
                "compliant_feed_products": feed_ok,
                "waste_biogas_audits_performed": waste_count,
                "sufficient_biogas_farms": waste_ok,
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

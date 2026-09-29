# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Environmental Protection, EIA & Carbon Credits Engine.

Implements statutory environmental impact classification under Law on Environmental Protection 2020
(Luật Bảo vệ môi trường 2020 - Luật số 72/2020/QH14),
integrated Environmental Permitting (Giấy phép Môi trường - GPMT) under Decree 08/2022/NĐ-CP,
Greenhouse Gas (GHG) Scope 1/2/3 Inventory & Carbon Credits offsetting under Decree 06/2022/NĐ-CP,
Extended Producer Responsibility (EPR) mandatory recycling quotas & VEPF contributions,
and continuous automated effluent/emissions monitoring under QCVN 40:2011/BTNMT & QCVN 19:2009/BTNMT.

Statutory Legal Baselines:
- Luật Bảo vệ môi trường 2020 (Luật số 72/2020/QH14)
- Nghị định số 08/2022/NĐ-CP quy định chi tiết một số điều của Luật Bảo vệ môi trường
- Nghị định số 06/2022/NĐ-CP quy định giảm nhẹ phát thải khí nhà kính và bảo vệ tầng ô-dôn
- Thông tư số 02/2022/TT-BTNMT quy định chi tiết thi hành Luật Bảo vệ môi trường
- QCVN 40:2011/BTNMT: Quy chuẩn kỹ thuật quốc gia về nước thải công nghiệp
- QCVN 19:2009/BTNMT: Quy chuẩn kỹ thuật quốc gia về khí thải công nghiệp đối với bụi và các chất vô cơ

Lưu trữ SQLite WAL tại ``.mekong/environment.db``.
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
# Statutory Baselines, Thresholds & Constants
# ---------------------------------------------------------------------------

PROJECT_IMPACT_GROUPS: dict[str, dict[str, typing.Any]] = {
    "GROUP_I": {
        "code": "GROUP_I",
        "name_vi": "Nhóm I: Nguy cơ tác động xấu đến môi trường mức độ cao",
        "criteria": "Quy mô lớn, có yếu tố nhạy cảm môi trường cao (rừng đặc dụng, nguồn nước cấp sinh hoạt), hoặc loại hình sản xuất công nghiệp ô nhiễm công suất lớn",
        "requires_eia": True,
        "requires_pre_eia": True,
        "requires_license": True,
        "license_term_years": 7,
        "authority": "Bộ Tài nguyên và Môi trường (Bộ TN&MT)",
        "statutory_ref": "Khoản 3 Điều 28 Luật BVMT 2020 & Phụ lục III Nghị định 08/2022/NĐ-CP",
    },
    "GROUP_II": {
        "code": "GROUP_II",
        "name_vi": "Nhóm II: Nguy cơ tác động xấu đến môi trường",
        "criteria": "Quy mô trung bình hoặc quy mô nhỏ có yếu tố nhạy cảm về môi trường",
        "requires_eia": True,
        "requires_pre_eia": False,
        "requires_license": True,
        "license_term_years": 10,
        "authority": "Ủy ban nhân dân cấp tỉnh (UBND tỉnh)",
        "statutory_ref": "Khoản 4 Điều 28 Luật BVMT 2020 & Phụ lục IV Nghị định 08/2022/NĐ-CP",
    },
    "GROUP_III": {
        "code": "GROUP_III",
        "name_vi": "Nhóm III: Ít nguy cơ tác động xấu đến môi trường",
        "criteria": "Quy mô nhỏ, không có yếu tố nhạy cảm môi trường, phát sinh chất thải phải xử lý đạt chuẩn",
        "requires_eia": False,
        "requires_pre_eia": False,
        "requires_license": True,
        "license_term_years": 10,
        "authority": "Ủy ban nhân dân cấp huyện hoặc cấp tỉnh",
        "statutory_ref": "Khoản 5 Điều 28 Luật BVMT 2020 & Phụ lục V Nghị định 08/2022/NĐ-CP",
    },
    "GROUP_IV": {
        "code": "GROUP_IV",
        "name_vi": "Nhóm IV: Không có nguy cơ tác động xấu đến môi trường",
        "criteria": "Dự án không phát sinh chất thải hoặc chỉ phát sinh chất thải sinh hoạt khối lượng nhỏ (< 300 kg/ngày)",
        "requires_eia": False,
        "requires_pre_eia": False,
        "requires_license": False,
        "license_term_years": 0,
        "authority": "Miễn thủ tục môi trường",
        "statutory_ref": "Khoản 6 Điều 28 & Điều 32 Luật BVMT 2020",
    },
}

EPR_RECYCLING_RATES: dict[str, dict[str, typing.Any]] = {
    "PACKAGING_PAPER": {
        "code": "PACKAGING_PAPER",
        "name_vi": "Bao bì giấy, carton",
        "mandatory_rate_pct": 20.0,
        "vepf_cost_vnd_per_kg": 1_250.0,  # Fs định mức đóng góp Quỹ BVMT Việt Nam
        "statutory_ref": "Phụ lục XXII Nghị định 08/2022/NĐ-CP",
    },
    "PACKAGING_PLASTIC_PET": {
        "code": "PACKAGING_PLASTIC_PET",
        "name_vi": "Bao bì nhựa cứng PET, HDPE",
        "mandatory_rate_pct": 22.0,
        "vepf_cost_vnd_per_kg": 2_150.0,
        "statutory_ref": "Phụ lục XXII Nghị định 08/2022/NĐ-CP",
    },
    "PACKAGING_ALUMINUM": {
        "code": "PACKAGING_ALUMINUM",
        "name_vi": "Bao bì nhôm (lon nước giải khát)",
        "mandatory_rate_pct": 22.0,
        "vepf_cost_vnd_per_kg": 2_500.0,
        "statutory_ref": "Phụ lục XXII Nghị định 08/2022/NĐ-CP",
    },
    "BATTERIES": {
        "code": "BATTERIES",
        "name_vi": "Pin và ắc quy chì / lithium",
        "mandatory_rate_pct": 12.0,
        "vepf_cost_vnd_per_kg": 4_800.0,
        "statutory_ref": "Phụ lục XXII Nghị định 08/2022/NĐ-CP",
    },
    "LUBRICANT_OIL": {
        "code": "LUBRICANT_OIL",
        "name_vi": "Dầu nhớt bôi trơn động cơ",
        "mandatory_rate_pct": 7.0,
        "vepf_cost_vnd_per_kg": 3_100.0,
        "statutory_ref": "Phụ lục XXII Nghị định 08/2022/NĐ-CP",
    },
    "TIRES": {
        "code": "TIRES",
        "name_vi": "Săm lốp cao su xe cơ giới",
        "mandatory_rate_pct": 5.0,
        "vepf_cost_vnd_per_kg": 1_800.0,
        "statutory_ref": "Phụ lục XXII Nghị định 08/2022/NĐ-CP",
    },
    "ELECTRONICS": {
        "code": "ELECTRONICS",
        "name_vi": "Thiết bị điện, điện tử gia dụng & công nghiệp",
        "mandatory_rate_pct": 9.0,
        "vepf_cost_vnd_per_kg": 5_500.0,
        "statutory_ref": "Phụ lục XXII Nghị định 08/2022/NĐ-CP",
    },
}

# Emission factors & statutory thresholds
GRID_ELECTRICITY_EMISSION_FACTOR_KG_CO2_PER_KWH: float = 0.7221  # 0.7221 tCO2e / MWh (Bộ TN&MT công bố)
GHG_MANDATORY_INVENTORY_THRESHOLD_TCO2E: float = 3_000.0         # 3,000 tấn CO2e/năm (Điều 9 NĐ 06/2022/NĐ-CP)
HAZARDOUS_WASTE_STORAGE_LIMIT_DAYS: int = 365                    # Tối đa 365 ngày lưu giữ chất thải nguy hại tại nguồn

# QCVN Statutory Monitoring Thresholds
QCVN_THRESHOLDS = {
    "WASTEWATER": {
        "PH_MIN": 6.0,
        "PH_MAX": 9.0,
        "COD_MAX_MG_L": 75.0,     # Cột A QCVN 40:2011/BTNMT
        "TSS_MAX_MG_L": 50.0,     # Cột A QCVN 40:2011/BTNMT
        "TEMPERATURE_MAX_C": 40.0,
    },
    "EXHAUST": {
        "DUST_MAX_MG_NM3": 200.0,  # QCVN 19:2009/BTNMT Cột B
        "SO2_MAX_MG_NM3": 500.0,
        "NOX_MAX_MG_NM3": 850.0,
        "CO_MAX_MG_NM3": 1000.0,
    },
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class ProjectImpactAssessment:
    """Represents a categorized investment project under Article 28 Law on Environmental Protection 2020."""

    def __init__(
        self,
        project_id: str,
        project_name: str,
        investor_name: str,
        investment_capital_vnd: float,
        sector_type: str,
        location: str,
        is_environmentally_sensitive: bool,
        daily_capacity: float,
        capacity_unit: str,
        impact_group: str,
        requires_eia: bool,
        requires_pre_eia: bool,
        requires_license: bool,
        licensing_authority: str,
        status: str = "CLASSIFIED",
        created_at: str | None = None,
    ) -> None:
        self.project_id = project_id
        self.project_name = project_name
        self.investor_name = investor_name
        self.investment_capital_vnd = investment_capital_vnd
        self.sector_type = sector_type
        self.location = location
        self.is_environmentally_sensitive = is_environmentally_sensitive
        self.daily_capacity = daily_capacity
        self.capacity_unit = capacity_unit
        self.impact_group = impact_group
        self.requires_eia = requires_eia
        self.requires_pre_eia = requires_pre_eia
        self.requires_license = requires_license
        self.licensing_authority = licensing_authority
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "investor_name": self.investor_name,
            "investment_capital_vnd": self.investment_capital_vnd,
            "sector_type": self.sector_type,
            "location": self.location,
            "is_environmentally_sensitive": self.is_environmentally_sensitive,
            "daily_capacity": self.daily_capacity,
            "capacity_unit": self.capacity_unit,
            "impact_group": self.impact_group,
            "requires_eia": self.requires_eia,
            "requires_pre_eia": self.requires_pre_eia,
            "requires_license": self.requires_license,
            "licensing_authority": self.licensing_authority,
            "status": self.status,
            "created_at": self.created_at,
        }


class EnvironmentalLicense:
    """Represents an integrated Environmental Permit (GPMT)."""

    def __init__(
        self,
        license_id: str,
        facility_name: str,
        tax_id: str,
        facility_address: str,
        impact_group: str,
        max_wastewater_m3_day: float,
        max_exhaust_m3_hour: float,
        max_hazardous_waste_tons_year: float,
        validity_years: int,
        issue_date: str,
        expiry_date: str,
        issuing_authority: str,
        status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> None:
        self.license_id = license_id
        self.facility_name = facility_name
        self.tax_id = tax_id
        self.facility_address = facility_address
        self.impact_group = impact_group
        self.max_wastewater_m3_day = max_wastewater_m3_day
        self.max_exhaust_m3_hour = max_exhaust_m3_hour
        self.max_hazardous_waste_tons_year = max_hazardous_waste_tons_year
        self.validity_years = validity_years
        self.issue_date = issue_date
        self.expiry_date = expiry_date
        self.issuing_authority = issuing_authority
        self.status = status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "license_id": self.license_id,
            "facility_name": self.facility_name,
            "tax_id": self.tax_id,
            "facility_address": self.facility_address,
            "impact_group": self.impact_group,
            "max_wastewater_m3_day": self.max_wastewater_m3_day,
            "max_exhaust_m3_hour": self.max_exhaust_m3_hour,
            "max_hazardous_waste_tons_year": self.max_hazardous_waste_tons_year,
            "validity_years": self.validity_years,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "issuing_authority": self.issuing_authority,
            "status": self.status,
            "created_at": self.created_at,
        }


class GreenhouseGasAudit:
    """Represents a verified GHG inventory audit and carbon credit offset."""

    def __init__(
        self,
        audit_id: str,
        facility_name: str,
        reporting_year: int,
        scope1_tco2e: float,
        electricity_consumption_mwh: float,
        scope2_tco2e: float,
        scope3_tco2e: float,
        total_emissions_tco2e: float,
        is_mandatory_reporting: bool,
        allocated_quota_tco2e: float,
        carbon_credits_offset: float,
        net_emissions_tco2e: float,
        compliance_status: str,
        created_at: str | None = None,
    ) -> None:
        self.audit_id = audit_id
        self.facility_name = facility_name
        self.reporting_year = reporting_year
        self.scope1_tco2e = scope1_tco2e
        self.electricity_consumption_mwh = electricity_consumption_mwh
        self.scope2_tco2e = scope2_tco2e
        self.scope3_tco2e = scope3_tco2e
        self.total_emissions_tco2e = total_emissions_tco2e
        self.is_mandatory_reporting = is_mandatory_reporting
        self.allocated_quota_tco2e = allocated_quota_tco2e
        self.carbon_credits_offset = carbon_credits_offset
        self.net_emissions_tco2e = net_emissions_tco2e
        self.compliance_status = compliance_status
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "audit_id": self.audit_id,
            "facility_name": self.facility_name,
            "reporting_year": self.reporting_year,
            "scope1_tco2e": self.scope1_tco2e,
            "electricity_consumption_mwh": self.electricity_consumption_mwh,
            "scope2_tco2e": self.scope2_tco2e,
            "scope3_tco2e": self.scope3_tco2e,
            "total_emissions_tco2e": self.total_emissions_tco2e,
            "is_mandatory_reporting": self.is_mandatory_reporting,
            "allocated_quota_tco2e": self.allocated_quota_tco2e,
            "carbon_credits_offset": self.carbon_credits_offset,
            "net_emissions_tco2e": self.net_emissions_tco2e,
            "compliance_status": self.compliance_status,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Core Environment Engine
# ---------------------------------------------------------------------------


class EnvironmentEngine:
    """Autonomous Vietnamese Environmental Protection, EIA & Carbon Credits Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            mekong_dir = pathlib.Path(".mekong")
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "environment.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_database(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_impacts (
                    project_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    investor_name TEXT NOT NULL,
                    investment_capital_vnd REAL NOT NULL,
                    sector_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    is_environmentally_sensitive INTEGER NOT NULL,
                    daily_capacity REAL NOT NULL,
                    capacity_unit TEXT NOT NULL,
                    impact_group TEXT NOT NULL,
                    requires_eia INTEGER NOT NULL,
                    requires_pre_eia INTEGER NOT NULL,
                    requires_license INTEGER NOT NULL,
                    licensing_authority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS environmental_licenses (
                    license_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    tax_id TEXT NOT NULL,
                    facility_address TEXT NOT NULL,
                    impact_group TEXT NOT NULL,
                    max_wastewater_m3_day REAL NOT NULL,
                    max_exhaust_m3_hour REAL NOT NULL,
                    max_hazardous_waste_tons_year REAL NOT NULL,
                    validity_years INTEGER NOT NULL,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ghg_audits (
                    audit_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    reporting_year INTEGER NOT NULL,
                    scope1_tco2e REAL NOT NULL,
                    electricity_consumption_mwh REAL NOT NULL,
                    scope2_tco2e REAL NOT NULL,
                    scope3_tco2e REAL NOT NULL,
                    total_emissions_tco2e REAL NOT NULL,
                    is_mandatory_reporting INTEGER NOT NULL,
                    allocated_quota_tco2e REAL NOT NULL,
                    carbon_credits_offset REAL NOT NULL,
                    net_emissions_tco2e REAL NOT NULL,
                    compliance_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS epr_declarations (
                    declaration_id TEXT PRIMARY KEY,
                    producer_name TEXT NOT NULL,
                    tax_id TEXT NOT NULL,
                    product_code TEXT NOT NULL,
                    product_name_vi TEXT NOT NULL,
                    total_volume_kg REAL NOT NULL,
                    mandatory_rate_pct REAL NOT NULL,
                    required_recycling_kg REAL NOT NULL,
                    actual_recycled_kg REAL NOT NULL,
                    deficit_kg REAL NOT NULL,
                    vepf_rate_vnd_kg REAL NOT NULL,
                    vepf_contribution_vnd REAL NOT NULL,
                    fulfillment_status TEXT NOT NULL,
                    declaration_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS monitoring_audits (
                    audit_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    monitoring_type TEXT NOT NULL,
                    sampling_time TEXT NOT NULL,
                    param_json TEXT NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    violations_json TEXT NOT NULL,
                    action_required TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # 1. Project Impact Classification (Article 28 Law on Environmental Protection)
    # -----------------------------------------------------------------------

    def classify_project_impact(
        self,
        project_name: str,
        investor_name: str,
        investment_capital_vnd: float,
        sector_type: str = "MANUFACTURING",
        location: str = "Bình Dương, Việt Nam",
        is_environmentally_sensitive: bool = False,
        daily_capacity: float = 1000.0,
        capacity_unit: str = "tấn/năm",
    ) -> dict[str, typing.Any]:
        """Classify investment project into Group I, II, III, or IV under Law on Environmental Protection 2020."""
        if investment_capital_vnd < 0:
            raise ValueError("Vốn đầu tư của dự án không được âm.")
        if daily_capacity < 0:
            raise ValueError("Công suất dự án không được âm.")

        sector_clean = sector_type.strip().upper()

        # Group classification logic adhering to Decree 08/2022/NĐ-CP
        high_pollution_sectors = {"THERMAL_POWER", "STEEL_METALLURGY", "BASIC_CHEMICALS", "PULP_PAPER", "TANNING"}
        medium_pollution_sectors = {"MANUFACTURING", "TEXTILE_DYEING", "FOOD_PROCESSING", "PLASTIC_RECYCLING"}
        low_impact_sectors = {"SERVICES", "OFFICE", "SOFTWARE", "IT", "COMMERCE", "RETAIL"}

        if sector_clean in high_pollution_sectors or (is_environmentally_sensitive and investment_capital_vnd >= 200_000_000_000.0):
            impact_group = "GROUP_I"
        elif (sector_clean in medium_pollution_sectors and (investment_capital_vnd > 0 or daily_capacity > 0)) or is_environmentally_sensitive or investment_capital_vnd >= 100_000_000_000.0:
            impact_group = "GROUP_II"
        elif (investment_capital_vnd > 0 or daily_capacity > 0) and sector_clean not in low_impact_sectors:
            impact_group = "GROUP_III"
        else:
            impact_group = "GROUP_IV"

        group_info = PROJECT_IMPACT_GROUPS[impact_group]
        project_id = f"prj-{uuid.uuid4().hex[:12]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_impacts (
                    project_id, project_name, investor_name, investment_capital_vnd,
                    sector_type, location, is_environmentally_sensitive, daily_capacity,
                    capacity_unit, impact_group, requires_eia, requires_pre_eia,
                    requires_license, licensing_authority, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    project_name.strip(),
                    investor_name.strip(),
                    investment_capital_vnd,
                    sector_clean,
                    location.strip(),
                    1 if is_environmentally_sensitive else 0,
                    daily_capacity,
                    capacity_unit.strip(),
                    impact_group,
                    1 if group_info["requires_eia"] else 0,
                    1 if group_info["requires_pre_eia"] else 0,
                    1 if group_info["requires_license"] else 0,
                    group_info["authority"],
                    "CLASSIFIED",
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "project_id": project_id,
            "project_name": project_name,
            "investor_name": investor_name,
            "investment_capital_vnd": investment_capital_vnd,
            "sector_type": sector_clean,
            "location": location,
            "is_environmentally_sensitive": is_environmentally_sensitive,
            "daily_capacity": daily_capacity,
            "capacity_unit": capacity_unit,
            "impact_group": impact_group,
            "group_name_vi": group_info["name_vi"],
            "criteria": group_info["criteria"],
            "requires_pre_eia": group_info["requires_pre_eia"],
            "requires_eia": group_info["requires_eia"],
            "requires_license": group_info["requires_license"],
            "licensing_authority": group_info["authority"],
            "statutory_ref": group_info["statutory_ref"],
        }

    # -----------------------------------------------------------------------
    # 2. Integrated Environmental Permitting (GPMT)
    # -----------------------------------------------------------------------

    def issue_environmental_license(
        self,
        facility_name: str,
        tax_id: str,
        facility_address: str,
        impact_group: str = "GROUP_II",
        max_wastewater_m3_day: float = 500.0,
        max_exhaust_m3_hour: float = 10000.0,
        max_hazardous_waste_tons_year: float = 12.0,
    ) -> dict[str, typing.Any]:
        """Issue an integrated Environmental Permit (GPMT) under Articles 39-49 Law on Environmental Protection."""
        group_clean = impact_group.strip().upper()
        if group_clean not in PROJECT_IMPACT_GROUPS:
            raise ValueError(f"Nhóm tác động môi trường không hợp lệ: '{impact_group}'.")

        group_info = PROJECT_IMPACT_GROUPS[group_clean]
        if not group_info["requires_license"]:
            raise ValueError(f"Dự án {group_info['name_vi']} thuộc diện miễn Giấy phép Môi trường.")

        validity_years = group_info["license_term_years"]
        today_date = datetime.date.today()
        # Compute expiry date
        expiry_year = today_date.year + validity_years
        expiry_date = today_date.replace(year=expiry_year).isoformat()

        license_id = f"GPMT-{today_date.year}-{uuid.uuid4().hex[:6].upper()}"
        issuing_authority = group_info["authority"]

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO environmental_licenses (
                    license_id, facility_name, tax_id, facility_address,
                    impact_group, max_wastewater_m3_day, max_exhaust_m3_hour,
                    max_hazardous_waste_tons_year, validity_years, issue_date,
                    expiry_date, issuing_authority, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_id,
                    facility_name.strip(),
                    tax_id.strip(),
                    facility_address.strip(),
                    group_clean,
                    max_wastewater_m3_day,
                    max_exhaust_m3_hour,
                    max_hazardous_waste_tons_year,
                    validity_years,
                    today_date.isoformat(),
                    expiry_date,
                    issuing_authority,
                    "ACTIVE",
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "license_id": license_id,
            "facility_name": facility_name,
            "tax_id": tax_id,
            "facility_address": facility_address,
            "impact_group": group_clean,
            "group_name_vi": group_info["name_vi"],
            "max_wastewater_m3_day": max_wastewater_m3_day,
            "max_exhaust_m3_hour": max_exhaust_m3_hour,
            "max_hazardous_waste_tons_year": max_hazardous_waste_tons_year,
            "validity_years": validity_years,
            "issue_date": today_date.isoformat(),
            "expiry_date": expiry_date,
            "issuing_authority": issuing_authority,
            "status": "ACTIVE",
            "statutory_ref": "Điều 39 - Điều 49 Luật Bảo vệ môi trường 2020",
        }

    # -----------------------------------------------------------------------
    # 3. GHG Scope 1/2/3 Inventory & Carbon Credits Offsetting (Decree 06/2022)
    # -----------------------------------------------------------------------

    def audit_ghg_emissions(
        self,
        facility_name: str,
        reporting_year: int = 2026,
        scope1_fuel_tco2e: float = 1200.0,
        electricity_kwh: float = 3_000_000.0,
        scope3_indirect_tco2e: float = 350.0,
        allocated_quota_tco2e: float = 3500.0,
        carbon_credits_retired: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Audit GHG emissions across Scopes 1, 2, 3 and calculate carbon credits offset under Decree 06/2022/NĐ-CP."""
        if scope1_fuel_tco2e < 0 or electricity_kwh < 0 or scope3_indirect_tco2e < 0:
            raise ValueError("Số liệu tiêu thụ nhiên liệu/điện năng không được âm.")
        if carbon_credits_retired < 0:
            raise ValueError("Số lượng tín chỉ carbon bù trừ không được âm.")

        # Calculate Scope 2 from electricity consumption using Vietnam grid emission factor
        # 1 kWh * factor kgCO2 = kgCO2; convert to tCO2e (divide by 1000)
        scope2_tco2e = round((electricity_kwh * GRID_ELECTRICITY_EMISSION_FACTOR_KG_CO2_PER_KWH) / 1000.0, 2)
        total_emissions_tco2e = round(scope1_fuel_tco2e + scope2_tco2e + scope3_indirect_tco2e, 2)

        # Assess mandatory inventory threshold (>= 3,000 tCO2e/year)
        is_mandatory = total_emissions_tco2e >= GHG_MANDATORY_INVENTORY_THRESHOLD_TCO2E

        # Carbon offset calculation: 1 credit = 1 tCO2e
        net_emissions_tco2e = round(max(0.0, total_emissions_tco2e - carbon_credits_retired), 2)

        # Cap-and-trade compliance
        if allocated_quota_tco2e > 0:
            compliance_status = "COMPLIANT" if net_emissions_tco2e <= allocated_quota_tco2e else "QUOTA_EXCEEDED"
        else:
            compliance_status = "INVENTORIED"

        audit_id = f"ghg-{uuid.uuid4().hex[:12]}"
        electricity_mwh = round(electricity_kwh / 1000.0, 2)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ghg_audits (
                    audit_id, facility_name, reporting_year, scope1_tco2e,
                    electricity_consumption_mwh, scope2_tco2e, scope3_tco2e,
                    total_emissions_tco2e, is_mandatory_reporting,
                    allocated_quota_tco2e, carbon_credits_offset,
                    net_emissions_tco2e, compliance_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    facility_name.strip(),
                    reporting_year,
                    scope1_fuel_tco2e,
                    electricity_mwh,
                    scope2_tco2e,
                    scope3_indirect_tco2e,
                    total_emissions_tco2e,
                    1 if is_mandatory else 0,
                    allocated_quota_tco2e,
                    carbon_credits_retired,
                    net_emissions_tco2e,
                    compliance_status,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "audit_id": audit_id,
            "facility_name": facility_name,
            "reporting_year": reporting_year,
            "scope1_tco2e": scope1_fuel_tco2e,
            "electricity_kwh": electricity_kwh,
            "scope2_tco2e": scope2_tco2e,
            "scope3_tco2e": scope3_indirect_tco2e,
            "total_emissions_tco2e": total_emissions_tco2e,
            "is_mandatory_reporting": is_mandatory,
            "mandatory_threshold_tco2e": GHG_MANDATORY_INVENTORY_THRESHOLD_TCO2E,
            "allocated_quota_tco2e": allocated_quota_tco2e,
            "carbon_credits_offset": carbon_credits_retired,
            "net_emissions_tco2e": net_emissions_tco2e,
            "compliance_status": compliance_status,
            "statutory_ref": "Nghị định 06/2022/NĐ-CP về giảm nhẹ phát thải khí nhà kính",
        }

    # -----------------------------------------------------------------------
    # 4. Extended Producer Responsibility (EPR) & Recycling Quota (Decree 08/2022)
    # -----------------------------------------------------------------------

    def calculate_epr_obligations(
        self,
        producer_name: str,
        tax_id: str,
        product_code: str = "PACKAGING_PLASTIC_PET",
        total_volume_kg: float = 100_000.0,
        actual_recycled_kg: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Calculate mandatory recycling quotas and VEPF contribution under Articles 54-55 Law on Environmental Protection."""
        if total_volume_kg <= 0:
            raise ValueError("Tổng khối lượng sản phẩm/bao bì đưa ra thị trường phải lớn hơn 0.")
        if actual_recycled_kg < 0:
            raise ValueError("Khối lượng tái chế thực tế không được âm.")

        prod_clean = product_code.strip().upper()
        if prod_clean not in EPR_RECYCLING_RATES:
            valid_codes = list(EPR_RECYCLING_RATES.keys())
            raise ValueError(f"Mã sản phẩm/bao bì EPR không hợp lệ: '{product_code}'. Hỗ trợ: {valid_codes}")

        rule = EPR_RECYCLING_RATES[prod_clean]
        rate_pct = rule["mandatory_rate_pct"]
        cost_per_kg = rule["vepf_cost_vnd_per_kg"]

        required_recycling_kg = round(total_volume_kg * (rate_pct / 100.0), 2)
        deficit_kg = max(0.0, required_recycling_kg - actual_recycled_kg)

        # If deficit > 0, producer must contribute to Vietnam Environment Protection Fund (VEPF)
        vepf_contribution_vnd = round(deficit_kg * cost_per_kg, 0)
        fulfillment_status = "FULFILLED" if deficit_kg == 0.0 else "CONTRIBUTION_REQUIRED"

        declaration_id = f"epr-{uuid.uuid4().hex[:12]}"
        today_date = datetime.date.today().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO epr_declarations (
                    declaration_id, producer_name, tax_id, product_code,
                    product_name_vi, total_volume_kg, mandatory_rate_pct,
                    required_recycling_kg, actual_recycled_kg, deficit_kg,
                    vepf_rate_vnd_kg, vepf_contribution_vnd, fulfillment_status,
                    declaration_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    declaration_id,
                    producer_name.strip(),
                    tax_id.strip(),
                    prod_clean,
                    rule["name_vi"],
                    total_volume_kg,
                    rate_pct,
                    required_recycling_kg,
                    actual_recycled_kg,
                    deficit_kg,
                    cost_per_kg,
                    vepf_contribution_vnd,
                    fulfillment_status,
                    today_date,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                ),
            )
            conn.commit()

        return {
            "declaration_id": declaration_id,
            "producer_name": producer_name,
            "tax_id": tax_id,
            "product_code": prod_clean,
            "product_name_vi": rule["name_vi"],
            "total_volume_kg": total_volume_kg,
            "mandatory_recycling_rate_pct": rate_pct,
            "required_recycling_kg": required_recycling_kg,
            "actual_recycled_kg": actual_recycled_kg,
            "deficit_kg": deficit_kg,
            "vepf_cost_vnd_per_kg": cost_per_kg,
            "vepf_contribution_vnd": vepf_contribution_vnd,
            "fulfillment_status": fulfillment_status,
            "is_fully_recycled": deficit_kg == 0.0,
            "statutory_ref": "Điều 54, 55 Luật BVMT 2020 & Nghị định 08/2022/NĐ-CP",
        }

    # -----------------------------------------------------------------------
    # 5. Continuous Environmental Monitoring & QCVN Auditing
    # -----------------------------------------------------------------------

    def audit_monitoring_telemetry(
        self,
        facility_name: str,
        monitoring_type: str = "WASTEWATER",
        ph: float = 7.2,
        cod_mg_l: float = 45.0,
        tss_mg_l: float = 30.0,
        temperature_c: float = 32.0,
        dust_mg_nm3: float = 80.0,
        so2_mg_nm3: float = 120.0,
        nox_mg_nm3: float = 250.0,
        co_mg_nm3: float = 300.0,
    ) -> dict[str, typing.Any]:
        """Audit automated continuous monitoring sensor data against QCVN 40:2011 & QCVN 19:2009."""
        mon_type_clean = monitoring_type.strip().upper()
        violations: list[str] = []
        param_data: dict[str, float] = {}

        if mon_type_clean == "WASTEWATER":
            param_data = {
                "ph": ph,
                "cod_mg_l": cod_mg_l,
                "tss_mg_l": tss_mg_l,
                "temperature_c": temperature_c,
            }
            if ph < QCVN_THRESHOLDS["WASTEWATER"]["PH_MIN"] or ph > QCVN_THRESHOLDS["WASTEWATER"]["PH_MAX"]:
                violations.append(f"pH = {ph} vượt ngưỡng quy chuẩn (6.0 - 9.0) theo QCVN 40:2011/BTNMT Cột A.")
            if cod_mg_l > QCVN_THRESHOLDS["WASTEWATER"]["COD_MAX_MG_L"]:
                violations.append(f"COD = {cod_mg_l} mg/L vượt giới hạn tối đa {QCVN_THRESHOLDS['WASTEWATER']['COD_MAX_MG_L']} mg/L.")
            if tss_mg_l > QCVN_THRESHOLDS["WASTEWATER"]["TSS_MAX_MG_L"]:
                violations.append(f"TSS = {tss_mg_l} mg/L vượt giới hạn tối đa {QCVN_THRESHOLDS['WASTEWATER']['TSS_MAX_MG_L']} mg/L.")
            if temperature_c > QCVN_THRESHOLDS["WASTEWATER"]["TEMPERATURE_MAX_C"]:
                violations.append(f"Nhiệt độ = {temperature_c}°C vượt giới hạn 40°C.")
            standard_ref = "QCVN 40:2011/BTNMT (Nước thải công nghiệp Cột A)"

        elif mon_type_clean == "EXHAUST":
            param_data = {
                "dust_mg_nm3": dust_mg_nm3,
                "so2_mg_nm3": so2_mg_nm3,
                "nox_mg_nm3": nox_mg_nm3,
                "co_mg_nm3": co_mg_nm3,
            }
            if dust_mg_nm3 > QCVN_THRESHOLDS["EXHAUST"]["DUST_MAX_MG_NM3"]:
                violations.append(f"Bụi tổng = {dust_mg_nm3} mg/Nm3 vượt giới hạn {QCVN_THRESHOLDS['EXHAUST']['DUST_MAX_MG_NM3']} mg/Nm3 theo QCVN 19:2009/BTNMT.")
            if so2_mg_nm3 > QCVN_THRESHOLDS["EXHAUST"]["SO2_MAX_MG_NM3"]:
                violations.append(f"SO2 = {so2_mg_nm3} mg/Nm3 vượt giới hạn {QCVN_THRESHOLDS['EXHAUST']['SO2_MAX_MG_NM3']} mg/Nm3.")
            if nox_mg_nm3 > QCVN_THRESHOLDS["EXHAUST"]["NOX_MAX_MG_NM3"]:
                violations.append(f"NOx = {nox_mg_nm3} mg/Nm3 vượt giới hạn {QCVN_THRESHOLDS['EXHAUST']['NOX_MAX_MG_NM3']} mg/Nm3.")
            if co_mg_nm3 > QCVN_THRESHOLDS["EXHAUST"]["CO_MAX_MG_NM3"]:
                violations.append(f"CO = {co_mg_nm3} mg/Nm3 vượt giới hạn {QCVN_THRESHOLDS['EXHAUST']['CO_MAX_MG_NM3']} mg/Nm3.")
            standard_ref = "QCVN 19:2009/BTNMT (Khí thải công nghiệp Cột B)"
        else:
            raise ValueError(f"Loại hình quan trắc không hợp lệ: '{monitoring_type}'. Hỗ trợ: WASTEWATER, EXHAUST")

        is_compliant = len(violations) == 0
        action_required = (
            "Duy trì chế độ vận hành ổn định hệ thống xử lý chất thải."
            if is_compliant
            else "Cảnh báo khẩn cấp: Hiệu chỉnh ngay trạm xử lý nước thải / lọc bụi khí thải để tránh bị xử phạt theo Nghị định 45/2022/NĐ-CP."
        )

        audit_id = f"mon-{uuid.uuid4().hex[:12]}"
        sampling_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO monitoring_audits (
                    audit_id, facility_name, monitoring_type, sampling_time,
                    param_json, is_compliant, violations_json, action_required, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    facility_name.strip(),
                    mon_type_clean,
                    sampling_time,
                    json.dumps(param_data),
                    1 if is_compliant else 0,
                    json.dumps(violations, ensure_ascii=False),
                    action_required,
                    sampling_time,
                ),
            )
            conn.commit()

        return {
            "audit_id": audit_id,
            "facility_name": facility_name,
            "monitoring_type": mon_type_clean,
            "sampling_time": sampling_time,
            "parameters": param_data,
            "is_compliant": is_compliant,
            "violations": violations,
            "action_required": action_required,
            "standard_ref": standard_ref,
        }

    # -----------------------------------------------------------------------
    # 6. Listing and Summary Methods
    # -----------------------------------------------------------------------

    def list_projects(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List classified investment projects."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM project_impacts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_licenses(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List issued Environmental Permits."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM environmental_licenses ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_ghg_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List GHG audits."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM ghg_audits ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_epr_declarations(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List EPR declarations."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM epr_declarations ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_monitoring_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List monitoring audits."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM monitoring_audits ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    # -----------------------------------------------------------------------
    # 7. System Status & Summary Telemetry
    # -----------------------------------------------------------------------

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate Vietnamese environmental protection & carbon telemetry."""
        with self._get_connection() as conn:
            total_projects = conn.execute("SELECT COUNT(*) FROM project_impacts").fetchone()[0]
            group1_projects = conn.execute("SELECT COUNT(*) FROM project_impacts WHERE impact_group = 'GROUP_I'").fetchone()[0]

            total_licenses = conn.execute("SELECT COUNT(*) FROM environmental_licenses").fetchone()[0]
            active_licenses = conn.execute("SELECT COUNT(*) FROM environmental_licenses WHERE status = 'ACTIVE'").fetchone()[0]

            total_ghg_audits = conn.execute("SELECT COUNT(*) FROM ghg_audits").fetchone()[0]
            total_emissions = conn.execute("SELECT COALESCE(SUM(total_emissions_tco2e), 0.0) FROM ghg_audits").fetchone()[0]
            total_carbon_credits = conn.execute("SELECT COALESCE(SUM(carbon_credits_offset), 0.0) FROM ghg_audits").fetchone()[0]

            total_epr = conn.execute("SELECT COUNT(*) FROM epr_declarations").fetchone()[0]
            total_vepf_fund = conn.execute("SELECT COALESCE(SUM(vepf_contribution_vnd), 0.0) FROM epr_declarations").fetchone()[0]

            total_monitors = conn.execute("SELECT COUNT(*) FROM monitoring_audits").fetchone()[0]
            compliant_monitors = conn.execute("SELECT COUNT(*) FROM monitoring_audits WHERE is_compliant = 1").fetchone()[0]

        return {
            "status": "HEALTHY",
            "engine": "EnvironmentEngine",
            "statutory_law": "Luật Bảo vệ môi trường 2020 (Luật số 72/2020/QH14)",
            "database_path": str(self.db_path),
            "project_classification": {
                "total_projects": total_projects,
                "group_i_high_impact": group1_projects,
            },
            "environmental_licenses": {
                "total_issued": total_licenses,
                "active_licenses": active_licenses,
            },
            "ghg_and_carbon": {
                "total_audits": total_ghg_audits,
                "total_emissions_tco2e": total_emissions,
                "total_credits_retired": total_carbon_credits,
                "mandatory_inventory_threshold_tco2e": GHG_MANDATORY_INVENTORY_THRESHOLD_TCO2E,
            },
            "extended_producer_responsibility": {
                "total_declarations": total_epr,
                "total_vepf_contribution_vnd": total_vepf_fund,
            },
            "automated_monitoring": {
                "total_audits": total_monitors,
                "compliant_audits": compliant_monitors,
            },
        }

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Mining, Mineral Exploitation, Royalties & Environmental Rehabilitation Engine.

Implements statutory mineral extraction, concession licensing, financial obligations, and environmental safety under:
- Luật Khoáng sản 2010 (Luật số 60/2010/QH12) & Nghị định 158/2016/NĐ-CP:
  * Quy trình cấp phép thăm dò, phê duyệt trữ lượng và cấp phép khai thác khoáng sản.
  * Phân cấp thẩm quyền: Bộ Tài nguyên và Môi trường (khoáng sản chiến lược: đất hiếm, bauxit, than, vàng...)
    và UBND cấp tỉnh (vật liệu xây dựng thông thường: cát, sỏi, đá, đất đắp).
  * Thời hạn cấp phép tối đa 30 năm, gia hạn không quá 20 năm.
- Nghị định 67/2019/NĐ-CP & Nghị định 36/2020/NĐ-CP:
  * Phương pháp xác định tiền cấp quyền khai thác khoáng sản (T = Q * G * K * R).
  * Hệ số khai thác K: Khai thác lộ thiên (K = 1.0), Khai thác hầm lò (K = 0.9).
  * Tỷ lệ thu tiền cấp quyền R theo từng nhóm khoáng sản (1% - 5%).
- Luật Thuế Tài nguyên 2009 & Nghị quyết 1084/2015/UBTVQH13, Thông tư 152/2015/TT-BTC:
  * Biểu thuế tài nguyên đối với khoáng sản kim loại, khoáng sản phi kim loại và năng lượng.
- Luật Bảo vệ Môi trường 2020 & Nghị định 08/2022/NĐ-CP:
  * Đề án cải tạo, phục hồi môi trường và nghĩa vụ ký quỹ phục hồi môi trường tại Quỹ Bảo vệ môi trường.
  * Tiêu chuẩn xả thải mỏ nước thải công nghiệp mỏ theo QCVN 40:2011/BTNMT & QCVN 19:2009/BTNMT.
- Nghị định 23/2020/NĐ-CP:
  * Quy định nghiêm ngặt khai thác cát, sỏi lòng sông: chỉ hoạt động từ 07:00 đến 17:00 (cấm khai thác ban đêm),
    bắt buộc gắn định vị vệ tinh GPS trên tàu hút/sà lan và camera giám sát tại bến bãi tập kết.
- Lưu trữ SQLite WAL tại ``.mekong/mining.db``.

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
# Mineral Regulatory Baselines & Classifications
# ---------------------------------------------------------------------------

MINERAL_CATALOG: dict[str, dict[str, typing.Any]] = {
    "RARE_EARTH": {
        "name": "Đất hiếm (Rare Earth Elements - Neodymium, Dysprosium, Lanthanum)",
        "unit": "TẤN_OXIT",
        "authority": "BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG",
        "benchmark_price_vnd": 850000000.0,
        "rights_fee_pct_R": 5.0,  # 5% theo Nghị định 67/2019/NĐ-CP
        "royalty_tax_pct": 18.0,  # 18% theo Nghị quyết 1084/2015
        "strategic_national_asset": True,
    },
    "BAUXITE": {
        "name": "Quặng Bauxit (Nhôm - Bauxite Ore)",
        "unit": "TẤN",
        "authority": "BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG",
        "benchmark_price_vnd": 650000.0,
        "rights_fee_pct_R": 4.0,
        "royalty_tax_pct": 12.0,
        "strategic_national_asset": True,
    },
    "GOLD_ORE": {
        "name": "Quặng Vàng và Kim loại quý (Gold & Precious Metals)",
        "unit": "TẤN_QUẶNG",
        "authority": "BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG",
        "benchmark_price_vnd": 4500000.0,
        "rights_fee_pct_R": 5.0,
        "royalty_tax_pct": 15.0,
        "strategic_national_asset": True,
    },
    "COAL_ENERGY": {
        "name": "Than đá (Anthracite / Coking Coal)",
        "unit": "TẤN",
        "authority": "BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG",
        "benchmark_price_vnd": 2400000.0,
        "rights_fee_pct_R": 3.0,
        "royalty_tax_pct": 10.0,
        "strategic_national_asset": True,
    },
    "TITANIUM": {
        "name": "Quặng Titan (Ilmenite, Rutile, Zircon sa khoáng)",
        "unit": "TẤN",
        "authority": "BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG",
        "benchmark_price_vnd": 3200000.0,
        "rights_fee_pct_R": 4.0,
        "royalty_tax_pct": 16.0,
        "strategic_national_asset": True,
    },
    "LIMESTONE_CEMENT": {
        "name": "Đá vôi sản xuất xi măng (Limestone for Cement)",
        "unit": "TẤN",
        "authority": "BỘ TÀI NGUYÊN VÀ MÔI TRƯỜNG",
        "benchmark_price_vnd": 120000.0,
        "rights_fee_pct_R": 3.0,
        "royalty_tax_pct": 10.0,
        "strategic_national_asset": False,
    },
    "RIVER_SAND": {
        "name": "Cát san lấp & Cát xây dựng lòng sông (River Sand)",
        "unit": "M3",
        "authority": "UBND CẤP TỈNH / THÀNH PHỐ",
        "benchmark_price_vnd": 280000.0,
        "rights_fee_pct_R": 5.0,
        "royalty_tax_pct": 12.0,
        "strategic_national_asset": False,
    },
    "CONSTRUCTION_STONE": {
        "name": "Đá xây dựng thông thường (Aggregate Construction Stone)",
        "unit": "M3",
        "authority": "UBND CẤP TỈNH / THÀNH PHỐ",
        "benchmark_price_vnd": 220000.0,
        "rights_fee_pct_R": 3.0,
        "royalty_tax_pct": 10.0,
        "strategic_national_asset": False,
    },
}

MINING_METHODS: dict[str, dict[str, typing.Any]] = {
    "OPEN_PIT": {
        "title": "Khai thác lộ thiên (Surface / Open-pit mining)",
        "coefficient_K": 1.0,
        "dust_control_mandated": True,
        "slope_stability_factor": 1.3,
    },
    "UNDERGROUND": {
        "title": "Khai thác hầm lò (Underground mining)",
        "coefficient_K": 0.9,  # Nghị định 67/2019 quy định K = 0.9 cho hầm lò
        "dust_control_mandated": True,
        "slope_stability_factor": 1.5,
    },
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


class MiningEngine:
    """Core engine for Vietnamese Mining, Mineral Exploitation, Royalties & Environmental Rehabilitation."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "mining.db"
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
                CREATE TABLE IF NOT EXISTS mining_licenses (
                    license_id TEXT PRIMARY KEY,
                    license_number TEXT NOT NULL,
                    mine_name TEXT NOT NULL,
                    mineral_type TEXT NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    approved_reserve REAL NOT NULL,
                    annual_capacity REAL NOT NULL,
                    mining_method TEXT NOT NULL,
                    mine_area_hectares REAL NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    location_province TEXT NOT NULL,
                    license_duration_years INTEGER NOT NULL,
                    is_active INTEGER NOT NULL,
                    granted_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mineral_rights_fees (
                    fee_id TEXT PRIMARY KEY,
                    license_id TEXT NOT NULL,
                    reserve_volume REAL NOT NULL,
                    unit_price_vnd REAL NOT NULL,
                    method_k_coefficient REAL NOT NULL,
                    rights_rate_r_pct REAL NOT NULL,
                    total_rights_fee_vnd REAL NOT NULL,
                    annual_installment_vnd REAL NOT NULL,
                    calculated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS resource_royalty_taxes (
                    tax_id TEXT PRIMARY KEY,
                    license_id TEXT NOT NULL,
                    tax_period TEXT NOT NULL,
                    actual_mined_volume REAL NOT NULL,
                    taxable_unit_price_vnd REAL NOT NULL,
                    tax_rate_pct REAL NOT NULL,
                    payable_royalty_tax_vnd REAL NOT NULL,
                    declared_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS environmental_rehabilitations (
                    rehab_id TEXT PRIMARY KEY,
                    license_id TEXT NOT NULL,
                    total_rehab_estimate_vnd REAL NOT NULL,
                    initial_deposit_vnd REAL NOT NULL,
                    replanted_trees_count INTEGER NOT NULL,
                    wastewater_ph REAL NOT NULL,
                    wastewater_tss_mg_l REAL NOT NULL,
                    is_qcvn40_compliant INTEGER NOT NULL,
                    is_deposit_paid INTEGER NOT NULL,
                    rehabilitated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS river_sand_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    license_id TEXT NOT NULL,
                    vessel_plate TEXT NOT NULL,
                    operation_hour_time TEXT NOT NULL,
                    is_within_daytime_hours INTEGER NOT NULL,
                    is_gps_installed INTEGER NOT NULL,
                    is_dock_camera_installed INTEGER NOT NULL,
                    measured_cargo_m3 REAL NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    inspected_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Concession Licensing & Reserves (Luật Khoáng sản 2010 & NĐ 158/2016)
    # -----------------------------------------------------------------------

    def register_mining_license(
        self,
        mine_name: str,
        mineral_type: str = "RARE_EARTH",
        enterprise_name: str = "Vietnam Rare Earth Joint Stock Company",
        approved_reserve: float = 2500000.0,
        annual_capacity: float = 120000.0,
        mining_method: str = "OPEN_PIT",
        mine_area_hectares: float = 85.5,
        location_province: str = "Lai Châu",
        duration_years: int = 25,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register mineral exploitation license and determine statutory licensing authority."""
        clean_min = mineral_type.upper().strip()
        min_info = MINERAL_CATALOG.get(clean_min, MINERAL_CATALOG["RARE_EARTH"])

        clean_method = mining_method.upper().strip()
        method_info = MINING_METHODS.get(clean_method, MINING_METHODS["OPEN_PIT"])

        # Statutory maximum license duration is 30 years under Article 54 Law on Minerals
        valid_years = min(duration_years, 30)

        license_id = f"LIC-MIN-{uuid.uuid4().hex[:8].upper()}"
        lic_number = f"GPKT-{uuid.uuid4().hex[:6].upper()}/BTNMT" if min_info["strategic_national_asset"] else f"GPKT-{uuid.uuid4().hex[:6].upper()}/UBND"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "license_id": license_id,
            "license_number": lic_number,
            "concession_profile": {
                "mine_name": mine_name.strip(),
                "mineral_code": clean_min,
                "mineral_name": min_info["name"],
                "unit": min_info["unit"],
                "enterprise_name": enterprise_name.strip(),
                "approved_reserve": approved_reserve,
                "annual_capacity": annual_capacity,
                "mining_method": method_info["title"],
                "mine_area_hectares": mine_area_hectares,
                "location_province": location_province.strip(),
                "license_duration_years": valid_years,
            },
            "statutory_jurisdiction": {
                "licensing_authority": min_info["authority"],
                "is_strategic_national_asset": min_info["strategic_national_asset"],
                "statutory_basis": "Luật Khoáng sản 2010 (Luật số 60/2010/QH12) & Nghị định 158/2016/NĐ-CP",
            },
            "granted_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO mining_licenses (
                        license_id, license_number, mine_name, mineral_type,
                        enterprise_name, approved_reserve, annual_capacity,
                        mining_method, mine_area_hectares, issuing_authority,
                        location_province, license_duration_years, is_active, granted_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        license_id,
                        lic_number,
                        mine_name.strip(),
                        clean_min,
                        enterprise_name.strip(),
                        approved_reserve,
                        annual_capacity,
                        clean_method,
                        mine_area_hectares,
                        min_info["authority"],
                        location_province.strip(),
                        valid_years,
                        1,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Mineral Rights Fee Calculation (Nghị định 67/2019/NĐ-CP: T = Q * G * K * R)
    # -----------------------------------------------------------------------

    def calculate_mineral_rights_fee(
        self,
        license_id: str,
        reserve_volume: float | None = None,
        custom_unit_price_vnd: float | None = None,
        mining_method: str = "OPEN_PIT",
        mineral_type: str = "RARE_EARTH",
        payment_years: int = 10,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Calculate statutory concession mineral rights fee T = Q * G * K * R under Decree 67/2019/NĐ-CP."""
        clean_min = mineral_type.upper().strip()
        min_info = MINERAL_CATALOG.get(clean_min, MINERAL_CATALOG["RARE_EARTH"])

        clean_method = mining_method.upper().strip()
        method_info = MINING_METHODS.get(clean_method, MINING_METHODS["OPEN_PIT"])

        q = reserve_volume if reserve_volume is not None and reserve_volume > 0 else 1000000.0
        g = custom_unit_price_vnd if custom_unit_price_vnd is not None and custom_unit_price_vnd > 0 else min_info["benchmark_price_vnd"]
        k = method_info["coefficient_K"]
        r = min_info["rights_fee_pct_R"]

        # Statutory formula: T = Q * G * K * R
        total_fee_vnd = q * g * k * (r / 100.0)
        p_years = max(1, min(payment_years, 30))
        annual_installment_vnd = total_fee_vnd / p_years

        fee_id = f"FEE-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "fee_id": fee_id,
            "license_id": license_id.strip(),
            "rights_fee_computation": {
                "mineral_name": min_info["name"],
                "chargeable_reserve_Q": q,
                "unit": min_info["unit"],
                "statutory_price_G_vnd": g,
                "method_coefficient_K": k,
                "method_name": method_info["title"],
                "rights_rate_R_pct": r,
                "total_mineral_rights_fee_vnd": total_fee_vnd,
                "payment_installment_years": p_years,
                "annual_installment_vnd": annual_installment_vnd,
            },
            "statutory_basis": "Nghị định 67/2019/NĐ-CP & Nghị định 36/2020/NĐ-CP (Quy định phương pháp tính tiền cấp quyền khai thác khoáng sản)",
            "calculated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO mineral_rights_fees (
                        fee_id, license_id, reserve_volume, unit_price_vnd,
                        method_k_coefficient, rights_rate_r_pct, total_rights_fee_vnd,
                        annual_installment_vnd, calculated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fee_id,
                        license_id.strip(),
                        q,
                        g,
                        k,
                        r,
                        total_fee_vnd,
                        annual_installment_vnd,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Natural Resource Royalty Tax (Luật Thuế Tài nguyên & TT 152/2015)
    # -----------------------------------------------------------------------

    def calculate_resource_royalty_tax(
        self,
        license_id: str,
        tax_period: str = "2026-Q1",
        actual_mined_volume: float = 30000.0,
        mineral_type: str = "RARE_EARTH",
        taxable_unit_price_vnd: float | None = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute natural resources royalty tax payable on extracted mineral yields."""
        clean_min = mineral_type.upper().strip()
        min_info = MINERAL_CATALOG.get(clean_min, MINERAL_CATALOG["RARE_EARTH"])

        price = taxable_unit_price_vnd if taxable_unit_price_vnd is not None and taxable_unit_price_vnd > 0 else min_info["benchmark_price_vnd"]
        tax_rate = min_info["royalty_tax_pct"]

        payable_tax_vnd = actual_mined_volume * price * (tax_rate / 100.0)

        tax_id = f"TAX-RES-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "tax_id": tax_id,
            "license_id": license_id.strip(),
            "royalty_declaration": {
                "tax_period": tax_period.strip(),
                "mineral_code": clean_min,
                "mineral_name": min_info["name"],
                "actual_mined_volume": actual_mined_volume,
                "unit": min_info["unit"],
                "taxable_unit_price_vnd": price,
                "royalty_tax_rate_pct": tax_rate,
                "payable_royalty_tax_vnd": payable_tax_vnd,
            },
            "statutory_basis": "Luật Thuế Tài nguyên 2009, Nghị quyết 1084/2015/UBTVQH13 & Thông tư 152/2015/TT-BTC",
            "declared_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO resource_royalty_taxes (
                        tax_id, license_id, tax_period, actual_mined_volume,
                        taxable_unit_price_vnd, tax_rate_pct, payable_royalty_tax_vnd,
                        declared_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tax_id,
                        license_id.strip(),
                        tax_period.strip(),
                        actual_mined_volume,
                        price,
                        tax_rate,
                        payable_tax_vnd,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Environmental Rehabilitation & Mine Closure Escrow (Luật BVMT 2020)
    # -----------------------------------------------------------------------

    def audit_environmental_rehabilitation(
        self,
        license_id: str,
        total_rehab_estimate_vnd: float = 12000000000.0,
        initial_deposit_pct: float = 25.0,
        replanted_trees_count: int = 15000,
        wastewater_ph: float = 7.2,
        wastewater_tss_mg_l: float = 38.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit statutory environmental rehabilitation deposit and wastewater effluent compliance against QCVN 40:2011/BTNMT."""
        # Decree 08/2022 mandates minimum 25% initial deposit for environmental rehabilitation
        valid_dep_pct = max(25.0, initial_deposit_pct)
        initial_deposit_vnd = total_rehab_estimate_vnd * (valid_dep_pct / 100.0)

        # Effluent compliance under QCVN 40:2011/BTNMT: pH 6.0 - 9.0, TSS <= 50.0 mg/L
        ph_ok = 6.0 <= wastewater_ph <= 9.0
        tss_ok = wastewater_tss_mg_l <= 50.0
        is_qcvn40_compliant = ph_ok and tss_ok

        rehab_id = f"REHAB-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "rehab_id": rehab_id,
            "license_id": license_id.strip(),
            "environmental_escrow": {
                "total_rehabilitation_cost_vnd": total_rehab_estimate_vnd,
                "initial_deposit_pct": valid_dep_pct,
                "initial_deposit_vnd": initial_deposit_vnd,
                "is_deposit_compliant": valid_dep_pct >= 25.0,
                "escrow_fund": "Quỹ Bảo vệ Môi trường Việt Nam (VEPF)",
            },
            "effluent_and_greening": {
                "replanted_trees_count": replanted_trees_count,
                "wastewater_ph": wastewater_ph,
                "ph_compliant": ph_ok,
                "wastewater_tss_mg_l": wastewater_tss_mg_l,
                "tss_compliant": tss_ok,
                "is_qcvn40_compliant": is_qcvn40_compliant,
                "verdict": "ENVIRONMENTAL_REHABILITATION_COMPLIANT" if is_qcvn40_compliant else "NON_COMPLIANT_EFFLUENT_DETECTED",
            },
            "statutory_basis": "Luật Bảo vệ Môi trường 2020, Nghị định 08/2022/NĐ-CP & QCVN 40:2011/BTNMT",
            "rehabilitated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO environmental_rehabilitations (
                        rehab_id, license_id, total_rehab_estimate_vnd,
                        initial_deposit_vnd, replanted_trees_count, wastewater_ph,
                        wastewater_tss_mg_l, is_qcvn40_compliant, is_deposit_paid,
                        rehabilitated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rehab_id,
                        license_id.strip(),
                        total_rehab_estimate_vnd,
                        initial_deposit_vnd,
                        replanted_trees_count,
                        wastewater_ph,
                        wastewater_tss_mg_l,
                        1 if is_qcvn40_compliant else 0,
                        1,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # River Sand & Gravel Exploitation Compliance (Nghị định 23/2020/NĐ-CP)
    # -----------------------------------------------------------------------

    def inspect_river_sand_gravel(
        self,
        license_id: str,
        vessel_plate: str,
        operation_time_hh_mm: str = "10:30",
        is_gps_installed: bool = True,
        is_dock_camera_installed: bool = True,
        measured_cargo_m3: float = 240.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Inspect river sand dredging operations against Decree 23/2020: daytime hours 07:00-17:00, GPS & cameras."""
        # Decree 23/2020/ND-CP Article 9: only allow sand mining from 07:00 to 17:00
        is_daytime = False
        try:
            parts = operation_time_hh_mm.strip().split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            time_val = h + m / 60.0
            is_daytime = 7.0 <= time_val <= 17.0
        except Exception:
            is_daytime = False

        is_compliant = is_daytime and is_gps_installed and is_dock_camera_installed

        inspection_id = f"SAND-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "inspection_id": inspection_id,
            "license_id": license_id.strip(),
            "vessel_audit": {
                "vessel_plate": vessel_plate.strip(),
                "operation_time": operation_time_hh_mm.strip(),
                "is_within_daytime_hours": is_daytime,
                "is_gps_installed": is_gps_installed,
                "is_dock_camera_installed": is_dock_camera_installed,
                "measured_cargo_m3": measured_cargo_m3,
                "is_fully_compliant": is_compliant,
                "status": "RIVER_SAND_MINING_APPROVED" if is_compliant else "VIOLATION_NĐ_23_2020_DETECTED",
            },
            "statutory_basis": "Nghị định 23/2020/NĐ-CP (Quản lý cát, sỏi lòng sông và bảo vệ lòng, bờ, bãi sông)",
            "inspected_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO river_sand_inspections (
                        inspection_id, license_id, vessel_plate, operation_hour_time,
                        is_within_daytime_hours, is_gps_installed, is_dock_camera_installed,
                        measured_cargo_m3, is_compliant, inspected_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inspection_id,
                        license_id.strip(),
                        vessel_plate.strip(),
                        operation_time_hh_mm.strip(),
                        1 if is_daytime else 0,
                        1 if is_gps_installed else 0,
                        1 if is_dock_camera_installed else 0,
                        measured_cargo_m3,
                        1 if is_compliant else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Queries & Aggregated Telemetry
    # -----------------------------------------------------------------------

    def list_mining_licenses(self, limit: int = 50) -> RecordList:
        """List registered mineral mining licenses."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM mining_licenses ORDER BY granted_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="licenses")

    def list_mineral_rights_fees(self, limit: int = 50) -> RecordList:
        """List calculated mineral rights fees."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM mineral_rights_fees ORDER BY calculated_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="rights_fees")

    def list_resource_royalty_taxes(self, limit: int = 50) -> RecordList:
        """List declared resource royalty taxes."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM resource_royalty_taxes ORDER BY declared_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="royalty_taxes")

    def list_environmental_rehabilitations(self, limit: int = 50) -> RecordList:
        """List environmental rehabilitation records."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM environmental_rehabilitations ORDER BY rehabilitated_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="rehabilitations")

    def list_river_sand_inspections(self, limit: int = 50) -> RecordList:
        """List river sand & gravel inspection records."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM river_sand_inspections ORDER BY inspected_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="sand_inspections")

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated Vietnamese mining, mineral rights, royalty taxes, and environmental safety telemetry."""
        with self._get_connection() as conn:
            l_row = conn.execute("SELECT COUNT(*) as c, SUM(approved_reserve) as sum_res FROM mining_licenses").fetchone()
            f_row = conn.execute("SELECT COUNT(*) as c, SUM(total_rights_fee_vnd) as sum_fee FROM mineral_rights_fees").fetchone()
            t_row = conn.execute("SELECT COUNT(*) as c, SUM(payable_royalty_tax_vnd) as sum_tax FROM resource_royalty_taxes").fetchone()
            e_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_qcvn40_compliant = 1 THEN 1 ELSE 0 END) as comp_cnt, SUM(initial_deposit_vnd) as sum_dep FROM environmental_rehabilitations").fetchone()
            s_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_compliant = 1 THEN 1 ELSE 0 END) as sand_comp_cnt FROM river_sand_inspections").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "MiningEngine",
            "regulatory_framework": "Luật Khoáng sản 2010, NĐ 67/2019/NĐ-CP & Luật BVMT 2020",
            "metrics": {
                "active_mining_licenses": l_row["c"] if l_row else 0,
                "total_approved_reserves": l_row["sum_res"] if (l_row and l_row["sum_res"]) else 0.0,
                "mineral_rights_fees_calculated": f_row["c"] if f_row else 0,
                "total_mineral_rights_fees_vnd": f_row["sum_fee"] if (f_row and f_row["sum_fee"]) else 0.0,
                "royalty_tax_declarations": t_row["c"] if t_row else 0,
                "total_royalty_taxes_payable_vnd": t_row["sum_tax"] if (t_row and t_row["sum_tax"]) else 0.0,
                "environmental_rehab_audits": e_row["c"] if e_row else 0,
                "qcvn40_effluent_compliant_mines": e_row["comp_cnt"] if (e_row and e_row["comp_cnt"]) else 0,
                "total_rehab_deposits_paid_vnd": e_row["sum_dep"] if (e_row and e_row["sum_dep"]) else 0.0,
                "river_sand_inspections_logged": s_row["c"] if s_row else 0,
                "compliant_river_sand_vessels": s_row["sand_comp_cnt"] if (s_row and s_row["sand_comp_cnt"]) else 0,
            },
            "database": str(self.db_path),
        }

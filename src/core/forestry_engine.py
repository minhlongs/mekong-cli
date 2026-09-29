# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Forestry, Timber Legality (VNTLAS), Wood Processing & Forest Carbon Sinks Engine.

Implements statutory forestry management, VNTLAS compliance, FSC/PEFC certification,
alternative afforestation and Payment for Forest Environmental Services (PFES) under:
- Luật Lâm nghiệp 2017 (Luật số 16/2017/QH14, có hiệu lực từ 01/01/2019) & Nghị định 156/2018/NĐ-CP, Nghị định 91/2024/NĐ-CP:
  * Phân loại 3 loại rừng: Rừng đặc dụng (Special-Use Forest), Rừng phòng hộ (Protection Forest), Rừng sản xuất (Production Forest).
  * Quy định về trồng rừng thay thế khi chuyển mục đích sử dụng rừng sang mục đích khác (Điều 21):
    - Rừng tự nhiên: Phải trồng rừng thay thế bằng tối thiểu 3 lần diện tích rừng tự nhiên chuyển đổi.
    - Rừng trồng: Phải trồng rừng thay thế bằng tối thiểu 1 lần diện tích rừng trồng chuyển đổi.
    - Trường hợp không có điều kiện tự trồng: Nộp tiền vào Quỹ Bảo vệ và Phát triển Rừng (VNFF) theo đơn giá UBND tỉnh phê duyệt.
- Hệ thống Bảo đảm Gỗ Hợp pháp Việt Nam (VNTLAS - Nghị định 102/2020/NĐ-CP & Hiệp định VPA/FLEGT Việt Nam - EU):
  * Phân loại doanh nghiệp chế biến và xuất khẩu gỗ:
    - Doanh nghiệp Nhóm I (Tier 1 - Compliant): Tuân thủ đầy đủ pháp luật, thủ tục hải quan và hồ sơ lâm sản được thông quan ưu tiên.
    - Doanh nghiệp Nhóm II (Tier 2 - Non-classified/Risk): Doanh nghiệp mới thành lập hoặc chưa đáp ứng đủ tiêu chí, phải xác minh 100% hồ sơ.
  * Giấy phép FLEGT và CITES cho lô hàng gỗ xuất khẩu sang EU, Mỹ (Lacey Act), Nhật Bản (Clean Wood Act).
  * Bảng kê lâm sản hợp pháp (Forest Product Manifest) kèm mã QR truy xuất nguồn gốc.
- Quản lý Rừng Bền vững & Chứng chỉ Quốc tế (Quyết định 1288/QĐ-TTg):
  * Chứng chỉ FSC-FM / PEFC-FM (Quản lý rừng bền vững) và FSC-CoC / PEFC-CoC (Chuỗi hành trình sản phẩm gỗ).
  * Tiêu chuẩn chứng chỉ rừng quốc gia VFCS/PEFC Việt Nam.
- Chi trả Dịch vụ Môi trường Rừng (PFES) & Thỏa thuận Giảm phát thải Carbon (ERPA World Bank - Nghị định 107/2022/NĐ-CP):
  * Mức chi trả PFES (Điều 63 Nghị định 156/2018/NĐ-CP):
    - Thủy điện: 36 VND/kWh điện thương phẩm.
    - Cơ sở cấp nước sinh hoạt: 52 VND/m3 nước thương phẩm.
    - Cơ sở công nghiệp dùng nước từ nguồn nước rừng: 50 VND/m3.
    - Du lịch sinh thái, nghỉ dưỡng: 1.0% - 2.0% doanh thu thực hiện tại khu rừng.
  * Giảm phát thải khí nhà kính (ERPA World Bank): Hấp thụ carbon rừng với đơn giá 5.0 USD/tấn CO2e theo thỏa thuận ERPA Bắc Trung Bộ.
- Dự báo Nguy cơ Cháy Rừng (Nghị định 156/2018/NĐ-CP):
  * Cấp dự báo cháy rừng từ Cấp I (Thấp) đến Cấp V (Cực kỳ nguy hiểm) theo chỉ số khí tượng (nhiệt độ, độ ẩm, số ngày khô hạn, vận tốc gió).
- Lưu trữ SQLite WAL tại ``.mekong/forestry.db``.

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
# Statutory Forestry Baselines & Classifications
# ---------------------------------------------------------------------------

FOREST_TYPES: dict[str, dict[str, typing.Any]] = {
    "SPECIAL_USE": {
        "title": "Rừng đặc dụng (Special-Use Forest)",
        "legal_basis": "Điều 5.1 Luật Lâm nghiệp 2017",
        "description": "Vườn quốc gia, khu bảo tồn thiên nhiên, khu bảo vệ cảnh quan, rừng nghiên cứu thực nghiệm khoa học",
        "conversion_multiplier": 3.0,  # Bắt buộc trồng mới gấp 3 lần diện tích
        "canopy_standard_pct": 70.0,
        "felling_prohibited": True,  # Cấm khai thác gỗ chính
    },
    "PROTECTION": {
        "title": "Rừng phòng hộ (Protection Forest)",
        "legal_basis": "Điều 5.2 Luật Lâm nghiệp 2017",
        "description": "Rừng phòng hộ đầu nguồn, chắn gió, chắn cát bay, chắn sóng ven biển và bảo vệ biên giới",
        "conversion_multiplier": 3.0,
        "canopy_standard_pct": 60.0,
        "felling_prohibited": True,
    },
    "PRODUCTION_NATURAL": {
        "title": "Rừng sản xuất tự nhiên (Natural Production Forest)",
        "legal_basis": "Điều 5.3 Luật Lâm nghiệp 2017",
        "description": "Rừng tự nhiên được giao hoặc cho thuê để phục hồi, quản lý bền vững và khai thác lâm sản phụ",
        "conversion_multiplier": 3.0,
        "canopy_standard_pct": 50.0,
        "felling_prohibited": False,
    },
    "PRODUCTION_PLANTATION": {
        "title": "Rừng sản xuất trồng (Plantation Production Forest)",
        "legal_basis": "Điều 5.3 Luật Lâm nghiệp 2017",
        "description": "Rừng trồng kinh tế gỗ lớn, gỗ nhỏ (Keo, Bạch đàn, Quế, Cao su) phục vụ chế biến đồ gỗ xuất khẩu",
        "conversion_multiplier": 1.0,  # Trồng mới tối thiểu bằng 1 lần diện tích chuyển đổi
        "canopy_standard_pct": 40.0,
        "felling_prohibited": False,
    },
}

PFES_RATES: dict[str, dict[str, typing.Any]] = {
    "HYDROPOWER": {
        "title": "Nhà máy Thủy điện (Hydroelectric Power Plant)",
        "unit": "VND/kWh",
        "rate_vnd": 36.0,
        "basis": "Khoản 1 Điều 63 Nghị định 156/2018/NĐ-CP",
    },
    "CLEAN_WATER": {
        "title": "Cơ sở sản xuất nước sạch sinh hoạt (Clean Water Supply)",
        "unit": "VND/m3",
        "rate_vnd": 52.0,
        "basis": "Khoản 2 Điều 63 Nghị định 156/2018/NĐ-CP",
    },
    "INDUSTRIAL_WATER": {
        "title": "Cơ sở sản xuất công nghiệp sử dụng nước từ rừng (Industrial Water)",
        "unit": "VND/m3",
        "rate_vnd": 50.0,
        "basis": "Khoản 3 Điều 63 Nghị định 156/2018/NĐ-CP",
    },
    "ECO_TOURISM": {
        "title": "Du lịch sinh thái, nghỉ dưỡng, giải trí (Eco-Tourism)",
        "unit": "% doanh thu",
        "rate_vnd": 1.5,  # 1.5% doanh thu bình quân
        "basis": "Khoản 4 Điều 63 Nghị định 156/2018/NĐ-CP",
    },
}

VNTLAS_ENTERPRISE_TIERS: dict[str, dict[str, typing.Any]] = {
    "TIER_1": {
        "title": "Doanh nghiệp Nhóm I (VNTLAS Tier 1 - Fully Compliant)",
        "description": "Tuân thủ nghiêm ngặt pháp luật lâm nghiệp, thuế, hải quan, lao động; được miễn kiểm tra thực tế hồ sơ",
        "green_channel": True,
        "risk_level": "LOW",
        "audit_frequency_years": 2,
    },
    "TIER_2": {
        "title": "Doanh nghiệp Nhóm II (VNTLAS Tier 2 - Non-classified or High Risk)",
        "description": "Doanh nghiệp mới thành lập hoặc từng có vi phạm; xác minh 100% nguồn gốc gỗ và kiểm tra thực tế",
        "green_channel": False,
        "risk_level": "HIGH",
        "audit_frequency_years": 1,
    },
}

FIRE_DANGER_LEVELS: dict[int, dict[str, str]] = {
    1: {"name": "CẤP I - THẤP", "color": "blue", "action": "Thời tiết bình thường, chuẩn bị lực lượng và phương tiện sẵn sàng."},
    2: {"name": "CẤP II - TRUNG BÌNH", "color": "green", "action": "Khô hạn nhẹ, tuần tra các vùng rừng trọng điểm có nguy cơ cháy."},
    3: {"name": "CẤP III - CAO", "color": "yellow", "action": "Thời tiết khô hanh, kiểm soát việc sử dụng lửa ven rừng và nương rẫy."},
    4: {"name": "CẤP IV - NGUY HIỂM", "color": "orange", "action": "Nguy cơ cháy rất lớn, cấm đốt dọn nương rẫy, trực canh lửa 12/24h."},
    5: {"name": "CẤP V - CỰC KỲ NGUY HIỂM", "color": "red", "action": "Khô hạn cực độ, cấm mọi hoạt động dùng lửa trong và ven rừng, trực chiến 24/24h."},
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


class ForestryEngine:
    """Core engine for Vietnamese Forestry Management, VNTLAS Timber Legality, FSC & Forest Carbon Sinks."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "forestry.db"
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
                CREATE TABLE IF NOT EXISTS forest_plots (
                    plot_id TEXT PRIMARY KEY,
                    plot_code TEXT NOT NULL,
                    plot_name TEXT NOT NULL,
                    forest_type TEXT NOT NULL,
                    province TEXT NOT NULL,
                    area_hectares REAL NOT NULL,
                    canopy_cover_pct REAL NOT NULL,
                    trees_per_hectare REAL NOT NULL,
                    main_species TEXT NOT NULL,
                    is_fsc_certified INTEGER NOT NULL,
                    fsc_code TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS timber_consignments (
                    consignment_id TEXT PRIMARY KEY,
                    consignment_code TEXT NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    enterprise_tier TEXT NOT NULL,
                    product_type TEXT NOT NULL,
                    volume_m3 REAL NOT NULL,
                    species TEXT NOT NULL,
                    origin_province TEXT NOT NULL,
                    flegt_cites_license TEXT,
                    is_vntlas_verified INTEGER NOT NULL,
                    export_market TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS alternative_afforestations (
                    afforestation_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    converted_forest_type TEXT NOT NULL,
                    converted_area_ha REAL NOT NULL,
                    required_new_area_ha REAL NOT NULL,
                    payment_rate_vnd_per_ha REAL NOT NULL,
                    total_vnff_payment_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    approved_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pfes_calculations (
                    pfes_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    facility_type TEXT NOT NULL,
                    production_volume REAL NOT NULL,
                    unit_rate_vnd REAL NOT NULL,
                    total_pfes_vnd REAL NOT NULL,
                    carbon_absorbed_tco2e REAL NOT NULL,
                    erpa_value_usd REAL NOT NULL,
                    calculated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fire_danger_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    plot_id TEXT NOT NULL,
                    temperature_c REAL NOT NULL,
                    humidity_pct REAL NOT NULL,
                    wind_speed_kmh REAL NOT NULL,
                    consecutive_dry_days INTEGER NOT NULL,
                    fire_danger_level INTEGER NOT NULL,
                    danger_label TEXT NOT NULL,
                    warning_measures TEXT NOT NULL,
                    assessed_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Forest Plot Registration & Sustainable Forest Management (SFM)
    # -----------------------------------------------------------------------

    def register_forest_plot(
        self,
        plot_name: str,
        forest_type: str = "PRODUCTION_PLANTATION",
        province: str = "Quảng Nam",
        area_hectares: float = 150.0,
        canopy_cover_pct: float = 65.0,
        trees_per_hectare: float = 1600.0,
        main_species: str = "Acacia auriculiformis (Keo lá tràm)",
        is_fsc_certified: bool = True,
        fsc_code: str | None = "FSC-C123456",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Register a forest plot with canopy coverage, species, and FSC/PEFC certification."""
        clean_type = forest_type.upper().strip()
        type_info = FOREST_TYPES.get(clean_type, FOREST_TYPES["PRODUCTION_PLANTATION"])

        plot_id = f"PLT-{uuid.uuid4().hex[:8].upper()}"
        plot_code = f"VN-FOR-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        canopy_pass = canopy_cover_pct >= type_info["canopy_standard_pct"]
        fsc_str = fsc_code.strip() if (is_fsc_certified and fsc_code) else "NONE"

        result = {
            "ok": True,
            "plot_id": plot_id,
            "plot_code": plot_code,
            "profile": {
                "plot_name": plot_name.strip(),
                "forest_type": clean_type,
                "type_title": type_info["title"],
                "province": province.strip(),
                "area_hectares": area_hectares,
                "canopy_cover_pct": canopy_cover_pct,
                "canopy_standard_met": canopy_pass,
                "trees_per_hectare": trees_per_hectare,
                "total_estimated_trees": round(area_hectares * trees_per_hectare),
                "main_species": main_species.strip(),
                "is_fsc_certified": is_fsc_certified,
                "fsc_code": fsc_str,
                "felling_prohibited": type_info["felling_prohibited"],
            },
            "statutory_mandate": {
                "legal_basis": type_info["legal_basis"],
                "sfm_policy": "Quyết định 1288/QĐ-TTg về phê duyệt Đề án Quản lý rừng bền vững và Chứng chỉ rừng",
            },
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO forest_plots (
                        plot_id, plot_code, plot_name, forest_type, province,
                        area_hectares, canopy_cover_pct, trees_per_hectare,
                        main_species, is_fsc_certified, fsc_code, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        plot_id,
                        plot_code,
                        plot_name.strip(),
                        clean_type,
                        province.strip(),
                        area_hectares,
                        canopy_cover_pct,
                        trees_per_hectare,
                        main_species.strip(),
                        1 if is_fsc_certified else 0,
                        result["profile"]["fsc_code"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # VNTLAS Timber Legality & FLEGT/CITES Verification (Nghị định 102/2020)
    # -----------------------------------------------------------------------

    def verify_timber_vntlas(
        self,
        enterprise_name: str,
        product_type: str = "FURNITURE",
        volume_m3: float = 120.0,
        species: str = "Tectona grandis (Gỗ Teak) / Keo tràm",
        origin_province: str = "Bình Dương",
        enterprise_tier: str = "TIER_1",
        flegt_cites_license: str | None = "FLEGT-VN-2026-00892",
        export_market: str = "EU",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Verify timber consignment legality under VNTLAS (Decree 102/2020) and issue export manifest."""
        clean_tier = enterprise_tier.upper().strip()
        tier_info = VNTLAS_ENTERPRISE_TIERS.get(clean_tier, VNTLAS_ENTERPRISE_TIERS["TIER_1"])

        consignment_id = f"CSG-{uuid.uuid4().hex[:8].upper()}"
        consignment_code = f"VNTLAS-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        # Tier 1 with valid license qualifies immediately; Tier 2 requires physical audit
        is_verified = (clean_tier == "TIER_1") and (bool(flegt_cites_license))

        result = {
            "ok": True,
            "consignment_id": consignment_id,
            "consignment_code": consignment_code,
            "verification_report": {
                "enterprise_name": enterprise_name.strip(),
                "enterprise_tier": clean_tier,
                "tier_title": tier_info["title"],
                "product_type": product_type.strip(),
                "volume_m3": volume_m3,
                "species": species.strip(),
                "origin_province": origin_province.strip(),
                "export_market": export_market.strip(),
                "flegt_cites_license": flegt_cites_license.strip() if flegt_cites_license else "NOT_ISSUED",
                "is_vntlas_verified": is_verified,
                "customs_channel": "GREEN_FAST_TRACK" if is_verified else "RED_FULL_VERIFICATION_REQUIRED",
                "risk_assessment": tier_info["risk_level"],
            },
            "statutory_compliance": {
                "legal_basis": "Nghị định 102/2020/NĐ-CP & Hiệp định VPA/FLEGT Việt Nam - EU",
                "eu_compliance": "Regulation (EU) 2023/1115 (EUDR) & EU Timber Regulation (EUTR)",
            },
            "verified_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO timber_consignments (
                        consignment_id, consignment_code, enterprise_name, enterprise_tier,
                        product_type, volume_m3, species, origin_province,
                        flegt_cites_license, is_vntlas_verified, export_market, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        consignment_id,
                        consignment_code,
                        enterprise_name.strip(),
                        clean_tier,
                        product_type.strip(),
                        volume_m3,
                        species.strip(),
                        origin_province.strip(),
                        result["verification_report"]["flegt_cites_license"],
                        1 if is_verified else 0,
                        export_market.strip(),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Alternative Afforestation Calculation (Điều 21 Luật Lâm nghiệp 2017)
    # -----------------------------------------------------------------------

    def calculate_alternative_afforestation(
        self,
        project_name: str,
        converted_forest_type: str = "PRODUCTION_NATURAL",
        converted_area_ha: float = 25.0,
        payment_rate_vnd_per_ha: float = 95000000.0,  # ~95 triệu VND/ha trồng rừng mới
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Calculate mandatory alternative afforestation area or Vietnam Forest Protection Fund (VNFF) deposit."""
        clean_type = converted_forest_type.upper().strip()
        type_info = FOREST_TYPES.get(clean_type, FOREST_TYPES["PRODUCTION_NATURAL"])

        multiplier = type_info["conversion_multiplier"]
        required_new_area = converted_area_ha * multiplier
        total_payment = required_new_area * payment_rate_vnd_per_ha

        afforestation_id = f"AFF-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "afforestation_id": afforestation_id,
            "project_profile": {
                "project_name": project_name.strip(),
                "converted_forest_type": clean_type,
                "type_title": type_info["title"],
                "converted_area_ha": converted_area_ha,
                "statutory_multiplier": multiplier,
                "required_new_afforestation_ha": required_new_area,
                "unit_cost_vnd_per_ha": payment_rate_vnd_per_ha,
                "total_vnff_payment_vnd": total_payment,
                "status": "APPROVED_FOR_VNFF_ESCROW",
            },
            "statutory_mandate": "Điều 21 Luật Lâm nghiệp 2017 & Nghị định 156/2018/NĐ-CP (Trồng rừng thay thế)",
            "calculated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO alternative_afforestations (
                        afforestation_id, project_name, converted_forest_type,
                        converted_area_ha, required_new_area_ha, payment_rate_vnd_per_ha,
                        total_vnff_payment_vnd, status, approved_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        afforestation_id,
                        project_name.strip(),
                        clean_type,
                        converted_area_ha,
                        required_new_area,
                        payment_rate_vnd_per_ha,
                        total_payment,
                        result["project_profile"]["status"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Payment for Forest Environmental Services (PFES) & ERPA Carbon Credit
    # -----------------------------------------------------------------------

    def calculate_pfes_and_carbon(
        self,
        facility_name: str,
        facility_type: str = "HYDROPOWER",
        production_volume: float = 250000000.0,  # 250 triệu kWh hoặc m3 nước
        forest_area_ha: float = 12000.0,
        carbon_sequestration_rate: float = 4.2,  # ~4.2 tấn CO2e/ha/năm
        erpa_price_usd_per_ton: float = 5.0,  # 5 USD/tấn theo ERPA WB
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute PFES obligation (Decree 156/2018) and World Bank ERPA forest carbon sequestration revenue."""
        clean_fac = facility_type.upper().strip()
        fac_info = PFES_RATES.get(clean_fac, PFES_RATES["HYDROPOWER"])

        # For eco-tourism, volume represents revenue in VND
        if clean_fac == "ECO_TOURISM":
            total_pfes_vnd = production_volume * (fac_info["rate_vnd"] / 100.0)
        else:
            total_pfes_vnd = production_volume * fac_info["rate_vnd"]

        # Carbon calculation (World Bank ERPA Northern Central Vietnam model)
        total_carbon_tco2e = forest_area_ha * carbon_sequestration_rate
        total_erpa_usd = total_carbon_tco2e * erpa_price_usd_per_ton

        pfes_id = f"PFE-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "pfes_id": pfes_id,
            "calculation_result": {
                "facility_name": facility_name.strip(),
                "facility_type": clean_fac,
                "facility_title": fac_info["title"],
                "production_volume": production_volume,
                "unit": fac_info["unit"],
                "statutory_rate": fac_info["rate_vnd"],
                "total_pfes_amount_vnd": total_pfes_vnd,
                "forest_basin_area_ha": forest_area_ha,
                "annual_carbon_sequestration_tco2e": total_carbon_tco2e,
                "erpa_transfer_price_usd": erpa_price_usd_per_ton,
                "total_erpa_carbon_revenue_usd": total_erpa_usd,
            },
            "statutory_mandates": {
                "pfes_mandate": fac_info["basis"],
                "erpa_mandate": "Nghị định 107/2022/NĐ-CP về thí điểm chuyển nhượng kết quả giảm phát thải (ERPA)",
            },
            "calculated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO pfes_calculations (
                        pfes_id, facility_name, facility_type, production_volume,
                        unit_rate_vnd, total_pfes_vnd, carbon_absorbed_tco2e,
                        erpa_value_usd, calculated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pfes_id,
                        facility_name.strip(),
                        clean_fac,
                        production_volume,
                        fac_info["rate_vnd"],
                        total_pfes_vnd,
                        total_carbon_tco2e,
                        total_erpa_usd,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Forest Fire Danger Level Assessment (Nghị định 156/2018/NĐ-CP)
    # -----------------------------------------------------------------------

    def assess_forest_fire_danger(
        self,
        plot_id: str,
        temperature_c: float = 37.5,
        humidity_pct: float = 38.0,
        wind_speed_kmh: float = 24.0,
        consecutive_dry_days: int = 14,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Assess forest fire danger level (Tier I to V) based on Nesterov-like weather index."""
        # Simple Nesterov dryness index approximation: I = T * (100 - H) / 100 * days
        dry_index = (temperature_c * (100.0 - humidity_pct) / 100.0) * max(1, consecutive_dry_days)
        if wind_speed_kmh > 20:
            dry_index *= 1.3

        if dry_index < 50:
            level = 1
        elif dry_index < 150:
            level = 2
        elif dry_index < 350:
            level = 3
        elif dry_index < 650:
            level = 4
        else:
            level = 5

        danger_info = FIRE_DANGER_LEVELS[level]
        assessment_id = f"FIR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "assessment_id": assessment_id,
            "plot_id": plot_id.strip(),
            "meteorological_telemetry": {
                "temperature_celsius": temperature_c,
                "relative_humidity_pct": humidity_pct,
                "wind_speed_kmh": wind_speed_kmh,
                "consecutive_dry_days": consecutive_dry_days,
                "calculated_dryness_index": round(dry_index, 2),
            },
            "fire_danger_verdict": {
                "danger_level": level,
                "danger_name": danger_info["name"],
                "badge_color": danger_info["color"],
                "statutory_actions": danger_info["action"],
            },
            "statutory_mandate": "Nghị định 156/2018/NĐ-CP (Quy định chi tiết thi hành Luật Lâm nghiệp về PCCC rừng)",
            "assessed_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO fire_danger_assessments (
                        assessment_id, plot_id, temperature_c, humidity_pct,
                        wind_speed_kmh, consecutive_dry_days, fire_danger_level,
                        danger_label, warning_measures, assessed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        plot_id.strip(),
                        temperature_c,
                        humidity_pct,
                        wind_speed_kmh,
                        consecutive_dry_days,
                        level,
                        danger_info["name"],
                        danger_info["action"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Queries & Aggregated Telemetry
    # -----------------------------------------------------------------------

    def list_forest_plots(self, limit: int = 50) -> RecordList:
        """List registered forest plots."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM forest_plots ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="plots")

    def list_timber_consignments(self, limit: int = 50) -> RecordList:
        """List timber consignments."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM timber_consignments ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="consignments")

    def list_afforestation_projects(self, limit: int = 50) -> RecordList:
        """List alternative afforestation projects."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM alternative_afforestations ORDER BY approved_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="afforestations")

    def list_pfes_records(self, limit: int = 50) -> RecordList:
        """List PFES calculation records."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM pfes_calculations ORDER BY calculated_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="pfes")

    def list_fire_danger_assessments(self, limit: int = 50) -> RecordList:
        """List fire danger assessments."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM fire_danger_assessments ORDER BY assessed_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="fire_assessments")

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated Vietnamese forestry, VNTLAS timber, PFES, and carbon telemetry."""
        with self._get_connection() as conn:
            p_row = conn.execute("SELECT COUNT(*) as c, SUM(area_hectares) as sum_a, SUM(CASE WHEN is_fsc_certified = 1 THEN area_hectares ELSE 0 END) as fsc_a FROM forest_plots").fetchone()
            t_row = conn.execute("SELECT COUNT(*) as c, SUM(volume_m3) as sum_v, SUM(CASE WHEN is_vntlas_verified = 1 THEN volume_m3 ELSE 0 END) as vnt_v FROM timber_consignments").fetchone()
            a_row = conn.execute("SELECT COUNT(*) as c, SUM(required_new_area_ha) as sum_new_a, SUM(total_vnff_payment_vnd) as sum_pay FROM alternative_afforestations").fetchone()
            pf_row = conn.execute("SELECT COUNT(*) as c, SUM(total_pfes_vnd) as sum_pfe, SUM(carbon_absorbed_tco2e) as sum_carb, SUM(erpa_value_usd) as sum_erpa FROM pfes_calculations").fetchone()
            f_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN fire_danger_level >= 4 THEN 1 ELSE 0 END) as high_f FROM fire_danger_assessments").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "ForestryEngine",
            "regulatory_framework": "Luật Lâm nghiệp 2017 (Luật số 16/2017/QH14) & Nghị định 102/2020/NĐ-CP VNTLAS",
            "metrics": {
                "registered_forest_plots": p_row["c"] if p_row else 0,
                "total_forest_area_ha": p_row["sum_a"] if (p_row and p_row["sum_a"]) else 0.0,
                "fsc_certified_area_ha": p_row["fsc_a"] if (p_row and p_row["fsc_a"]) else 0.0,
                "timber_consignments_processed": t_row["c"] if t_row else 0,
                "total_timber_volume_m3": t_row["sum_v"] if (t_row and t_row["sum_v"]) else 0.0,
                "vntlas_verified_volume_m3": t_row["vnt_v"] if (t_row and t_row["vnt_v"]) else 0.0,
                "alternative_afforestation_projects": a_row["c"] if a_row else 0,
                "mandated_new_afforestation_ha": a_row["sum_new_a"] if (a_row and a_row["sum_new_a"]) else 0.0,
                "total_vnff_escrow_deposit_vnd": a_row["sum_pay"] if (a_row and a_row["sum_pay"]) else 0.0,
                "pfes_evaluations_conducted": pf_row["c"] if pf_row else 0,
                "total_pfes_collected_vnd": pf_row["sum_pfe"] if (pf_row and pf_row["sum_pfe"]) else 0.0,
                "total_carbon_sequestration_tco2e": pf_row["sum_carb"] if (pf_row and pf_row["sum_carb"]) else 0.0,
                "total_erpa_carbon_revenue_usd": pf_row["sum_erpa"] if (pf_row and pf_row["sum_erpa"]) else 0.0,
                "fire_danger_assessments_recorded": f_row["c"] if f_row else 0,
                "high_danger_warnings_active": f_row["high_f"] if (f_row and f_row["high_f"]) else 0,
            },
            "database": str(self.db_path),
        }

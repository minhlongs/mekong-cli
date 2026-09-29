# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Environmental, Social & Governance (ESG), Green Transition & Carbon Trading Compliance Engine.

Implements Vietnamese statutory environmental, GHG inventory & ESG disclosures:
- Luật Bảo vệ Môi trường 2020 (Luật số 72/2020/QH14) có hiệu lực từ 01/01/2022:
  * Điều 91: Giảm nhẹ phát thải khí nhà kính (GHG mitigation) và bảo vệ tầng ô-dôn.
  * Điều 93 & 94: Phát triển thị trường carbon trong nước (Domestic Carbon Credit Market) & trao đổi quốc tế.
  * Điều 39: Giấy phép môi trường (GPMT - Environmental Permit) đối với dự án đầu tư nhóm I, II, III.
- Nghị định 06/2022/NĐ-CP & Quyết định 01/2022/QĐ-TTg, Quyết định 13/2024/QĐ-TTg:
  * Quy định giảm nhẹ phát thải khí nhà kính và bảo vệ tầng ô-dôn.
  * Danh mục cơ sở phát thải bắt buộc kiểm kê khí nhà kính định kỳ (ngưỡng ≥ 3,000 tCO2e/năm hoặc ≥ 1,000 TOE/năm).
  * Hệ số phát thải lưới điện quốc gia Việt Nam (Grid Emission Factor - GEF): 0.7221 tCO2/MWh.
  * Định mức quy đổi: 1 tín chỉ carbon = 1 tấn CO2 tương đương (1 credit = 1 tCO2e).
  * Quy chuẩn MRV (Đo đạc, Báo cáo, Thẩm định) theo chuẩn GHG Protocol / ISO 14064-1:
    - Scope 1: Phát thải trực tiếp (nhiên liệu hóa thạch, xăng, diesel, LPG, than).
    - Scope 2: Phát thải gián tiếp từ điện năng tiêu thụ lưới điện quốc gia.
    - Scope 3: Phát thải gián tiếp trong chuỗi giá trị và vận chuyển logistics.
- Cơ chế Điều chỉnh Biên giới Carbon EU (CBAM - Regulation EU 2023/956):
  * Khai báo lượng phát thải carbon nhúng (Embedded Emissions) cho sắt thép, nhôm, xi măng, phân bón.
- Tiêu chuẩn công bố thông tin ESG (Thông tư 96/2020/TT-BTC & GRI Standards):
  * Báo cáo Phát triển bền vững doanh nghiệp niêm yết (Trụ cột E, S, G và xếp hạng tín nhiệm xanh).
- Lưu trữ SQLite WAL tại ``.mekong/esg.db``.

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
# Emission Factor & Conversion Constants (IPCC & MONRE Vietnam)
# ---------------------------------------------------------------------------

GRID_EMISSION_FACTOR_VIETNAM: float = 0.7221  # tCO2e / MWh (hoặc kg CO2e / kWh)

# Hệ số phát thải trực tiếp (IPCC Guidelines for National GHG Inventories)
EMISSION_FACTORS: dict[str, float] = {
    "DIESEL_KG_PER_LITER": 2.68,        # kg CO2e / lít dầu diesel
    "GASOLINE_KG_PER_LITER": 2.31,      # kg CO2e / lít xăng Ron 95
    "COAL_TONS_PER_TON": 2.45,          # tấn CO2e / tấn than antraxit
    "LPG_KG_PER_KG": 2.98,              # kg CO2e / kg khí dầu mỏ hóa lỏng LPG
    "CNG_KG_PER_M3": 2.02,              # kg CO2e / m3 khí thiên nhiên nén
}

MANDATORY_REPORTING_THRESHOLD_TCO2E: float = 3_000.0  # Quyết định 13/2024/QĐ-TTg

USD_VND_EXCHANGE_RATE: float = 25_450.0
EUR_VND_EXCHANGE_RATE: float = 27_800.0


class EsgEngine:
    """Autonomous Environmental, Social & Governance (ESG), Green Transition & Carbon Trading Compliance Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "esg.db"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS ghg_inventories (
                    inventory_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    reporting_year INTEGER NOT NULL,
                    scope1_tco2e REAL NOT NULL,
                    scope2_tco2e REAL NOT NULL,
                    scope3_tco2e REAL NOT NULL,
                    total_tco2e REAL NOT NULL,
                    is_mandatory_reporting INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS carbon_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    credit_type TEXT NOT NULL,
                    quantity_tco2e REAL NOT NULL,
                    unit_price_usd REAL NOT NULL,
                    total_amount_usd REAL NOT NULL,
                    action TEXT NOT NULL,
                    counterparty TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS esg_ratings (
                    rating_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    e_score REAL NOT NULL,
                    s_score REAL NOT NULL,
                    g_score REAL NOT NULL,
                    composite_score REAL NOT NULL,
                    rating_grade TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_ghg_enterprise ON ghg_inventories(enterprise_name);
                CREATE INDEX IF NOT EXISTS idx_carbon_action ON carbon_transactions(action);
                CREATE INDEX IF NOT EXISTS idx_esg_grade ON esg_ratings(rating_grade);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # GHG Emissions Inventory & Carbon Footprint (Nghị định 06/2022/NĐ-CP)
    # -----------------------------------------------------------------------

    def calculate_ghg_inventory(
        self,
        enterprise_name: str,
        reporting_year: int,
        fuel_diesel_liters: float = 0.0,
        fuel_gasoline_liters: float = 0.0,
        coal_tons: float = 0.0,
        lpg_kg: float = 0.0,
        electricity_kwh: float = 0.0,
        scope3_logistics_tco2e: float = 0.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Compute enterprise GHG inventory conforming to ISO 14064-1 & Decision 13/2024/QD-TTg."""
        # Scope 1: Direct emissions from fuel combustion
        diesel_emissions_t = (fuel_diesel_liters * EMISSION_FACTORS["DIESEL_KG_PER_LITER"]) / 1000.0
        gasoline_emissions_t = (fuel_gasoline_liters * EMISSION_FACTORS["GASOLINE_KG_PER_LITER"]) / 1000.0
        coal_emissions_t = coal_tons * EMISSION_FACTORS["COAL_TONS_PER_TON"]
        lpg_emissions_t = (lpg_kg * EMISSION_FACTORS["LPG_KG_PER_KG"]) / 1000.0

        scope1_tco2e = round(diesel_emissions_t + gasoline_emissions_t + coal_emissions_t + lpg_emissions_t, 3)

        # Scope 2: Indirect emissions from grid electricity
        scope2_tco2e = round((electricity_kwh * GRID_EMISSION_FACTOR_VIETNAM) / 1000.0, 3)

        # Scope 3: Value chain, logistics & travel
        scope3_tco2e = round(scope3_logistics_tco2e, 3)

        total_tco2e = round(scope1_tco2e + scope2_tco2e + scope3_tco2e, 3)
        is_mandatory = total_tco2e >= MANDATORY_REPORTING_THRESHOLD_TCO2E

        inventory_id = f"GHG-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "inventory_id": inventory_id,
            "enterprise_name": enterprise_name,
            "reporting_year": reporting_year,
            "breakdown": {
                "scope_1_direct_tco2e": scope1_tco2e,
                "scope_1_details": {
                    "diesel_tco2e": round(diesel_emissions_t, 3),
                    "gasoline_tco2e": round(gasoline_emissions_t, 3),
                    "coal_tco2e": round(coal_emissions_t, 3),
                    "lpg_tco2e": round(lpg_emissions_t, 3),
                },
                "scope_2_indirect_electricity_tco2e": scope2_tco2e,
                "scope_2_details": {
                    "electricity_kwh": electricity_kwh,
                    "grid_emission_factor_tco2_per_mwh": GRID_EMISSION_FACTOR_VIETNAM,
                },
                "scope_3_value_chain_tco2e": scope3_tco2e,
            },
            "total_ghg_emissions_tco2e": total_tco2e,
            "mandatory_reporting_status": {
                "threshold_tco2e": MANDATORY_REPORTING_THRESHOLD_TCO2E,
                "is_mandatory_reporting_facility": is_mandatory,
                "statutory_basis": "Quyết định 13/2024/QĐ-TTg & Nghị định 06/2022/NĐ-CP.",
                "conclusion": (
                    "BẮT BUỘC KIỂM KÊ KHÍ NHÀ KÍNH VÀ NỘP BÁO CÁO MRV CHO BỘ TN&MT"
                    if is_mandatory
                    else "DƯỚI NGƯỠNG BẮT BUỘC KIỂM KÊ — KHUYẾN KHÍCH CÔNG BỐ TỰ NGUYỆN"
                ),
            },
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO ghg_inventories (
                        inventory_id, enterprise_name, reporting_year,
                        scope1_tco2e, scope2_tco2e, scope3_tco2e, total_tco2e,
                        is_mandatory_reporting, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inventory_id,
                        enterprise_name,
                        reporting_year,
                        scope1_tco2e,
                        scope2_tco2e,
                        scope3_tco2e,
                        total_tco2e,
                        1 if is_mandatory else 0,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # EU CBAM Cross-Border Carbon Adjustment (Regulation EU 2023/956)
    # -----------------------------------------------------------------------

    def evaluate_cbam_liability(
        self,
        product_type: str,
        export_volume_tons: float,
        direct_emissions_tco2: float,
        indirect_emissions_tco2: float = 0.0,
        cbam_carbon_price_eur_per_ton: float = 75.0,
        exchange_rate_eur_vnd: float = EUR_VND_EXCHANGE_RATE,
    ) -> dict[str, typing.Any]:
        """Evaluate EU CBAM embedded emissions and financial certificate liability for Vietnam exports."""
        clean_prod = product_type.upper().strip()
        supported_cbam_goods = {"STEEL", "ALUMINUM", "CEMENT", "FERTILIZER", "HYDROGEN"}
        if clean_prod not in supported_cbam_goods:
            clean_prod = "STEEL"

        total_embedded_emissions = direct_emissions_tco2 + indirect_emissions_tco2
        specific_emissions_per_ton = (
            round(total_embedded_emissions / export_volume_tons, 4) if export_volume_tons > 0 else 0.0
        )

        estimated_cbam_liability_eur = round(total_embedded_emissions * cbam_carbon_price_eur_per_ton, 2)
        estimated_cbam_liability_vnd = round(estimated_cbam_liability_eur * exchange_rate_eur_vnd)

        return {
            "ok": True,
            "product_type": clean_prod,
            "export_volume_tons": export_volume_tons,
            "direct_emissions_tco2": direct_emissions_tco2,
            "indirect_emissions_tco2": indirect_emissions_tco2,
            "total_embedded_emissions_tco2e": round(total_embedded_emissions, 3),
            "specific_embedded_emissions_tco2_per_ton": specific_emissions_per_ton,
            "cbam_carbon_price_eur": cbam_carbon_price_eur_per_ton,
            "estimated_cbam_liability_eur": estimated_cbam_liability_eur,
            "estimated_cbam_liability_vnd": estimated_cbam_liability_vnd,
            "regulatory_framework": "Cơ chế Điều chỉnh Biên giới Carbon của EU (CBAM - Regulation EU 2023/956)",
            "compliance_advice": (
                f"Sản phẩm {clean_prod} xuất khẩu sang EU có suất phát thải {specific_emissions_per_ton} tCO2e/tấn. "
                "Cần chuẩn bị Báo cáo phát thải thực tế (Actual Emissions Data) có kiểm định viên độc lập xác nhận "
                "để tránh bị áp định mức mặc định (default values) bất lợi của Ủy ban Châu Âu."
            ),
        }

    # -----------------------------------------------------------------------
    # Comprehensive ESG Scoring & Disclosures (Thông tư 96/2020/TT-BTC)
    # -----------------------------------------------------------------------

    def audit_esg_score(
        self,
        enterprise_name: str,
        # Environmental (0-100)
        has_iso_14001: bool = True,
        renewable_energy_ratio_pct: float = 20.0,
        has_waste_treatment_license: bool = True,
        # Social (0-100)
        full_social_insurance_compliance: bool = True,
        workplace_accident_rate: float = 0.0,
        female_leadership_ratio_pct: float = 30.0,
        # Governance (0-100)
        independent_board_members_ratio_pct: float = 33.3,
        has_anti_corruption_policy: bool = True,
        has_audited_financial_report: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit and synthesize corporate ESG composite score and rating under Circular 96/2020/TT-BTC."""
        # 1. Environmental Pillar Score (Weight: 40%)
        e_score = 0.0
        if has_iso_14001:
            e_score += 35.0
        e_score += min(35.0, (renewable_energy_ratio_pct / 50.0) * 35.0)
        if has_waste_treatment_license:
            e_score += 30.0
        e_score = round(min(100.0, e_score), 1)

        # 2. Social Pillar Score (Weight: 30%)
        s_score = 0.0
        if full_social_insurance_compliance:
            s_score += 40.0
        if workplace_accident_rate == 0.0:
            s_score += 30.0
        s_score += min(30.0, (female_leadership_ratio_pct / 40.0) * 30.0)
        s_score = round(min(100.0, s_score), 1)

        # 3. Governance Pillar Score (Weight: 30%)
        g_score = 0.0
        g_score += min(40.0, (independent_board_members_ratio_pct / 33.3) * 40.0)
        if has_anti_corruption_policy:
            g_score += 30.0
        if has_audited_financial_report:
            g_score += 30.0
        g_score = round(min(100.0, g_score), 1)

        # Composite Weighted Score
        composite_score = round(e_score * 0.4 + s_score * 0.3 + g_score * 0.3, 1)

        if composite_score >= 90.0:
            rating_grade = "AAA"
        elif composite_score >= 80.0:
            rating_grade = "AA"
        elif composite_score >= 70.0:
            rating_grade = "A"
        elif composite_score >= 60.0:
            rating_grade = "BBB"
        elif composite_score >= 50.0:
            rating_grade = "BB"
        elif composite_score >= 40.0:
            rating_grade = "B"
        else:
            rating_grade = "CCC"

        rating_id = f"ESG-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "rating_id": rating_id,
            "enterprise_name": enterprise_name,
            "pillars": {
                "environmental": {
                    "score": e_score,
                    "weight_pct": 40.0,
                    "weighted_points": round(e_score * 0.4, 2),
                    "iso_14001": has_iso_14001,
                    "renewable_energy_ratio_pct": renewable_energy_ratio_pct,
                    "waste_treatment_license": has_waste_treatment_license,
                },
                "social": {
                    "score": s_score,
                    "weight_pct": 30.0,
                    "weighted_points": round(s_score * 0.3, 2),
                    "bhxh_compliance": full_social_insurance_compliance,
                    "workplace_accidents": workplace_accident_rate,
                    "female_leadership_pct": female_leadership_ratio_pct,
                },
                "governance": {
                    "score": g_score,
                    "weight_pct": 30.0,
                    "weighted_points": round(g_score * 0.3, 2),
                    "independent_directors_pct": independent_board_members_ratio_pct,
                    "anti_corruption_policy": has_anti_corruption_policy,
                    "audited_financials": has_audited_financial_report,
                },
            },
            "composite_score": composite_score,
            "rating_grade": rating_grade,
            "standard_benchmark": "Thông tư 96/2020/TT-BTC & Chuẩn mực Báo cáo Phát triển Bền vững GRI",
            "evaluated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO esg_ratings (
                        rating_id, enterprise_name, e_score, s_score, g_score,
                        composite_score, rating_grade, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rating_id,
                        enterprise_name,
                        e_score,
                        s_score,
                        g_score,
                        composite_score,
                        rating_grade,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Carbon Credit Trading & Offset Registry (Điều 93 & 94 Luật BVMT 2020)
    # -----------------------------------------------------------------------

    def trade_carbon_credits(
        self,
        project_name: str,
        credit_type: str,
        quantity_tco2e: float,
        unit_price_usd: float,
        action: str = "BUY",
        counterparty: str = "Sàn giao dịch Carbon Quốc gia",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Execute carbon credit transaction or surrender/offset allocation under Environmental Law 2020."""
        clean_action = action.upper().strip()
        if clean_action not in ("BUY", "SELL", "OFFSET"):
            clean_action = "BUY"

        total_amount_usd = round(quantity_tco2e * unit_price_usd, 2)
        total_amount_vnd = round(total_amount_usd * USD_VND_EXCHANGE_RATE)
        tx_id = f"CTX-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        record = {
            "ok": True,
            "transaction_id": tx_id,
            "project_name": project_name,
            "credit_type": credit_type.upper().strip(),
            "action": clean_action,
            "quantity_tco2e": quantity_tco2e,
            "unit_price_usd": unit_price_usd,
            "total_amount_usd": total_amount_usd,
            "total_amount_vnd": total_amount_vnd,
            "counterparty": counterparty,
            "statutory_basis": "Điều 93 & 94 Luật Bảo vệ Môi trường 2020 (Thị trường carbon trong nước)",
            "transaction_summary": (
                f"{clean_action} {quantity_tco2e:,.1f} tín chỉ carbon ({credit_type}) từ dự án '{project_name}' "
                f"với đơn giá ${unit_price_usd:,.2f}/tCO2e (Tổng: ${total_amount_usd:,.2f} ~ {total_amount_vnd:,.0f} VND)."
            ),
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO carbon_transactions (
                        transaction_id, project_name, credit_type, quantity_tco2e,
                        unit_price_usd, total_amount_usd, action, counterparty, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx_id,
                        project_name,
                        credit_type.upper().strip(),
                        quantity_tco2e,
                        unit_price_usd,
                        total_amount_usd,
                        clean_action,
                        counterparty,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return record

    # -----------------------------------------------------------------------
    # Portfolio & Status Telemetry
    # -----------------------------------------------------------------------

    def list_inventories(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered enterprise GHG inventories."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM ghg_inventories ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_transactions(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List executed carbon credit trades and offset allocations."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM carbon_transactions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated ESG compliance, green transition, and carbon telemetry."""
        with self._get_connection() as conn:
            g_row = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_tco2e), 0) as sm FROM ghg_inventories").fetchone()
            t_row = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(quantity_tco2e), 0) as q, COALESCE(SUM(total_amount_usd), 0) as sm FROM carbon_transactions").fetchone()
            r_row = conn.execute("SELECT COUNT(*) as c, COALESCE(AVG(composite_score), 0) as sc FROM esg_ratings").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "EsgEngine",
            "regulatory_framework": "Luật Bảo vệ Môi trường 2020 (72/2020/QH14) & Nghị định 06/2022/NĐ-CP",
            "standards": "GHG Protocol, ISO 14064-1, Quyết định 13/2024/QĐ-TTg & EU CBAM",
            "metrics": {
                "total_ghg_inventories": g_row["c"] if g_row else 0,
                "total_emissions_tracked_tco2e": round(g_row["sm"] if g_row else 0.0, 2),
                "total_carbon_transactions": t_row["c"] if t_row else 0,
                "total_credits_traded_tco2e": round(t_row["q"] if t_row else 0.0, 2),
                "total_credits_value_usd": round(t_row["sm"] if t_row else 0.0, 2),
                "total_credits_value_vnd": round((t_row["sm"] if t_row else 0.0) * USD_VND_EXCHANGE_RATE),
                "total_esg_ratings": r_row["c"] if r_row else 0,
                "average_esg_composite_score": round(r_row["sc"] if r_row else 0.0, 1),
            },
            "database": str(self.db_path),
        }

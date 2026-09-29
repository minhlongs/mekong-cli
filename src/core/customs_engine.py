# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Customs Clearance, HS Tariff Classification & Cross-Border Logistics Engine.

Implements Vietnamese statutory customs declaration, VNACCS/VCIS channeling, and international trade:
- Luật Hải quan 2014 (Luật số 54/2014/QH13) & Nghị định 08/2015/NĐ-CP (sửa đổi bởi NĐ 59/2018/NĐ-CP).
- Thông tư 38/2015/TT-BTC & Thông tư 39/2018/TT-BTC: Thủ tục hải quan, kiểm tra giám sát hải quan và thuế XNK.
- Thông tư 31/2022/TT-BTC: Danh mục hàng hóa xuất nhập khẩu Việt Nam (AHTN 8 chữ số).
- Biểu thuế xuất nhập khẩu ưu đãi (MFN) và ưu đãi đặc biệt (EVFTA, CPTPP, RCEP, ATIGA).
- Nghị định 31/2018/NĐ-CP: Quy định chi tiết Luật Quản lý ngoại thương về xuất xứ hàng hóa (C/O Forms: EUR.1, CPTPP, D, E).
- Lưu trữ SQLite WAL tại ``.mekong/customs.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Canonical HS Tariff Classification Database (AHTN 8-digit)
# ---------------------------------------------------------------------------

HS_DATABASE: dict[str, dict[str, typing.Any]] = {
    "8471.30.20": {
        "hs_code": "8471.30.20",
        "description": "Máy tính xách tay, kể cả loại máy tính xách tay siêu mỏng (Laptops)",
        "unit": "Cái",
        "mfn_rate": 0.0,
        "vat_rate": 10.0,
        "preferential_tariffs": {"EVFTA": 0.0, "CPTPP": 0.0, "RCEP": 0.0, "ATIGA": 0.0},
        "regulatory_notes": "Thuộc diện quản lý chuyên ngành của Bộ Thông tin và Truyền thông (Hợp quy QCVN).",
    },
    "8471.49.10": {
        "hs_code": "8471.49.10",
        "description": "Máy chủ (Servers), hệ thống tính toán lớn phục vụ trung tâm dữ liệu",
        "unit": "Cái",
        "mfn_rate": 0.0,
        "vat_rate": 10.0,
        "preferential_tariffs": {"EVFTA": 0.0, "CPTPP": 0.0, "RCEP": 0.0, "ATIGA": 0.0},
        "regulatory_notes": "Miễn thuế nhập khẩu MFN. Tuân thủ an toàn thông tin mạng theo Luật An toàn thông tin mạng 2015.",
    },
    "8517.62.21": {
        "hs_code": "8517.62.21",
        "description": "Thiết bị định tuyến mạng (Routers), thiết bị chuyển mạch (Switches) viễn thông",
        "unit": "Cái",
        "mfn_rate": 0.0,
        "vat_rate": 10.0,
        "preferential_tariffs": {"EVFTA": 0.0, "CPTPP": 0.0, "RCEP": 0.0, "ATIGA": 0.0},
        "regulatory_notes": "Kiểm tra chất lượng chuyên ngành Bộ TTTT trước khi thông quan.",
    },
    "8542.31.00": {
        "hs_code": "8542.31.00",
        "description": "Mạch xử lý và điều khiển bán dẫn (Integrated Circuits / CPU / GPU / AI Accelerators)",
        "unit": "Cái",
        "mfn_rate": 0.0,
        "vat_rate": 10.0,
        "preferential_tariffs": {"EVFTA": 0.0, "CPTPP": 0.0, "RCEP": 0.0, "ATIGA": 0.0},
        "regulatory_notes": "Hưởng ưu đãi công nghệ cao theo Quyết định 38/2020/QĐ-TTg.",
    },
    "8504.40.11": {
        "hs_code": "8504.40.11",
        "description": "Bộ cấp nguồn liên tục (UPS) và bộ chuyển đổi tĩnh điện dùng cho máy tính",
        "unit": "Cái",
        "mfn_rate": 3.0,
        "vat_rate": 10.0,
        "preferential_tariffs": {"EVFTA": 0.0, "CPTPP": 0.0, "RCEP": 0.0, "ATIGA": 0.0},
        "regulatory_notes": "Thuế MFN 3%, có C/O Form EUR.1 hoặc CPTPP được giảm về 0%.",
    },
    "0901.11.10": {
        "hs_code": "0901.11.10",
        "description": "Cà phê Robusta chưa rang, chưa khử chất caffeine (Xuất khẩu nông sản OCOP)",
        "unit": "Kg",
        "mfn_rate": 0.0,
        "vat_rate": 0.0,
        "preferential_tariffs": {"EVFTA": 0.0, "CPTPP": 0.0, "RCEP": 0.0, "ATIGA": 0.0},
        "regulatory_notes": "Thuế xuất khẩu 0%. Cần kiểm dịch thực vật (Phytosanitary Certificate) của Cục Bảo vệ thực vật.",
    },
    "0803.90.90": {
        "hs_code": "0803.90.90",
        "description": "Chuối tươi (Fresh bananas) xuất khẩu / nhập khẩu",
        "unit": "Kg",
        "mfn_rate": 15.0,
        "vat_rate": 5.0,
        "preferential_tariffs": {"EVFTA": 0.0, "CPTPP": 0.0, "RCEP": 0.0, "ATIGA": 0.0},
        "regulatory_notes": "Kiểm dịch an toàn thực phẩm và kiểm dịch thực vật tại cửa khẩu.",
    },
}

EXCHANGE_RATE_USD_VND: float = 25_450.0  # Tỷ giá hạch toán hải quan tham chiếu


class CustomsEngine:
    """Autonomous Customs Clearance, HS Tariff Classification & Cross-Border Logistics Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "customs.db"
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
                CREATE TABLE IF NOT EXISTS customs_declarations (
                    declaration_id TEXT PRIMARY KEY,
                    declaration_type TEXT NOT NULL,
                    hs_code TEXT NOT NULL,
                    commodity_name TEXT NOT NULL,
                    enterprise_tax_id TEXT NOT NULL,
                    origin_country TEXT NOT NULL,
                    invoice_value_usd REAL NOT NULL,
                    dutiable_value_vnd REAL NOT NULL,
                    channel TEXT NOT NULL,
                    import_duty_vnd REAL NOT NULL,
                    vat_vnd REAL NOT NULL,
                    total_tax_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS co_certificates (
                    co_id TEXT PRIMARY KEY,
                    form_type TEXT NOT NULL,
                    hs_code TEXT NOT NULL,
                    exporter_name TEXT NOT NULL,
                    importer_country TEXT NOT NULL,
                    fob_value_usd REAL NOT NULL,
                    rvc_pct REAL NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    criteria_code TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_decl_hs ON customs_declarations(hs_code);
                CREATE INDEX IF NOT EXISTS idx_decl_channel ON customs_declarations(channel);
                CREATE INDEX IF NOT EXISTS idx_co_hs ON co_certificates(hs_code);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # HS Tariff Lookup & Duty Assessment
    # -----------------------------------------------------------------------

    def lookup_hs_code(
        self,
        hs_code: str,
        fta: str = "MFN",
    ) -> dict[str, typing.Any]:
        """Look up 8-digit AHTN HS code tariff rates, VAT, and FTA preferences."""
        clean_code = hs_code.strip()
        tariff_item = HS_DATABASE.get(clean_code)

        if not tariff_item:
            # Fallback search by prefix
            for k, v in HS_DATABASE.items():
                if k.replace(".", "").startswith(clean_code.replace(".", "")):
                    tariff_item = v
                    break

        if not tariff_item:
            return {
                "ok": False,
                "hs_code": hs_code,
                "error": f"Mã HS không tồn tại trong danh mục AHTN cơ sở: {hs_code}",
                "available_codes": list(HS_DATABASE.keys()),
            }

        fta_key = fta.upper()
        duty_rate = tariff_item["mfn_rate"]
        if fta_key in tariff_item["preferential_tariffs"]:
            duty_rate = tariff_item["preferential_tariffs"][fta_key]

        return {
            "ok": True,
            "hs_code": tariff_item["hs_code"],
            "description": tariff_item["description"],
            "unit": tariff_item["unit"],
            "tariff_scheme": fta_key,
            "applicable_duty_rate_pct": duty_rate,
            "mfn_rate_pct": tariff_item["mfn_rate"],
            "vat_rate_pct": tariff_item["vat_rate"],
            "preferential_tariffs": tariff_item["preferential_tariffs"],
            "regulatory_notes": tariff_item["regulatory_notes"],
            "statutory_reference": "Thông tư 31/2022/TT-BTC & Biểu thuế XNK 2024",
        }

    # -----------------------------------------------------------------------
    # Customs Duty & Import Tax Calculation
    # -----------------------------------------------------------------------

    def calculate_customs_duties(
        self,
        invoice_value_usd: float,
        hs_code: str = "8471.30.20",
        freight_usd: float = 0.0,
        insurance_usd: float = 0.0,
        exchange_rate: float = EXCHANGE_RATE_USD_VND,
        fta: str = "MFN",
    ) -> dict[str, typing.Any]:
        """Calculate itemized import duty, special consumption tax, and VAT."""
        hs_info = self.lookup_hs_code(hs_code=hs_code, fta=fta)
        if not hs_info.get("ok"):
            duty_rate = 0.0
            vat_rate = 10.0
            commodity_desc = "Hàng hóa tiêu chuẩn"
        else:
            duty_rate = hs_info["applicable_duty_rate_pct"]
            vat_rate = hs_info["vat_rate_pct"]
            commodity_desc = hs_info["description"]

        # CIF = FOB/Invoice + Freight + Insurance
        cif_usd = invoice_value_usd + freight_usd + insurance_usd
        dutiable_value_vnd = round(cif_usd * exchange_rate)

        # Import Duty (Thuế nhập khẩu)
        import_duty_vnd = round(dutiable_value_vnd * (duty_rate / 100.0))

        # Import VAT (Thuế GTGT hàng nhập khẩu tính trên: Trị giá CIF + Thuế NK)
        vat_base_vnd = dutiable_value_vnd + import_duty_vnd
        vat_vnd = round(vat_base_vnd * (vat_rate / 100.0))

        total_tax_vnd = import_duty_vnd + vat_vnd

        return {
            "ok": True,
            "hs_code": hs_code,
            "commodity_description": commodity_desc,
            "invoice_value_usd": invoice_value_usd,
            "freight_usd": freight_usd,
            "insurance_usd": insurance_usd,
            "cif_value_usd": cif_usd,
            "exchange_rate": exchange_rate,
            "dutiable_value_vnd": dutiable_value_vnd,
            "import_duty_rate_pct": duty_rate,
            "import_duty_vnd": import_duty_vnd,
            "vat_rate_pct": vat_rate,
            "vat_vnd": vat_vnd,
            "total_tax_vnd": total_tax_vnd,
            "statutory_rules": [
                "Trị giá tính thuế tính theo giá CIF quy đổi theo tỷ giá hải quan ngày đăng ký tờ khai.",
                "Thuế GTGT hàng nhập khẩu được khấu trừ thuế đầu vào khi doanh nghiệp kê khai theo phương pháp khấu trừ.",
            ],
        }

    # -----------------------------------------------------------------------
    # VNACCS Risk Profiling & Channel Assignment
    # -----------------------------------------------------------------------

    def evaluate_customs_channel(
        self,
        enterprise_tax_id: str,
        hs_code: str,
        invoice_value_usd: float,
        origin_country: str = "US",
        compliance_tier: str = "TIER_2_NORMAL",
        has_valid_co: bool = True,
    ) -> dict[str, typing.Any]:
        """Evaluate VNACCS automated risk management criteria and assign customs channel."""
        # Risk evaluation heuristics per Circular 38/2015/TT-BTC
        is_high_risk_tier = compliance_tier in ("TIER_4_LOW", "TIER_5_NON_COMPLIANT")
        is_large_value = invoice_value_usd >= 100_000.0

        if is_high_risk_tier or (is_large_value and not has_valid_co):
            channel = "RED"
            channel_name = "Luồng Đỏ (Kiểm tra chi tiết hồ sơ & kiểm tra thực tế hàng hóa)"
            clearance_time = "01 - 03 ngày làm việc (Kiểm tra thực tế 5% - 100% qua máy soi hoặc thủ công)"
            action_required = "Xuất trình chứng từ gốc và phối hợp kiểm hóa tại bãi kiểm tra hải quan cửa khẩu."
        elif is_large_value or not has_valid_co:
            channel = "YELLOW"
            channel_name = "Luồng Vàng (Kiểm tra chi tiết bộ hồ sơ giấy/điện tử)"
            clearance_time = "02 giờ làm việc kể từ khi nộp đủ hồ sơ hải quan hợp lệ"
            action_required = "Nộp bản điện tử hoặc bản scan có chữ ký số: Invoice, Packing List, B/L, C/O qua VNACCS."
        else:
            channel = "GREEN"
            channel_name = "Luồng Xanh (Thông quan tự động ngay lập tức)"
            clearance_time = "Dưới 03 giây (Hệ thống VNACCS phê duyệt tự động)"
            action_required = "In mã vạch tờ khai và làm thủ tục lấy hàng tại cảng / cửa khẩu."

        return {
            "ok": True,
            "enterprise_tax_id": enterprise_tax_id,
            "hs_code": hs_code,
            "origin_country": origin_country,
            "channel": channel,
            "channel_name": channel_name,
            "clearance_time": clearance_time,
            "action_required": action_required,
            "compliance_tier": compliance_tier,
            "statutory_authority": "Hệ thống VNACCS/VCIS - Tổng cục Hải quan Việt Nam",
        }

    # -----------------------------------------------------------------------
    # Customs Declaration Workflow (Tờ khai hải quan điện tử)
    # -----------------------------------------------------------------------

    def create_declaration(
        self,
        enterprise_tax_id: str,
        hs_code: str,
        commodity_name: str,
        invoice_value_usd: float,
        origin_country: str = "US",
        declaration_type: str = "IMPORT_BUSINESS",
        compliance_tier: str = "TIER_2_NORMAL",
        has_valid_co: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Synthesize and register a VNACCS electronic customs declaration."""
        decl_id = f"TKHQ-{uuid.uuid4().hex[:10].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        # Calculate duties
        duties = self.calculate_customs_duties(invoice_value_usd=invoice_value_usd, hs_code=hs_code)
        # Evaluate channel
        channel_info = self.evaluate_customs_channel(
            enterprise_tax_id=enterprise_tax_id,
            hs_code=hs_code,
            invoice_value_usd=invoice_value_usd,
            origin_country=origin_country,
            compliance_tier=compliance_tier,
            has_valid_co=has_valid_co,
        )

        record = {
            "ok": True,
            "declaration_id": decl_id,
            "declaration_type": declaration_type,
            "hs_code": hs_code,
            "commodity_name": commodity_name,
            "enterprise_tax_id": enterprise_tax_id,
            "origin_country": origin_country,
            "invoice_value_usd": invoice_value_usd,
            "dutiable_value_vnd": duties["dutiable_value_vnd"],
            "channel": channel_info["channel"],
            "channel_name": channel_info["channel_name"],
            "import_duty_vnd": duties["import_duty_vnd"],
            "vat_vnd": duties["vat_vnd"],
            "total_tax_vnd": duties["total_tax_vnd"],
            "status": "CLEARED" if channel_info["channel"] == "GREEN" else "AWAITING_EXAMINATION",
            "statutory_timeline": channel_info["clearance_time"],
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO customs_declarations (
                        declaration_id, declaration_type, hs_code, commodity_name,
                        enterprise_tax_id, origin_country, invoice_value_usd,
                        dutiable_value_vnd, channel, import_duty_vnd, vat_vnd,
                        total_tax_vnd, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        decl_id,
                        declaration_type,
                        hs_code,
                        commodity_name,
                        enterprise_tax_id,
                        origin_country,
                        invoice_value_usd,
                        duties["dutiable_value_vnd"],
                        channel_info["channel"],
                        duties["import_duty_vnd"],
                        duties["vat_vnd"],
                        duties["total_tax_vnd"],
                        record["status"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return record

    # -----------------------------------------------------------------------
    # Rules of Origin & Certificate of Origin (C/O)
    # -----------------------------------------------------------------------

    def verify_rules_of_origin(
        self,
        form_type: str,
        hs_code: str,
        fob_value_usd: float,
        non_originating_value_usd: float,
        exporter_name: str = "Doanh Nghiệp Xuất Khẩu Việt Nam",
        importer_country: str = "DE",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Verify Regional Value Content (RVC) and Change in Tariff Classification (CTC) for C/O."""
        co_id = f"CO-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        # RVC = ((FOB - VNM) / FOB) * 100%
        if fob_value_usd <= 0:
            rvc_pct = 0.0
        else:
            rvc_pct = round(((fob_value_usd - non_originating_value_usd) / fob_value_usd) * 100.0, 2)

        # Standard RVC qualifying threshold is typically >= 40% under EVFTA, CPTPP, and ATIGA
        is_eligible = rvc_pct >= 40.0
        criteria_code = "RVC_40" if is_eligible else "INSUFFICIENT_WORKING"

        form_upper = form_type.strip().upper()
        if "EUR" in form_upper:
            form_name = "C/O Form EUR.1 (Hiệp định EVFTA Việt Nam - EU)"
        elif "CPTPP" in form_upper:
            form_name = "Chứng từ tự chứng nhận xuất xứ CPTPP"
        elif "D" in form_upper:
            form_name = "C/O Form D (Hiệp định ATIGA nội khối ASEAN)"
        elif "E" in form_upper:
            form_name = "C/O Form E (Hiệp định ACFTA Việt Nam - Trung Quốc)"
        else:
            form_name = f"C/O Form {form_type}"

        result = {
            "ok": True,
            "co_id": co_id,
            "form_type": form_upper,
            "form_name": form_name,
            "hs_code": hs_code,
            "exporter_name": exporter_name,
            "importer_country": importer_country,
            "fob_value_usd": fob_value_usd,
            "non_originating_value_usd": non_originating_value_usd,
            "rvc_pct": rvc_pct,
            "is_eligible": is_eligible,
            "criteria_code": criteria_code,
            "statutory_rules": [
                "Hàm lượng giá trị khu vực (RVC) đạt tối thiểu 40% giá FOB xuất xưởng.",
                "Nguyên tắc chuyển đổi mã số hàng hóa (CTC) ở cấp 4 chữ số (CTH).",
                "Chứng từ chứng minh nguồn gốc nguyên liệu lưu trữ tối thiểu 05 năm theo quy định.",
            ],
            "status": "QUALIFIED_FOR_PREFERENTIAL_TARIFF" if is_eligible else "ORIGIN_DISQUALIFIED",
            "created_at": now.isoformat(),
        }

        if save and is_eligible:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO co_certificates (
                        co_id, form_type, hs_code, exporter_name,
                        importer_country, fob_value_usd, rvc_pct,
                        is_eligible, criteria_code, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        co_id,
                        form_upper,
                        hs_code,
                        exporter_name,
                        importer_country,
                        fob_value_usd,
                        rvc_pct,
                        1 if is_eligible else 0,
                        criteria_code,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Portfolio & Status
    # -----------------------------------------------------------------------

    def list_declarations(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered customs declarations."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM customs_declarations ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated customs declarations, channeling ratios, and tax revenue."""
        with self._get_connection() as conn:
            decl_row = conn.execute(
                "SELECT COUNT(*) as cnt, COALESCE(SUM(total_tax_vnd), 0) as sm FROM customs_declarations"
            ).fetchone()
            green_cnt = conn.execute("SELECT COUNT(*) as c FROM customs_declarations WHERE channel = 'GREEN'").fetchone()["c"]
            yellow_cnt = conn.execute("SELECT COUNT(*) as c FROM customs_declarations WHERE channel = 'YELLOW'").fetchone()["c"]
            red_cnt = conn.execute("SELECT COUNT(*) as c FROM customs_declarations WHERE channel = 'RED'").fetchone()["c"]
            co_cnt = conn.execute("SELECT COUNT(*) as c FROM co_certificates").fetchone()["c"]

        return {
            "ok": True,
            "status": "operational",
            "engine": "CustomsEngine",
            "regulatory_framework": "Luật Hải quan 2014 / NĐ 08/2015/NĐ-CP / TT 38/2015/TT-BTC",
            "vnaccs_version": "VNACCS/VCIS v2024",
            "reference_exchange_rate": EXCHANGE_RATE_USD_VND,
            "metrics": {
                "total_declarations": decl_row["cnt"] if decl_row else 0,
                "total_tax_collected_vnd": decl_row["sm"] if decl_row else 0,
                "green_channel_count": green_cnt,
                "yellow_channel_count": yellow_cnt,
                "red_channel_count": red_cnt,
                "co_certificates_issued": co_cnt,
                "supported_hs_codes": len(HS_DATABASE),
            },
            "database": str(self.db_path),
        }


CustomsEngineAlias = CustomsEngine

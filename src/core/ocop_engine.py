# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous OCOP (One Commune One Product) Agricultural Export, Star Rating & Compliance Engine.

Implements Vietnamese national standard evaluation and export readiness:
- Quyết định 919/QĐ-TTg (Chương trình Mỗi Xã Một Sản Phẩm quốc gia giai đoạn 2021-2025).
- Quyết định 148/QĐ-TTg (Bộ tiêu chí và quy trình đánh giá, phân hạng 1 sao đến 5 sao OCOP).
- HS code agricultural classification (Gạo ST25, Cà phê Robusta, Hạt điều, Chè Shan Tuyết, v.v.).
- Multi-market export compliance requirements (EVFTA, US FDA, Japan AJCEP, China Lệnh 248/249).
- B2B export marketplace listing generation (Alibaba, Amazon, Shopee Cross-Border).
- Persistent SQLite WAL storage in ``.mekong/ocop.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import sqlite3
import typing
import uuid

CANONICAL_OCOP_PRODUCTS: list[dict[str, typing.Any]] = [
    {
        "product_id": "OCOP-ST25",
        "name": "Gạo ST25 Ông Cua Sóc Trăng",
        "category": "Thực phẩm (Lương thực)",
        "origin_commune": "Xã Viên An",
        "origin_province": "Sóc Trăng",
        "star_rating": 5,
        "hs_code": "1006.30",
        "certifications": ["VietGAP", "ISO 22000", "Organic USDA", "HACCP"],
        "export_ready": True,
        "primary_markets": ["EU", "US", "Japan", "Singapore"],
    },
    {
        "product_id": "OCOP-CF-BMT",
        "name": "Cà Phê Robusta Đặc Sản Buôn Ma Thuột",
        "category": "Đồ uống",
        "origin_commune": "Xã Ea Tu",
        "origin_province": "Đắk Lắk",
        "star_rating": 4,
        "hs_code": "0901.11",
        "certifications": ["UTZ", "Fairtrade", "VietGAP", "HACCP"],
        "export_ready": True,
        "primary_markets": ["EU", "Germany", "Japan", "Korea"],
    },
    {
        "product_id": "OCOP-DIEU-BP",
        "name": "Hạt Điều Rang Muối Bình Phước",
        "category": "Thực phẩm (Hạt dinh dưỡng)",
        "origin_commune": "Xã Phú Riềng",
        "origin_province": "Bình Phước",
        "star_rating": 4,
        "hs_code": "0801.32",
        "certifications": ["HACCP", "ISO 22000", "FDA Registered", "Halal"],
        "export_ready": True,
        "primary_markets": ["China", "US", "Middle East", "EU"],
    },
    {
        "product_id": "OCOP-TRA-HG",
        "name": "Trà Shan Tuyết Cổ Thụ Tây Côn Lĩnh",
        "category": "Đồ uống (Chè búp)",
        "origin_commune": "Xã Cao Bồ",
        "origin_province": "Hà Giang",
        "star_rating": 5,
        "hs_code": "0902.20",
        "certifications": ["EU Organic", "VietGAP", "Chỉ dẫn địa lý (GI)"],
        "export_ready": True,
        "primary_markets": ["Taiwan", "EU", "Japan", "China"],
    },
    {
        "product_id": "OCOP-XOA-HL",
        "name": "Xoài Cát Hòa Lộc Tiền Giang",
        "category": "Thực phẩm (Trái cây tươi)",
        "origin_commune": "Xã Hòa Hưng",
        "origin_province": "Tiền Giang",
        "star_rating": 4,
        "hs_code": "0804.50",
        "certifications": ["GlobalGAP", "Mã số vùng trồng (PUC)"],
        "export_ready": True,
        "primary_markets": ["Japan", "US", "Australia", "Korea"],
    },
]

MARKET_STANDARDS: dict[str, dict[str, typing.Any]] = {
    "EU": {
        "free_trade_agreement": "EVFTA",
        "mandatory_certifications": ["HACCP", "ISO 22000", "MRLs Compliance (Dư lượng BVTV)"],
        "tariff_preference": "0% theo lộ trình EVFTA",
        "packaging_rules": "Bao bì tái chế, ghi nhãn dinh dưỡng theo Quy định 1169/2011/EU",
    },
    "US": {
        "free_trade_agreement": "BTA (Song phương)",
        "mandatory_certifications": ["US FDA Facility Registration", "FSMA Preventive Controls"],
        "tariff_preference": "MFN",
        "packaging_rules": "FDA Nutrition Facts, Tiêu chuẩn tiếng Anh, Cảnh báo dị ứng",
    },
    "Japan": {
        "free_trade_agreement": "VJEPA & CPTPP",
        "mandatory_certifications": ["JAS (Nông nghiệp Nhật Bản)", "Kiểm dịch thực vật (MAFF)"],
        "tariff_preference": "0% theo CPTPP / VJEPA",
        "packaging_rules": "Nhãn phụ tiếng Nhật, kiểm soát dư lượng nghiêm ngặt",
    },
    "China": {
        "free_trade_agreement": "ACFTA & RCEP",
        "mandatory_certifications": ["Mã số doanh nghiệp GACC (Lệnh 248)", "Mã số vùng trồng (Lệnh 249)"],
        "tariff_preference": "0% theo ACFTA",
        "packaging_rules": "Bao bì in mã số GACC, truy xuất nguồn gốc QR code",
    },
    "Middle East": {
        "free_trade_agreement": "Bilateral / CEPA",
        "mandatory_certifications": ["Chứng nhận Halal (JAKIM/GCC công nhận)", "HACCP"],
        "tariff_preference": "Biểu thuế ưu đãi song phương",
        "packaging_rules": "Nhãn song ngữ Anh - Ả Rập, Logo chứng nhận Halal",
    },
}


class OcopEngine:
    """Autonomous Vietnamese OCOP Star Rating, HS Code & Export Compliance Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            base_dir = pathlib.Path(".mekong")
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "ocop.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    origin_commune TEXT NOT NULL,
                    origin_province TEXT NOT NULL,
                    star_rating INTEGER NOT NULL,
                    hs_code TEXT NOT NULL,
                    certifications TEXT NOT NULL,
                    export_ready INTEGER NOT NULL DEFAULT 1,
                    primary_markets TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluations (
                    eval_id TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    part_a_score REAL NOT NULL,
                    part_b_score REAL NOT NULL,
                    part_c_score REAL NOT NULL,
                    total_score REAL NOT NULL,
                    star_grade INTEGER NOT NULL,
                    grade_title TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS export_listings (
                    listing_id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL,
                    target_market TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    title_en TEXT NOT NULL,
                    description_en TEXT NOT NULL,
                    compliance_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM products")
            if cursor.fetchone()["cnt"] == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for p in CANONICAL_OCOP_PRODUCTS:
                    conn.execute(
                        """
                        INSERT INTO products (
                            product_id, name, category, origin_commune, origin_province,
                            star_rating, hs_code, certifications, export_ready, primary_markets, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            p["product_id"],
                            p["name"],
                            p["category"],
                            p["origin_commune"],
                            p["origin_province"],
                            p["star_rating"],
                            p["hs_code"],
                            json.dumps(p["certifications"]),
                            1 if p["export_ready"] else 0,
                            json.dumps(p["primary_markets"]),
                            now,
                        ),
                    )
                conn.commit()

    def evaluate_star_rating(
        self,
        product_name: str,
        part_a_community: float = 30.0,
        part_b_marketing: float = 22.0,
        part_c_quality: float = 38.0,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Evaluate OCOP star classification (1 to 5 stars) per Decision 148/QĐ-TTg."""
        score_a = max(0.0, min(35.0, float(part_a_community)))
        score_b = max(0.0, min(25.0, float(part_b_marketing)))
        score_c = max(0.0, min(40.0, float(part_c_quality)))
        total_score = round(score_a + score_b + score_c, 1)

        if total_score >= 90.0:
            stars = 5
            title = "OCOP 5 Sao (Cấp Quốc gia — Tiêu chuẩn xuất khẩu toàn cầu)"
            export_potential = "Rất cao (Đạt chuẩn xuất khẩu vào EU, Mỹ, Nhật Bản)"
        elif total_score >= 70.0:
            stars = 4
            title = "OCOP 4 Sao (Cấp Tỉnh — Tiềm năng xuất khẩu khu vực)"
            export_potential = "Cao (Đáp ứng tiêu chuẩn thị trường ASEAN, Trung Quốc)"
        elif total_score >= 50.0:
            stars = 3
            title = "OCOP 3 Sao (Cấp Huyện/Tỉnh — Tiêu thụ nội địa mở rộng)"
            export_potential = "Trung bình (Cần nâng cấp bao bì và chứng nhận quốc tế)"
        elif total_score >= 30.0:
            stars = 2
            title = "OCOP 2 Sao (Khởi đầu cấp xã/huyện)"
            export_potential = "Thấp (Tập trung hoàn thiện quy trình sản xuất)"
        else:
            stars = 1
            title = "OCOP 1 Sao (Ý tưởng sơ khai)"
            export_potential = "Chưa đủ điều kiện xuất khẩu"

        eval_id = f"OEVAL-{str(uuid.uuid4())[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        res = {
            "ok": True,
            "eval_id": eval_id,
            "product_name": product_name,
            "scores": {
                "part_a_community_max35": score_a,
                "part_b_marketing_max25": score_b,
                "part_c_quality_max40": score_c,
                "total_score_max100": total_score,
            },
            "star_rating": stars,
            "grade_title": title,
            "export_potential": export_potential,
            "decree": "Quyết định 148/QĐ-TTg",
            "evaluated_at": now_iso,
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO evaluations (
                        eval_id, product_name, part_a_score, part_b_score, part_c_score,
                        total_score, star_grade, grade_title, evaluated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eval_id,
                        product_name,
                        score_a,
                        score_b,
                        score_c,
                        total_score,
                        stars,
                        title,
                        now_iso,
                    ),
                )
                conn.commit()

        return res

    def list_products(
        self,
        min_stars: int = 1,
        province: str = "all",
    ) -> list[dict[str, typing.Any]]:
        """List registered OCOP products with star ratings and HS codes."""
        with self._get_connection() as conn:
            query = "SELECT * FROM products WHERE star_rating >= ?"
            params: list[typing.Any] = [min_stars]
            if province != "all":
                query += " AND origin_province LIKE ?"
                params.append(f"%{province}%")
            query += " ORDER BY star_rating DESC, name ASC"

            cursor = conn.execute(query, tuple(params))
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                d["certifications"] = json.loads(d["certifications"]) if isinstance(d["certifications"], str) else d["certifications"]
                d["primary_markets"] = json.loads(d["primary_markets"]) if isinstance(d["primary_markets"], str) else d["primary_markets"]
                d["export_ready"] = bool(d["export_ready"])
                results.append(d)
            return results

    def get_market_compliance(self, market: str) -> dict[str, typing.Any]:
        """Query export regulations and tariff benefits for an overseas market."""
        market_key = market.upper().strip()
        for k, v in MARKET_STANDARDS.items():
            if market_key == k.upper() or market_key in k.upper() or k.upper() in market_key:
                return {"ok": True, "market": k, **v}
        return {
            "ok": True,
            "market": market,
            "free_trade_agreement": "WTO MFN",
            "mandatory_certifications": ["HACCP", "Kiểm dịch thực vật (Phytosanitary Certificate)"],
            "tariff_preference": "Biểu thuế thông thường",
            "packaging_rules": "Tiếng Anh tiêu chuẩn thương mại quốc tế",
        }

    def generate_b2b_listing(
        self,
        product_id: str,
        target_market: str = "EU",
        platform: str = "alibaba",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Generate high-converting international B2B product listing for export marketplaces."""
        with self._get_connection() as conn:
            prod = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
            if not prod:
                # Ad-hoc product fallback
                prod_name = product_id
                hs_code = "1006.30"
                stars = 4
                origin = "Vietnam"
                certs = ["VietGAP", "ISO 22000"]
            else:
                prod_name = prod["name"]
                hs_code = prod["hs_code"]
                stars = prod["star_rating"]
                origin = f"{prod['origin_commune']}, {prod['origin_province']}, Vietnam"
                certs = json.loads(prod["certifications"]) if isinstance(prod["certifications"], str) else prod["certifications"]

        compliance = self.get_market_compliance(target_market)
        listing_id = f"OLIST-{str(uuid.uuid4())[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        title_en = f"Premium Vietnamese {prod_name} — OCOP {stars}-Star Certified (HS: {hs_code})"
        desc_en = (
            f"Authentic agricultural specialty directly from {origin}.\n"
            f"Rated OCOP {stars} Stars under Vietnam National Standards.\n"
            f"Quality Certifications: {', '.join(certs)}.\n"
            f"Market Compliant: {target_market} ({compliance['free_trade_agreement']}).\n"
            f"Available for OEM/Bulk B2B orders with global container shipping (FOB/CIF)."
        )

        res = {
            "ok": True,
            "listing_id": listing_id,
            "product_id": product_id,
            "product_name": prod_name,
            "hs_code": hs_code,
            "star_rating": stars,
            "target_market": target_market,
            "platform": platform.lower(),
            "title_en": title_en,
            "description_en": desc_en,
            "compliance_summary": {
                "fta": compliance["free_trade_agreement"],
                "certifications_required": compliance["mandatory_certifications"],
                "tariff_rate": compliance["tariff_preference"],
            },
            "status": "active_ready",
            "created_at": now_iso,
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO export_listings (
                        listing_id, product_id, target_market, platform,
                        title_en, description_en, compliance_status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        listing_id,
                        product_id,
                        target_market,
                        platform.lower(),
                        title_en,
                        desc_en,
                        "compliant",
                        now_iso,
                    ),
                )
                conn.commit()

        return res

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated OCOP program telemetry and export readiness metrics."""
        with self._get_connection() as conn:
            total_prods = conn.execute("SELECT COUNT(*) AS cnt FROM products").fetchone()["cnt"]
            five_star = conn.execute("SELECT COUNT(*) AS cnt FROM products WHERE star_rating = 5").fetchone()["cnt"]
            four_star = conn.execute("SELECT COUNT(*) AS cnt FROM products WHERE star_rating = 4").fetchone()["cnt"]
            three_star = conn.execute("SELECT COUNT(*) AS cnt FROM products WHERE star_rating = 3").fetchone()["cnt"]
            total_evals = conn.execute("SELECT COUNT(*) AS cnt FROM evaluations").fetchone()["cnt"]
            total_listings = conn.execute("SELECT COUNT(*) AS cnt FROM export_listings").fetchone()["cnt"]

            recent_evals = [dict(r) for r in conn.execute("SELECT * FROM evaluations ORDER BY evaluated_at DESC LIMIT 5").fetchall()]
            recent_listings = [dict(r) for r in conn.execute("SELECT * FROM export_listings ORDER BY created_at DESC LIMIT 5").fetchall()]

        return {
            "ok": True,
            "status": "operational",
            "program": "Chương trình Mỗi Xã Một Sản Phẩm (OCOP) Quốc Gia",
            "governing_decrees": ["Quyết định 919/QĐ-TTg", "Quyết định 148/QĐ-TTg"],
            "total_products": total_prods,
            "star_breakdown": {
                "5_stars_national_export": five_star,
                "4_stars_provincial_high": four_star,
                "3_stars_regional": three_star,
            },
            "total_evaluations_run": total_evals,
            "total_export_listings": total_listings,
            "supported_target_markets": list(MARKET_STANDARDS.keys()),
            "recent_evaluations": recent_evals,
            "recent_listings": recent_listings,
        }

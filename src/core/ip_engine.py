# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Intellectual Property (IP), Trademark, Patent & Copyright Engine.

Implements Vietnamese statutory intellectual property rights management conforming to:
- Luật Sở hữu trí tuệ 2005 (sửa đổi, bổ sung 2022 — Luật số 07/2022/QH15).
- Thỏa ước Nice phiên bản 12-2024 (Nice Classification) phân loại hàng hóa & dịch vụ nhãn hiệu.
- Nghị định 65/2023/NĐ-CP: Quy định chi tiết một số điều và biện pháp thi hành Luật SHTT về sở hữu công nghiệp.
- Nghị định 17/2023/NĐ-CP: Hướng dẫn thi hành một số điều của Luật SHTT về quyền tác giả, quyền liên quan.
- Thông tư 263/2016/TT-BTC: Biểu mức thu phí, lệ phí sở hữu công nghiệp (Cục Sở hữu trí tuệ - IP VIETNAM).
- Lưu trữ SQLite WAL tại ``.mekong/ip.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import difflib
import json
import os
import pathlib
import re
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Canonical Nice Classification (Tech, AI, Software & Commercial Classes)
# ---------------------------------------------------------------------------

NICE_CLASSES: dict[str, dict[str, typing.Any]] = {
    "09": {
        "class_number": "09",
        "title": "Phần mềm máy tính, Trí tuệ nhân tạo (AI), Thiết bị kỹ thuật số",
        "scope": "Phần mềm máy tính ghi sẵn, phần mềm máy tính có thể tải về, các mô hình học máy và AI, ứng dụng di động, thiết bị xử lý dữ liệu.",
        "typical_items": [
            "Phần mềm máy tính có thể tải xuống sử dụng công nghệ trí tuệ nhân tạo",
            "Mô hình học sâu và thuật toán xử lý ngôn ngữ tự nhiên",
            "Ứng dụng di động để quản lý tài chính và điều hành doanh nghiệp",
            "Thiết bị điện tử và phần cứng chuyên dụng cho tính toán biên",
        ],
    },
    "35": {
        "class_number": "35",
        "title": "Quảng cáo, Quản lý kinh doanh, Sàn thương mại điện tử",
        "scope": "Dịch vụ quảng cáo, điều hành kinh doanh, dịch vụ văn phòng, quản lý sàn giao dịch trực tuyến và dịch vụ bán lẻ phần mềm.",
        "typical_items": [
            "Dịch vụ quảng cáo trực tuyến và tiếp thị kỹ thuật số",
            "Quản lý và điều hành hệ thống kinh doanh tự động",
            "Cung cấp sàn giao dịch thương mại điện tử trực tuyến cho người mua và người bán",
            "Dịch vụ tư vấn tổ chức kinh doanh cho các công ty khởi nghiệp",
        ],
    },
    "36": {
        "class_number": "36",
        "title": "Dịch vụ tài chính, Fintech, Cổng thanh toán",
        "scope": "Dịch vụ tiền tệ, ngân hàng số, xử lý thanh toán điện tử, công nghệ tài chính và bảo hiểm.",
        "typical_items": [
            "Dịch vụ trung gian thanh toán và cổng thanh toán điện tử",
            "Dịch vụ ví điện tử và chuyển tiền qua mạng máy tính",
            "Tư vấn đầu tư tài chính và quản lý tài sản số",
        ],
    },
    "38": {
        "class_number": "38",
        "title": "Dịch vụ viễn thông, Truyền dẫn dữ liệu số",
        "scope": "Truyền dữ liệu qua mạng máy tính, dịch vụ liên lạc vệ tinh, truyền phát thông tin kỹ thuật số.",
        "typical_items": [
            "Dịch vụ truyền dẫn dữ liệu kỹ thuật số qua mạng viễn thông",
            "Cung cấp quyền truy cập vào cổng thông tin điện tử và mạng toàn cầu",
            "Truyền phát thông tin và tin nhắn bằng máy tính",
        ],
    },
    "41": {
        "class_number": "41",
        "title": "Giáo dục, Đào tạo công nghệ, Xuất bản số",
        "scope": "Dịch vụ giáo dục, tổ chức hội nghị công nghệ, xuất bản nội dung điện tử trực tuyến.",
        "typical_items": [
            "Dịch vụ đào tạo và giảng dạy về kỹ thuật phần mềm và AI",
            "Tổ chức các hội thảo, hội nghị công nghệ và cuộc thi hackathon",
            "Xuất bản ấn phẩm điện tử và tài liệu kỹ thuật trực tuyến",
        ],
    },
    "42": {
        "class_number": "42",
        "title": "Thiết kế & phát triển phần mềm, SaaS, Điện toán đám mây, R&D AI",
        "scope": "Nghiên cứu khoa học và công nghệ, thiết kế và phát triển phần mềm máy tính, điện toán đám mây (Cloud Hosting), SaaS (Phần mềm dưới dạng dịch vụ).",
        "typical_items": [
            "Thiết kế, phát triển và cập nhật phần mềm máy tính cho bên thứ ba",
            "Cung cấp phần mềm dưới dạng dịch vụ (SaaS) dựa trên trí tuệ nhân tạo",
            "Nghiên cứu và phát triển công nghệ trong lĩnh vực học máy và AI",
            "Dịch vụ tư vấn kiến trúc công nghệ thông tin và an toàn không gian mạng",
        ],
    },
    "45": {
        "class_number": "45",
        "title": "Dịch vụ pháp lý, Cấp phép bản quyền sở hữu trí tuệ",
        "scope": "Dịch vụ pháp lý, quản lý và cấp phép quyền sở hữu trí tuệ, đăng ký bản quyền phần mềm.",
        "typical_items": [
            "Dịch vụ cấp phép bản quyền phần mềm và công nghệ",
            "Dịch vụ tư vấn bảo hộ tài sản trí tuệ và nhãn hiệu",
            "Đại diện nộp đơn đăng ký quyền sở hữu công nghiệp",
        ],
    },
}

# ---------------------------------------------------------------------------
# Official Fees Schedule (Thông tư 263/2016/TT-BTC)
# ---------------------------------------------------------------------------

STATUTORY_FEES_VND = {
    # Trademark (Nhãn hiệu)
    "TM_FILING_FEE": 150_000,
    "TM_PUBLICATION_FEE": 120_000,
    "TM_SEARCH_FEE_PER_CLASS": 180_000,
    "TM_EXAMINATION_FEE_PER_CLASS": 550_000,
    # Patent (Sáng chế)
    "PAT_FILING_FEE": 150_000,
    "PAT_PUBLICATION_FEE": 120_000,
    "PAT_SEARCH_FEE_PER_CLAIM": 600_000,
    "PAT_EXAMINATION_FEE_PER_CLAIM": 720_000,
    # Software Copyright (Quyền tác giả phần mềm)
    "COPYRIGHT_SOFTWARE_FEE": 100_000,
}


class IpEngine:
    """Autonomous Intellectual Property, Trademark, Patent & Copyright Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "ip.db"
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
                CREATE TABLE IF NOT EXISTS trademarks (
                    mark_id TEXT PRIMARY KEY,
                    mark_name TEXT NOT NULL,
                    nice_class TEXT NOT NULL,
                    applicant_name TEXT NOT NULL,
                    goods_services_spec TEXT NOT NULL,
                    status TEXT NOT NULL,
                    filing_date TEXT NOT NULL,
                    priority_date TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS patents (
                    patent_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    technical_field TEXT NOT NULL,
                    applicant_name TEXT NOT NULL,
                    claims_count INTEGER NOT NULL,
                    claims_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    filing_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS software_copyrights (
                    copyright_id TEXT PRIMARY KEY,
                    software_name TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    lines_of_code INTEGER,
                    repository_url TEXT,
                    status TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_tm_name ON trademarks(mark_name);
                CREATE INDEX IF NOT EXISTS idx_tm_class ON trademarks(nice_class);
                CREATE INDEX IF NOT EXISTS idx_pat_applicant ON patents(applicant_name);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Trademark Management & Nice Classification
    # -----------------------------------------------------------------------

    def register_trademark(
        self,
        mark_name: str,
        nice_class: str = "09",
        applicant_name: str = "Doanh Nghiệp Đăng Ký",
        goods_services_spec: str = "",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Synthesize and register a trademark application under Nice Classification & Law on IP."""
        mark_id = f"TM-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        class_key = nice_class.zfill(2)
        class_info = NICE_CLASSES.get(class_key, NICE_CLASSES["09"])

        spec = goods_services_spec.strip()
        if not spec:
            spec = "; ".join(class_info["typical_items"][:2])

        # Calculate official filing fee for 1 class with up to 6 goods/services items
        official_fees = (
            STATUTORY_FEES_VND["TM_FILING_FEE"]
            + STATUTORY_FEES_VND["TM_PUBLICATION_FEE"]
            + STATUTORY_FEES_VND["TM_SEARCH_FEE_PER_CLASS"]
            + STATUTORY_FEES_VND["TM_EXAMINATION_FEE_PER_CLASS"]
        )

        record = {
            "ok": True,
            "mark_id": mark_id,
            "mark_name": mark_name.strip(),
            "nice_class": class_key,
            "class_title": class_info["title"],
            "applicant_name": applicant_name.strip(),
            "goods_services_spec": spec,
            "status": "FILED_FORMAL_EXAMINATION",
            "filing_date": now.strftime("%Y-%m-%d"),
            "statutory_authority": "Cục Sở hữu trí tuệ Việt Nam (IP VIETNAM - NOIP)",
            "official_fee_vnd": official_fees,
            "timeline": {
                "formal_examination": "01 tháng kể từ ngày nộp đơn",
                "publication": "02 tháng kể từ ngày chấp nhận đơn hợp lệ",
                "substantive_examination": "09 tháng kể từ ngày công bố đơn",
            },
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO trademarks (
                        mark_id, mark_name, nice_class, applicant_name,
                        goods_services_spec, status, filing_date, priority_date, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mark_id,
                        mark_name.strip(),
                        class_key,
                        applicant_name.strip(),
                        spec,
                        "FILED_FORMAL_EXAMINATION",
                        now.strftime("%Y-%m-%d"),
                        now.strftime("%Y-%m-%d"),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return record

    # -----------------------------------------------------------------------
    # Trademark Similarity & Conflict Search
    # -----------------------------------------------------------------------

    def search_trademark_similarity(
        self,
        mark_name: str,
        nice_class: str = "09",
    ) -> dict[str, typing.Any]:
        """Perform phonetical and orthographical similarity analysis against existing marks."""
        query_mark = mark_name.strip().lower()
        class_key = nice_class.zfill(2)

        # Pre-seeded reference tech marks in Vietnam & international
        reference_marks = [
            ("MekongMind", "09"),
            ("MekongAI", "42"),
            ("MekongCloud", "42"),
            ("MekongPay", "36"),
            ("ViettelAI", "09"),
            ("VNPT Tech", "09"),
            ("FPT Software", "42"),
            ("VNG Corporation", "09"),
            ("Zalo", "38"),
            ("MoMo", "36"),
            ("OpenAI", "09"),
            ("Antigravity", "42"),
        ]

        # Query database for registered trademarks
        with self._get_connection() as conn:
            rows = conn.execute("SELECT mark_name, nice_class FROM trademarks").fetchall()
            for r in rows:
                reference_marks.append((r["mark_name"], r["nice_class"]))

        matches: list[dict[str, typing.Any]] = []
        highest_score = 0.0

        for ref_name, ref_class in reference_marks:
            clean_ref = ref_name.strip().lower()
            # String orthographic similarity
            matcher = difflib.SequenceMatcher(None, query_mark, clean_ref)
            ratio = round(matcher.ratio(), 3)

            # Phonetic heuristic (prefix / sound matching)
            prefix_match = query_mark[:3] == clean_ref[:3] if len(query_mark) >= 3 and len(clean_ref) >= 3 else False
            if prefix_match:
                ratio = min(1.0, round(ratio + 0.15, 3))

            class_conflict = ref_class == class_key

            if ratio >= 0.40 or (class_conflict and ratio >= 0.35):
                matches.append(
                    {
                        "existing_mark": ref_name,
                        "nice_class": ref_class,
                        "similarity_score": ratio,
                        "class_identical": class_conflict,
                        "conflict_risk": "HIGH" if (ratio >= 0.70 and class_conflict) else ("MEDIUM" if ratio >= 0.50 else "LOW"),
                    }
                )
                if ratio > highest_score:
                    highest_score = ratio

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_matches = matches[:5]

        has_high_risk = any(m["conflict_risk"] == "HIGH" for m in top_matches)
        assessment = (
            "NGUY CƠ XUNG ĐỘT CAO: Nhãn hiệu tương tự gây nhầm lẫn với nhãn hiệu đã đăng ký (Điều 74.2.e Luật SHTT)"
            if has_high_risk
            else (
                "CÓ NGUY CƠ TRUNG BÌNH: Nên xem xét điều chỉnh thành phần từ ngữ hoặc đăng ký thêm yếu tố hình ảnh (Logo)"
                if highest_score >= 0.50
                else "KHẢ NĂNG PHÂN BIỆT CAO: Đủ điều kiện bảo hộ sơ bộ theo Điều 72 Luật SHTT"
            )
        )

        return {
            "ok": True,
            "query_mark": mark_name,
            "target_nice_class": class_key,
            "highest_similarity_score": highest_score,
            "overall_conflict_risk": "HIGH" if has_high_risk else ("MEDIUM" if highest_score >= 0.50 else "LOW"),
            "legal_assessment": assessment,
            "matches_count": len(top_matches),
            "top_similar_marks": top_matches,
            "regulatory_framework": "Article 74 Law on Intellectual Property (Distinctiveness of Marks)",
        }

    # -----------------------------------------------------------------------
    # Patent Specification & Claims Synthesis
    # -----------------------------------------------------------------------

    def draft_patent_specification(
        self,
        title: str,
        technical_field: str,
        applicant_name: str = "Tổ chức Nghiên cứu Mekong",
        independent_claims: int = 1,
        dependent_claims: int = 2,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Draft a complete statutory patent specification and claims under Article 102 Law on IP."""
        patent_id = f"PAT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        claims: list[dict[str, str]] = []
        for i in range(1, independent_claims + 1):
            claims.append(
                {
                    "claim_number": str(i),
                    "type": "INDEPENDENT",
                    "text": (
                        f"1. Phương pháp {title.lower()} trong {technical_field.lower()}, đặc trưng bởi các bước: "
                        f"a) Thu thập và chuẩn hóa dữ liệu đầu vào qua pipeline xử lý phân tán; "
                        f"b) Thực thi thuật toán tối ưu hóa đa mục tiêu với độ trễ thấp; "
                        f"c) Xác thực tính hợp lệ của kết quả đầu ra theo cơ chế kiểm chứng bất biến."
                    ),
                }
            )

        for j in range(1, dependent_claims + 1):
            claim_idx = independent_claims + j
            claims.append(
                {
                    "claim_number": str(claim_idx),
                    "type": "DEPENDENT",
                    "text": (
                        f"{claim_idx}. Phương pháp theo điểm 1, trong đó bước b) được thực thi "
                        f"thông qua mạng nơ-ron học sâu tích hợp cơ chế tự phục hồi (self-healing resilience)."
                    ),
                }
            )

        total_claims = independent_claims + dependent_claims
        official_fees = (
            STATUTORY_FEES_VND["PAT_FILING_FEE"]
            + STATUTORY_FEES_VND["PAT_PUBLICATION_FEE"]
            + (independent_claims * STATUTORY_FEES_VND["PAT_SEARCH_FEE_PER_CLAIM"])
            + (independent_claims * STATUTORY_FEES_VND["PAT_EXAMINATION_FEE_PER_CLAIM"])
        )

        specification = {
            "ok": True,
            "patent_id": patent_id,
            "title": title.strip(),
            "technical_field": technical_field.strip(),
            "applicant_name": applicant_name.strip(),
            "status": "DRAFT_SPECIFICATION_READY",
            "filing_date": now.strftime("%Y-%m-%d"),
            "sections": {
                "field_of_invention": f"Sáng chế này đề cập đến lĩnh vực {technical_field}, cụ thể là {title}.",
                "background_art": "Các giải pháp hiện hành trong ngành còn hạn chế về độ tin cậy, chi phí tính toán cao và chưa có khả năng tự động thích ứng với môi trường phân tán.",
                "summary_of_invention": f"Mục đích của sáng chế là cung cấp {title} nhằm khắc phục hoàn toàn các nhược điểm trên, nâng cao hiệu năng và đảm bảo tính khả thi công nghiệp.",
                "detailed_description": "Mô tả chi tiết cấu trúc hệ thống, quy trình thuật toán và ví dụ triển khai thực tế trên phần cứng tối ưu.",
            },
            "claims": claims,
            "total_claims_count": total_claims,
            "official_fee_vnd": official_fees,
            "statutory_requirements": [
                "Tính mới (Novelty): Chưa bị bộc lộ công khai trên thế giới trước ngày nộp đơn (Điều 60).",
                "Trình độ sáng tạo (Inventive Step): Không thể tạo ra một cách hiển nhiên bởi người có hiểu biết trung bình (Điều 61).",
                "Khả năng áp dụng công nghiệp (Industrial Applicability): Có thể thực hiện chế tạo hoặc áp dụng lặp lại (Điều 62).",
            ],
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO patents (
                        patent_id, title, technical_field, applicant_name,
                        claims_count, claims_text, status, filing_date, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        patent_id,
                        title.strip(),
                        technical_field.strip(),
                        applicant_name.strip(),
                        total_claims,
                        json.dumps(claims, ensure_ascii=False),
                        "DRAFT_SPECIFICATION_READY",
                        now.strftime("%Y-%m-%d"),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return specification

    # -----------------------------------------------------------------------
    # Software Copyright Registration (Decree 17/2023/NĐ-CP)
    # -----------------------------------------------------------------------

    def register_software_copyright(
        self,
        software_name: str,
        author_name: str,
        version: str = "1.0.0",
        repository_url: str = "",
        lines_of_code: int = 10000,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Synthesize software copyright registration dossier under Decree 17/2023/ND-CP."""
        copyright_id = f"COPY-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        dossier = {
            "ok": True,
            "copyright_id": copyright_id,
            "software_name": software_name.strip(),
            "author_name": author_name.strip(),
            "version": version.strip(),
            "lines_of_code": lines_of_code,
            "repository_url": repository_url.strip() or "Internal Secured VCS",
            "statutory_authority": "Cục Bản quyền tác giả (Bộ Văn hóa, Thể thao và Du lịch)",
            "official_fee_vnd": STATUTORY_FEES_VND["COPYRIGHT_SOFTWARE_FEE"],
            "required_dossier_items": [
                "Tờ khai đăng ký quyền tác giả tác phẩm phần mềm máy tính (Mẫu số 01 NĐ 17/2023/NĐ-CP).",
                "02 bản đĩa CD/DVD hoặc USB chứa mã nguồn (Source Code) và bản cài đặt hoàn chỉnh.",
                "02 bản in giấy chứa toàn bộ giao diện phần mềm và 25 trang đầu, 25 trang cuối mã nguồn.",
                "Văn bản cam đoan của tác giả về việc tự sáng tạo tác phẩm, không sao chép.",
                "Văn bản giao nhiệm vụ hoặc hợp đồng thuê sáng tạo (nếu tác giả thuộc doanh nghiệp).",
            ],
            "timeline": "15 ngày làm việc kể từ ngày nhận đủ hồ sơ hợp lệ để cấp Giấy chứng nhận.",
            "status": "DOSSIER_COMPILED",
            "registered_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO software_copyrights (
                        copyright_id, software_name, author_name, version,
                        lines_of_code, repository_url, status, registered_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        copyright_id,
                        software_name.strip(),
                        author_name.strip(),
                        version.strip(),
                        lines_of_code,
                        repository_url.strip(),
                        "DOSSIER_COMPILED",
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return dossier

    # -----------------------------------------------------------------------
    # Statutory Fees Calculator (Thông tư 263/2016/TT-BTC)
    # -----------------------------------------------------------------------

    def calculate_statutory_fees(
        self,
        trademark_classes: int = 1,
        patent_claims: int = 1,
        software_copyrights: int = 1,
    ) -> dict[str, typing.Any]:
        """Calculate itemized official state fees for IP registration under Circular 263/2016/TT-BTC."""
        tm_cost = (
            STATUTORY_FEES_VND["TM_FILING_FEE"]
            + STATUTORY_FEES_VND["TM_PUBLICATION_FEE"]
            + (trademark_classes * STATUTORY_FEES_VND["TM_SEARCH_FEE_PER_CLASS"])
            + (trademark_classes * STATUTORY_FEES_VND["TM_EXAMINATION_FEE_PER_CLASS"])
        )

        pat_cost = (
            STATUTORY_FEES_VND["PAT_FILING_FEE"]
            + STATUTORY_FEES_VND["PAT_PUBLICATION_FEE"]
            + (patent_claims * STATUTORY_FEES_VND["PAT_SEARCH_FEE_PER_CLAIM"])
            + (patent_claims * STATUTORY_FEES_VND["PAT_EXAMINATION_FEE_PER_CLAIM"])
        )

        copy_cost = software_copyrights * STATUTORY_FEES_VND["COPYRIGHT_SOFTWARE_FEE"]
        total = tm_cost + pat_cost + copy_cost

        return {
            "ok": True,
            "trademark_fees_vnd": tm_cost,
            "trademark_classes_count": trademark_classes,
            "patent_fees_vnd": pat_cost,
            "patent_claims_count": patent_claims,
            "software_copyright_fees_vnd": copy_cost,
            "software_copyrights_count": software_copyrights,
            "total_official_fees_vnd": total,
            "regulatory_framework": "Thông tư 263/2016/TT-BTC về phí và lệ phí sở hữu công nghiệp",
        }

    # -----------------------------------------------------------------------
    # Portfolio & Telemetry
    # -----------------------------------------------------------------------

    def list_portfolio(self, limit: int = 50) -> dict[str, typing.Any]:
        """Query complete IP portfolio across trademarks, patents, and software copyrights."""
        with self._get_connection() as conn:
            tm_rows = conn.execute("SELECT * FROM trademarks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            pat_rows = conn.execute("SELECT * FROM patents ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            copy_rows = conn.execute("SELECT * FROM software_copyrights ORDER BY registered_at DESC LIMIT ?", (limit,)).fetchall()

        return {
            "ok": True,
            "trademarks": [dict(r) for r in tm_rows],
            "patents": [dict(r) for r in pat_rows],
            "software_copyrights": [dict(r) for r in copy_rows],
            "totals": {
                "trademarks_count": len(tm_rows),
                "patents_count": len(pat_rows),
                "software_copyrights_count": len(copy_rows),
            },
        }

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated IP statistics, Nice classes, and legal framework."""
        with self._get_connection() as conn:
            tm_cnt = conn.execute("SELECT COUNT(*) as c FROM trademarks").fetchone()["c"]
            pat_cnt = conn.execute("SELECT COUNT(*) as c FROM patents").fetchone()["c"]
            copy_cnt = conn.execute("SELECT COUNT(*) as c FROM software_copyrights").fetchone()["c"]

        return {
            "ok": True,
            "status": "operational",
            "engine": "IPEngine",
            "regulatory_framework": "Luật Sở hữu trí tuệ 2005 (sửa đổi 2022) / NĐ 65/2023/NĐ-CP / NĐ 17/2023/NĐ-CP",
            "nice_classification_version": "Nice Classification 12-2024",
            "metrics": {
                "registered_trademarks": tm_cnt,
                "drafted_patents": pat_cnt,
                "software_copyrights": copy_cnt,
                "supported_nice_classes": len(NICE_CLASSES),
            },
            "database": str(self.db_path),
        }


IPEngine = IpEngine

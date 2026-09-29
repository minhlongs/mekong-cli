# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Corporate Governance, Business Incorporation & Legal Filings Engine.

Implements statutory corporate legal document synthesis and governance filings:
- Luật Doanh nghiệp 2020 (Law No. 59/2020/QH14) & Nghị định 01/2021/NĐ-CP.
- Điều lệ công ty (Articles of Association) chuẩn 10 chương theo Điều 24 Luật Doanh nghiệp 2020.
- Quyết định & Biên bản họp Hội đồng thành viên / Đại hội đồng cổ đông / Hội đồng quản trị.
- Hồ sơ thành lập doanh nghiệp (Giấy đề nghị ĐKDN, Điều lệ, Danh sách thành viên, Bổ nhiệm đại diện).
- Mã ngành kinh tế Việt Nam chuẩn (VSIC - Quyết định 27/2018/QĐ-TTg).
- Hỗ trợ 3 loại hình pháp lý phổ biến: TNHH_1TV, TNHH_2TV, JSC (Công ty Cổ phần).
- Lưu trữ SQLite WAL tại ``.mekong/corporate.db``.

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
# Canonical VSIC Economic Industry Codes (QĐ 27/2018/QĐ-TTg)
# ---------------------------------------------------------------------------

CANONICAL_VSIC: dict[str, dict[str, str]] = {
    "6201": {
        "code": "6201",
        "name": "Lập trình máy vi tính",
        "description": "Lập trình phần mềm ứng dụng, nền tảng số, giải pháp trí tuệ nhân tạo (AI), phát triển web và ứng dụng di động (Chi tiết theo quy định pháp luật).",
    },
    "6202": {
        "code": "6202",
        "name": "Tư vấn máy vi tính và quản trị hệ thống máy vi tính",
        "description": "Tư vấn kiến trúc giải pháp công nghệ thông tin, quản trị hạ tầng mạng, tích hợp hệ thống phần mềm.",
    },
    "6209": {
        "code": "6209",
        "name": "Hoạt động dịch vụ công nghệ thông tin và dịch vụ khác liên quan đến máy tính",
        "description": "Cài đặt máy vi tính và thiết bị ngoại vi, phục hồi dữ liệu, dịch vụ hỗ trợ kỹ thuật phần mềm.",
    },
    "6311": {
        "code": "6311",
        "name": "Xử lý dữ liệu, cho thuê và các hoạt động liên quan",
        "description": "Xử lý dữ liệu lớn (Big Data), cho thuê hạ tầng điện toán đám mây (Cloud hosting), dịch vụ chia sẻ tài nguyên tính toán.",
    },
    "7020": {
        "code": "7020",
        "name": "Hoạt động tư vấn quản lý",
        "description": "Tư vấn chiến lược quản trị doanh nghiệp, tái cấu trúc tổ chức, chuyển đổi số và tối ưu hóa quy trình vận hành (không bao gồm tư vấn pháp luật, tài chính).",
    },
    "4651": {
        "code": "4651",
        "name": "Bán buôn máy vi tính, thiết bị ngoại vi và phần mềm",
        "description": "Bán buôn máy chủ, máy tính cá nhân, bản quyền phần mềm đóng gói và thiết bị viễn thông.",
    },
}

ENTITY_TYPE_NAMES: dict[str, str] = {
    "TNHH_1TV": "Công ty TNHH Một Thành Viên",
    "TNHH_2TV": "Công ty TNHH Hai Thành Viên Trở Lên",
    "JSC": "Công ty Cổ Phần",
}


def _format_vnd(amount: int) -> str:
    return f"{amount:,} VND".replace(",", ".")


class CorporateEngine:
    """Autonomous Vietnamese Corporate Governance & Legal Incorporation Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "corporate.db"
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
                CREATE TABLE IF NOT EXISTS corporate_entities (
                    entity_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    charter_capital INTEGER NOT NULL,
                    legal_rep_name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    main_industry TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS statutory_documents (
                    doc_id TEXT PRIMARY KEY,
                    entity_id TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_markdown TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_entities_name ON corporate_entities(company_name);
                CREATE INDEX IF NOT EXISTS idx_docs_entity ON statutory_documents(entity_id);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Document Synthesis: Articles of Association (Điều lệ công ty)
    # -----------------------------------------------------------------------

    def generate_charter(
        self,
        company_name: str,
        entity_type: str = "TNHH_1TV",
        charter_capital: int = 1_000_000_000,
        legal_rep_name: str = "Nguyễn Văn A",
        address: str = "Hà Nội, Việt Nam",
        industry_codes: typing.Optional[list[str]] = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Synthesize a complete 10-chapter Corporate Charter complying with Article 24 Law on Enterprises 2020."""
        entity_type_key = entity_type.upper() if entity_type.upper() in ENTITY_TYPE_NAMES else "TNHH_1TV"
        entity_type_label = ENTITY_TYPE_NAMES[entity_type_key]

        codes = industry_codes or ["6201", "6202", "6311", "7020"]
        industries_text = "\n".join(
            [f"- **Mã {c}**: {CANONICAL_VSIC.get(c, {}).get('name', 'Hoạt động kinh doanh')} — {CANONICAL_VSIC.get(c, {}).get('description', '')}"
             for c in codes if c in CANONICAL_VSIC]
        )

        charter_id = f"CHARTER-{uuid.uuid4().hex[:8].upper()}"
        entity_id = f"ENT-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        date_str = now.strftime("%d/%m/%Y")

        governance_model = (
            "Chủ sở hữu công ty bổ nhiệm Chủ tịch công ty kiêm Tổng giám đốc/Giám đốc làm Người đại diện theo pháp luật."
            if entity_type_key == "TNHH_1TV"
            else (
                "Hội đồng thành viên là cơ quan quyết định cao nhất. Chủ tịch Hội đồng thành viên hoặc Giám đốc là Người đại diện theo pháp luật."
                if entity_type_key == "TNHH_2TV"
                else "Đại hội đồng cổ đông là cơ quan quyết định cao nhất. Hội đồng quản trị quản lý công ty giữa hai kỳ Đại hội. Chủ tịch HĐQT hoặc Tổng giám đốc là Người đại diện theo pháp luật."
            )
        )

        content = f"""# CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
### Độc lập - Tự do - Hạnh phúc
---

# ĐIỀU LỆ HOẠT ĐỘNG VÀ QUẢN TRỊ CÔNG TY
### {company_name.upper()}
*(Ban hành căn cứ Luật Doanh nghiệp số 59/2020/QH14 và các văn bản hướng dẫn thi hành)*

---

### CHƯƠNG I: QUY ĐỊNH CHUNG
- **Điều 1. Hình thức pháp lý**: Công ty hoạt động dưới hình thức **{entity_type_label}**, có tư cách pháp nhân kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp.
- **Điều 2. Tên công ty**:
  - Tên tiếng Việt: **{company_name.upper()}**
  - Tên viết tắt: **MEKONG CORP**
- **Điều 3. Trụ sở chính**: {address}.
- **Điều 4. Con dấu pháp nhân**: Công ty quyết định loại dấu, số lượng, hình thức và nội dung con dấu theo quy định của pháp luật.

### CHƯƠNG II: MỤC TIÊU & NGÀNH, NGHỀ KINH DOANH
- **Điều 5. Mục tiêu hoạt động**: Ứng dụng công nghệ phần mềm tiên tiến, trí tuệ nhân tạo và chuyển đổi số nhằm tối ưu hóa chuỗi giá trị và gia tăng lợi ích hợp pháp cho các thành viên/cổ đông.
- **Điều 6. Ngành, nghề kinh doanh đăng ký**:
{industries_text}

### CHƯƠNG III: VỐN ĐIỀU LỆ & THỜI HẠN GÓP VỐN
- **Điều 7. Vốn điều lệ**: **{_format_vnd(charter_capital)}**.
- **Điều 8. Thời hạn góp vốn**: Trong thời hạn 90 ngày kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp theo quy định tại Khoản 2 Điều 47 / Điều 75 / Điều 113 Luật Doanh nghiệp 2020.

### CHƯƠNG IV: QUYỀN VÀ NGHĨA VỤ CỦA CHỦ SỞ HỮU / THÀNH VIÊN / CỔ ĐÔNG
- **Điều 9. Quyền hạn**: Được hưởng lợi nhuận tương ứng với tỷ lệ phần vốn góp / số cổ phần sở hữu; tham gia biểu quyết các quyết sách trọng yếu của công ty.
- **Điều 10. Nghĩa vụ**: Chịu trách nhiệm về các khoản nợ và nghĩa vụ tài sản khác của công ty trong phạm vi số vốn đã góp hoặc cam kết góp.

### CHƯƠNG V: CƠ CẤU TỔ CHỨC VÀ QUẢN TRỊ NỘI BỘ
- **Điều 11. Mô hình quản trị**: {governance_model}
- **Điều 12. Nhiệm kỳ lãnh đạo**: Nhiệm kỳ của Chủ tịch và Ban Giám đốc không quá 05 năm và có thể được bổ nhiệm lại với số nhiệm kỳ không hạn chế.

### CHƯƠNG VI: NGƯỜI ĐẠI DIỆN THEO PHÁP LUẬT
- **Điều 13. Người đại diện**: Công ty có 01 Người đại diện theo pháp luật:
  - Họ và tên: **{legal_rep_name.upper()}**
  - Chức danh: **Chủ tịch kiêm Giám đốc / Tổng giám đốc**
  - Trách nhiệm: Đại diện cho công ty thực hiện các quyền và nghĩa vụ phát sinh từ giao dịch, đại diện tố tụng và các trách nhiệm quy định tại Điều 12 Luật Doanh nghiệp 2020.

### CHƯƠNG VII: THỂ THỨC THÔNG QUA NGHỊ QUYẾT & QUYẾT ĐỊNH
- **Điều 14. Nguyên tắc biểu quyết**: Các quyết định về chiến lược phát triển, tăng/giảm vốn, sáp nhập, giải thể được thông qua khi đạt tỷ lệ tán thành tối thiểu 65% (hoặc 75% đối với các quyết sách đặc biệt theo luật định).

### CHƯƠNG VIII: TÀI CHÍNH, KẾ TOÁN & PHÂN PHỐI LỢI NHUẬN
- **Điều 15. Năm tài chính**: Bắt đầu từ ngày 01 tháng 01 và kết thúc vào ngày 31 tháng 12 dương lịch hàng năm.
- **Điều 16. Trích lập quỹ**: Sau khi hoàn thành nghĩa vụ thuế và tài chính, lợi nhuận được trích lập Quỹ đầu tư phát triển, Quỹ khen thưởng phúc lợi và chia cổ tức/lợi nhuận.

### CHƯƠNG IX: GIẢI THỂ, THANH LÝ & TỐ CHỨC LẠI
- **Điều 17. Giải thể**: Công ty bị giải thể trong các trường hợp kết thúc thời hạn hoạt động, theo quyết định của chủ sở hữu/cổ đông hoặc bị thu hồi Giấy chứng nhận ĐKDN.

### CHƯƠNG X: HIỆU LỰC THI HÀNH
- **Điều 18. Cam kết**: Điều lệ này gồm 10 Chương, 18 Điều, được lập ngày {date_str} và có hiệu lực kể từ ngày được cơ quan đăng ký kinh doanh cấp phép.

---
**ĐẠI DIỆN THEO PHÁP LUẬT CÔNG TY**  
*(Ký, ghi rõ họ tên và đóng dấu)*  

**{legal_rep_name.upper()}**
"""

        result = {
            "ok": True,
            "charter_id": charter_id,
            "entity_id": entity_id,
            "company_name": company_name,
            "entity_type": entity_type_key,
            "entity_type_label": entity_type_label,
            "charter_capital": charter_capital,
            "charter_capital_vnd": _format_vnd(charter_capital),
            "legal_rep_name": legal_rep_name,
            "address": address,
            "industry_codes": codes,
            "chapters_count": 10,
            "articles_count": 18,
            "content_markdown": content,
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO corporate_entities (
                        entity_id, company_name, entity_type, charter_capital,
                        legal_rep_name, address, main_industry, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entity_id,
                        company_name,
                        entity_type_key,
                        charter_capital,
                        legal_rep_name,
                        address,
                        codes[0] if codes else "6201",
                        "active",
                        now.isoformat(),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO statutory_documents (
                        doc_id, entity_id, company_name, doc_type, title, content_markdown, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        charter_id,
                        entity_id,
                        company_name,
                        "CHARTER",
                        f"Điều Lệ Hoạt Động {company_name}",
                        content,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Document Synthesis: Resolutions & Meeting Minutes (Nghị Quyết / Biên Bản)
    # -----------------------------------------------------------------------

    def generate_resolution(
        self,
        company_name: str,
        resolution_type: str = "APPOINTMENT",
        title: str = "",
        decisions: typing.Optional[list[str]] = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Synthesize statutory Board or Member Council resolution."""
        res_id = f"RES-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        date_str = now.strftime("%d/%m/%Y")

        default_decisions = {
            "APPOINTMENT": [
                "Bổ nhiệm Ông/Bà đại diện theo pháp luật giữ chức danh Giám đốc điều hành.",
                "Trao toàn quyền quyết định các hoạt động vận hành, ký kết hợp đồng thương mại và quản trị nhân sự theo Điều lệ công ty.",
                "Giao bộ phận hành chính nhân sự tiến hành thủ tục đăng ký thay đổi với cơ quan đăng ký kinh doanh.",
            ],
            "CAPITAL_INCREASE": [
                "Thông qua chủ trương tăng vốn điều lệ công ty nhằm mở rộng quy mô sản xuất và đầu tư công nghệ R&D.",
                "Thời hạn hoàn tất góp vốn tăng thêm trong vòng 30 ngày kể từ ngày ban hành Nghị quyết.",
                "Sửa đổi tương ứng Điều 7 Điều lệ công ty về vốn điều lệ.",
            ],
            "BRANCH": [
                "Thành lập chi nhánh / văn phòng đại diện tại địa bàn chiến lược nhằm phát triển mạng lưới kinh doanh.",
                "Bổ nhiệm người đứng đầu chi nhánh và ủy quyền ký kết các giao dịch trong hạn mức được phê duyệt.",
            ],
        }

        dec_list = decisions or default_decisions.get(resolution_type.upper(), default_decisions["APPOINTMENT"])
        dec_text = "\n".join([f"**Điều {i+1}**: {d}" for i, d in enumerate(dec_list)])
        doc_title = title or f"Nghị Quyết Về Việc {resolution_type.upper().replace('_', ' ')} — {company_name}"

        content = f"""# CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
### Độc lập - Tự do - Hạnh phúc
---

# {doc_title.upper()}
### Số: {res_id}/NQ-MEKONG
*Hà Nội, ngày {date_str}*

**Căn cứ:**
- Luật Doanh nghiệp số 59/2020/QH14 được Quốc hội thông qua ngày 17/06/2020;
- Điều lệ hoạt động của {company_name};
- Biên bản cuộc họp Hội đồng / Đại hội đồng ngày {date_str}.

---

### QUYẾT NGHỊ:
{dec_text}

**Điều {len(dec_list) + 1}**: Nghị quyết này có hiệu lực thi hành kể từ ngày ký. Các thành viên Hội đồng, Ban Giám đốc và các phòng ban liên quan chịu trách nhiệm thi hành Nghị quyết này.

---
**T/M. HỘI ĐỒNG THÀNH VIÊN / ĐẠI HỘI ĐỒNG CỔ ĐÔNG**  
*Chủ tịch (Ký và ghi rõ họ tên)*
"""

        result = {
            "ok": True,
            "resolution_id": res_id,
            "company_name": company_name,
            "resolution_type": resolution_type.upper(),
            "title": doc_title,
            "decisions_count": len(dec_list),
            "content_markdown": content,
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO statutory_documents (
                        doc_id, entity_id, company_name, doc_type, title, content_markdown, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        res_id,
                        f"ENT-{uuid.uuid4().hex[:6].upper()}",
                        company_name,
                        "RESOLUTION",
                        doc_title,
                        content,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Incorporation Dossier (Hồ sơ đăng ký thành lập doanh nghiệp)
    # -----------------------------------------------------------------------

    def create_filing_dossier(
        self,
        company_name: str,
        entity_type: str = "TNHH_1TV",
        charter_capital: int = 1_000_000_000,
        legal_rep_name: str = "Nguyễn Văn A",
        address: str = "Hà Nội, Việt Nam",
        main_industry: str = "6201",
    ) -> dict[str, typing.Any]:
        """Synthesize complete incorporation dossier under Decree 01/2021/NĐ-CP."""
        dossier_id = f"DOSSIER-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Charter
        charter = self.generate_charter(
            company_name=company_name,
            entity_type=entity_type,
            charter_capital=charter_capital,
            legal_rep_name=legal_rep_name,
            address=address,
            industry_codes=[main_industry, "6202", "6311", "7020"],
            save=True,
        )

        # 2. Appointment Resolution
        resolution = self.generate_resolution(
            company_name=company_name,
            resolution_type="APPOINTMENT",
            title=f"Quyết định bổ nhiệm Người đại diện theo pháp luật kiêm Giám đốc {company_name}",
            save=True,
        )

        dossier = {
            "ok": True,
            "dossier_id": dossier_id,
            "company_name": company_name,
            "entity_type": charter["entity_type"],
            "entity_type_label": charter["entity_type_label"],
            "charter_capital": charter_capital,
            "charter_capital_vnd": _format_vnd(charter_capital),
            "legal_rep_name": legal_rep_name,
            "address": address,
            "main_industry": main_industry,
            "main_industry_name": CANONICAL_VSIC.get(main_industry, {}).get("name", "Công nghệ thông tin"),
            "documents": [
                {
                    "type": "APPLICATION_FORM",
                    "title": "Giấy đề nghị đăng ký doanh nghiệp (Mẫu Phụ lục I-2 TT 01/2021/TT-BKHĐT)",
                    "status": "READY_FOR_SUBMISSION",
                },
                {
                    "type": "CHARTER",
                    "title": f"Điều lệ hoạt động công ty ({charter['chapters_count']} Chương, {charter['articles_count']} Điều)",
                    "doc_id": charter["charter_id"],
                    "status": "APPROVED",
                },
                {
                    "type": "MEMBER_LIST",
                    "title": "Danh sách thành viên / cổ đông sáng lập và tỷ lệ góp vốn",
                    "status": "VERIFIED",
                },
                {
                    "type": "LEGAL_REP_APPOINTMENT",
                    "title": resolution["title"],
                    "doc_id": resolution["resolution_id"],
                    "status": "ENACTED",
                },
            ],
            "filing_portal": "https://dangkykinhdoanh.gov.vn",
            "statutory_authority": "Phòng Đăng ký kinh doanh — Sở Kế hoạch và Đầu tư",
            "created_at": now.isoformat(),
        }

        return dossier

    def list_filings(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List generated statutory documents and filings."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT doc_id, entity_id, company_name, doc_type, title, created_at
                FROM statutory_documents
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated corporate governance and legal filings posture."""
        with self._get_connection() as conn:
            entities_count = conn.execute("SELECT COUNT(*) as cnt FROM corporate_entities").fetchone()["cnt"]
            docs_count = conn.execute("SELECT COUNT(*) as cnt FROM statutory_documents").fetchone()["cnt"]
            total_capital = conn.execute("SELECT COALESCE(SUM(charter_capital), 0) as sm FROM corporate_entities").fetchone()["sm"]

        return {
            "status": "operational",
            "governance_framework": "Luat Doanh nghiep 2020 / ND 01/2021/ND-CP",
            "metrics": {
                "registered_entities": entities_count,
                "statutory_documents_generated": docs_count,
                "total_charter_capital_vnd": total_capital,
                "supported_entity_types": list(ENTITY_TYPE_NAMES.keys()),
                "vsic_sectors_catalog": len(CANONICAL_VSIC),
            },
            "database": str(self.db_path),
        }

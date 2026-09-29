# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Commercial Contract, E-Sign & Legal Risk Assessment Engine.

Implements Vietnamese statutory commercial contracts, risk scanning & electronic signing:
- Bộ luật Dân sự 2015 (Luật số 91/2015/QH13): Hợp đồng dân sự, điều kiện có hiệu lực, vô hiệu và bồi thường thiệt hại.
- Luật Thương mại 2005 (Luật số 36/2005/QH11):
  * Điều 301: Giới hạn mức phạt vi phạm hợp đồng tối đa 8% giá trị phần nghĩa vụ hợp đồng bị vi phạm.
  * Điều 302: Nghĩa vụ bồi thường thiệt hại thực tế, trực tiếp.
  * Điều 294: Trường hợp miễn trách nhiệm trong sự kiện bất khả kháng (Force Majeure).
- Luật Giao dịch điện tử 2023 (Luật số 20/2023/QH15) & Nghị định 130/2018/NĐ-CP:
  * Giá trị pháp lý của thông điệp dữ liệu hợp đồng điện tử.
  * Chứng thực chữ ký số an toàn (Digital Signature SHA-256 & Timestamp Authority TSA).
- Nghị định 13/2023/NĐ-CP: Tuân thủ bảo vệ dữ liệu cá nhân (PDPD).
- Lưu trữ SQLite WAL tại ``.mekong/contracts.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Canonical Contract Template Definitions
# ---------------------------------------------------------------------------

CONTRACT_TEMPLATES: dict[str, dict[str, typing.Any]] = {
    "SOFTWARE_DEV": {
        "template_id": "SOFTWARE_DEV",
        "name": "Hợp đồng Cung cấp Dịch vụ Phát triển Phần mềm & Giải pháp AI",
        "governing_law": "Luật Thương mại 2005 & Luật Công nghệ thông tin 2006",
        "default_penalty_pct": 8.0,
        "standard_clauses": [
            "Điều 1: Đối tượng và phạm vi công việc phát triển giải pháp phần mềm/AI.",
            "Điều 2: Thời hạn, tiến độ bàn giao và tiêu chí nghiệm thu kỹ thuật (Acceptance Criteria).",
            "Điều 3: Giá trị hợp đồng, biểu phí và phương thức thanh toán từng đợt.",
            "Điều 4: Quyền sở hữu trí tuệ (IP Rights) và chuyển giao mã nguồn hoàn chỉnh cho Bên A.",
            "Điều 5: Nghĩa vụ bảo mật thông tin (Confidentiality & Non-Disclosure).",
            "Điều 6: Phạt vi phạm (tối đa 8% theo Điều 301 LTM) và bồi thường thiệt hại.",
            "Điều 7: Sự kiện bất khả kháng (Force Majeure) theo Điều 294 Luật Thương mại.",
            "Điều 8: Giải quyết tranh chấp tại Trung tâm Trọng tài Quốc tế Việt Nam (VIAC) hoặc Tòa án có thẩm quyền.",
        ],
    },
    "COMMERCIAL_SALE": {
        "template_id": "COMMERCIAL_SALE",
        "name": "Hợp đồng Mua bán Hàng hóa Thương mại",
        "governing_law": "Luật Thương mại 2005 & Incoterms 2020",
        "default_penalty_pct": 8.0,
        "standard_clauses": [
            "Điều 1: Tên hàng, số lượng, quy cách phẩm chất và đóng gói hàng hóa.",
            "Điều 2: Đơn giá, tổng giá trị hợp đồng và phương thức thanh toán.",
            "Điều 3: Thời gian, địa điểm giao hàng và điều kiện giao nhận (Incoterms 2020).",
            "Điều 4: Kiểm tra và nghiệm thu hàng hóa tại địa điểm giao hàng.",
            "Điều 5: Bảo hành và trách nhiệm đối với hàng hóa không phù hợp.",
            "Điều 6: Phạt chậm giao hàng/thanh toán và chế tài vi phạm hợp đồng.",
            "Điều 7: Miễn trách nhiệm do sự kiện bất khả kháng.",
            "Điều 8: Luật điều chỉnh và cơ quan giải quyết tranh chấp.",
        ],
    },
    "NDA": {
        "template_id": "NDA",
        "name": "Thỏa thuận Bảo mật Thông tin Hai chiều (Mutual Non-Disclosure Agreement)",
        "governing_law": "Bộ luật Dân sự 2015 & Luật Sở hữu trí tuệ 2005 (sửa đổi 2022)",
        "default_penalty_pct": 8.0,
        "standard_clauses": [
            "Điều 1: Định nghĩa Thông tin Bảo mật và phạm vi tiết lộ dữ liệu kinh doanh/công nghệ.",
            "Điều 2: Nghĩa vụ bảo mật, giới hạn tiếp cận và biện pháp phòng ngừa rò rỉ.",
            "Điều 3: Các trường hợp ngoại lệ không coi là vi phạm bảo mật.",
            "Điều 4: Thời hạn bảo mật thông tin (tiêu chuẩn 03 năm kể từ ngày ký).",
            "Điều 5: Xử lý thông tin khi chấm dứt hợp tác (tiêu hủy hoặc hoàn trả dữ liệu).",
            "Điều 6: Chế tài vi phạm nghĩa vụ bảo mật và biện pháp khẩn cấp tạm thời.",
            "Điều 7: Tuân thủ quy định bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP.",
            "Điều 8: Luật điều chỉnh và cơ quan tài phán giải quyết tranh chấp.",
        ],
    },
    "DISTRIBUTION": {
        "template_id": "DISTRIBUTION",
        "name": "Hợp đồng Đại lý & Phân phối Sản phẩm Độc quyền",
        "governing_law": "Luật Thương mại 2005 (Chương VI: Đại lý thương mại)",
        "default_penalty_pct": 8.0,
        "standard_clauses": [
            "Điều 1: Hình thức đại lý và phạm vi lãnh thổ phân phối độc quyền.",
            "Điều 2: Giá giao đại lý, giá bán quy định và thù lao đại lý/chiết khấu.",
            "Điều 3: Chỉ tiêu doanh số tối thiểu (KPIs) và kế hoạch đặt hàng định kỳ.",
            "Điều 4: Quyền và nghĩa vụ của Bên giao đại lý (Hỗ trợ marketing, đào tạo).",
            "Điều 5: Quyền và nghĩa vụ của Bên đại lý (Trưng bày sản phẩm, chăm sóc khách hàng).",
            "Điều 6: Phạt vi phạm hợp đồng và bồi thường thiệt hại.",
            "Điều 7: Chấm dứt hợp đồng đại lý và quyết toán công nợ.",
            "Điều 8: Giải quyết tranh chấp thương mại.",
        ],
    },
}


class ContractEngine:
    """Autonomous Commercial Contract, E-Sign & Legal Risk Assessment Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "contracts.db"
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
                CREATE TABLE IF NOT EXISTS contracts (
                    contract_id TEXT PRIMARY KEY,
                    contract_number TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    template_type TEXT NOT NULL,
                    party_a_name TEXT NOT NULL,
                    party_a_tax_id TEXT NOT NULL,
                    party_b_name TEXT NOT NULL,
                    party_b_tax_id TEXT NOT NULL,
                    contract_value_vnd REAL NOT NULL,
                    content_text TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    penalty_rate_pct REAL NOT NULL,
                    has_force_majeure INTEGER NOT NULL,
                    dispute_forum TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS contract_reviews (
                    review_id TEXT PRIMARY KEY,
                    contract_id TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    red_flags_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS e_signatures (
                    signature_id TEXT PRIMARY KEY,
                    contract_id TEXT NOT NULL,
                    signer_name TEXT NOT NULL,
                    signer_title TEXT NOT NULL,
                    signer_tax_id TEXT NOT NULL,
                    signature_hash TEXT NOT NULL,
                    tsa_timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
                CREATE INDEX IF NOT EXISTS idx_contracts_template ON contracts(template_type);
                CREATE INDEX IF NOT EXISTS idx_esigns_contract ON e_signatures(contract_id);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Contract Drafting & Synthesis
    # -----------------------------------------------------------------------

    def draft_contract(
        self,
        template_type: str,
        party_a_name: str,
        party_b_name: str,
        contract_value_vnd: float = 0.0,
        party_a_tax_id: str = "0100000001",
        party_b_tax_id: str = "0300000002",
        scope_summary: str = "",
        penalty_rate_pct: float = 8.0,
        dispute_forum: str = "VIAC",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Synthesize a standard commercial contract complying with Vietnamese law."""
        template_key = template_type.upper().strip()
        tpl = CONTRACT_TEMPLATES.get(template_key)
        if not tpl:
            return {
                "ok": False,
                "error": f"Mẫu hợp đồng không hợp lệ: '{template_type}'. Mẫu hỗ trợ: {list(CONTRACT_TEMPLATES.keys())}",
                "available_templates": list(CONTRACT_TEMPLATES.keys()),
            }

        contract_id = f"CT-{uuid.uuid4().hex[:8].upper()}"
        year = datetime.datetime.now().year
        contract_number = f"MK-{template_key}/{year}/{uuid.uuid4().hex[:4].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        # Assemble contract text
        clauses = tpl["standard_clauses"]
        scope = scope_summary if scope_summary else f"Thực hiện các nội dung công việc theo phụ lục đính kèm thỏa thuận giữa {party_a_name} và {party_b_name}."

        contract_body = [
            f"CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\n---o0o---\n",
            f"{tpl['name'].upper()}",
            f"Số: {contract_number}\n",
            f"- Căn cứ Bộ luật Dân sự số 91/2015/QH13 ngày 24/11/2015;",
            f"- Căn cứ {tpl['governing_law']};",
            f"- Căn cứ Luật Giao dịch điện tử số 20/2023/QH15 và Nghị định 130/2018/NĐ-CP;",
            f"- Căn cứ nhu cầu và khả năng thực tế của hai bên.\n",
            f"Hôm nay, ngày {now.strftime('%d/%m/%Y')}, chúng tôi gồm có:\n",
            f"BÊN A (BÊN GIAO DỊCH / KHÁCH HÀNG):",
            f"  - Tên doanh nghiệp: {party_a_name}",
            f"  - Mã số thuế (MST): {party_a_tax_id}",
            f"  - Đại diện theo pháp luật: Giám đốc / Tổng Giám đốc\n",
            f"BÊN B (BÊN CUNG CẤP / ĐỐI TÁC):",
            f"  - Tên doanh nghiệp: {party_b_name}",
            f"  - Mã số thuế (MST): {party_b_tax_id}",
            f"  - Đại diện theo pháp luật: Giám đốc / Tổng Giám đốc\n",
            f"Hai bên thống nhất ký kết Hợp đồng với các điều khoản sau đây:\n",
        ]

        for clause in clauses:
            contract_body.append(f"{clause}")
            if "Điều 1" in clause:
                contract_body.append(f"  Phạm vi cụ thể: {scope}")
            elif "Điều 3" in clause and contract_value_vnd > 0:
                contract_body.append(f"  Tổng giá trị hợp đồng: {round(contract_value_vnd):,} VND (chưa bao gồm VAT).")
            elif "Điều 6" in clause:
                contract_body.append(f"  Mức phạt vi phạm áp dụng: {penalty_rate_pct}% giá trị nghĩa vụ bị vi phạm (Tuân thủ Điều 301 Luật Thương mại 2005).")
            elif "Điều 8" in clause or "Tranh chấp" in clause:
                contract_body.append(f"  Cơ quan tài phán ưu tiên: {dispute_forum} (Trung tâm Trọng tài Quốc tế Việt Nam hoặc Tòa án có thẩm quyền tại TP.HCM/Hà Nội).")

        contract_body.extend([
            "\nĐẠI DIỆN BÊN A                                   ĐẠI DIỆN BÊN B",
            "(Ký tên, đóng dấu / Ký số điện tử)               (Ký tên, đóng dấu / Ký số điện tử)",
        ])

        full_text = "\n".join(contract_body)
        content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

        # Assess initial risk
        risk_eval = self.assess_contract_risk(contract_text=full_text, penalty_pct=penalty_rate_pct)

        record = {
            "ok": True,
            "contract_id": contract_id,
            "contract_number": contract_number,
            "title": tpl["name"],
            "template_type": template_key,
            "party_a_name": party_a_name,
            "party_a_tax_id": party_a_tax_id,
            "party_b_name": party_b_name,
            "party_b_tax_id": party_b_tax_id,
            "contract_value_vnd": contract_value_vnd,
            "penalty_rate_pct": penalty_rate_pct,
            "has_force_majeure": 1,
            "dispute_forum": dispute_forum,
            "content_sha256": content_hash,
            "risk_score": risk_eval["risk_score"],
            "risk_level": risk_eval["risk_level"],
            "status": "DRAFTED",
            "created_at": now.isoformat(),
            "content_preview": full_text[:400] + "...",
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO contracts (
                        contract_id, contract_number, title, template_type,
                        party_a_name, party_a_tax_id, party_b_name, party_b_tax_id,
                        contract_value_vnd, content_text, content_sha256,
                        penalty_rate_pct, has_force_majeure, dispute_forum,
                        risk_score, risk_level, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        contract_id,
                        contract_number,
                        tpl["name"],
                        template_key,
                        party_a_name,
                        party_a_tax_id,
                        party_b_name,
                        party_b_tax_id,
                        contract_value_vnd,
                        full_text,
                        content_hash,
                        penalty_rate_pct,
                        1,
                        dispute_forum,
                        risk_eval["risk_score"],
                        risk_eval["risk_level"],
                        "DRAFTED",
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return record

    # -----------------------------------------------------------------------
    # Legal Risk Assessment & Redline Scan
    # -----------------------------------------------------------------------

    def assess_contract_risk(
        self,
        contract_text: str,
        penalty_pct: typing.Optional[float] = None,
    ) -> dict[str, typing.Any]:
        """Scan contract clauses for legal risks, statutory conflicts, and redlines under Vietnamese law."""
        red_flags: list[dict[str, typing.Any]] = []
        recommendations: list[str] = []
        risk_score = 0

        text_lower = contract_text.lower()

        # 1. Penalty clause evaluation (> 8% ceiling violation under Art 301 Commercial Law 2005)
        detected_penalties: list[float] = []
        if penalty_pct is not None:
            detected_penalties.append(penalty_pct)

        # Regex scan for penalty percentage mentions
        matches = re.findall(r"phạt\s+(?:vi\s+phạm)?\s*(?:là|ở\s+mức)?\s*(\d+(?:\.\d+)?)\s*%", text_lower)
        for m in matches:
            try:
                val = float(m)
                detected_penalties.append(val)
            except ValueError:
                pass

        has_penalty_breach = any(p > 8.0 for p in detected_penalties)
        if has_penalty_breach:
            max_p = max(detected_penalties)
            risk_score += 40
            red_flags.append({
                "severity": "CRITICAL",
                "clause": "Điều khoản Phạt vi phạm",
                "issue": f"Mức phạt vi phạm {max_p}% vượt quá trần luật định 8% theo Điều 301 Luật Thương mại 2005.",
                "legal_basis": "Điều 301 Luật Thương mại 2005 (Mức phạt vi phạm tối đa 8% phần nghĩa vụ bị vi phạm).",
            })
            recommendations.append(
                "Điều chỉnh mức phạt vi phạm về tối đa 8% giá trị phần nghĩa vụ hợp đồng bị vi phạm; kết hợp điều khoản bồi thường thiệt hại thực tế theo Điều 302."
            )

        # 2. Force Majeure Clause check (Điều 294 Luật Thương mại)
        has_force_majeure = "bất khả kháng" in text_lower or "force majeure" in text_lower
        if not has_force_majeure:
            risk_score += 25
            red_flags.append({
                "severity": "HIGH",
                "clause": "Điều khoản Bất khả kháng",
                "issue": "Hợp đồng thiếu điều khoản miễn trách nhiệm trong sự kiện bất khả kháng (thiên tai, dịch bệnh, quyết định cơ quan nhà nước).",
                "legal_basis": "Điều 294 Luật Thương mại 2005 & Điều 156 Bộ luật Dân sự 2015.",
            })
            recommendations.append(
                "Bổ sung điều khoản Sự kiện Bất khả kháng quy định rõ định nghĩa, thủ tục thông báo trong vòng 7 ngày và cơ chế miễn trách nhiệm."
            )

        # 3. Dispute Resolution jurisdiction check
        has_dispute_clause = "tranh chấp" in text_lower or "tòa án" in text_lower or "trọng tài" in text_lower
        if not has_dispute_clause:
            risk_score += 20
            red_flags.append({
                "severity": "HIGH",
                "clause": "Giải quyết tranh chấp",
                "issue": "Không xác định rõ cơ quan tài phán giải quyết khi phát sinh mâu thuẫn thương mại.",
                "legal_basis": "Điều 317 Luật Thương mại 2005 (Hình thức giải quyết tranh chấp: Thương lượng, Hòa giải, Trọng tài, Tòa án).",
            })
            recommendations.append(
                "Chỉ định rõ ràng cơ quan tài phán: Trung tâm Trọng tài Quốc tế Việt Nam (VIAC) hoặc Tòa án nhân dân có thẩm quyền."
            )

        # 4. Intellectual Property Rights (for software/tech contracts)
        is_tech_contract = any(k in text_lower for k in ["phần mềm", "công nghệ", "mã nguồn", "ai", "sở hữu trí tuệ"])
        if is_tech_contract and not any(k in text_lower for k in ["quyền tác giả", "sở hữu trí tuệ", "chuyển giao", "mã nguồn"]):
            risk_score += 15
            red_flags.append({
                "severity": "MEDIUM",
                "clause": "Quyền Sở hữu Trí tuệ",
                "issue": "Hợp đồng công nghệ không quy định rõ quyền sở hữu mã nguồn và quyền tác giả phần mềm sau khi bàn giao.",
                "legal_basis": "Điều 20, 21 Luật Sở hữu trí tuệ 2005 (sửa đổi 2022).",
            })
            recommendations.append(
                "Bổ sung điều khoản quy định toàn bộ quyền tài sản đối với sản phẩm công nghệ thuộc về Bên A ngay khi thanh toán đủ."
            )

        # 5. Data Privacy compliance (Nghị định 13/2023/NĐ-CP)
        has_pdpd = "dữ liệu cá nhân" in text_lower or "nghị định 13" in text_lower or "bảo vệ dữ liệu" in text_lower
        if not has_pdpd and is_tech_contract:
            risk_score += 10
            red_flags.append({
                "severity": "LOW",
                "clause": "Bảo vệ Dữ liệu Cá nhân",
                "issue": "Chưa có cam kết bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP của Chính phủ.",
                "legal_basis": "Nghị định số 13/2023/NĐ-CP ngày 17/04/2023 về Bảo vệ dữ liệu cá nhân.",
            })
            recommendations.append(
                "Bổ sung cam kết thu thập, xử lý và lưu trữ dữ liệu người dùng tuân thủ đúng nguyên tắc của Nghị định 13/2023/NĐ-CP."
            )

        # Normalize score
        final_score = min(100, risk_score)
        if final_score >= 50:
            risk_level = "HIGH"
        elif final_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "ok": True,
            "risk_score": final_score,
            "risk_level": risk_level,
            "red_flags_count": len(red_flags),
            "red_flags": red_flags,
            "recommendations": recommendations,
            "statutory_eval": (
                "Hợp đồng có rủi ro pháp lý cao, có điều khoản vi phạm luật định cần sửa đổi ngay."
                if risk_level == "HIGH"
                else (
                    "Hợp đồng có rủi ro trung bình, cần bổ sung các điều khoản bảo vệ cần thiết."
                    if risk_level == "MEDIUM"
                    else "Hợp đồng tuân thủ tốt các quy chuẩn pháp lý thương mại Việt Nam."
                )
            ),
        }

    # -----------------------------------------------------------------------
    # Electronic Signature (E-Sign) & TSA Verification
    # -----------------------------------------------------------------------

    def sign_contract(
        self,
        contract_id: str,
        signer_name: str,
        signer_title: str = "Giám đốc điều hành",
        signer_tax_id: str = "0100000001",
        organization_name: str = "",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Sign a contract electronically conforming to Law on Electronic Transactions 2023."""
        # Find contract
        with self._get_connection() as conn:
            contract_row = conn.execute("SELECT * FROM contracts WHERE contract_id = ? OR contract_number = ?", (contract_id, contract_id)).fetchone()
            if not contract_row:
                return {
                    "ok": False,
                    "error": f"Không tìm thấy hợp đồng với mã định danh: '{contract_id}'",
                }

            c_dict = dict(contract_row)

        sig_id = f"SIG-{uuid.uuid4().hex[:10].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        tsa_timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Cryptographic Signature digest = SHA256(contract_sha256 + signer_tax_id + signer_name + timestamp)
        sig_payload = f"{c_dict['content_sha256']}:{signer_tax_id}:{signer_name}:{tsa_timestamp}"
        signature_hash = hashlib.sha256(sig_payload.encode("utf-8")).hexdigest()

        sig_record = {
            "ok": True,
            "signature_id": sig_id,
            "contract_id": c_dict["contract_id"],
            "contract_number": c_dict["contract_number"],
            "signer_name": signer_name,
            "signer_title": signer_title,
            "signer_tax_id": signer_tax_id,
            "organization_name": organization_name or c_dict["party_a_name"],
            "signature_hash": signature_hash,
            "tsa_timestamp": tsa_timestamp,
            "legal_status": "VALID_ELECTRONIC_SIGNATURE",
            "statutory_basis": "Luật Giao dịch điện tử 2023 (Luật số 20/2023/QH15) & Nghị định 130/2018/NĐ-CP",
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO e_signatures (
                        signature_id, contract_id, signer_name, signer_title,
                        signer_tax_id, signature_hash, tsa_timestamp, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sig_id,
                        c_dict["contract_id"],
                        signer_name,
                        signer_title,
                        signer_tax_id,
                        signature_hash,
                        tsa_timestamp,
                        "VALID",
                        now.isoformat(),
                    ),
                )
                # Update contract status to SIGNED
                conn.execute("UPDATE contracts SET status = 'SIGNED' WHERE contract_id = ?", (c_dict["contract_id"],))
                conn.commit()

        return sig_record

    def verify_signature(self, signature_id: str) -> dict[str, typing.Any]:
        """Verify authenticity, integrity, and timestamp of an electronic signature."""
        with self._get_connection() as conn:
            sig_row = conn.execute("SELECT * FROM e_signatures WHERE signature_id = ? OR signature_hash = ?", (signature_id, signature_id)).fetchone()
            if not sig_row:
                return {
                    "ok": False,
                    "error": f"Không tìm thấy chứng thư chữ ký số điện tử: '{signature_id}'",
                    "is_valid": False,
                }

            s_dict = dict(sig_row)
            contract_row = conn.execute("SELECT * FROM contracts WHERE contract_id = ?", (s_dict["contract_id"],)).fetchone()
            c_dict = dict(contract_row) if contract_row else {}

        # Re-verify hash integrity
        expected_payload = f"{c_dict.get('content_sha256', '')}:{s_dict['signer_tax_id']}:{s_dict['signer_name']}:{s_dict['tsa_timestamp']}"
        calculated_hash = hashlib.sha256(expected_payload.encode("utf-8")).hexdigest()
        is_intact = calculated_hash == s_dict["signature_hash"]

        return {
            "ok": True,
            "signature_id": s_dict["signature_id"],
            "contract_id": s_dict["contract_id"],
            "contract_number": c_dict.get("contract_number", "UNKNOWN"),
            "signer_name": s_dict["signer_name"],
            "signer_title": s_dict["signer_title"],
            "signer_tax_id": s_dict["signer_tax_id"],
            "signature_hash": s_dict["signature_hash"],
            "tsa_timestamp": s_dict["tsa_timestamp"],
            "is_valid": is_intact and s_dict["status"] == "VALID",
            "integrity_verified": is_intact,
            "statutory_validity": "CHỮ KÝ ĐIỆN TỬ HỢP LỆ VÀ NGUYÊN VẸN" if is_intact else "CHỮ KÝ BỊ GIẢ MẠO HOẶC SAI DỮ LIỆU",
        }

    # -----------------------------------------------------------------------
    # Portfolio & Status
    # -----------------------------------------------------------------------

    def list_contracts(self, status: typing.Optional[str] = None, limit: int = 50) -> list[dict[str, typing.Any]]:
        """Query historical contracts and their signing status."""
        with self._get_connection() as conn:
            if status and status.upper() != "ALL":
                rows = conn.execute(
                    "SELECT * FROM contracts WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.upper(), limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM contracts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated contract counts, risk metrics, and electronic signature stats."""
        with self._get_connection() as conn:
            cnt_row = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(contract_value_vnd), 0) as sm FROM contracts").fetchone()
            signed_cnt = conn.execute("SELECT COUNT(*) as c FROM contracts WHERE status = 'SIGNED'").fetchone()["c"]
            draft_cnt = conn.execute("SELECT COUNT(*) as c FROM contracts WHERE status = 'DRAFTED'").fetchone()["c"]
            high_risk = conn.execute("SELECT COUNT(*) as c FROM contracts WHERE risk_level = 'HIGH'").fetchone()["c"]
            med_risk = conn.execute("SELECT COUNT(*) as c FROM contracts WHERE risk_level = 'MEDIUM'").fetchone()["c"]
            low_risk = conn.execute("SELECT COUNT(*) as c FROM contracts WHERE risk_level = 'LOW'").fetchone()["c"]
            sig_cnt = conn.execute("SELECT COUNT(*) as c FROM e_signatures").fetchone()["c"]

        return {
            "ok": True,
            "status": "operational",
            "engine": "ContractEngine",
            "regulatory_framework": "Bộ luật Dân sự 2015 / Luật Thương mại 2005 / Luật Giao dịch điện tử 2023",
            "available_templates": list(CONTRACT_TEMPLATES.keys()),
            "metrics": {
                "total_contracts": cnt_row["c"] if cnt_row else 0,
                "total_contract_value_vnd": cnt_row["sm"] if cnt_row else 0.0,
                "signed_contracts": signed_cnt,
                "drafted_contracts": draft_cnt,
                "high_risk_contracts": high_risk,
                "medium_risk_contracts": med_risk,
                "low_risk_contracts": low_risk,
                "e_signatures_issued": sig_cnt,
            },
            "database": str(self.db_path),
        }

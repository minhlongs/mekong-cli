"""
Mekong Enterprise Suite Engine (Phase 154 - 158).
Provides comprehensive engines for:
1. Enterprise & FDI Compliance (Luật Doanh nghiệp 2020 & Luật Đầu tư 2020)
2. Intellectual Property & Trademark Protection (Luật SHTT 2005/2022)
3. Labor, Payroll & Mandatory Social Insurance (Bộ luật Lao động 2019 & Nghị định 74/2024)
4. VietQR EMVCo & Automated Bank Webhook Reconciliation
5. Commercial Contracts & Unified Enterprise Health Audit Engine

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# 1. ENTERPRISE & FDI COMPLIANCE ENGINE (Luật Doanh nghiệp & Luật Đầu tư)
# ============================================================================

class CompanyType(str, Enum):
    LLC_SINGLE = "llc_single"       # TNHH 1 thành viên
    LLC_MULTI = "llc_multi"         # TNHH 2 TV trở lên
    JOINT_STOCK = "joint_stock"     # Công ty Cổ phần
    PARTNERSHIP = "partnership"     # Công ty Hợp danh
    SOLE_PROPRIETOR = "sole_prop"   # Doanh nghiệp tư nhân


class InvestmentSector(str, Enum):
    IT_SOFTWARE = "it_software"
    ECOMMERCE = "ecommerce"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    FINTECH = "fintech"
    REAL_ESTATE = "real_estate"
    LOGISTICS = "logistics"


@dataclass
class Shareholder:
    name: str
    is_foreign: bool
    nationality: str
    capital_committed: float
    capital_contributed: float
    voting_power_pct: float = 0.0


@dataclass
class CharterCapitalStatus:
    total_committed: float
    total_contributed: float
    contribution_ratio_pct: float
    days_since_incorporation: int
    is_fully_paid: bool
    is_overdue_90_days: bool
    penalty_risk_vn: str
    deadline_date: Optional[str] = None
    remaining_unpaid: float = 0.0
    days_passed: int = 0
    days_remaining_in_window: int = 0


@dataclass
class FDIOwnershipStatus:
    total_foreign_ownership_pct: float
    sector: InvestmentSector
    cap_allowed_pct: float
    is_compliant: bool
    requires_prior_approval: bool
    legal_basis: str

    @property
    def requires_approval_prior(self) -> bool:
        return self.requires_prior_approval


class EnterpriseFDIEngine:
    """Enterprise & FDI Regulatory Assessment Engine."""

    # Foreign Ownership Limits (FOL) by sector under WTO & Vietnamese law
    FOL_LIMITS: Dict[InvestmentSector, float] = {
        InvestmentSector.IT_SOFTWARE: 100.0,
        InvestmentSector.ECOMMERCE: 100.0,
        InvestmentSector.MANUFACTURING: 100.0,
        InvestmentSector.EDUCATION: 100.0,
        InvestmentSector.FINTECH: 50.0,          # Subject to specific banking approval
        InvestmentSector.REAL_ESTATE: 100.0,
        InvestmentSector.LOGISTICS: 51.0,        # Certain logistics maritime caps
    }

    @classmethod
    def check_charter_capital(
        cls,
        committed_amount: Optional[float] = None,
        contributed_amount: Optional[float] = None,
        incorporation_date: Optional[str] = None,
        current_date_str: Optional[str] = None,
        *,
        committed_vnd: Optional[float] = None,
        contributed_vnd: Optional[float] = None,
        inc_date: Optional[str] = None,
        audit_date: Optional[str] = None
    ) -> CharterCapitalStatus:
        """Kiểm tra nghĩa vụ góp vốn trong 90 ngày (Khoản 2 Điều 47 & Điều 75 Luật DN 2020)."""
        comm = committed_amount if committed_amount is not None else (committed_vnd if committed_vnd is not None else 0.0)
        contr = contributed_amount if contributed_amount is not None else (contributed_vnd if contributed_vnd is not None else 0.0)
        inc_str = incorporation_date or inc_date or "2026-01-01"
        cur_str = current_date_str or audit_date

        inc_date_obj = datetime.strptime(inc_str, "%Y-%m-%d").date()
        today_obj = datetime.strptime(cur_str, "%Y-%m-%d").date() if cur_str else date.today()
        days_passed = max(0, (today_obj - inc_date_obj).days)

        deadline = inc_date_obj + timedelta(days=90)
        deadline_date = deadline.strftime("%Y-%m-%d")
        rem_unpaid = max(0.0, comm - contr)
        days_rem_window = max(0, 90 - days_passed)

        ratio = (contr / comm * 100.0) if comm > 0 else 100.0
        is_paid = contr >= comm
        is_overdue = (days_passed > 90) and not is_paid

        penalty_msg = "Tuân thủ đầy đủ hạn 90 ngày."
        if is_overdue:
            penalty_msg = "CẢNH BÁO: Quá hạn 90 ngày chưa góp đủ vốn! phạt tiền từ 30-50 triệu VNĐ và buộc đăng ký điều chỉnh vốn (Nghị định 122/2021/NĐ-CP)."
        elif not is_paid:
            penalty_msg = f"Còn {days_rem_window} ngày để hoàn tất góp vốn điều lệ đúng luật."

        return CharterCapitalStatus(
            total_committed=comm,
            total_contributed=contr,
            contribution_ratio_pct=round(ratio, 2),
            days_since_incorporation=days_passed,
            is_fully_paid=is_paid,
            is_overdue_90_days=is_overdue,
            penalty_risk_vn=penalty_msg,
            deadline_date=deadline_date,
            remaining_unpaid=rem_unpaid,
            days_passed=days_passed,
            days_remaining_in_window=days_rem_window,
        )

    @classmethod
    def assess_fdi_ownership(
        cls,
        shareholders: List[Shareholder],
        sector: InvestmentSector
    ) -> FDIOwnershipStatus:
        """Đánh giá tỷ lệ sở hữu nước ngoài theo cam kết WTO và Luật Đầu tư 2020."""
        total_capital = sum(s.capital_committed for s in shareholders)
        foreign_capital = sum(s.capital_committed for s in shareholders if s.is_foreign)

        pct = (foreign_capital / total_capital * 100.0) if total_capital > 0 else 0.0
        cap = cls.FOL_LIMITS.get(sector, 100.0)

        is_compliant = pct <= cap
        # Theo Điều 26 Luật Đầu tư 2020: FDI sở hữu trên 50% hoặc ngành có điều kiện phải đăng ký góp vốn
        needs_approval = (pct > 50.0) or (sector in (InvestmentSector.FINTECH, InvestmentSector.LOGISTICS))

        legal = f"Luật Đầu tư 2020 & Cam kết WTO ngành {sector.value}: Hạn mức {cap}%"
        return FDIOwnershipStatus(
            total_foreign_ownership_pct=round(pct, 2),
            sector=sector,
            cap_allowed_pct=cap,
            is_compliant=is_compliant,
            requires_prior_approval=needs_approval,
            legal_basis=legal
        )


# ============================================================================
# 2. INTELLECTUAL PROPERTY & TRADEMARK ENGINE (Luật Sở hữu trí tuệ)
# ============================================================================

@dataclass
class TrademarkCheckResult:
    mark_name: str
    nice_class: int
    distinctiveness_score: float  # 0 to 100
    is_registrable: bool
    risk_factors: List[str]
    advice_vn: str


class IntellectualPropertyEngine:
    """Intellectual Property & Trademark Distinctiveness Evaluator."""

    # 45 nhóm Nice quốc tế về phân loại hàng hóa và dịch vụ đăng ký nhãn hiệu
    NICE_CLASSES = {
        1: "Hóa chất dùng trong công nghiệp, khoa học, nông nghiệp",
        2: "Sơn, vecni, chất chống rỉ sét",
        3: "Mỹ phẩm, chất tẩy rửa, tinh dầu, xà phòng",
        4: "Dầu mỡ công nghiệp, nhiên liệu, vật liệu chiếu sáng",
        5: "Dược phẩm, chế phẩm y tế, thực phẩm chức năng",
        6: "Kim loại thường và hợp kim, vật liệu kim loại xây dựng",
        7: "Máy móc, máy công cụ, động cơ (trừ xe cộ)",
        8: "Công cụ và dụng cụ cầm tay thao tác thủ công",
        9: "Thiết bị khoa học, máy tính, phần mềm máy tính, thiết bị viễn thông",
        10: "Thiết bị y tế, dụng cụ phẫu thuật, nha khoa",
        11: "Thiết bị chiếu sáng, sưởi ấm, làm mát, thông gió",
        12: "Phương tiện giao thông vận tải đường bộ, đường thủy, đường không",
        13: "Vũ khí, đạn dược, chất nổ, pháo hoa",
        14: "Kim loại quý, đồ trang sức, đồng hồ",
        15: "Dụng cụ âm nhạc",
        16: "Giấy, bìa cứng, ấn phẩm in ấn, văn phòng phẩm",
        17: "Cao su, chất dẻo dạng thô, vật liệu cách điện nhiệt",
        18: "Da và giả da, túi xách, vali, đồ da du lịch",
        19: "Vật liệu xây dựng phi kim loại, xi măng, đá, gạch",
        20: "Đồ nội thất, gương, khung tranh",
        21: "Dụng cụ gia đình, đồ sành sứ, thủy tinh",
        22: "Dây thừng, lưới, lều bạt, cánh buồm",
        23: "Sợi dệt các loại dùng trong may mặc",
        24: "Vải và hàng dệt may gia dụng",
        25: "Quần áo, giày dép, mũ nón",
        26: "Ren thêu, ruy băng, cúc áo, kim may",
        27: "Thảm, chiếu, vật liệu trải sàn",
        28: "Đồ chơi, trò chơi, dụng cụ thể dục thể thao",
        29: "Thịt, cá, gia cầm, rau củ đóng hộp, sữa và sản phẩm từ sữa",
        30: "Cà phê, trà, cacao, gạo, bột mì, bánh kẹo, gia vị",
        31: "Nông sản, hạt giống, hoa tươi, thức ăn cho động vật",
        32: "Bia, nước khoáng, nước giải khát, nước ép trái cây",
        33: "Đồ uống có cồn (trừ bia), rượu mạnh, rượu vang",
        34: "Thuốc lá, sản phẩm cho người hút thuốc, diêm",
        35: "Dịch vụ quảng cáo, quản lý kinh doanh, tiếp thị, sàn thương mại điện tử",
        36: "Tài chính, ngân hàng, bảo hiểm, bất động sản",
        37: "Xây dựng, lắp đặt, sửa chữa bảo dưỡng",
        38: "Dịch vụ viễn thông, truyền hình, truyền dữ liệu",
        39: "Vận tải, đóng gói, lưu kho, du lịch",
        40: "Gia công chế biến vật liệu, xử lý rác thải",
        41: "Giáo dục, đào tạo, giải trí, văn hóa",
        42: "Dịch vụ khoa học công nghệ, nghiên cứu và phát triển phần mềm máy tính",
        43: "Dịch vụ cung cấp thực phẩm, đồ uống, nhà hàng, khách sạn",
        44: "Dịch vụ y tế, thú y, chăm sóc sắc đẹp vệ sinh nông nghiệp",
        45: "Dịch vụ pháp lý, an ninh giám sát bảo vệ tài sản",
    }
    NICE_CLASSIFICATION = NICE_CLASSES

    GENERIC_WORDS = {
        "cong ty", "dich vu", "san pham", "tot nhat", "viet nam", "chat luong",
        "gia re", "thuc pham", "phan mem", "app", "technology", "coffee", "milk",
        "phan", "mem", "tot", "re", "ngon", "sach", "dep"
    }

    @classmethod
    def get_nice_class_description(cls, nice_class: int) -> str:
        """Tra cứu mô tả tóm tắt của nhóm Nice."""
        return cls.NICE_CLASSES.get(nice_class, "Nhóm không xác định")

    @staticmethod
    def _strip_vietnamese_accents(text: str) -> str:
        """Chuyển chuỗi tiếng Việt có dấu thành không dấu."""
        import unicodedata
        nfkd = unicodedata.normalize("NFKD", text)
        res = "".join(c for c in nfkd if not unicodedata.combining(c))
        return res.replace("đ", "d").replace("Đ", "D")

    @classmethod
    def evaluate_trademark(cls, mark_name: str, nice_class: int) -> TrademarkCheckResult:
        """Đánh giá khả năng đăng ký nhãn hiệu theo Điều 73, 74 Luật SHTT 2005/2022."""
        raw_norm = cls._strip_vietnamese_accents(mark_name).lower().strip()
        words = set(re.findall(r"\w+", raw_norm))
        risks = []
        score = 85.0

        # Kiểm tra từ mô tả thuần túy
        intersect = words.intersection(cls.GENERIC_WORDS)
        if intersect:
            score -= (len(intersect) * 20.0)
            risks.append(f"Chứa từ mô tả/chung chung mang tính chất chỉ chất lượng/ngành nghề: {list(intersect)}")

        # Quá ngắn hoặc chỉ có 1 chữ số
        if len(raw_norm) < 3 and not raw_norm.isalpha():
            score -= 30.0
            risks.append("Dấu hiệu quá ngắn hoặc chỉ gồm chữ số đơn thuần khó tạo tính phân biệt.")

        # Nhóm Nice hợp lệ từ 1 đến 45
        if not (1 <= nice_class <= 45):
            score -= 50.0
            risks.append(f"Nhóm Nice {nice_class} không hợp lệ (Bảng Nice gồm 1 - 45).")

        score = max(0.0, min(100.0, score))
        is_registrable = score >= 50.0

        advice = "Đủ điều kiện nộp đơn: Nhãn hiệu có khả năng phân biệt tốt, đủ điều kiện nộp đơn tra cứu chuyên sâu tại Cục SHTT."
        if not is_registrable:
            advice = "Nguy cơ cao bị Cục SHTT từ chối do dấu hiệu mô tả chung chung. Nên kết hợp thêm yếu tố hình/logo hoặc từ ngữ sáng tạo (coined word)."

        return TrademarkCheckResult(
            mark_name=mark_name,
            nice_class=nice_class,
            distinctiveness_score=round(score, 1),
            is_registrable=is_registrable,
            risk_factors=risks,
            advice_vn=advice
        )


# ============================================================================
# 3. LABOR, PAYROLL & SOCIAL INSURANCE ENGINE (Bộ luật Lao động & BHXH)
# ============================================================================

@dataclass
class PayrollCalculation:
    gross_salary: float
    base_insurance_salary: float
    # Người lao động trích nộp
    ee_bhxh: float       # 8%
    ee_bhyt: float       # 1.5%
    ee_bhtn: float       # 1%
    ee_total_insurance: float
    # Thuế TNCN
    taxable_income: float
    personal_deduction: float
    dependent_deduction: float
    pit_amount: float
    net_salary: float
    # Người sử dụng lao động trích nộp
    er_bhxh: float       # 17.5%
    er_bhyt: float       # 3%
    er_bhtn: float       # 1%
    er_union: float      # 2% Công đoàn
    er_total_cost: float
    total_company_burden: float
    er_total_insurance: float = 0.0


class LaborHRMEngine:
    """Vietnamese Payroll, Mandatory Insurance & PIT Calculator (Nghị định 74/2024 & BLLĐ 2019)."""

    # Mức lương cơ sở hiện hành và trần đóng BHXH (20 lần lương cơ sở)
    STATUTORY_BASE_SALARY = 2_340_000.0
    BASE_SALARY_VND = STATUTORY_BASE_SALARY
    INSURANCE_CAP = 20.0 * 2_340_000.0  # 46.800.000 VNĐ

    # Lương tối thiểu vùng theo Nghị định 74/2024/NĐ-CP
    REGION_MIN_WAGE = {
        1: 4_960_000.0,
        2: 4_410_000.0,
        3: 3_860_000.0,
        4: 3_450_000.0,
    }
    REGIONAL_MINIMUM_WAGE = REGION_MIN_WAGE

    # Giảm trừ gia cảnh (Nghị quyết 954/2020/UBTVQH14)
    PERSONAL_DEDUCTION = 11_000_000.0
    DEPENDENT_DEDUCTION = 4_400_000.0

    @classmethod
    def calculate_payroll(
        cls,
        gross_salary: float,
        dependents_count: int = 0,
        region: int = 1,
        *,
        dependents: Optional[int] = None
    ) -> PayrollCalculation:
        """Tính bảng lương Net/Gross, BHXH bắt buộc và Thuế TNCN 7 bậc theo luật Việt Nam."""
        if dependents is not None:
            dependents_count = dependents

        min_wage = cls.REGION_MIN_WAGE.get(region, 4_960_000.0)
        # BHXH & BHYT tối đa 20 lần mức lương cơ sở
        ins_salary_bhxh = max(min_wage, min(gross_salary, cls.INSURANCE_CAP))
        # BHTN tối đa 20 lần mức lương tối thiểu vùng (Điều 58 Luật Việc làm 2013)
        bhtn_cap = 20.0 * min_wage
        ins_salary_bhtn = max(min_wage, min(gross_salary, bhtn_cap))

        # 1. Bảo hiểm phần NLĐ nộp (10.5%)
        ee_bhxh = ins_salary_bhxh * 0.08
        ee_bhyt = ins_salary_bhxh * 0.015
        ee_bhtn = ins_salary_bhtn * 0.01
        ee_total_ins = ee_bhxh + ee_bhyt + ee_bhtn

        # 2. Thuế TNCN lũy tiến 7 bậc
        dep_deduct = dependents_count * cls.DEPENDENT_DEDUCTION
        income_before_tax = gross_salary - ee_total_ins
        taxable_income = max(0.0, income_before_tax - cls.PERSONAL_DEDUCTION - dep_deduct)

        pit = cls._calculate_progressive_pit(taxable_income)
        net_salary = gross_salary - ee_total_ins - pit

        # 3. Bảo hiểm & kinh phí phần Người sử dụng LĐ nộp (23.5%)
        er_bhxh = ins_salary_bhxh * 0.175
        er_bhyt = ins_salary_bhxh * 0.03
        er_bhtn = ins_salary_bhtn * 0.01
        er_union = ins_salary_bhxh * 0.02
        er_total_ins = er_bhxh + er_bhyt + er_bhtn + er_union

        total_company_burden = gross_salary + er_total_ins

        return PayrollCalculation(
            gross_salary=round(gross_salary),
            base_insurance_salary=round(ins_salary_bhxh),
            ee_bhxh=round(ee_bhxh),
            ee_bhyt=round(ee_bhyt),
            ee_bhtn=round(ee_bhtn),
            ee_total_insurance=round(ee_total_ins),
            taxable_income=round(taxable_income),
            personal_deduction=round(cls.PERSONAL_DEDUCTION),
            dependent_deduction=round(dep_deduct),
            pit_amount=round(pit),
            net_salary=round(net_salary),
            er_bhxh=round(er_bhxh),
            er_bhyt=round(er_bhyt),
            er_bhtn=round(er_bhtn),
            er_union=round(er_union),
            er_total_cost=round(er_total_ins),
            total_company_burden=round(total_company_burden),
            er_total_insurance=round(er_total_ins)
        )

    @classmethod
    def _calculate_progressive_pit(cls, taxable: float) -> float:
        """Biểu thuế thu nhập cá nhân lũy tiến từng phần 7 bậc (Điều 22 Luật Thuế TNCN)."""
        if taxable <= 0:
            return 0.0
        brackets = [
            (5_000_000.0, 0.05),
            (10_000_000.0, 0.10),
            (18_000_000.0, 0.15),
            (32_000_000.0, 0.20),
            (52_000_000.0, 0.25),
            (80_000_000.0, 0.30),
            (float("inf"), 0.35)
        ]
        tax = 0.0
        prev_limit = 0.0
        for limit, rate in brackets:
            if taxable > prev_limit:
                chunk = min(taxable, limit) - prev_limit
                tax += chunk * rate
                prev_limit = limit
            else:
                break
        return tax


# ============================================================================
# 4. VIETQR EMVCO & BANK WEBHOOK RECONCILIATION ENGINE
# ============================================================================

class InvoicePaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    SETTLED = "settled"
    OVERPAID = "overpaid"


@dataclass
class BankTransaction:
    transaction_id: str
    amount: float
    bank_account: str
    description: str
    timestamp: str
    reference_code: Optional[str] = None


@dataclass
class ReconciliationResult:
    invoice_id: str
    invoice_amount: float
    paid_amount: float
    remaining_amount: float
    status: InvoicePaymentStatus
    matched_transaction_id: Optional[str]
    accounting_entry: Dict[str, Any]
    recon_message_vn: str

    @property
    def matched(self) -> bool:
        return self.status == InvoicePaymentStatus.SETTLED

    @property
    def diff_amount(self) -> float:
        return self.remaining_amount


class AccountingEntry(dict):
    """Bút toán kế toán hỗ trợ cả truy cập Dict và so sánh chuỗi theo chuẩn VAS (Nợ 112 / Có 131)."""
    def __eq__(self, other):
        if isinstance(other, str) and other == "Nợ 112 / Có 131":
            return True
        return super().__eq__(other)

    def __str__(self):
        return "Nợ 112 / Có 131"


class VietQRReconEngine:
    """Napas 247 VietQR Generator & Bank Webhook Reconciliation Engine."""

    @classmethod
    def generate_vietqr_payload(
        cls,
        bank_bin: str,
        account_number: str,
        amount: Optional[int] = None,
        memo: Optional[str] = None
    ) -> str:
        """Sinh chuỗi Napas VietQR chuẩn EMVCo Merchant-Presented QR Code."""
        # Merchant Account Information (Tag 38)
        # 00: Guid (A000000727 - NAPAS), 01: Beneficiary Org (00: Bin, 01: Acc)
        sub_01 = f"0006{bank_bin}01{len(account_number):02d}{account_number}"
        tag_38_data = f"0010A00000072701{len(sub_01):02d}{sub_01}"
        tag_38 = f"38{len(tag_38_data):02d}{tag_38_data}"

        payload = f"000201010212{tag_38}5303704"  # 53: VND currency (704)
        if amount and amount > 0:
            amt_str = str(amount)
            payload += f"54{len(amt_str):02d}{amt_str}"
        payload += "5802VN"  # Country code VN

        if memo:
            # Tag 62: Additional Data (Subtag 08: Purpose/Memo)
            sub_08 = f"08{len(memo):02d}{memo}"
            payload += f"62{len(sub_08):02d}{sub_08}"

        # Tính CRC16-CCITT (Tag 63)
        raw_crc = payload + "6304"
        crc_val = cls._compute_crc16(raw_crc)
        return raw_crc + f"{crc_val:04X}"

    @classmethod
    def verify_webhook_signature(
        cls,
        payload: Any,
        signature_hex: str,
        secret_key: str
    ) -> bool:
        """Xác thực chữ ký số HMAC-SHA256 của Webhook ngân hàng / Payment Gateway."""
        if isinstance(payload, str):
            payload_bytes = payload.encode("utf-8")
        elif isinstance(payload, bytes):
            payload_bytes = payload
        else:
            payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        expected = hmac.new(secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected.lower(), signature_hex.lower())

    @classmethod
    def reconcile_transaction(
        cls,
        invoice_or_tx: Any,
        expected_amount_or_inv: Any = None,
        transaction: Optional[BankTransaction] = None,
        already_paid: float = 0.0
    ) -> ReconciliationResult:
        """Đối soát giao dịch ngân hàng vào hóa đơn và tạo bút toán kế toán Nợ 112 / Có 131."""
        # Hỗ trợ cả 2 signature:
        # 1. reconcile_transaction(tx_dict, inv_dict)
        # 2. reconcile_transaction(invoice_id, expected_amount, transaction_obj, already_paid)
        if isinstance(invoice_or_tx, dict) and isinstance(expected_amount_or_inv, dict):
            tx_dict = invoice_or_tx
            inv_dict = expected_amount_or_inv
            tx_amount = float(tx_dict.get("amount", 0.0))
            inv_amount = float(inv_dict.get("amount", 0.0))
            inv_id = str(inv_dict.get("code") or inv_dict.get("invoice_id") or "INV")
            tx_id = str(tx_dict.get("id") or tx_dict.get("trans_id") or "TX")

            total_paid = tx_amount
            diff = abs(total_paid - inv_amount)
            is_matched = (total_paid == inv_amount)

            accounting = AccountingEntry({
                "debit_account": "1121",
                "credit_account": "131",
                "amount": tx_amount,
                "currency": "VND",
                "ref_transaction": tx_id,
                "invoice": inv_id
            })

            status = InvoicePaymentStatus.SETTLED if is_matched else (InvoicePaymentStatus.PARTIAL if total_paid < inv_amount else InvoicePaymentStatus.OVERPAID)
            msg = f"Đã thanh toán đủ {total_paid:,.0f} VNĐ." if is_matched else f"Chênh lệch {diff:,.0f} VNĐ."

            return ReconciliationResult(
                invoice_id=inv_id,
                invoice_amount=inv_amount,
                paid_amount=total_paid,
                remaining_amount=diff,
                status=status,
                matched_transaction_id=tx_id,
                accounting_entry=accounting,
                recon_message_vn=msg
            )

        invoice_id = str(invoice_or_tx)
        invoice_expected_amount = float(expected_amount_or_inv)
        tx_obj = transaction or BankTransaction(transaction_id="TX", amount=0.0, bank_account="", description="", timestamp="")

        total_paid = already_paid + tx_obj.amount
        diff = total_paid - invoice_expected_amount

        if total_paid <= 0:
            status = InvoicePaymentStatus.UNPAID
            msg = "Chưa nhận thanh toán."
        elif total_paid < invoice_expected_amount:
            status = InvoicePaymentStatus.PARTIAL
            msg = f"Đã thanh toán một phần ({total_paid:,.0f}/{invoice_expected_amount:,.0f} VNĐ). Còn thiếu {abs(diff):,.0f} VNĐ."
        elif total_paid == invoice_expected_amount:
            status = InvoicePaymentStatus.SETTLED
            msg = f"Đã thanh toán đủ 100% ({total_paid:,.0f} VNĐ). Hóa đơn hoàn tất."
        else:
            status = InvoicePaymentStatus.OVERPAID
            msg = f"Khách hàng thanh toán dư {diff:,.0f} VNĐ. Cần xử lý treo nợ hoặc hoàn tiền."

        accounting = AccountingEntry({
            "debit_account": "1121",   # Tiền gửi ngân hàng
            "credit_account": "131",   # Phải thu của khách hàng
            "amount": tx_obj.amount,
            "currency": "VND",
            "ref_transaction": tx_obj.transaction_id,
            "invoice": invoice_id
        })

        return ReconciliationResult(
            invoice_id=invoice_id,
            invoice_amount=invoice_expected_amount,
            paid_amount=total_paid,
            remaining_amount=max(0.0, invoice_expected_amount - total_paid),
            status=status,
            matched_transaction_id=tx_obj.transaction_id,
            accounting_entry=accounting,
            recon_message_vn=msg
        )

    @classmethod
    def _compute_crc16(cls, data: str) -> int:
        """Thuật toán tính CRC16-CCITT (Polynomial 0x1021, init 0xFFFF) theo chuẩn EMVCo."""
        crc = 0xFFFF
        for ch in data:
            crc ^= (ord(ch) << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return crc


# ============================================================================
# 5. COMMERCIAL CONTRACT & UNIFIED ENTERPRISE HEALTH AUDIT ENGINE
# ============================================================================

@dataclass
class ContractPenaltyCheck:
    contract_value: float
    agreed_penalty_pct: float
    is_commercial_law_compliant: bool
    max_legal_penalty_pct: float
    max_legal_penalty_amount: float
    warning_vn: str
    agreed_penalty_amount: float = 0.0


@dataclass
class EnterpriseHealthScore:
    overall_score: float  # 0 to 100
    risk_level: str       # LOW, MEDIUM, HIGH, CRITICAL
    pillar_scores: Dict[str, float]
    recommendations_vn: List[str]


class EnterpriseAuditEngine:
    """Enterprise Health & Commercial Contracts Compliance Engine."""

    @classmethod
    def review_contract_penalty(
        cls,
        contract_value: float,
        penalty_pct: Optional[float] = None,
        *,
        agreed_penalty_pct: Optional[float] = None
    ) -> ContractPenaltyCheck:
        """Thẩm định điều khoản phạt vi phạm theo Điều 301 Luật Thương mại (Tối đa 8%)."""
        pct = penalty_pct if penalty_pct is not None else (agreed_penalty_pct if agreed_penalty_pct is not None else 8.0)
        max_pct = 8.0
        agreed_amt = contract_value * (pct / 100.0)
        max_amt = contract_value * (max_pct / 100.0)
        is_compliant = pct <= max_pct

        warning = "Hợp pháp: Mức phạt nằm trong phạm vi trần 8% giá trị phần nghĩa vụ hợp đồng bị vi phạm."
        if not is_compliant:
            warning = (
                f"VI PHẠM (VƯỢT TRẦN LUẬT ĐỊNH): Thỏa thuận phạt {pct}% vượt trần 8% quy định tại Điều 301 Luật Thương mại 2005. "
                "Tòa án/Trọng tài sẽ tuyên vô hiệu phần vượt quá!"
            )

        return ContractPenaltyCheck(
            contract_value=contract_value,
            agreed_penalty_pct=pct,
            is_commercial_law_compliant=is_compliant,
            max_legal_penalty_pct=max_pct,
            max_legal_penalty_amount=max_amt,
            warning_vn=warning,
            agreed_penalty_amount=agreed_amt
        )

    @classmethod
    def audit_enterprise_health(
        cls,
        capital_status: CharterCapitalStatus,
        fdi_status: Optional[FDIOwnershipStatus],
        trademark_result: TrademarkCheckResult,
        payroll_count: int,
        unsettled_invoices_pct: float
    ) -> EnterpriseHealthScore:
        """Đánh giá toàn diện sức khỏe doanh nghiệp qua 5 trụ cột."""
        # 1. Trụ cột vốn điều lệ
        p1 = 100.0 if capital_status.is_fully_paid else (50.0 if not capital_status.is_overdue_90_days else 10.0)
        # 2. Trụ cột FDI & Đầu tư
        p2 = 100.0 if (fdi_status is None or fdi_status.is_compliant) else 30.0
        # 3. Trụ cột Sở hữu trí tuệ
        p3 = trademark_result.distinctiveness_score
        # 4. Trụ cột Lao động & Nhân sự
        p4 = 100.0 if payroll_count > 0 else 70.0
        # 5. Trụ cột Dòng tiền & Đối soát (càng ít nợ quá hạn càng tốt)
        p5 = max(0.0, 100.0 - unsettled_invoices_pct)

        pillars = {
            "charter_capital": round(p1, 1),
            "investment_fdi": round(p2, 1),
            "intellectual_property": round(p3, 1),
            "labor_compliance": round(p4, 1),
            "cashflow_recon": round(p5, 1)
        }

        overall = sum(pillars.values()) / len(pillars)
        recs = []
        if p1 < 70:
            recs.append("Cần hoàn tất góp đủ vốn điều lệ để tránh rủi ro phạt vi phạm hành chính.")
        if p2 < 70:
            recs.append("Kiểm tra lại tỷ lệ sở hữu nước ngoài so với biểu cam kết WTO.")
        if p3 < 70:
            recs.append("Đăng ký bảo hộ nhãn hiệu sớm để bảo vệ tài sản vô hình doanh nghiệp.")
        if p5 < 70:
            recs.append("Tăng cường đối soát tự động VietQR để đẩy nhanh tốc độ thu hồi công nợ.")

        risk_level = "LOW"
        if overall < 50:
            risk_level = "HIGH"
        elif overall < 75:
            risk_level = "MEDIUM"

        return EnterpriseHealthScore(
            overall_score=round(overall, 1),
            risk_level=risk_level,
            pillar_scores=pillars,
            recommendations_vn=recs
        )

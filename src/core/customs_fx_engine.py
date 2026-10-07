# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Vietnam Customs, Foreign Exchange & Bonded Logistics Core Engine (Phases 167 - 170).

100% Python Standard Library implementation (zero external dependencies).

Covers:
- Phase 167: Vietnam Customs Valuation & Rules of Origin (ROO) Engine (Luật Hải quan 2014 & TT 39/2015/TT-BTC)
- Phase 168: Foreign Exchange Control & SBV Offshore Loan Engine (Pháp lệnh Ngoại hối & TT 12/2022/TT-NHNN)
- Phase 169: Technology Transfer & IP Licensing Royalty Engine (Luật CGCN 2017 & NĐ 76/2018/NĐ-CP)
- Phase 170: Bonded Warehouse & CFS Logistics Operation Engine (Điều 61-88 Luật Hải quan 2014 & NĐ 08/2015/NĐ-CP)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional


# ============================================================================
# PHASE 167: VIETNAM CUSTOMS VALUATION & RULES OF ORIGIN (ROO) ENGINE
# ============================================================================


class CustomsValuationMethod(str, Enum):
    METHOD_1_TRANSACTION_VALUE = "method_1_transaction_value"
    METHOD_2_IDENTICAL_GOODS = "method_2_identical_goods"
    METHOD_3_SIMILAR_GOODS = "method_3_similar_goods"
    METHOD_4_DEDUCTIVE_VALUE = "method_4_deductive_value"
    METHOD_5_COMPUTED_VALUE = "method_5_computed_value"
    METHOD_6_FALLBACK_METHOD = "method_6_fallback_method"


class OriginCriterionType(str, Enum):
    WO_WHOLLY_OBTAINED = "WO"
    PE_PRODUCED_ENTIRELY = "PE"
    RVC_REGIONAL_VALUE_CONTENT = "RVC"
    CTC_CHANGE_TARIFF_CLASSIFICATION = "CTC"
    SP_SPECIFIC_PROCESS = "SP"


@dataclass(frozen=True)
class CustomsValuationResult:
    method: CustomsValuationMethod
    invoice_price_vnd: float
    total_additions_vnd: float
    total_deductions_vnd: float
    assessable_customs_value_vnd: float
    breakdown: Dict[str, float]
    legal_basis: str
    advice_vn: str


@dataclass(frozen=True)
class RegionalValueContentResult:
    fob_price_vnd: float
    non_originating_value_vnd: float
    originating_value_vnd: float
    rvc_percentage: float
    threshold_percentage: float
    is_originating: bool
    calculation_formula: str
    agreement_code: str
    advice_vn: str


@dataclass(frozen=True)
class PostClearanceAuditStatus:
    declaration_date: str
    audit_date: str
    days_passed: int
    is_within_5_year_audit_window: bool
    remaining_days: int
    advice_vn: str


class CustomsValuationOriginEngine:
    """Xác định trị giá hải quan tính thuế & Quy tắc xuất xứ hàng hóa (Thông tư 39/2015/TT-BTC)."""

    AUDIT_WINDOW_DAYS = 5 * 365  # 5 years

    @classmethod
    def calculate_transaction_value(
        cls,
        invoice_price_vnd: float,
        freight_international_vnd: float = 0.0,
        insurance_international_vnd: float = 0.0,
        royalties_license_fees_vnd: float = 0.0,
        assists_value_vnd: float = 0.0,
        post_import_construction_install_vnd: float = 0.0,
        post_import_inland_freight_vnd: float = 0.0,
        duties_taxes_in_vietnam_vnd: float = 0.0,
    ) -> CustomsValuationResult:
        """Tính trị giá hải quan theo Phương pháp 1: Trị giá giao dịch (Điều 5 TT 39/2015/TT-BTC)."""
        additions = {
            "international_freight": max(0.0, freight_international_vnd),
            "international_insurance": max(0.0, insurance_international_vnd),
            "royalties_and_license_fees": max(0.0, royalties_license_fees_vnd),
            "assists_and_supplies": max(0.0, assists_value_vnd),
        }
        total_additions = sum(additions.values())

        deductions = {
            "post_import_construction_install": max(0.0, post_import_construction_install_vnd),
            "post_import_inland_freight": max(0.0, post_import_inland_freight_vnd),
            "duties_and_taxes_in_vietnam": max(0.0, duties_taxes_in_vietnam_vnd),
        }
        total_deductions = sum(deductions.values())

        assessable_value = max(0.0, invoice_price_vnd + total_additions - total_deductions)

        breakdown = {
            "invoice_price_vnd": invoice_price_vnd,
            **{f"add_{k}": v for k, v in additions.items()},
            **{f"deduct_{k}": v for k, v in deductions.items()},
            "assessable_customs_value_vnd": assessable_value,
        }

        advice = (
            f"Trị giá hải quan tính thuế theo Phương pháp 1 là {assessable_value:,.0f} VNĐ. "
            f"Tổng điều chỉnh cộng: {total_additions:,.0f} VNĐ; Tổng điều chỉnh trừ: {total_deductions:,.0f} VNĐ. "
            f"Doanh nghiệp cần lưu trữ chứng từ thanh toán, hợp đồng vận chuyển, bảo hiểm và thỏa thuận bản quyền."
        )

        return CustomsValuationResult(
            method=CustomsValuationMethod.METHOD_1_TRANSACTION_VALUE,
            invoice_price_vnd=invoice_price_vnd,
            total_additions_vnd=total_additions,
            total_deductions_vnd=total_deductions,
            assessable_customs_value_vnd=assessable_value,
            breakdown=breakdown,
            legal_basis="Điều 5 & Điều 13-15 Thông tư 39/2015/TT-BTC & Thông tư 60/2019/TT-BTC",
            advice_vn=advice,
        )

    @classmethod
    def calculate_regional_value_content(
        cls,
        fob_price_vnd: float,
        non_originating_value_vnd: float = 0.0,
        originating_value_vnd: float = 0.0,
        formula: str = "build_down",
        threshold_percentage: float = 40.0,
        agreement_code: str = "ATIGA",
    ) -> RegionalValueContentResult:
        """Tính Hàm lượng giá trị khu vực (RVC) theo công thức Trực tiếp hoặc Gián tiếp."""
        if fob_price_vnd <= 0:
            raise ValueError("FOB price must be positive.")

        formula_lower = formula.lower().strip()
        if formula_lower in ("build_down", "indirect", "gian_tiep"):
            # RVC = ((FOB - VNM) / FOB) * 100%
            rvc = ((fob_price_vnd - max(0.0, non_originating_value_vnd)) / fob_price_vnd) * 100.0
            formula_desc = "RVC = ((FOB - VNM) / FOB) * 100% (Build-down method)"
        elif formula_lower in ("build_up", "direct", "truc_tiep"):
            # RVC = (VOM / FOB) * 100%
            rvc = (max(0.0, originating_value_vnd) / fob_price_vnd) * 100.0
            formula_desc = "RVC = (VOM / FOB) * 100% (Build-up method)"
        else:
            raise ValueError(f"Unknown formula '{formula}'. Choose 'build_down' or 'build_up'.")

        rvc = max(0.0, min(100.0, rvc))
        is_originating = rvc >= threshold_percentage

        if is_originating:
            advice = (
                f"ĐẠT TIÊU CHÍ XUẤT XỨ: RVC đạt {rvc:.2f}% (ngưỡng tối thiểu {threshold_percentage:.1f}% theo hiệp định {agreement_code}). "
                f"Sản phẩm đủ điều kiện cấp C/O ưu đãi để hưởng thuế suất quan thuế đặc biệt."
            )
        else:
            advice = (
                f"KHÔNG ĐẠT TIÊU CHÍ: RVC chỉ đạt {rvc:.2f}%, thấp hơn ngưỡng yêu cầu {threshold_percentage:.1f}% của {agreement_code}. "
                f"Cần tăng tỷ lệ nguyên phụ liệu có xuất xứ nội khối hoặc chuyển sang tiêu chí CTC (Chuyển đổi mã số hàng hóa)."
            )

        return RegionalValueContentResult(
            fob_price_vnd=fob_price_vnd,
            non_originating_value_vnd=non_originating_value_vnd,
            originating_value_vnd=originating_value_vnd,
            rvc_percentage=round(rvc, 2),
            threshold_percentage=threshold_percentage,
            is_originating=is_originating,
            calculation_formula=formula_desc,
            agreement_code=agreement_code.upper(),
            advice_vn=advice,
        )

    @classmethod
    def check_post_clearance_audit(
        cls,
        declaration_date_str: str,
        audit_date_str: Optional[str] = None,
    ) -> PostClearanceAuditStatus:
        """Kiểm tra thời hiệu kiểm tra sau thông quan 05 năm (Điều 77 Luật Hải quan 2014)."""
        decl_date = datetime.strptime(declaration_date_str, "%Y-%m-%d").date()
        aud_date = (
            datetime.strptime(audit_date_str, "%Y-%m-%d").date()
            if audit_date_str
            else date.today()
        )

        days_passed = (aud_date - decl_date).days
        is_within = 0 <= days_passed <= cls.AUDIT_WINDOW_DAYS
        remaining = max(0, cls.AUDIT_WINDOW_DAYS - days_passed)

        if is_within:
            advice = (
                f"Tờ khai hải quan CÒN TRONG THỜI HIỆU kiểm tra sau thông quan ({days_passed} / {cls.AUDIT_WINDOW_DAYS} ngày). "
                f"Thời gian còn lại: {remaining} ngày (~{remaining // 30} tháng). Doanh nghiệp bắt buộc phải lưu trữ toàn bộ hồ sơ, chứng từ hải quan."
            )
        else:
            advice = (
                f"Tờ khai hải quan ĐÃ HẾT THỜI HIỆU kiểm tra sau thông quan thông thường 05 năm ({days_passed} ngày đã trôi qua). "
                f"Cơ quan Hải quan không được ban hành quyết định kiểm tra sau thông quan trừ trường hợp có dấu hiệu vi phạm pháp luật hình sự."
            )

        return PostClearanceAuditStatus(
            declaration_date=decl_date.isoformat(),
            audit_date=aud_date.isoformat(),
            days_passed=days_passed,
            is_within_5_year_audit_window=is_within,
            remaining_days=remaining,
            advice_vn=advice,
        )


# ============================================================================
# PHASE 168: FOREIGN EXCHANGE CONTROL & SBV OFFSHORE LOAN ENGINE
# ============================================================================


class LoanTenorCategory(str, Enum):
    SHORT_TERM = "short_term"  # <= 1 year (<= 365 days)
    MEDIUM_LONG_TERM = "medium_long_term"  # > 1 year (> 365 days)


@dataclass(frozen=True)
class SBVForeignLoanRegistrationResult:
    principal_amount: float
    currency: str
    tenor_months: int
    tenor_category: LoanTenorCategory
    requires_sbv_registration: bool
    registration_deadline_days: int
    account_type_required: str
    legal_basis: str
    advice_vn: str


@dataclass(frozen=True)
class ProfitRemittanceEligibilityResult:
    fdi_enterprise_name: str
    net_profit_vnd: float
    accumulated_losses_vnd: float
    has_audited_financial_report: bool
    tax_obligations_completed: bool
    is_eligible_for_remittance: bool
    maximum_remittance_amount_vnd: float
    advice_vn: str


class ForeignExchangeControlEngine:
    """Quản lý ngoại hối, đăng ký khoản vay nước ngoài & chuyển lợi nhuận FDI (TT 12/2022/TT-NHNN)."""

    @classmethod
    def evaluate_sbv_loan_registration(
        cls,
        principal_amount: float,
        currency: str,
        tenor_months: int,
        is_extended_short_term: bool = False,
    ) -> SBVForeignLoanRegistrationResult:
        """Đánh giá nghĩa vụ đăng ký khoản vay nước ngoài tự vay tự trả với NHNN."""
        if principal_amount <= 0:
            raise ValueError("Loan principal must be positive.")
        if tenor_months <= 0:
            raise ValueError("Tenor must be at least 1 month.")

        is_medium_long = tenor_months > 12 or is_extended_short_term
        tenor_cat = LoanTenorCategory.MEDIUM_LONG_TERM if is_medium_long else LoanTenorCategory.SHORT_TERM

        if is_medium_long:
            requires_registration = True
            deadline_days = 30
            advice = (
                f"Khoản vay {principal_amount:,.2f} {currency.upper()} thuộc diện VAY TRUNG/DÀI HẠN ({tenor_months} tháng). "
                f"BẮT BUỘC PHẢI ĐĂNG KÝ VỚI NGÂN HÀNG NHÀ NƯỚC (NHNN) trong vòng 30 ngày làm việc kể từ ngày ký thỏa thuận vay và trước khi rút vốn. "
                f"Mọi dòng tiền rút vốn và trả nợ phải thực hiện qua 01 Tài khoản vay, trả nợ nước ngoài hợp lệ."
            )
        else:
            requires_registration = False
            deadline_days = 0
            advice = (
                f"Khoản vay ngắn hạn ({tenor_months} tháng) KHÔNG PHẢI ĐĂNG KÝ với NHNN. "
                f"Tuy nhiên, nếu khoản vay được gia hạn mà tổng thời hạn trên 12 tháng, doanh nghiệp phải thực hiện đăng ký với NHNN trong vòng 30 ngày kể từ ngày thỏa thuận gia hạn."
            )

        return SBVForeignLoanRegistrationResult(
            principal_amount=principal_amount,
            currency=currency.upper(),
            tenor_months=tenor_months,
            tenor_category=tenor_cat,
            requires_sbv_registration=requires_registration,
            registration_deadline_days=deadline_days,
            account_type_required="Tài khoản vay, trả nợ nước ngoài (DICA / Offshore Loan Account)",
            legal_basis="Điều 11 & Điều 13 Thông tư 12/2022/TT-NHNN & Thông tư 06/2019/TT-NHNN",
            advice_vn=advice,
        )

    @classmethod
    def check_fdi_profit_remittance(
        cls,
        enterprise_name: str,
        current_year_net_profit_vnd: float,
        accumulated_losses_vnd: float,
        has_audited_financial_statements: bool,
        tax_obligations_completed: bool,
    ) -> ProfitRemittanceEligibilityResult:
        """Kiểm tra điều kiện chuyển lợi nhuận ra nước ngoài của doanh nghiệp FDI (TT 186/2010/TT-BTC)."""
        reasons = []
        if not has_audited_financial_statements:
            reasons.append("Chưa có Báo cáo tài chính năm được kiểm toán độc lập")
        if not tax_obligations_completed:
            reasons.append("Chưa hoàn thành toàn bộ nghĩa vụ thuế TNDN và các nghĩa vụ tài chính với Nhà nước")
        if accumulated_losses_vnd > 0:
            reasons.append(f"Doanh nghiệp còn lỗ lũy kế ({accumulated_losses_vnd:,.0f} VNĐ) theo luật Thuế TNDN")

        is_eligible = len(reasons) == 0 and current_year_net_profit_vnd > 0
        max_remittance = max(0.0, current_year_net_profit_vnd - accumulated_losses_vnd) if is_eligible else 0.0

        if is_eligible:
            advice = (
                f"DOANH NGHIỆP ĐỦ ĐIỀU KIỆN CHUYỂN LỢI NHUẬN: Số tiền tối đa được phép chuyển ra nước ngoài là "
                f"{max_remittance:,.0f} VNĐ. Doanh nghiệp phải thông báo cho cơ quan thuế trực tiếp quản lý ít nhất 07 ngày làm việc trước khi thực hiện chuyển tiền."
            )
        else:
            advice = (
                f"CHƯA ĐỦ ĐIỀU KIỆN CHUYỂN LỢI NHUẬN RA NƯỚC NGOÀI. Các vướng mắc cần xử lý: {'; '.join(reasons)}. "
                f"Theo Thông tư 186/2010/TT-BTC, nhà đầu tư nước ngoài không được chuyển lợi nhuận khi doanh nghiệp còn lỗ lũy kế."
            )

        return ProfitRemittanceEligibilityResult(
            fdi_enterprise_name=enterprise_name,
            net_profit_vnd=current_year_net_profit_vnd,
            accumulated_losses_vnd=accumulated_losses_vnd,
            has_audited_financial_report=has_audited_financial_statements,
            tax_obligations_completed=tax_obligations_completed,
            is_eligible_for_remittance=is_eligible,
            maximum_remittance_amount_vnd=max_remittance,
            advice_vn=advice,
        )


# ============================================================================
# PHASE 169: TECHNOLOGY TRANSFER & IP LICENSING ROYALTY ENGINE
# ============================================================================


@dataclass(frozen=True)
class TechnologyTransferRegistrationCheck:
    transfer_type: str
    involves_state_capital: bool
    is_cross_border: bool
    requires_mandatory_registration: bool
    registration_authority: str
    registration_deadline_days: int
    advice_vn: str


@dataclass(frozen=True)
class RoyaltyCalculationResult:
    gross_revenue_vnd: float
    deductions_vnd: float
    net_sales_vnd: float
    royalty_rate_pct: float
    royalty_payable_vnd: float
    is_within_market_standard: bool
    profit_split_benchmark_vnd: float
    legal_basis: str
    advice_vn: str


class TechnologyTransferEngine:
    """Đăng ký chuyển giao công nghệ & Định giá tiền bản quyền (Luật CGCN 2017 & NĐ 76/2018/NĐ-CP)."""

    @classmethod
    def evaluate_contract_registration(
        cls,
        transfer_type: str,
        is_cross_border: bool = True,
        involves_state_capital: bool = False,
    ) -> TechnologyTransferRegistrationCheck:
        """Đánh giá nghĩa vụ đăng ký hợp đồng CGCN theo Điều 31 Luật Chuyển giao công nghệ 2017."""
        requires_reg = is_cross_border or involves_state_capital
        authority = (
            "Bộ Khoa học và Công nghệ (BKHCN) hoặc Sở KHCN tỉnh/thành phố"
            if requires_reg
            else "Tự nguyện đăng ký để hưởng ưu đãi thuế"
        )
        deadline = 90 if requires_reg else 0

        if requires_reg:
            advice = (
                "Hợp đồng CGCN thuộc diện BẮT BUỘC ĐĂNG KÝ (Do chuyển giao công nghệ xuyên biên giới hoặc sử dụng vốn nhà nước). "
                "Thời hạn nộp hồ sơ đăng ký: Trong vòng 90 ngày kể từ ngày ký kết hợp đồng. Giấy chứng nhận đăng ký là căn cứ để chuyển tiền ra nước ngoài và khấu trừ thuế."
            )
        else:
            advice = (
                "Hợp đồng CGCN trong nước không sử dụng vốn nhà nước KHÔNG BẮT BUỘC ĐĂNG KÝ. "
                "Tuy nhiên, các bên có quyền đăng ký tự nguyện để được hưởng các chính sách ưu đãi thuế TNDN và hỗ trợ chuyển giao công nghệ của Nhà nước."
            )

        return TechnologyTransferRegistrationCheck(
            transfer_type=transfer_type,
            involves_state_capital=involves_state_capital,
            is_cross_border=is_cross_border,
            requires_mandatory_registration=requires_reg,
            registration_authority=authority,
            registration_deadline_days=deadline,
            advice_vn=advice,
        )

    @classmethod
    def calculate_running_royalty(
        cls,
        gross_revenue_vnd: float,
        discounts_returns_vnd: float = 0.0,
        packing_shipping_vnd: float = 0.0,
        duties_taxes_vnd: float = 0.0,
        royalty_rate_pct: float = 3.0,
        projected_operating_profit_vnd: Optional[float] = None,
    ) -> RoyaltyCalculationResult:
        """Tính tiền bản quyền theo Phương pháp Running Royalty trên Doanh thu thuần (Net Sales)."""
        deductions = max(0.0, discounts_returns_vnd) + max(0.0, packing_shipping_vnd) + max(0.0, duties_taxes_vnd)
        net_sales = max(0.0, gross_revenue_vnd - deductions)
        royalty_payable = round(net_sales * (royalty_rate_pct / 100.0), 2)

        # 25% Profit Split Rule benchmark
        profit_split_benchmark = (
            projected_operating_profit_vnd * 0.25
            if projected_operating_profit_vnd is not None and projected_operating_profit_vnd > 0
            else 0.0
        )

        is_standard = 0.5 <= royalty_rate_pct <= 8.0

        advice = (
            f"Tiền bản quyền tính theo doanh thu thuần ({net_sales:,.0f} VNĐ) với tỷ lệ {royalty_rate_pct:.2f}% là "
            f"{royalty_payable:,.0f} VNĐ. "
        )
        if profit_split_benchmark > 0:
            advice += (
                f"Đối chiếu theo Quy tắc chia sẻ lợi nhuận 25% (25% Profit Split Rule), mức tham chiếu hợp lý là "
                f"{profit_split_benchmark:,.0f} VNĐ. "
            )
        if not is_standard:
            advice += "CẢNH BÁO: Mức tỷ lệ ngoài khung thông lệ 0.5% - 8.0%, cần thẩm định kỹ rủi ro chuyển giá (Transfer Pricing - NĐ 132/2020)."

        return RoyaltyCalculationResult(
            gross_revenue_vnd=gross_revenue_vnd,
            deductions_vnd=deductions,
            net_sales_vnd=net_sales,
            royalty_rate_pct=royalty_rate_pct,
            royalty_payable_vnd=royalty_payable,
            is_within_market_standard=is_standard,
            profit_split_benchmark_vnd=profit_split_benchmark,
            legal_basis="Điều 12 & Điều 22 Luật Chuyển giao công nghệ 2017 & Nghị định 76/2018/NĐ-CP",
            advice_vn=advice,
        )


# ============================================================================
# PHASE 170: BONDED WAREHOUSE & CFS LOGISTICS OPERATION ENGINE
# ============================================================================


class StorageFacilityType(str, Enum):
    BONDED_WAREHOUSE = "bonded_warehouse"  # Kho ngoại quan
    CFS_STATION = "cfs_station"  # Trạm thu gom hàng lẻ CFS
    TAX_SUSPENDED_WAREHOUSE = "tax_suspended_warehouse"  # Kho bảo thuế


@dataclass(frozen=True)
class StorageLimitationStatus:
    facility_type: StorageFacilityType
    entry_date: str
    check_date: str
    days_stored: int
    statutory_max_initial_days: int
    maximum_possible_days_with_extension: int
    is_within_initial_term: bool
    is_expired: bool
    can_request_extension: bool
    remaining_initial_days: int
    remaining_total_days: int
    allowed_operations: List[str]
    advice_vn: str


class BondedLogisticsEngine:
    """Vận hành kho ngoại quan, trạm CFS & kho bảo thuế (Điều 61-88 Luật Hải quan 2014)."""

    BONDED_INITIAL_DAYS = 365  # 12 months
    BONDED_MAX_EXTENSION_DAYS = 365  # 1 extension max 12 months (Total 730 days)
    CFS_MAX_DAYS = 90  # 90 days max for CFS

    @classmethod
    def evaluate_storage_period(
        cls,
        facility_type: str,
        entry_date_str: str,
        check_date_str: Optional[str] = None,
        already_extended: bool = False,
    ) -> StorageLimitationStatus:
        """Kiểm tra thời hạn lưu kho ngoại quan và trạm CFS (Điều 61 Luật Hải quan 2014)."""
        f_type_str = facility_type.lower().strip()
        if "cfs" in f_type_str:
            facility = StorageFacilityType.CFS_STATION
            initial_days = cls.CFS_MAX_DAYS
            max_days = cls.CFS_MAX_DAYS
            allowed_ops = [
                "Đóng gói, sắp xếp lại hàng hóa của nhiều chủ hàng",
                "Chia tách, đóng ghép hàng hóa xuất khẩu/nhập khẩu",
                "Lấy mẫu hàng hóa phục vụ kiểm tra hải quan",
            ]
        elif "bao_thue" in f_type_str or "suspended" in f_type_str:
            facility = StorageFacilityType.TAX_SUSPENDED_WAREHOUSE
            initial_days = cls.BONDED_INITIAL_DAYS
            max_days = cls.BONDED_INITIAL_DAYS
            allowed_ops = [
                "Lưu trữ nguyên liệu nhập khẩu để sản xuất hàng xuất khẩu",
                "Quản lý theo dõi định mức tiêu hao nguyên vật liệu",
            ]
        else:
            facility = StorageFacilityType.BONDED_WAREHOUSE
            initial_days = cls.BONDED_INITIAL_DAYS
            max_days = cls.BONDED_INITIAL_DAYS + cls.BONDED_MAX_EXTENSION_DAYS
            allowed_ops = [
                "Gia cố, đóng gói lại, chia gói, đóng ghép hàng hóa",
                "Phân loại, bảo dưỡng và lấy mẫu hàng hóa",
                "Chuyển quyền sở hữu hàng hóa trong thời gian lưu kho",
                "Tái xuất ra nước ngoài hoặc nhập khẩu vào nội địa",
            ]

        entry_d = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
        chk_d = (
            datetime.strptime(check_date_str, "%Y-%m-%d").date()
            if check_date_str
            else date.today()
        )

        days_stored = (chk_d - entry_d).days
        is_within_initial = 0 <= days_stored <= initial_days
        is_expired = days_stored > (max_days if already_extended else initial_days)
        can_extend = (
            facility == StorageFacilityType.BONDED_WAREHOUSE
            and not already_extended
            and days_stored <= initial_days
        )

        remaining_init = max(0, initial_days - days_stored)
        remaining_tot = max(0, max_days - days_stored)

        if facility == StorageFacilityType.CFS_STATION:
            if is_expired:
                advice = (
                    f"HÀNG HÓA TẠI CFS ĐÃ QUÁ THỜI HẠN 90 NGÀY ({days_stored} ngày). "
                    f"Cơ quan Hải quan sẽ tiến hành lập biên bản và xử lý theo quy định (tịch thu hoặc bán đấu giá)."
                )
            else:
                advice = (
                    f"Hàng hóa trong thời hạn lưu trữ CFS hợp lệ ({days_stored} / 90 ngày). "
                    f"Còn lại {remaining_init} ngày để hoàn tất việc gom/tách và thông quan xuất nhập khẩu."
                )
        else:
            if is_expired:
                advice = (
                    f"HÀNG HÓA KHO NGOẠI QUAN ĐÃ HẾT HẠN LƯU KHO ({days_stored} ngày). "
                    f"Hàng hóa buộc phải tái xuất hoặc nhập khẩu vào nội địa, nếu không sẽ bị xử lý thanh lý theo quy định."
                )
            elif already_extended:
                advice = (
                    f"Hàng hóa đang trong giai đoạn gia hạn lưu kho ({days_stored} / {max_days} ngày). "
                    f"Thời gian lưu kho còn lại: {remaining_tot} ngày. Không được gia hạn thêm lần thứ hai."
                )
            else:
                advice = (
                    f"Hàng hóa đang trong thời hạn lưu kho đợt đầu 12 tháng ({days_stored} / 365 ngày). "
                    f"Còn lại {remaining_init} ngày. Trước khi hết hạn 30 ngày, doanh nghiệp có thể nộp đơn xin gia hạn 01 lần lên Cục Hải quan."
                )

        return StorageLimitationStatus(
            facility_type=facility,
            entry_date=entry_d.isoformat(),
            check_date=chk_d.isoformat(),
            days_stored=days_stored,
            statutory_max_initial_days=initial_days,
            maximum_possible_days_with_extension=max_days,
            is_within_initial_term=is_within_initial,
            is_expired=is_expired,
            can_request_extension=can_extend,
            remaining_initial_days=remaining_init,
            remaining_total_days=remaining_tot,
            allowed_operations=allowed_ops,
            advice_vn=advice,
        )

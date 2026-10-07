"""
Core Engine for Vietnam Free Trade Agreements (FTAs), Export Processing Enterprises (EPE),
Authorized Economic Operator (AEO), and Customs Duty Exemption & Refund Suite (Phases 171-174).

100% Python Standard Library - Zero External Dependencies.

Statutory References:
- Phase 171: FTAs & Rules of Origin
  * Nghị định 115/2022/NĐ-CP (Biểu thuế EVFTA 2022-2027)
  * Nghị định 116/2022/NĐ-CP (Biểu thuế CPTPP 2022-2027)
  * Nghị định 129/2022/NĐ-CP (Biểu thuế RCEP 2022-2027)
  * Thông tư 11/2020/TT-BCT (EVFTA ROO), Thông tư 03/2019/TT-BCT (CPTPP ROO), Thông tư 32/2022/TT-BCT (RCEP ROO)
- Phase 172: EPE & Industrial Parks
  * Nghị định 35/2022/NĐ-CP (Quản lý KCN & KKT, Điều 26-28 DNCX)
  * Luật Thuế XNK 2016 (Điều 2), Luật Thuế GTGT (Điều 9)
  * Thông tư 38/2015/TT-BTC & Thông tư 39/2018/TT-BTC (Điều 86 XNK tại chỗ, Điều 75 Phế liệu/phế phẩm)
  * Quyết định 247/QĐ-TCHQ (Camera giám sát DNCX)
- Phase 173: AEO & Risk Management
  * Luật Hải quan 2014 (Điều 42-45 Doanh nghiệp ưu tiên)
  * Thông tư 72/2015/TT-BTC & Thông tư 07/2019/TT-BTC
  * Quyết định 1399/QĐ-TCHQ (Phân luồng hải quan Xanh / Vàng / Đỏ)
- Phase 174: Duty Exemption, Refund & BCQT 15
  * Luật Thuế XNK 2016 (Luật số 107/2016/QH13)
  * Nghị định 134/2016/NĐ-CP & Nghị định 18/2021/NĐ-CP (Điều 10, Điều 34, Điều 36)
  * Mẫu 15/BCQT-NVL/GSQL (Thông tư 39/2018/TT-BTC)
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# =====================================================================
# Phase 171: FTAs Preferential Tariffs & Rules of Origin
# =====================================================================

class FTAAgreement(str, Enum):
    EVFTA = "EVFTA"
    CPTPP = "CPTPP"
    RCEP = "RCEP"
    ATIGA = "ATIGA"
    VKFTA = "VKFTA"
    VJEPA = "VJEPA"
    ACFTA = "ACFTA"
    AHKFTA = "AHKFTA"
    VN_EAEU = "VN_EAEU"


class OriginCriterion(str, Enum):
    WO = "WO"          # Wholly Obtained (Xuất xứ thuần túy)
    CC = "CC"          # Change of Chapter (Chuyển đổi Chương 2 số)
    CTH = "CTH"        # Change of Tariff Heading (Chuyển đổi Nhóm 4 số)
    CTSH = "CTSH"      # Change of Tariff Sub-heading (Chuyển đổi Phân nhóm 6 số)
    RVC = "RVC"        # Regional Value Content (Hàm lượng giá trị khu vực)
    SP = "SP"          # Specific Process (Công đoạn chế biến cụ thể)
    DE_MINIMIS = "DE_MINIMIS"  # Dung sai tỷ lệ nguyên liệu không xuất xứ


@dataclass
class FTATariffComparison:
    customs_value_vnd: float
    mfn_rate_pct: float
    fta_rate_pct: float
    mfn_duty_vnd: float
    fta_duty_vnd: float
    duty_savings_vnd: float
    savings_pct: float
    effective_agreement: str
    advice_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OriginQualificationResult:
    product_hs: str
    criterion: str
    is_qualified: bool
    rvc_calculated_pct: Optional[float]
    rvc_threshold_pct: Optional[float]
    non_originating_value_pct: Optional[float]
    de_minimis_threshold_pct: Optional[float]
    proof_type_required: str
    details_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FTATariffOriginEngine:
    """Engine tính toán tiết kiệm thuế ưu đãi đặc biệt và thẩm định tiêu chí xuất xứ FTA."""

    @staticmethod
    def calculate_tariff_savings(
        customs_value_vnd: float,
        mfn_rate_pct: float,
        fta_rate_pct: float,
        agreement: str = "EVFTA",
    ) -> FTATariffComparison:
        """Tính số tiền thuế nhập khẩu tiết kiệm khi hưởng ưu đãi FTA so với thuế MFN."""
        if customs_value_vnd <= 0:
            raise ValueError("Trị giá hải quan phải là số dương lớn hơn 0.")
        if mfn_rate_pct < 0 or fta_rate_pct < 0:
            raise ValueError("Thuế suất không được là số âm.")

        mfn_duty = round(customs_value_vnd * (mfn_rate_pct / 100.0), 2)
        fta_duty = round(customs_value_vnd * (fta_rate_pct / 100.0), 2)
        savings = round(mfn_duty - fta_duty, 2)
        savings_pct = round((savings / mfn_duty * 100.0), 2) if mfn_duty > 0 else 0.0

        decree_map = {
            "EVFTA": "Nghị định 115/2022/NĐ-CP",
            "CPTPP": "Nghị định 116/2022/NĐ-CP",
            "RCEP": "Nghị định 129/2022/NĐ-CP",
            "ATIGA": "Nghị định 126/2022/NĐ-CP",
        }
        decree_ref = decree_map.get(agreement.upper(), "Nghị định Biểu thuế ưu đãi đặc biệt")

        if savings > 0:
            advice = (
                f"Sử dụng ưu đãi thuế quan đặc biệt theo hiệp định {agreement} ({decree_ref}) giúp doanh nghiệp tiết kiệm "
                f"{savings:,.0f} VNĐ tiền thuế nhập khẩu (giảm {savings_pct}% so với thuế suất MFN). "
                f"Cần chuẩn bị bộ chứng từ chứng nhận xuất xứ (C/O hoặc Chứng nhận tự chứng nhận xuất xứ) hợp lệ."
            )
        elif savings == 0:
            advice = (
                f"Thuế suất FTA ({fta_rate_pct}%) bằng với thuế suất MFN ({mfn_rate_pct}%). "
                f"Biểu thuế ưu đãi FTA không mang lại chênh lệch tiền thuế phải nộp."
            )
        else:
            advice = (
                f"Cảnh báo: Thuế suất FTA ({fta_rate_pct}%) đang cao hơn thuế suất MFN ({mfn_rate_pct}%). "
                f"Doanh nghiệp nên áp dụng thuế suất MFN để tối ưu chi phí."
            )

        return FTATariffComparison(
            customs_value_vnd=customs_value_vnd,
            mfn_rate_pct=mfn_rate_pct,
            fta_rate_pct=fta_rate_pct,
            mfn_duty_vnd=mfn_duty,
            fta_duty_vnd=fta_duty,
            duty_savings_vnd=savings,
            savings_pct=savings_pct,
            effective_agreement=agreement.upper(),
            advice_vn=advice,
        )

    @staticmethod
    def evaluate_origin_criterion(
        product_hs: str,
        criterion: str,
        non_originating_materials_hs: Optional[List[str]] = None,
        rvc_actual_pct: Optional[float] = None,
        rvc_threshold_pct: float = 40.0,
        non_originating_value_fob_pct: Optional[float] = None,
        agreement: str = "CPTPP",
    ) -> OriginQualificationResult:
        """
        Thẩm định điều kiện đáp ứng xuất xứ theo tiêu chí cụ thể (WO, CC, CTH, CTSH, RVC, De Minimis).
        """
        product_clean = product_hs.replace(".", "").strip()
        criterion_upper = criterion.upper().strip()
        non_originating_materials = non_originating_materials_hs or []

        is_qualified = False
        rvc_calc = None
        rvc_thresh = None
        non_orig_val = None
        de_minimis_thresh = None
        proof_type = "C/O Form hoặc Chứng từ tự chứng nhận xuất xứ hợp lệ"
        details = ""

        # Determine proof type standard
        agr_upper = agreement.upper()
        if "EVFTA" in agr_upper:
            proof_type = "C/O Form EUR.1 (cho lô > 6,000 EUR) hoặc Tự chứng nhận REX (lô <= 6,000 EUR)"
        elif "CPTPP" in agr_upper:
            proof_type = "Chứng từ tự chứng nhận xuất xứ CPTPP (Certification of Origin)"
        elif "RCEP" in agr_upper:
            proof_type = "C/O Form RCEP hoặc Tự chứng nhận xuất xứ bởi Nhà xuất khẩu đủ điều kiện"
        elif "ATIGA" in agr_upper:
            proof_type = "C/O Form D hoặc C/O điện tử e-Form D"

        if criterion_upper == "WO":
            is_qualified = len(non_originating_materials) == 0 and (non_originating_value_fob_pct is None or non_originating_value_fob_pct == 0.0)
            details = (
                "Hàng hóa có xuất xứ thuần túy (Wholly Obtained) 100% được sản xuất/thu hoạch tại lãnh thổ nước thành viên."
                if is_qualified else "Hàng hóa KHÔNG đạt tiêu chí WO do có sử dụng nguyên liệu không có xuất xứ."
            )

        elif criterion_upper == "CC":
            # Change of Chapter (2-digit HS)
            prod_chapter = product_clean[:2]
            conflict_hs = [hs for hs in non_originating_materials if hs.replace(".", "")[:2] == prod_chapter]
            is_qualified = len(conflict_hs) == 0
            if is_qualified:
                details = f"Đạt tiêu chí Chuyển đổi Chương (CC): Toàn bộ nguyên liệu không xuất xứ thuộc các Chương khác Chương {prod_chapter}."
            else:
                details = f"Không đạt tiêu chí Chuyển đổi Chương (CC): Có nguyên liệu không xuất xứ cùng Chương {prod_chapter} ({', '.join(conflict_hs)})."

        elif criterion_upper == "CTH":
            # Change of Tariff Heading (4-digit HS)
            prod_heading = product_clean[:4]
            conflict_hs = [hs for hs in non_originating_materials if hs.replace(".", "")[:4] == prod_heading]
            is_qualified = len(conflict_hs) == 0
            if is_qualified:
                details = f"Đạt tiêu chí CTH: Toàn bộ nguyên liệu không xuất xứ có mã HS 4 số khác Nhóm {prod_heading}."
            else:
                details = f"Không đạt CTH: Có nguyên liệu không xuất xứ trùng Nhóm 4 số {prod_heading} ({', '.join(conflict_hs)})."

        elif criterion_upper == "CTSH":
            # Change of Tariff Sub-heading (6-digit HS)
            prod_subheading = product_clean[:6]
            conflict_hs = [hs for hs in non_originating_materials if hs.replace(".", "")[:6] == prod_subheading]
            is_qualified = len(conflict_hs) == 0
            if is_qualified:
                details = f"Đạt tiêu chí CTSH: Toàn bộ nguyên liệu không xuất xứ có mã HS 6 số khác Phân nhóm {prod_subheading}."
            else:
                details = f"Không đạt CTSH: Có nguyên liệu không xuất xứ trùng Phân nhóm 6 số {prod_subheading} ({', '.join(conflict_hs)})."

        elif criterion_upper == "RVC":
            rvc_thresh = rvc_threshold_pct
            if rvc_actual_pct is None:
                raise ValueError("Cần cung cấp tỷ lệ hàm lượng giá trị khu vực thực tế (rvc_actual_pct).")
            rvc_calc = round(rvc_actual_pct, 2)
            is_qualified = rvc_calc >= rvc_threshold_pct
            if is_qualified:
                details = f"Đạt tiêu chí hàm lượng RVC: Hàm lượng khu vực thực tế ({rvc_calc}%) >= ngưỡng yêu cầu ({rvc_threshold_pct}%)."
            else:
                details = f"Không đạt tiêu chí RVC: Hàm lượng khu vực thực tế ({rvc_calc}%) thấp hơn ngưỡng yêu cầu ({rvc_threshold_pct}%)."

        elif criterion_upper in ("DE_MINIMIS", "DEMINIMIS"):
            # De Minimis Rule (Tolerance threshold typically 10% FOB)
            de_minimis_thresh = 10.0
            if non_originating_value_fob_pct is None:
                raise ValueError("Cần cung cấp tỷ lệ giá trị nguyên liệu không xuất xứ so với FOB (non_originating_value_fob_pct).")
            non_orig_val = round(non_originating_value_fob_pct, 2)
            is_qualified = non_orig_val <= de_minimis_thresh
            if is_qualified:
                details = (
                    f"Đạt quy tắc De Minimis: Tỷ lệ nguyên liệu không chuyển đổi mã số ({non_orig_val}%) "
                    f"nằm trong hạn mức cho phép <= 10% giá trị FOB theo hiệp định {agreement}."
                )
            else:
                details = (
                    f"Không đạt quy tắc De Minimis: Tỷ lệ nguyên liệu không chuyển đổi mã số ({non_orig_val}%) "
                    f"vượt quá hạn mức tối đa cho phép 10% FOB."
                )
        else:
            raise ValueError(f"Tiêu chí xuất xứ không hợp lệ: {criterion}. Các tiêu chí hỗ trợ: WO, CC, CTH, CTSH, RVC, DE_MINIMIS.")

        return OriginQualificationResult(
            product_hs=product_hs,
            criterion=criterion_upper,
            is_qualified=is_qualified,
            rvc_calculated_pct=rvc_calc,
            rvc_threshold_pct=rvc_thresh,
            non_originating_value_pct=non_orig_val,
            de_minimis_threshold_pct=de_minimis_thresh,
            proof_type_required=proof_type,
            details_vn=details,
        )

    @staticmethod
    def determine_proof_of_origin(
        agreement: str,
        consignment_value_eur: float = 0.0,
        is_approved_exporter: bool = False,
    ) -> Dict[str, Any]:
        """Xác định hình thức chứng từ chứng nhận xuất xứ cần xuất trình."""
        agr = agreement.upper()
        if agr == "EVFTA":
            if consignment_value_eur <= 6000.0 or is_approved_exporter:
                form = "Tự chứng nhận xuất xứ REX (Statement on Origin with REX number)"
                mechanism = "Tự chứng nhận trên hóa đơn hoặc chứng từ thương mại"
            else:
                form = "C/O Form EUR.1"
                mechanism = "Cấp bởi Phòng Quản lý XNK - Bộ Công Thương Việt Nam"
        elif agr == "CPTPP":
            form = "Chứng từ tự chứng nhận xuất xứ CPTPP"
            mechanism = "Nhà xuất khẩu / Nhà sản xuất tự khai và ký tên chịu trách nhiệm theo Điều 3.20 Hiệp định CPTPP"
        elif agr == "RCEP":
            if is_approved_exporter:
                form = "Tự chứng nhận xuất xứ RCEP (Approved Exporter Declaration)"
                mechanism = "Tự chứng nhận bởi nhà xuất khẩu đủ điều kiện đã đăng ký mã số với Bộ Công Thương"
            else:
                form = "C/O Form RCEP"
                mechanism = "Cấp bởi cơ quan cấp C/O có thẩm quyền của nước thành viên"
        elif agr == "ATIGA":
            form = "C/O Mẫu D (Form D) hoặc e-Form D"
            mechanism = "Cấp giấy hoặc cấp điện tử qua Cổng thông tin một cửa quốc gia (NSW/ASW)"
        else:
            form = f"C/O Ưu đãi theo hiệp định {agreement}"
            mechanism = "Cấp bởi cơ quan có thẩm quyền theo quy chế hiệp định"

        return {
            "agreement": agr,
            "consignment_value_eur": consignment_value_eur,
            "is_approved_exporter": is_approved_exporter,
            "required_proof_form": form,
            "issuance_mechanism": mechanism,
        }


# =====================================================================
# Phase 172: Export Processing Enterprises (EPE) & Industrial Parks
# =====================================================================

@dataclass
class EPEComplianceCheck:
    is_compliant: bool
    missing_conditions: List[str]
    customs_supervision_status: str
    recommendations_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnSpotDeclarationStatus:
    export_declaration_date: str
    days_elapsed: int
    deadline_days: int
    is_overdue: bool
    remaining_days: int
    compliance_status: str
    advice_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScrapDomesticSaleDuty:
    scrap_value_vnd: float
    scrap_hs_code: str
    import_duty_rate_pct: float
    vat_rate_pct: float
    import_duty_vnd: float
    vat_vnd: float
    total_tax_payable_vnd: float
    declaration_type: str
    notes_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EPECustomsEngine:
    """Engine quản lý thủ tục hải quan, giám sát và chính sách thuế Doanh nghiệp chế xuất (DNCX)."""

    @classmethod
    def verify_supervision_conditions(
        cls,
        has_physical_fence: bool = True,
        has_24_7_camera_streaming: bool = True,
        has_separate_gate: bool = True,
        has_erp_connected: bool = True,
        has_physical_barrier: Optional[bool] = None,
        has_camera_24_7: Optional[bool] = None,
        has_erp_inventory: Optional[bool] = None,
    ) -> EPEComplianceCheck:
        """
        Kiểm tra 4 điều kiện kiểm tra, giám sát hải quan bắt buộc đối với DNCX
        theo Điều 26 Nghị định 35/2022/NĐ-CP & Quyết định 247/QĐ-TCHQ.
        """
        fence = has_physical_barrier if has_physical_barrier is not None else has_physical_fence
        camera = has_camera_24_7 if has_camera_24_7 is not None else has_24_7_camera_streaming
        gate = has_separate_gate
        erp = has_erp_inventory if has_erp_inventory is not None else has_erp_connected

        missing = []
        if not fence:
            missing.append("Hàng rào cứng ngăn cách hoàn toàn với khu vực bên ngoài (Physical fence)")
        if not camera:
            missing.append("Hệ thống camera giám sát 24/7 kết nối dữ liệu trực tuyến với Chi cục Hải quan (Camera)")
        if not gate:
            missing.append("Cổng/cửa ra vào riêng biệt đảm bảo kiểm soát phương tiện và hàng hóa (Separate gate)")
        if not erp:
            missing.append("Phần mềm quản lý ERP xuất nhập tồn nguyên liệu minh bạch (ERP software)")

        is_compliant = len(missing) == 0
        if is_compliant:
            status = "ĐỦ ĐIỀU KIỆN KIỂM TRA, GIÁM SÁT HẢI QUAN (DNCX)"
            rec = (
                "Doanh nghiệp ĐỦ ĐIỀU KIỆN đáp ứng đầy đủ 4/4 điều kiện quy định tại Điều 26 Nghị định 35/2022/NĐ-CP. "
                "Được áp dụng chính sách thuế đối với khu phi thuế quan (Thuế NK 0%, thuế GTGT 0% khi mua từ nội địa, không chịu thuế GTGT khi nhập từ nước ngoài)."
            )
        else:
            status = "CHƯA ĐỦ ĐIỀU KIỆN ÁP DỤNG CƠ CHẾ DNCX"
            rec = (
                f"Doanh nghiệp CHƯA ĐỦ ĐIỀU KIỆN, còn thiếu {len(missing)} điều kiện bắt buộc: {'; '.join(missing)}. "
                f"Cần khẩn trương hoàn thiện hạ tầng và gửi văn bản đề nghị Chi cục Hải quan kiểm tra xác nhận trước khi đưa vào vận hành."
            )

        return EPEComplianceCheck(
            is_compliant=is_compliant,
            missing_conditions=missing,
            customs_supervision_status=status,
            recommendations_vn=rec,
        )

    verify_epe_conditions = verify_supervision_conditions

    @classmethod
    def enforce_on_spot_deadline(
        cls,
        export_declaration_date_str: Optional[str] = None,
        reference_date_str: Optional[str] = None,
        export_declaration_date: Optional[str] = None,
        reference_date: Optional[str] = None,
    ) -> OnSpotDeclarationStatus:
        """
        Kiểm tra thời hạn hoàn thành tờ khai nhập khẩu tại chỗ đối ứng trong vòng 15 ngày làm việc
        kể từ ngày thông quan tờ khai xuất khẩu tại chỗ theo Điều 86 Thông tư 38/2015/TT-BTC & TT 39/2018/TT-BTC.
        """
        exp_input = export_declaration_date_str or export_declaration_date
        if not exp_input:
            raise ValueError("Định dạng ngày khai báo không hợp lệ (yêu cầu YYYY-MM-DD).")

        try:
            exp_date = datetime.strptime(exp_input.strip(), "%Y-%m-%d").date()
        except Exception:
            raise ValueError("Định dạng ngày khai báo không hợp lệ (yêu cầu YYYY-MM-DD).")

        ref_input = reference_date_str or reference_date
        if ref_input:
            try:
                ref_date = datetime.strptime(ref_input.strip(), "%Y-%m-%d").date()
            except Exception:
                raise ValueError("Định dạng ngày tham chiếu không hợp lệ (yêu cầu YYYY-MM-DD).")
        else:
            ref_date = datetime.now().date()

        days_elapsed = (ref_date - exp_date).days
        if days_elapsed < 0:
            raise ValueError("Ngày tham chiếu không thể trước ngày mở tờ khai xuất khẩu.")

        deadline = 15
        is_overdue = days_elapsed > deadline
        remaining = deadline - days_elapsed

        if is_overdue:
            comp_status = "QUÁ HẠN TỜ KHAI ĐỐI ỨNG (QUÁ HẠN)"
            advice = (
                f"Đã quá hạn {days_elapsed - deadline} ngày kể từ ngày thông quan tờ khai xuất khẩu tại chỗ ({days_elapsed} > 15 ngày). "
                f"Người nhập khẩu tại chỗ vi phạm thủ tục thời hạn hoàn thành tờ khai hải quan, bị xử phạt vi phạm hành chính và kiểm tra sau thông quan."
            )
        else:
            comp_status = "TRONG THỜI HẠN QUY ĐỊNH (HỢP LỆ)"
            advice = (
                f"Tờ khai nhập khẩu tại chỗ đang trong thời hạn xử lý hợp lệ ({days_elapsed}/{deadline} ngày). "
                f"Thời gian còn lại để hoàn thành thủ tục đối ứng: {remaining} ngày."
            )

        return OnSpotDeclarationStatus(
            export_declaration_date=exp_input,
            days_elapsed=days_elapsed,
            deadline_days=deadline,
            is_overdue=is_overdue,
            remaining_days=remaining,
            compliance_status=comp_status,
            advice_vn=advice,
        )

    check_on_spot_deadline = enforce_on_spot_deadline

    @classmethod
    def calculate_scrap_domestic_sale(
        cls,
        scrap_value_vnd: float,
        scrap_hs_code: str,
        import_duty_rate_pct: float,
        vat_rate_pct: float = 10.0,
    ) -> ScrapDomesticSaleDuty:
        """
        Tính tiền thuế nhập khẩu và thuế GTGT khi DNCX bán phế liệu, phế phẩm vào thị trường nội địa
        theo Điều 75 Thông tư 38/2015/TT-BTC sửa đổi bởi Thông tư 39/2018/TT-BTC.
        """
        if scrap_value_vnd <= 0:
            raise ValueError("Giá trị phế liệu bán nội địa phải lớn hơn 0.")
        if import_duty_rate_pct < 0 or vat_rate_pct < 0:
            raise ValueError("Thuế suất không được là số âm.")

        import_duty = round(scrap_value_vnd * (import_duty_rate_pct / 100.0), 2)
        vat_taxable_value = scrap_value_vnd + import_duty
        vat_amount = round(vat_taxable_value * (vat_rate_pct / 100.0), 2)
        total_tax = round(import_duty + vat_amount, 2)

        notes = (
            f"Khi bán phế liệu, phế phẩm vào thị trường nội địa, DNCX hoặc người mua nội địa phải mở tờ khai hải quan "
            f"theo loại hình A42 (Chuyển tiêu thụ nội địa). Trị giá tính thuế áp dụng theo giá bán thực tế "
            f"của phế liệu ({scrap_value_vnd:,.0f} VNĐ) theo mã HS {scrap_hs_code}."
        )

        return ScrapDomesticSaleDuty(
            scrap_value_vnd=scrap_value_vnd,
            scrap_hs_code=scrap_hs_code,
            import_duty_rate_pct=import_duty_rate_pct,
            vat_rate_pct=vat_rate_pct,
            import_duty_vnd=import_duty,
            vat_vnd=vat_amount,
            total_tax_payable_vnd=total_tax,
            declaration_type="A42",
            notes_vn=notes,
        )

    calculate_scrap_domestic_sale_tax = calculate_scrap_domestic_sale


# =====================================================================
# Phase 173: Authorized Economic Operator (AEO) & Risk Profiling
# =====================================================================

class EnterpriseType(str, Enum):
    GENERAL_TRADER = "GENERAL_TRADER"          # XNK chung (ngưỡng 100 triệu USD)
    AGRI_AQUA_TEXTILE = "AGRI_AQUA_TEXTILE"    # Nông thủy sản, dệt may, da giày (ngưỡng 40 triệu USD)
    HIGH_TECH_SOFTWARE = "HIGH_TECH_SOFTWARE"  # Công nghệ cao / Phần mềm (ngưỡng 30 triệu USD)
    CUSTOMS_BROKER = "CUSTOMS_BROKER"          # Đại lý thủ tục hải quan (20,000 tờ khai/năm)


@dataclass
class AEOEligibilityResult:
    is_eligible: bool
    enterprise_type: str
    annual_turnover_usd: float
    turnover_threshold_usd: float
    turnover_qualified: bool
    compliance_years: int
    compliance_qualified: bool
    audit_opinion_clean: bool
    reasons_unqualified: List[str]
    statutory_benefits_vn: List[str]
    summary_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CustomsChannelingAssessment:
    channel: str
    inspection_ratio_pct: float
    documentary_check_required: bool
    physical_inspection_required: bool
    handling_timeline_hours: float
    rationale_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AEOComplianceEngine:
    """Engine thẩm định điều kiện Doanh nghiệp Ưu tiên (AEO) và phân luồng quản lý rủi ro hải quan."""

    TURNOVER_THRESHOLDS_USD = {
        EnterpriseType.GENERAL_TRADER.value: 100_000_000.0,
        EnterpriseType.AGRI_AQUA_TEXTILE.value: 40_000_000.0,
        EnterpriseType.HIGH_TECH_SOFTWARE.value: 30_000_000.0,
        EnterpriseType.CUSTOMS_BROKER.value: 0.0,  # Đại lý tính theo tờ khai
    }

    @classmethod
    def evaluate_aeo_eligibility(
        cls,
        enterprise_type: str,
        annual_turnover_usd: float = 0.0,
        compliance_years: int = 2,
        had_major_tax_violations: bool = False,
        has_unqualified_audit: bool = False,
        custom_broker_declarations: int = 0,
        had_major_customs_tax_violations: Optional[bool] = None,
        customs_broker_declarations: Optional[int] = None,
    ) -> AEOEligibilityResult:
        """
        Thẩm định điều kiện công nhận Doanh nghiệp Ưu tiên (AEO)
        theo Điều 42 Luật Hải quan 2014 và Thông tư 72/2015/TT-BTC, Thông tư 07/2019/TT-BTC.
        """
        ent_type = enterprise_type.upper().strip()
        threshold = cls.TURNOVER_THRESHOLDS_USD.get(ent_type, 100_000_000.0)

        tax_violations = (
            had_major_customs_tax_violations
            if had_major_customs_tax_violations is not None
            else had_major_tax_violations
        )
        broker_decls = (
            customs_broker_declarations
            if customs_broker_declarations is not None
            else custom_broker_declarations
        )

        unqualified_reasons = []

        # 1. Turnover condition
        if ent_type == EnterpriseType.CUSTOMS_BROKER.value:
            turnover_qualified = broker_decls >= 20000
            if not turnover_qualified:
                unqualified_reasons.append(
                    f"Số lượng tờ khai hải quan ({broker_decls:,}) chưa đạt ngưỡng tối thiểu 20,000 tờ khai/năm đối với đại lý làm thủ tục hải quan."
                )
        else:
            turnover_qualified = annual_turnover_usd >= threshold
            if not turnover_qualified:
                unqualified_reasons.append(
                    f"Kim ngạch xuất nhập khẩu ({annual_turnover_usd:,.0f} USD) chưa đạt ngưỡng luật định tối thiểu ({threshold:,.0f} USD/năm)."
                )

        # 2. Compliance history condition
        compliance_qualified = compliance_years >= 2 and not tax_violations
        if compliance_years < 2:
            unqualified_reasons.append(
                f"Thời gian hoạt động tuân thủ pháp luật hải quan/thuế ({compliance_years} năm) chưa đủ tối thiểu 02 năm liên tục."
            )
        if tax_violations:
            unqualified_reasons.append(
                "Doanh nghiệp có lịch sử vi phạm nghiêm trọng pháp luật thuế hoặc hải quan trong 02 năm gần nhất."
            )

        # 3. Independent audit opinion condition
        audit_opinion_clean = not has_unqualified_audit
        if not audit_opinion_clean:
            unqualified_reasons.append(
                "Báo cáo tài chính không có ý kiến chấp nhận toàn phần (unqualified audit opinion) từ công ty kiểm toán độc lập."
            )

        is_eligible = len(unqualified_reasons) == 0

        benefits = [
            "Miễn kiểm tra hồ sơ hải quan chi tiết (tỷ lệ thông quan Luồng Xanh tự động >= 99%)",
            "Miễn kiểm tra thực tế hàng hóa (trừ trường hợp phát hiện dấu hiệu vi phạm rõ ràng)",
            "Được làm thủ tục hải quan bằng tờ khai chưa hoàn chỉnh và nộp tờ khai hoàn chỉnh trong 30 ngày",
            "Được nộp Báo cáo quyết toán năm trong thời hạn 90 ngày kể từ khi kết thúc năm tài chính",
            "Được ưu tiên làm thủ tục hải quan và giám sát 24/7 tại trụ sở doanh nghiệp hoặc chân công trình",
        ] if is_eligible else []

        summary = (
            "DOANH NGHIỆP ĐỦ ĐIỀU KIỆN ĐƯỢC XEM XÉT CÔNG NHẬN DOANH NGHIỆP ƯU TIÊN (AEO)."
            if is_eligible else
            f"DOANH NGHIỆP CHƯA ĐỦ ĐIỀU KIỆN AEO. Nguyên nhân: {'; '.join(unqualified_reasons)}"
        )

        return AEOEligibilityResult(
            is_eligible=is_eligible,
            enterprise_type=ent_type,
            annual_turnover_usd=annual_turnover_usd,
            turnover_threshold_usd=threshold,
            turnover_qualified=turnover_qualified,
            compliance_years=compliance_years,
            compliance_qualified=compliance_qualified,
            audit_opinion_clean=audit_opinion_clean,
            reasons_unqualified=unqualified_reasons,
            statutory_benefits_vn=benefits,
            summary_vn=summary,
        )

    @classmethod
    def assess_customs_risk_channel(
        cls,
        is_aeo: bool = False,
        enterprise_risk_score: float = 0.0,
        has_intelligence_alert: bool = False,
        random_inspection_hit: bool = False,
        risk_score: Optional[float] = None,
    ) -> CustomsChannelingAssessment:
        """Đánh giá phân luồng hải quan (Xanh / Vàng / Đỏ) và ước tính thời gian thông quan."""
        score = risk_score if risk_score is not None else enterprise_risk_score

        if has_intelligence_alert:
            channel = "RED"
            ratio = 100.0
            doc_check = True
            phy_check = True
            hours = 24.0
            rationale = "Cảnh báo nghiệp vụ trọng điểm từ cơ quan hải quan/tình báo chống buôn lậu."
        elif is_aeo:
            if random_inspection_hit:
                channel = "RED"
                ratio = 0.5
                doc_check = True
                phy_check = True
                hours = 4.0
                rationale = "Doanh nghiệp AEO rơi vào diện kiểm tra ngẫu nhiên định kỳ của hệ thống (tỷ lệ <= 0.5%)."
            else:
                channel = "GREEN"
                ratio = 0.0
                doc_check = False
                phy_check = False
                hours = 0.05
                rationale = "Ưu tiên luồng Xanh: Doanh nghiệp Ưu tiên (AEO) được miễn kiểm tra hồ sơ và miễn kiểm tra thực tế hàng hóa."
        else:
            if score >= 70.0:
                channel = "RED"
                ratio = 10.0
                doc_check = True
                phy_check = True
                hours = 12.0
                rationale = f"Điểm số rủi ro cao ({score}/100), yêu cầu kiểm tra thực tế hàng hóa (Luồng Đỏ)."
            elif score >= 30.0:
                channel = "YELLOW"
                ratio = 0.0
                doc_check = True
                phy_check = False
                hours = 2.0
                rationale = f"Điểm số rủi ro trung bình ({score}/100), yêu cầu kiểm tra chi tiết hồ sơ hải quan (Luồng Vàng)."
            else:
                channel = "GREEN"
                ratio = 0.0
                doc_check = False
                phy_check = False
                hours = 0.2
                rationale = f"Điểm số tuân thủ cao / rủi ro thấp ({score}/100), thông quan tự động (Luồng Xanh)."

        return CustomsChannelingAssessment(
            channel=channel,
            inspection_ratio_pct=ratio,
            documentary_check_required=doc_check,
            physical_inspection_required=phy_check,
            handling_timeline_hours=hours,
            rationale_vn=rationale,
        )

    assess_customs_channel = assess_customs_risk_channel


# =====================================================================
# Phase 174: Duty Exemption, Refund & Reconciliation (BCQT 15)
# =====================================================================

@dataclass
class DutyRefundCalculation:
    relief_type: str
    raw_material_imported_qty: float
    raw_material_exported_qty: float
    total_duty_paid_vnd: float
    refund_ratio_pct: float
    refund_duty_amount_vnd: float
    retained_duty_amount_vnd: float
    conditions_checked: List[str]
    advice_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MaterialReconciliationReport:
    opening_balance: float
    imported_in_period: float
    exported_finished_goods_qty: float
    bom_consumption_norm: float
    approved_scrap_qty: float
    theoretical_closing_balance: float
    actual_physical_inventory: float
    variance_qty: float
    is_balanced: bool
    is_deficit_risk: bool
    potential_unpaid_duty_vnd: float
    late_payment_interest_per_day_vnd: float
    audit_warning_vn: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DutyExemptionRefundEngine:
    """Engine tính toán hoàn thuế, miễn thuế XNK và cân đối Báo cáo Quyết toán Mẫu 15/BCQT-NVL/GSQL."""

    @classmethod
    def calculate_sxxk_duty_refund(
        cls,
        total_duty_paid_vnd: float,
        raw_material_imported_qty: float,
        raw_material_exported_qty: float,
    ) -> DutyRefundCalculation:
        """
        Tính số thuế nhập khẩu được hoàn đối với nguyên liệu nhập khẩu để sản xuất hàng xuất khẩu (SXXK)
        theo Điều 36 Nghị định 134/2016/NĐ-CP và Nghị định 18/2021/NĐ-CP.
        """
        if total_duty_paid_vnd <= 0:
            raise ValueError("Số thuế nhập khẩu đã nộp phải lớn hơn 0.")
        if raw_material_imported_qty <= 0:
            raise ValueError("Số lượng nguyên liệu nhập khẩu phải lớn hơn 0.")
        if raw_material_exported_qty < 0:
            raise ValueError("Số lượng nguyên liệu cấu thành trong sản phẩm xuất khẩu không được âm.")
        if raw_material_exported_qty > raw_material_imported_qty:
            raise ValueError("Số lượng nguyên liệu xuất khẩu không thể vượt quá tổng số lượng nguyên liệu nhập khẩu.")

        refund_ratio = round((raw_material_exported_qty / raw_material_imported_qty) * 100.0, 2)
        refund_amount = round(total_duty_paid_vnd * (raw_material_exported_qty / raw_material_imported_qty), 2)
        retained_amount = round(total_duty_paid_vnd - refund_amount, 2)

        conditions = [
            "Doanh nghiệp có quyền sở hữu hoặc sử dụng hợp pháp cơ sở sản xuất tại Việt Nam",
            "Nguyên liệu nhập khẩu đã thực tế đưa vào cấu thành sản phẩm đã thực xuất khẩu",
            "Đã thực hiện thủ tục hải quan xuất khẩu và nộp hồ sơ đề nghị hoàn thuế theo Mẫu số 09 Phụ lục VII NĐ 134/2016",
        ]

        advice = (
            f"Doanh nghiệp đủ điều kiện được hoàn {refund_amount:,.0f} VNĐ tiền thuế nhập khẩu "
            f"({refund_ratio}% tổng số thuế đã nộp) theo Điều 36 Nghị định 134/2016/NĐ-CP. "
            f"Số thuế nhập khẩu còn lại chưa hoàn ({retained_amount:,.0f} VNĐ) tương ứng với lượng nguyên liệu tồn kho hoặc tiêu thụ nội địa."
        )

        return DutyRefundCalculation(
            relief_type="HOÀN THUẾ SẢN XUẤT XUẤT KHẨU (Điều 36 NĐ 134/2016)",
            raw_material_imported_qty=raw_material_imported_qty,
            raw_material_exported_qty=raw_material_exported_qty,
            total_duty_paid_vnd=total_duty_paid_vnd,
            refund_ratio_pct=refund_ratio,
            refund_duty_amount_vnd=refund_amount,
            retained_duty_amount_vnd=retained_amount,
            conditions_checked=conditions,
            advice_vn=advice,
        )

    @classmethod
    def calculate_reexport_refund(
        cls,
        total_duty_paid_vnd: float,
        is_goods_unused_in_vietnam: bool = True,
        is_unused: Optional[bool] = None,
        re_exported_ratio: float = 1.0,
    ) -> DutyRefundCalculation:
        """
        Tính số thuế nhập khẩu được hoàn đối với hàng nhập khẩu nhưng phải tái xuất ra nước ngoài
        theo Điều 34 Nghị định 134/2016/NĐ-CP.
        """
        if total_duty_paid_vnd <= 0:
            raise ValueError("Số thuế nhập khẩu đã nộp phải lớn hơn 0.")
        if re_exported_ratio <= 0 or re_exported_ratio > 1.0:
            raise ValueError("Tỷ lệ hàng tái xuất phải nằm trong khoảng (0, 1.0].")

        unused = is_unused if is_unused is not None else is_goods_unused_in_vietnam

        if not unused:
            refund_amount = 0.0
            retained_amount = total_duty_paid_vnd
            refund_ratio = 0.0
            advice = (
                "Hàng hóa đã qua sử dụng, gia công hoặc chế biến tại Việt Nam KHÔNG ĐỦ ĐIỀU KIỆN hoàn thuế "
                "khi tái xuất theo quy định tại Khoản 1 Điều 34 Nghị định 134/2016/NĐ-CP."
            )
        else:
            refund_amount = round(total_duty_paid_vnd * re_exported_ratio, 2)
            retained_amount = round(total_duty_paid_vnd - refund_amount, 2)
            refund_ratio = round(re_exported_ratio * 100.0, 2)
            advice = (
                f"Doanh nghiệp ĐỦ ĐIỀU KIỆN được hoàn {refund_amount:,.0f} VNĐ "
                f"({refund_ratio}% tiền thuế nhập khẩu đã nộp) theo Điều 34 Nghị định 134/2016/NĐ-CP."
            )

        return DutyRefundCalculation(
            relief_type="HOÀN THUẾ HÀNG TÁI XUẤT (Điều 34 NĐ 134/2016)",
            raw_material_imported_qty=1.0,
            raw_material_exported_qty=re_exported_ratio,
            total_duty_paid_vnd=total_duty_paid_vnd,
            refund_ratio_pct=refund_ratio,
            refund_duty_amount_vnd=refund_amount,
            retained_duty_amount_vnd=retained_amount,
            conditions_checked=[
                "Hàng hóa chưa qua sử dụng, gia công, chế biến tại Việt Nam",
                "Có tờ khai tái xuất thông quan hợp lệ",
                "Có chứng từ thanh toán quốc tế hợp lệ",
            ],
            advice_vn=advice,
        )

    calculate_re_export_refund = calculate_reexport_refund

    @classmethod
    def reconcile_raw_materials_bcqt15(
        cls,
        opening_balance: float,
        imported_in_period: float,
        exported_finished_goods_qty: float,
        bom_consumption_norm: float,
        approved_scrap_qty: float = 0.0,
        actual_physical_inventory: float = 0.0,
        raw_material_unit_duty_vnd: float = 0.0,
    ) -> MaterialReconciliationReport:
        """
        Cân đối đối soát xuất nhập tồn nguyên liệu theo Báo cáo Quyết toán Mẫu 15/BCQT-NVL/GSQL
        (Thông tư 39/2018/TT-BTC) và cảnh báo rủi ro truy thu thuế chênh lệch âm (thiếu nguyên liệu).
        """
        if opening_balance < 0 or imported_in_period < 0 or exported_finished_goods_qty < 0:
            raise ValueError("Số lượng tồn, nhập, xuất không được âm.")
        if bom_consumption_norm <= 0:
            raise ValueError("Định mức tiêu hao nguyên vật liệu (BOM) phải lớn hơn 0.")

        total_consumed = exported_finished_goods_qty * bom_consumption_norm
        theoretical_closing = round(opening_balance + imported_in_period - total_consumed - approved_scrap_qty, 4)
        variance = round(actual_physical_inventory - theoretical_closing, 4)

        is_balanced = abs(variance) < 1e-4
        is_deficit = variance < -1e-4

        potential_unpaid_duty = 0.0
        late_fee_per_day = 0.0

        if is_deficit:
            deficit_qty = abs(variance)
            potential_unpaid_duty = round(deficit_qty * raw_material_unit_duty_vnd, 2)
            late_fee_per_day = round(potential_unpaid_duty * 0.0003, 2)  # 0.03%/ngày theo Luật QLT 2019
            warning = (
                f"CẢNH BÁO RỦI RO THIẾU HỤT NGUYÊN LIỆU ({deficit_qty:,.2f} đơn vị): Tồn kho thực tế thấp hơn tồn sổ sách lý thuyết. "
                f"Nguy cơ bị cơ quan Hải quan ấn định thuế nhập khẩu truy thu ({potential_unpaid_duty:,.0f} VNĐ) "
                f"và tiền chậm nộp ({late_fee_per_day:,.0f} VNĐ/ngày)."
            )
        elif variance > 1e-4:
            warning = (
                f"CẢNH BÁO CHÊNH LỆCH DƯ THỪA NGUYÊN LIỆU ({variance:,.2f} đơn vị): Tồn kho thực tế cao hơn tồn lý thuyết. "
                f"Cần rà soát lại định mức tiêu hao thực tế (BOM) hoặc nguồn gốc nguyên phụ liệu mua bổ sung từ thị trường nội địa."
            )
        else:
            warning = (
                "Báo cáo quyết toán CÂN BẰNG hoàn hảo: Tồn kho thực tế khớp đúng 100% với số liệu xuất nhập tồn lý thuyết."
            )

        return MaterialReconciliationReport(
            opening_balance=opening_balance,
            imported_in_period=imported_in_period,
            exported_finished_goods_qty=exported_finished_goods_qty,
            bom_consumption_norm=bom_consumption_norm,
            approved_scrap_qty=approved_scrap_qty,
            theoretical_closing_balance=theoretical_closing,
            actual_physical_inventory=actual_physical_inventory,
            variance_qty=variance,
            is_balanced=is_balanced,
            is_deficit_risk=is_deficit,
            potential_unpaid_duty_vnd=potential_unpaid_duty,
            late_payment_interest_per_day_vnd=late_fee_per_day,
            audit_warning_vn=warning,
        )

    reconcile_materials_bcqt15 = reconcile_raw_materials_bcqt15

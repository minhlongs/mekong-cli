# Research Report 14: Maritime SAR Operations, Wreck Salvage & ISPS Code Port Security

## 1. Statutory & Regulatory Framework
- **Nghị định 05/2017/NĐ-CP & Nghị định 30/2017/NĐ-CP**: Xử lý tài sản chìm đắm (Wreck Removal), hoạt động tìm kiếm cứu nạn hàng hải (SAR - Search and Rescue):
  - Phân vùng trách nhiệm SAR Việt Nam (Vietnam SAR Region I - Hải Phòng, Region II - Đà Nẵng, Region III - Vũng Tàu, Region IV - Nha Trang).
  - Trục vớt tài sản chìm đắm nguy hiểm cản trở luồng hàng hải: Thời hạn chủ tàu phải lập phương án trục vớt trong vòng 30 ngày kể từ ngày tàu chìm; quá hạn Cảng vụ Hàng hải chỉ định đơn vị trục vớt bắt buộc với chi phí do chủ tàu chịu kèm quyền lưu giữ hàng hải theo Bộ luật Hàng hải Việt Nam 2015 Điều 284.
- **ISPS Code (International Ship and Port Facility Security Code - SOLAS Ch. XI-2) & Nghị định 159/2018/NĐ-CP**:
  - 3 Cấp độ An ninh Cảng biển (Security Levels):
    - Level 1 (Normal): Các biện pháp an ninh tối thiểu thường xuyên (kiểm tra thẻ 100%, tuần tra định kỳ, rà soát xe ra vào ngẫu nhiên 20%).
    - Level 2 (Heightened): Tăng cường an ninh khi có nguy cơ an ninh (kiểm tra 100% người/xe, hạn chế cổng ra vào, tăng tuần tra bờ/mặt nước gấp đôi, chiếu sáng bổ sung).
    - Level 3 (Exceptional): Cấp độ đặc biệt nghiêm trọng khi nguy cơ an ninh sắp xảy ra hoặc đã xảy ra (dừng hoạt động bốc dỡ hàng, sơ tán khu vực, thiết lập vùng cấm tiếp cận, bàn giao an ninh cho lực lượng quốc phòng/công an).
  - Tuyên bố An ninh Cảng biển (Declaration of Security - DoS): Bắt buộc khi tàu và cảng hoạt động ở cấp độ an ninh khác nhau hoặc khi có yêu cầu đặc biệt từ SSO/PFSO.

## 2. Mathematical Models & Operational Invariants
- **SAR Search Area & Resource Allocation (IAMSAR Manual)**:
  - Bán kính tìm kiếm (Search Radius):
    $$R_{\text{search}} = \sqrt{E_{\text{datum}}^2 + E_{\text{nav}}^2} \times f_{\text{safety}}$$
  - Diện tích quét tìm kiếm (Area Coverage): $A = 2 \times R \times L_{\text{track}}$.
- **ISPS Code Compliance & Security Escalation State Machine**:
  - Quy tắc xác lập cấp độ an ninh giữa Tàu và Cảng: $\text{Operating Level} = \max(\text{Port Level}, \text{Ship Level})$.
  - Nếu $\text{Ship Level} \neq \text{Port Level} \rightarrow$ Bắt buộc ký và thực thi Tuyên bố An ninh (DoS).

## 3. Implementation Plan
- Class: `MaritimeSARAndSecurityEngine`
- Methods: `calculate_sar_datum_search_box`, `assess_wreck_removal_deadline`, `evaluate_isps_security_level`.

# Phase 01: VTS & TSS Traffic Management Engine

**Mục tiêu:** Xây dựng micro-engine kiểm soát phân luồng hàng hải TSS và hệ thống giám sát hành hải VTS theo IMO Res. A.1158(32) và COLREGs Rule 10.

## Yêu cầu Kỹ thuật
1. Kiểm tra tuân thủ luồng (Inbound/Outbound TSS lane compliance).
2. Phát hiện tàu đi ngược luồng ($\Delta \theta > 90^\circ$ so với hướng quy chuẩn).
3. Đánh giá khoảng cách tiếp cận gần nhất (CPA) và thời gian tiếp cận gần nhất (TCPA):
   - Cảnh báo rủi ro va chạm khi $\text{CPA} < 1.0\text{ NM}$ và $\text{TCPA} < 15.0\text{ phút}$.
4. Phân loại cấp độ dịch vụ VTS: Information Service (INS), Traffic Organization Service (TOS), Navigational Assistance Service (NAS).
5. File code: `src/core/maritime/phase_335_vts_tss_navigation.py` ($< 200\text{ LOC}$).

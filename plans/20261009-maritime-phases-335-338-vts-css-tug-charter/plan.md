# Kế hoạch Triển khai: Maritime Phases 335–338

**Chủ đề:** VTS/TSS Navigation, CSS Cargo Lashing, Electric Tug Cold Ironing & Charterparty Arbitration  
**Kiến trúc:** Hybrid Modular Facade (<200 LOC/file)

## Các Phân hệ Triển khai (Phases)

| Phase | Nội dung | Trạng thái |
|---|---|---|
| [Phase 01](phase-01-vts-tss-navigation.md) | VTS & TSS Phân luồng Hàng hải & CPA/TCPA (COLREGs Rule 10, IMO Res. A.1158(32)) | TODO |
| [Phase 02](phase-02-project-cargo-css-lashing.md) | Chằng buộc Hàng Siêu trường Siêu trọng OOG (IMO CSS Code Annex 13, $S_F \ge 1.25$) | TODO |
| [Phase 03](phase-03-electric-tug-cold-ironing.md) | Năng lượng Tàu lai Điện & Cấp điện Bến Cold Ironing (IEC/IEEE 80005, Peak Shaving) | TODO |
| [Phase 04](phase-04-charterparty-arbitration.md) | Hợp đồng Thuê tàu BIMCO & Phân xử Trọng tài LMAA/VMAC (Good Weather, Laytime) | TODO |
| [Phase 05](phase-05-facade-cli-mcp-tests.md) | Central Facade, Typer CLI, 8 Vietnamese Aliases, FastMCP & Zero-Mock Tests | TODO |

## Tiêu chí Nghiệm thu
- 100% file mã nguồn $< 200\text{ LOC}$.
- Không sử dụng mock data/giả lập.
- Tất cả unit tests và CLI tests đều vượt qua (100% green).
- Đăng ký công cụ FastMCP và tài liệu cập nhật đầy đủ.

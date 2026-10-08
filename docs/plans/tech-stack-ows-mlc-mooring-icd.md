# Tech Stack & Kiến trúc Hệ thống: Phases 283–286

Phạm vi:
- **Phase 283**: Thiết bị phân ly dầu nước OWS 15 ppm & Nhật ký dầu điện tử (ORB) Engine.
- **Phase 284**: Hợp đồng lao động thuyền viên, Tính lương MLC 2006 & Ký quỹ bảo lãnh hồi hương Engine.
- **Phase 285**: Dịch vụ buộc cởi dây tàu cảng biển Thông tư 39/2023/TT-BGTVT & An toàn dây MEG4 Engine.
- **Phase 286**: Cảng cạn ICD, Tờ khai vận chuyển độc lập OLA & Giám sát hải quan liên cảng Engine.

---

## 1. Nguyên tắc Kỹ thuật
- **Ngôn ngữ**: Python 3.9+ / Thư viện chuẩn (`dataclasses`, `enum`, `datetime`, `hashlib`, `math`, `typing`).
- **Zero External Dependencies**: AST-safe, deterministic, pure-Python logic.
- **Typer CLI**: Tích hợp trực tiếp vào cây lệnh `mekong` thông qua `build_app()`.
- **FastMCP**: JSON-RPC schema tuân thủ nghiêm ngặt, trả về chuỗi JSON rõ ràng với mã thông báo hash bảo mật 24 ký tự SHA-256.

## 2. Cấu trúc Module
- Lõi logic: `src/core/maritime_ows_mlc_mooring_icd_engine.py`
- Lệnh CLI: `src/cli/commands/maritime_ows_mlc_mooring_icd_command.py`
- Tích hợp App: `src/cli/app_setup.py` (nhóm lệnh `ows` / `tachdaula`, `mlcwages` / `luongthuyenvien`, `mooring` / `buocdaytau`, `icdtransit` / `cangcanicd`)
- FastMCP Server: `scripts/mcp_server.py`
- Bộ kiểm thử tự động: `tests/test_maritime_ows_mlc_mooring_icd_suite.py`

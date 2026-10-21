# Phase 03: Đăng ký FastMCP Tools trong MCP Server

## 1. Mục tiêu
Thêm 4 công cụ FastMCP an toàn vào `scripts/mcp_server.py`:
- `mekong_ballast_water_uscg_evaluate`
- `mekong_maritime_decarb_fueleu_evaluate`
- `mekong_port_lifting_gear_inspect`
- `mekong_oil_spill_oprc_neba_evaluate`

## 2. Checklist Thực hiện
- [x] Thêm các tools vào `scripts/mcp_server.py`.
- [x] Kiểm tra cú pháp bằng `python3 -m py_compile scripts/mcp_server.py` hoặc AST check.

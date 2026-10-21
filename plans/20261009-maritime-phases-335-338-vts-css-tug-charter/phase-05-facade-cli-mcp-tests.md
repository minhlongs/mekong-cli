# Phase 05: Central Facade, Typer CLI, 8 Vietnamese Aliases, FastMCP & Tests

**Mục tiêu:** Tích hợp toàn diện các phân hệ vào Mekong CLI v6.0 qua Central Facade, Typer CLI commands, song ngữ tiếng Việt, FastMCP tools và bộ kiểm thử zero-mock.

## Yêu cầu Kỹ thuật
1. Central Facade: `src/core/maritime_vts_css_tug_charter_engine.py` (< 200 LOC).
2. Typer CLI commands: `src/cli/commands/maritime_vts_css_tug_charter_command.py` (< 200 LOC).
3. Đăng ký trong `src/cli/app_setup.py`:
   - Nhóm lệnh: `vts`, `csscargo`, `electug`, `charter`.
   - Bí danh tiếng Việt: `luonghanghai`, `phanquyvts`, `hangsieutruong`, `changketoog`, `taulaidien`, `dienbencang`, `thuetautrongtai`, `tranhchaphanghai`.
4. FastMCP server endpoints trong `scripts/mcp_server.py`.
5. Zero-mock unit & integration tests trong `tests/test_maritime_vts_css_tug_charter_suite.py` (tối thiểu 18 tests xanh 100%).

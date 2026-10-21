# Phase 02: Tích hợp CLI Commands & Bilingual Aliases

## 1. Mục tiêu
Tạo file lệnh CLI `src/cli/commands/maritime_ballast_decarb_lifting_spill_command.py` và đăng ký 4 Typer apps cùng 8 bí danh tiếng Việt trong `src/cli/app_setup.py`.

## 2. Các Lệnh & Bí danh
- Lệnh: `ballast` (alias: `nuocdan`, `bwmuscg`) -> `ballast eval`
- Lệnh: `decarb` (alias: `giamphatthai`, `fueleu`) -> `decarb eval`
- Lệnh: `lifting` (alias: `thietbinang`, `cauport`) -> `lifting test`, `lifting inspect`
- Lệnh: `spill` (alias: `trandau`, `oprcneba`) -> `spill eval`

## 3. Checklist Thực hiện
- [x] Viết `src/cli/commands/maritime_ballast_decarb_lifting_spill_command.py`.
- [x] Đăng ký command groups trong `src/cli/app_setup.py`.
- [x] Kiểm tra số lượng groups đăng ký với `python3 -c "from src.cli.app_setup import build_app; print(len(build_app().registered_groups))"`.

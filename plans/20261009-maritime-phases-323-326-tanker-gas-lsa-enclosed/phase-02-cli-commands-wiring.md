# Phase 02: Xây dựng CLI Typer Commands & Đăng ký App Setup

## 1. Mục tiêu
- Xây dựng file command `src/cli/commands/maritime_tanker_gas_lsa_enclosed_command.py` hỗ trợ 4 Typer sub-apps với định dạng bảng rich / JSON xuất chuẩn.
- Đăng ký vào `src/cli/app_setup.py` với 8 bí danh tiếng Việt trực quan theo đúng convention hệ thống Mekong CLI v6.0.

## 2. Thiết kế Lệnh CLI
1. **Lệnh Rửa tàu dầu & hóa chất (`cow_app`)**:
   - `mekong cow eval --tank-id TK-01P --o2 6.5 --pressure 150 --cow-bar 8.5 ...`
   - `mekong cow chem-prewash --tank-id TK-03C --category CAT_X --viscosity 10 ...`
   - Alias tiếng Việt: `mekong ruaketdau`, `mekong cowmarpol`.
2. **Lệnh Quản lý khí bốc & CTMS (`bog_app`)**:
   - `mekong bog eval --volume 160000 --density 460 --heat-kw 220 ...`
   - Alias tiếng Việt: `mekong khigaslng`, `mekong ctmslng`.
3. **Lệnh Cơ cấu móc nhả & FPD xuồng cứu sinh (`lifeboat_app`)**:
   - `mekong lifeboat eval --boat-id LB-STBD --mode OFF_LOAD --total-weight 8500 --mbl 35 ...`
   - Alias tiếng Việt: `mekong xuongcuusinh`, `mekong fpdrelease`.
4. **Lệnh Cấp phép vào không gian kín (`enclosed_app`)**:
   - `mekong enclosed permit --space-name "Cargo Tank 1C" --o2 20.9 --lel 0.2 --h2s 1.0 --co 5.0 ...`
   - Alias tiếng Việt: `mekong khonggiankin`, `mekong entrypermit`.

## 3. Checklist Thực hiện
- [x] Viết `src/cli/commands/maritime_tanker_gas_lsa_enclosed_command.py`.
- [x] Đăng ký 4 Typer apps và 8 aliases vào `src/cli/app_setup.py`.
- [x] Thử nghiệm lệnh CLI trợ giúp: `python3 -m src.cli.entry cow --help`, v.v.

# Phase 02: Tích hợp CLI Commands & Bilingual Aliases

## 1. Mục tiêu
Tạo file CLI command `src/cli/commands/maritime_aton_vnsw_imsbc_hm_command.py` (< 200 LOC):
- 4 Typer apps: `aton_app`, `vnsw_app`, `imsbc_app`, `hm_app`.
- Đăng ký vào `src/cli/app_setup.py`:
  - `aton` / `phaotieu` / `iala`
  - `vnsw` / `motcua` / `imofal`
  - `imsbc` / `hangnguyhiem` / `hamhang`
  - `hmsurvey` / `giamdinhtau` / `tonthathm`

## 2. Checklist Thực hiện
- [ ] Xây dựng `src/cli/commands/maritime_aton_vnsw_imsbc_hm_command.py`
- [ ] Đăng ký command groups & aliases vào `src/cli/app_setup.py`
- [ ] Kiểm tra CLI hiển thị `--help` chính xác

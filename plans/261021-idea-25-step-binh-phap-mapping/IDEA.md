# /idea 25 buoc Open-Core — chay lai, chinh xac, co Anh xa Binh Phap (`--deep`)

## Problem / outcome

Chay lai toan bo pipeline `/idea` 25 buoc Open-Core (`TWENTY_FIVE_OPENCORE_STEPS`) o che do `--deep`, nhung lan nay **anh xa moi buoc vao dung mot chuong Binh Phap co the dispatch duoc**, va xac nhan trang thai thuc cua tung buoc trong repo — thay vi dua tren verdict xanh cua engine.

**Outcome cu the:**
1. Bang 25 dong: `buoc -> phase -> trang thai thuc (DONE/PARTIAL/MISSING/N/A) -> bang chung -> edition (community|cloud) -> chuong Binh Phap -> dispatch command`.
2. Moi chuong anh xa phai tro vao mot command **da ton tai** trong `CHAPTER_COMMANDS` (`src/core/binh_phap/topology.py`), vi `_command_to_chapter()` tra ve `0` cho command chua dang ky — va chapter 0 khong nam trong `COMMERCIAL_CHAPTERS`, nen no vo hinh voi route Fable 5 va voi approval gate.
3. Verdict trung thuc: tach ro "hygiene xanh" (da dat) khoi "monetization co enforce duoc" (chua).

## Users

- Founder/dev duy nhat cua Mekong CLI v6.0 — nguoi ra quyet dinh community vs cloud edition.
- Nguoi maintain repo cong khai MIT, can biet buoc nao chan public push va buoc nao chan thu tien.

## Scope (in)

- **25 buoc day du**, khong cat: trang thai, bang chung, edition, chuong Binh Phap, acceptance check cho tung buoc.
- Kiem tra lai toan bo baseline (khong tin plan 20:14 cu).
- Anh xa Binh Phap 13 chuong, dung `CHAPTER_COMMANDS` lam authority.
- Neu ro mau thuan noi bo da tim thay (chapter dispatch vs lifecycle, cac namespace tier).

## Scope (out) — Non-goals

- **Khong sua code trong phase plan nay.** Day la `/binh-phap plan` — dung o phe duyet plan, implement la phase rieng.
- **Khong mo lai quyet dinh da chot cua founder:** license GATE thuoc `community`, ENFORCEMENT cua tier tra phi thuoc `cloud`.
- **Khong sua `.mekong/company.json`** (da co `open_core_25_steps_aligned: true`, `revenue_events: []`).
- Khong dung `apps/dashboard/` (93 file public co chu dich).
- Khong xoa cac file false-positive IMO **Polar Code** (`phase_339_polar_code_polaris_rio.py`, `maritime_polar_wash_*`).
- Khong xoa webhook Polar trong `apps/dashboard/` — do la quyet dinh san pham can founder duyet.

## Acceptance checks

| # | Kiem tra | Lenh / dieu kien |
|---|---|---|
| 1 | Bang 25 buoc day du, moi buoc co trang thai + bang chung | Doc `plan.md` — 25 dong, 0 o trong |
| 2 | Moi chuong anh xa vao command that su dispatch duoc | Moi `dispatch_command` thuoc `CHAPTER_COMMANDS[ch]` |
| 3 | Blueprint van 25/25 dong bo | `audit_blueprint('.')` -> `synchronized=True, matched_steps_count=25` |
| 4 | Hygiene van xanh sau khi kiem tra | `verify_filesystem_hygiene('.').missing_items == ()` |
| 5 | Test suite xanh | `pytest tests/test_idea_deep_opencore_brainstorm.py` -> 6 passed |
| 6 | Moi claim co nhan that | Verified / Hypothesis / Target — khong con so bia |

## Constraints & risks

1. **Cay git dang ban** — 11 modified + 14 untracked, tat ca trong `src/cli/commands/*_commands_records_table.py`, `compliance_table_renderers.py`, 12 command module, `DEPLOYMENT_SUMMARY.md`, `ORIGINAL_REQUEST.md`. Phase implement phai xep hang quanh chung.
2. **LOC guard <= 180** cho cac folder duoc canh (`src/core/opencore`, `src/raas`, `src/api`, `src/middleware`, `src/cli` top-level, va cac danh sach `core_checked`/`cmd_checked` trong test).
3. **Verdict xanh khong bang monetization chay duoc.** `audit_repository()` nhan `jwt_license_gate_enforced=True` va `mcu_http402_billing_wired=True` la tham so tu phia goi, khong he tinh. CLI cung yeu tuong duong (`typer.Option(True, ...)`). Day la blocker trung thuc can dua vao plan.
4. **Loi MASTER:** `aliases()` gap ca `MASTER->pro` lan `ENTERPRISE->pro`, va `quotas.get(tier, quotas["free"])` tu dong ha tien lang ve free.
5. **Polar removal can founder duyet** — co webhook public trong `apps/dashboard/` va traffic that co the con goi.

## Evidence (Verified / Hypothesis / Target)

- **Verified:** moi du kien trong [evidence-baseline.md](evidence-baseline.md) — da chay lenh hom nay 2026-10-21.
- **Hypothesis:** trigger nang cap PLG (user tu host can multi-tenant/queue 24-7). Can phong van khach, chua co so lieu.
- **Target:** $199/$399/$799/$4,999 — muc gia founder dat, chua co giao dich thuc.

---

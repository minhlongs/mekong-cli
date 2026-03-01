# Plan: Fix Build — `turbo: command not found`

**Mission ID:** fix_mekong_cli_fix_build_1772358777885
**Priority:** HIGH
**Date:** 2026-03-01
**Status:** PLANNED (chưa implement)
**Max files sửa:** < 5

---

## Phân Tích Lỗi (Deep Research)

### Error Log
```
> mekong-cli@2.1.33 build
> npx turbo run build
sh: turbo: command not found
```

### Root Cause (đã xác nhận)

```
node_modules/turbo/              ✅ TỒN TẠI (v2.8.8)
node_modules/turbo/bin/turbo     ✅ CHẠY ĐƯỢC (output: 2.8.8)
node_modules/turbo-darwin-arm64  ❌ MISSING (optional dep chưa install)
node_modules/.bin/turbo          ❌ SYMLINK KHÔNG TỒN TẠI
npx turbo                        ❌ FAIL (tìm trong .bin/ → không thấy)
```

**Kết luận:** `pnpm install` đã chạy **không đầy đủ** — turbo package downloaded nhưng:
1. Symlink `.bin/turbo` chưa được tạo
2. Platform binary `turbo-darwin-arm64` chưa install

### Môi trường
- **pnpm** 9.15.0 (package manager chính, có `pnpm-lock.yaml`)
- **Node** v25.2.1
- **npm** 11.6.2
- **macOS ARM64** (M1 — cần `turbo-darwin-arm64`)
- **node_modules/.bin/** chỉ có 6 entries (rất ít cho monorepo)

---

## Giải Pháp (3 options, xếp theo ưu tiên)

### Option A: `pnpm install` lại (KHUYẾN NGHỊ — 0 file sửa)

```bash
cd /Users/macbookprom1/mekong-cli
pnpm install
```

Sẽ rebuild symlinks và install optional deps đúng platform.

**Ưu điểm:** Sửa đúng gốc, portable, đúng monorepo workflow
**Nhược điểm:** Mất 1-3 phút, cần network

### Option B: Tạo symlink thủ công (NHANH — 0 file sửa)

```bash
ln -sf ../turbo/bin/turbo /Users/macbookprom1/mekong-cli/node_modules/.bin/turbo
```

**Ưu điểm:** Instant fix, không cần network
**Nhược điểm:** Workaround, có thể bị mất khi install lại

### Option C: Sửa scripts dùng đường dẫn trực tiếp (1 file sửa)

Sửa `package.json` scripts thay `npx turbo` bằng `node node_modules/turbo/bin/turbo`:

```json
{
  "build": "node node_modules/turbo/bin/turbo run build",
  "test": "node node_modules/turbo/bin/turbo run test"
}
```

**Ưu điểm:** Không phụ thuộc symlink
**Nhược điểm:** Hacky, không conventional

---

## Implementation Steps (theo Option A → B fallback)

### Step 1: Thử `pnpm install`

```bash
cd /Users/macbookprom1/mekong-cli
pnpm install
```

### Step 2: Verify turbo binary

```bash
ls -la node_modules/.bin/turbo
npx turbo --version
```

### Step 3: Nếu Step 1 fail → Fallback symlink

```bash
ln -sf ../turbo/bin/turbo node_modules/.bin/turbo
chmod +x node_modules/.bin/turbo
npx turbo --version  # phải ra 2.8.8
```

### Step 4: Chạy build

```bash
npm run build
```

### Step 5: Nếu build fail vì workspace errors → debug từng package

---

## Files Cần Sửa

| # | File | Action | Điều kiện |
|---|------|--------|-----------|
| 0 | (none) | `pnpm install` | Option A — luôn thử trước |
| 1 | (none) | `ln -sf` symlink | Option B — nếu A fail |
| 2 | `package.json` | Sửa scripts | Option C — last resort |

**Worst case: 1 file sửa (package.json)**

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| `pnpm install` fail (network) | LOW | Fallback Option B (symlink) |
| Build fail vì lỗi khác (TS errors) | MEDIUM | Debug từng package riêng |
| Symlink bị xóa khi install lại | LOW | Chạy `pnpm install` lần sau sẽ tạo lại |

---

## Success Criteria

- [ ] `npx turbo --version` → `2.8.8`
- [ ] `node_modules/.bin/turbo` tồn tại
- [ ] `npm run build` exit code 0
- [ ] Không sửa quá 5 files

---

## Unresolved Questions

1. Tại sao `pnpm install` ban đầu không tạo symlink? Có thể do `--no-optional` flag hoặc install bị interrupt
2. Monorepo có 6 workspace packages — build có thể fail ở package nào đó sau khi turbo chạy được

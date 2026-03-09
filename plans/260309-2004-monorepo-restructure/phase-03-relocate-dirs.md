# Phase 3: Di Dời Root Dirs — Đưa Vào Đúng Vị Trí

## Overview
- **Ưu tiên:** P1 HIGH
- **Trạng thái:** TODO
- **Mô tả:** 19 thư mục rogue ở root không thuộc chuẩn monorepo. Mỗi cái cần đi vào đúng chỗ.

## Phân Tích 19 Root Dirs

### Nhóm A: DI CHUYỂN VÀO apps/ (sản phẩm deployable)

| Dir | Files | Lý do | Đích |
|-----|-------|-------|------|
| `frontend/` | **30,867** | Có thể chứa node_modules bị commit! Kiểm tra trước | `apps/web/` hoặc xóa nếu legacy |
| `api/` | 61 | FastAPI backend | `apps/api/` (đã có?) → gộp |
| `backend/` | 1,002 | Backend riêng | `apps/backend/` hoặc gộp vào api |
| `antigravity/` | 976 | Proxy system | `apps/antigravity-proxy/` |
| `cli/` | 54 | CLI frontend? | Gộp vào `src/cli/` nếu Python, hoặc `apps/cli/` |

### Nhóm B: DI CHUYỂN VÀO infra/ (DevOps, config)

| Dir | Files | Đích |
|-----|-------|------|
| `docker/` | 10 | `infra/docker/` |
| `config/` | 15 | `infra/config/` |
| `scripts/` | **215 files** | `infra/scripts/` (giữ root scripts/ symlink?) |
| `supabase/` | 51 | `infra/supabase/` |
| `templates/` | 11 | `infra/templates/` |

### Nhóm C: DI CHUYỂN VÀO packages/ hoặc src/

| Dir | Files | Đích |
|-----|-------|------|
| `core/` | 512 | Nếu Python → gộp `src/core/`. Nếu JS → `packages/core/` |
| `mekong/` | 6 | Gộp vào `src/` (Python package) |
| `lib/` | 2 | Gộp vào `packages/` hoặc `src/` |
| `locales/` | 8 | `packages/i18n/locales/` |

### Nhóm D: DI CHUYỂN VÀO docs/ hoặc XÓA

| Dir | Files | Đích |
|-----|-------|------|
| `knowledge/` | 22 | `docs/knowledge/` |
| `examples/` | 16 | `docs/examples/` |
| `recipes/` | 8 | `docs/recipes/` hoặc `src/recipes/` |
| `data/` | 0 | XÓA (rỗng) |
| `bin/` | 1 | Kiểm tra — có thể gộp vào scripts |
| `build/` | 1 | XÓA hoặc thêm vào .gitignore (build artifact) |

## Điểm Nóng: frontend/ (30K files!)

```bash
# KIỂM TRA TRƯỚC: có node_modules bị commit không?
ls frontend/node_modules 2>/dev/null && echo "NODE_MODULES COMMITTED!" || echo "OK"
du -sh frontend/
find frontend/ -name "node_modules" -type d
```

Nếu có `node_modules` → xóa khỏi git, thêm vào `.gitignore`.
Nếu frontend/ là legacy (đã có `apps/web/`) → archive hoặc xóa.

## Kiến Trúc Root Sau Di Dời

```
mekong-cli/
├── apps/                    # Deployable applications
├── packages/                # Shared libraries
├── src/                     # Python CLI core
├── tests/                   # Python tests
├── infra/                   # DevOps & infrastructure
│   ├── docker/
│   ├── scripts/
│   ├── config/
│   ├── supabase/
│   └── templates/
├── docs/                    # Documentation
│   ├── knowledge/
│   ├── examples/
│   └── recipes/
├── plans/                   # Implementation plans
├── tasks/                   # Mission files (openclaw)
├── .claude/                 # Claude config
├── .mekong/                 # Project state
├── .antigravity/            # Telemetry
└── [config files at root]
```

## Implementation Steps

1. **Kiểm tra frontend/** — xác định có node_modules không, có legacy không
2. **Phân tích core/** — xác định Python hay JS
3. **Tạo `infra/`** và di chuyển docker, scripts, config, supabase, templates
4. **Di chuyển knowledge, examples, recipes** vào docs/
5. **Xử lý antigravity/** — di chuyển vào apps/ nếu là deployable
6. **Gộp api/ + backend/** — quyết định 1 vị trí
7. **Xóa data/, build/** nếu rỗng/artifact
8. **Cập nhật mọi import paths** bị ảnh hưởng
9. **Cập nhật scripts** có hardcode paths

## Todo List

- [ ] Audit `frontend/` — node_modules? legacy?
- [ ] Audit `core/` — Python hay JS?
- [ ] Audit `cli/` — trùng với src/cli/?
- [ ] Tạo `infra/` directory
- [ ] Di chuyển infra dirs (docker, scripts, config, supabase, templates)
- [ ] Di chuyển docs dirs (knowledge, examples, recipes)
- [ ] Xử lý antigravity → apps/
- [ ] Gộp api + backend
- [ ] Xóa dirs rỗng
- [ ] Cập nhật imports + paths
- [ ] Verify build + tests

## Rủi Ro

- **scripts/ có 215 files** — nhiều scripts hardcode paths. Cần sed/replace cẩn thận
- **openclaw-worker** tham chiếu `../../scripts/` → cần cập nhật
- **factory-loop.sh** ở root tham chiếu nhiều paths
- **night-monitor.sh** hardcode `~/mekong-cli/apps/...`
- **frontend/ 30K files** — nếu có node_modules bị commit, git rm sẽ tốn thời gian

## Success Criteria

- Root chỉ còn: apps/, packages/, src/, tests/, infra/, docs/, plans/, tasks/, + config files
- Không còn thư mục rogue ở root
- Tất cả scripts vẫn chạy đúng
- Tests pass

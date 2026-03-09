# Phase 4: Tổ Chức apps/ — Tách Submodules, Phân Loại Apps

## Overview
- **Ưu tiên:** P1 HIGH
- **Trạng thái:** TODO
- **Mô tả:** 35 apps lẫn lộn: submodules, production apps, demos, legacy. Phân loại rõ ràng.

## Phân Tích 35 Apps

### Nhóm A: PRODUCTION APPS (GIỮ trong apps/) — 8 apps

| App | Loại | Stack | Submodule? |
|-----|------|-------|------------|
| `openclaw-worker/` | CTO Daemon | Node.js | Có (nhưng là core) |
| `algo-trader/` | Trading Bot | Node.js + Dashboard | Không |
| `raas-gateway/` | RaaS API | Node.js | Không |
| `raas-gateway-cli/` | RaaS CLI | Node.js | Không |
| `dashboard/` | Admin UI | React | Không |
| `web/` | Marketing site | Next.js | Không |
| `engine/` | Core engine | Node.js | Không |
| `analytics/` | Analytics | Node.js | Không |

### Nhóm B: SUBMODULE PRODUCTS (DI CHUYỂN → external/) — 9 apps

| App | Repo | Submodule |
|-----|------|-----------|
| `sophia-ai-factory/` | longtho638-jpg/sophia-ai-factory | ✅ |
| `well/` | longtho638-jpg/Well | ✅ |
| `84tea/` | longtho638-jpg/84tea | ✅ |
| `apex-os/` | longtho638-jpg/apex-os | ✅ |
| `anima119/` | longtho638-jpg/anima119 | ✅ |
| `com-anh-duong/` | PHIHOANG160314/COM-ANH-DUONG | ✅ |
| `com-anh-duong-10x/` | PHIHOANG160314/COM-ANH-DUONG | ✅ (trùng repo!) |
| `gemini-proxy-clone/` | lehuygiang28/gemini-proxy | ✅ |
| `starter-template/` | longtho638-jpg/agencyos-starter | ✅ |

### Nhóm C: CẦN ĐÁNH GIÁ (có thể legacy/demo)

| App | Files | Nhận xét |
|-----|-------|----------|
| `admin/` | 7 | Admin panel — có trùng với dashboard? |
| `agencyos-landing/` | 20 | Landing page — trùng với landing/? |
| `agencyos-web/` | 16 | Web app — trùng với web/? |
| `agentic-brain/` | 4 | Chỉ 4 files — stub? |
| `antigravity-cli/` | 3 | CLI wrapper — gộp vào antigravity? |
| `antigravity-gateway/` | 5 | Gateway — gộp vào raas-gateway? |
| `developers/` | 10 | Developer portal? |
| `docs/` | 12 | Docs app — trùng với root docs/? |
| `landing/` | 12 | Landing — trùng với agencyos-landing? |
| `project/` | 4 | Chỉ 4 files — stub? |
| `raas-demo/` | 10 | Demo — production hay prototype? |
| `sa-dec-flower-hunt/` | **134 files** | Side project? Không liên quan? |
| `sophia-proposal/` | 12 | Proposal doc — nên ở docs/ |
| `stealth-engine/` | 8 | Stealth — legacy? |
| `tasks/` | 25 | Không phải app — nên ở root tasks/ |
| `vibe-coding-cafe/` | 10 | Side project? |
| `worker/` | 7 | Worker — trùng với openclaw-worker? |

## Hành Động Đề Xuất

### 1. Tạo `external/` cho submodules
```bash
mkdir external/
git mv apps/sophia-ai-factory external/
git mv apps/well external/
git mv apps/84tea external/
git mv apps/apex-os external/
git mv apps/anima119 external/
git mv apps/com-anh-duong external/
git mv apps/com-anh-duong-10x external/  # Hoặc xóa vì trùng repo
git mv apps/gemini-proxy-clone external/
git mv apps/starter-template external/
```

### 2. Cập nhật `.gitmodules`
Thay tất cả `path = apps/X` → `path = external/X`

### 3. Xóa/Archive apps legacy
```bash
# Archive
mkdir -p .archive/legacy-apps
git mv apps/agentic-brain .archive/legacy-apps/
git mv apps/project .archive/legacy-apps/
git mv apps/sa-dec-flower-hunt .archive/legacy-apps/
git mv apps/vibe-coding-cafe .archive/legacy-apps/
git mv apps/sophia-proposal .archive/legacy-apps/

# Gộp trùng lặp
# agencyos-landing + landing → giữ 1
# agencyos-web + web → giữ 1
# admin + dashboard → giữ dashboard
# worker + openclaw-worker → giữ openclaw-worker
# antigravity-cli + antigravity-gateway → gộp
```

### 4. Di chuyển `apps/tasks/` → root `tasks/`
```bash
# apps/tasks/ không phải app — nó chứa mission files
# Gộp vào root tasks/ nếu khác nhau, hoặc xóa
```

## Kiến Trúc apps/ Sau Tổ Chức

```
apps/
├── algo-trader/          # Trading bot + dashboard
├── analytics/            # Analytics service
├── dashboard/            # Admin UI (React)
├── engine/               # Core engine
├── openclaw-worker/      # CTO Daemon (Tôm Hùm)
├── raas-gateway/         # RaaS API
├── raas-gateway-cli/     # RaaS CLI
└── web/                  # Marketing site (Next.js)

external/                 # Git submodules (separate repos)
├── sophia-ai-factory/
├── well/
├── 84tea/
├── apex-os/
├── anima119/
├── com-anh-duong/
├── gemini-proxy-clone/
└── starter-template/
```

## Cập Nhật Cần Thiết

- `apps/openclaw-worker/config.js` — PROJECTS array, routing paths
- `brain-spawn-manager.js` — dynamic routing tham chiếu apps/ paths
- `auto-cto-pilot.js` — project scanning paths
- `night-monitor.sh` — DIRS array
- `factory-loop.sh` — project paths
- `.gitmodules` — tất cả submodule paths
- `pnpm-workspace.yaml` — thêm `external/*`
- `turbo.json` — pipeline config

## Todo List

- [ ] Audit từng app trong Nhóm C — legacy hay production?
- [ ] Tạo `external/` directory
- [ ] Di chuyển 9 submodules
- [ ] Cập nhật `.gitmodules`
- [ ] Archive legacy apps
- [ ] Gộp trùng lặp (landing, web, admin, worker)
- [ ] Cập nhật config paths trong openclaw-worker
- [ ] Cập nhật night-monitor.sh, factory-loop.sh
- [ ] `pnpm install` verify
- [ ] Tests pass

## Rủi Ro

- **openclaw-worker di chuyển submodules** → Tôm Hùm dispatch hardcode `~/mekong-cli/apps/well` etc → phải đổi thành `~/mekong-cli/external/well`
- **tmux pane CWD** — dynamic routing đọc pane CWD, nếu panes đang cd vào `apps/well` → phải cd lại
- **com-anh-duong vs com-anh-duong-10x** — cùng 1 repo, 1 cái nên xóa
- **CI/CD** — nếu có workflow tham chiếu `apps/sophia-ai-factory` → cần update

## Success Criteria

- apps/ chỉ chứa production deployable apps (~8)
- Submodules ở external/ với paths đúng
- Legacy apps ở .archive/
- Không còn apps trùng lặp
- openclaw-worker routing vẫn hoạt động
- Tests pass

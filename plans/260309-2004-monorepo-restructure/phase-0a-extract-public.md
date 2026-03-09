# Phase 0A: Tach Private Code — Tao agencyos-sdk Public Repo

**Uu tien:** P0 SUPREME | **Effort:** ~4h | **Phu thuoc:** Khong
**Nhanh:** master | **Ngay:** 2026-03-09

## Muc tieu

Tach code public tu `mekong-cli` (PRIVATE) sang `agencyos-sdk` (PUBLIC repo moi).
Sau phase nay: mekong-cli chi con private code, agencyos-sdk san sang cho dev.

## Chien luoc

**KHONG dung git filter-branch.** Copy sach, khong lich su git cu (clean start).
Ly do: repo hien tai co secrets, 83MB repomix, .archive 848MB — khong the public git history.

---

## Buoc 1: Tao agencyos-sdk repo moi

```bash
# 1.1 Tao repo tren GitHub
gh repo create longtho638-jpg/agencyos-sdk --public --description "AgencyOS SDK — Revenue-as-a-Service for developers" --license MIT

# 1.2 Clone va init
cd ~/Projects
git clone git@github.com:longtho638-jpg/agencyos-sdk.git
cd agencyos-sdk

# 1.3 Init monorepo
pnpm init
mkdir -p packages apps docs examples tests .github/workflows
```

## Buoc 2: Copy PUBLIC packages tu mekong-cli

Danh sach CHINH XAC cac thu muc can copy:

### Packages (10 packages)

| Source (mekong-cli) | Dest (agencyos-sdk) | npm name |
|---------------------|---------------------|----------|
| `packages/core/` | `packages/core/` | `@mekong/core` |
| `packages/billing/` | `packages/billing/` | `@mekong/billing` |
| `packages/agents/` | `packages/agents/` | `@mekong/agents` |
| `packages/ui/` | `packages/ui/` | `@mekong/ui` |
| `packages/vibe-auth/` | `packages/auth/` | `@mekong/auth` |
| `packages/i18n/` | `packages/i18n/` | `@mekong/i18n` |
| `packages/observability/` | `packages/observability/` | `@mekong/observability` |
| `packages/vibe-dev/` | `packages/vibe-dev/` | `@mekong/vibe-dev` |
| `src/raas/` (partial) | `packages/raas/` | `@mekong/raas` |
| `packages/shared/` | `packages/shared/` | `@mekong/shared` |

```bash
SRC=~/mekong-cli
DST=~/Projects/agencyos-sdk

# Copy packages (exclude node_modules, __pycache__, dist)
for pkg in core billing agents ui i18n shared; do
  rsync -av --exclude='node_modules' --exclude='__pycache__' --exclude='dist' \
    "$SRC/packages/$pkg/" "$DST/packages/$pkg/"
done

# Rename copies
rsync -av --exclude='node_modules' --exclude='dist' \
  "$SRC/packages/vibe-auth/" "$DST/packages/auth/"
rsync -av --exclude='node_modules' --exclude='dist' \
  "$SRC/packages/vibe-dev/" "$DST/packages/vibe-dev/"
rsync -av --exclude='__pycache__' \
  "$SRC/packages/observability/" "$DST/packages/observability/"
```

### RaaS Package (special — extract tu Python)

`@mekong/raas` = TypeScript wrapper goi RaaS API. Extract TU `src/raas/` nhung CHI lay:
- `sdk.py` logic → convert sang TS
- `license_models.py` types → TS interfaces
- `billing.py`, `credits.py` → billing integration

**CHU Y:** Day la package moi, KHONG copy Python truc tiep. Tao TS package moi voi:
- `packages/raas/src/index.ts` — RaaS client
- `packages/raas/src/types.ts` — license/billing types
- `packages/raas/src/checkout.ts` — Polar checkout integration
- `packages/raas/package.json` — `"name": "@mekong/raas"`

### Apps (4 apps)

| Source | Dest | Mo ta |
|--------|------|-------|
| `apps/web/` | `apps/web/` | Marketing site |
| `apps/dashboard/` | `apps/dashboard/` | Admin UI demo |
| `apps/raas-demo/` | `apps/raas-demo/` | RaaS demo |
| `apps/docs/` | `apps/docs/` | Docs app |

```bash
for app in web dashboard raas-demo docs; do
  rsync -av --exclude='node_modules' --exclude='.next' --exclude='dist' \
    "$SRC/apps/$app/" "$DST/apps/$app/"
done
```

### Docs & Examples

```bash
# Copy docs (filter internal-only files)
rsync -av "$SRC/docs/" "$DST/docs/" \
  --exclude='HIEN_PHAP*' --exclude='BINH_PHAP*' --exclude='SKILLS_REGISTRY*'

# Copy examples
rsync -av --exclude='node_modules' "$SRC/examples/" "$DST/examples/"

# Copy tests (only public package tests)
rsync -av --exclude='__pycache__' "$SRC/tests/raas/" "$DST/tests/raas/"
```

### Root Config Files

```bash
cp "$SRC/tsconfig.base.json" "$DST/"
cp "$SRC/tsconfig.json" "$DST/"
cp "$SRC/turbo.json" "$DST/"
cp "$SRC/.prettierrc" "$DST/" 2>/dev/null
cp "$SRC/.eslintrc.*" "$DST/" 2>/dev/null
```

## Buoc 3: Setup agencyos-sdk workspace

### pnpm-workspace.yaml

```yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

### package.json (root)

```json
{
  "name": "agencyos-sdk",
  "version": "0.1.0",
  "private": true,
  "packageManager": "pnpm@9.15.0",
  "description": "AgencyOS SDK — Revenue-as-a-Service for developers",
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "publish-packages": "pnpm -r publish --access public"
  },
  "devDependencies": {
    "turbo": "^2.0.0",
    "typescript": "^5.4.0"
  }
}
```

### .gitignore

```
node_modules/
dist/
.next/
__pycache__/
*.pyc
.env*
.DS_Store
```

## Buoc 4: Lam sach mekong-cli (PRIVATE)

SAU KHI copy xong, KHONG xoa gi tu mekong-cli ngay. Chi:

1. **Them .gitignore entries** cho files da copy (tranh confuse)
2. **Update pnpm-workspace.yaml** — loai bo public packages khoi workspace neu can
3. **Cap nhat imports** trong openclaw-worker, algo-trader neu chung tro den packages da extract

**KHONG XOA** code tu mekong-cli trong phase nay. Phase 0B se lam viec xoa.

## Buoc 5: Verify agencyos-sdk

```bash
cd ~/Projects/agencyos-sdk

# 5.1 Install deps
pnpm install

# 5.2 Build all
pnpm build

# 5.3 Type check
pnpm exec tsc --noEmit

# 5.4 Test
pnpm test

# 5.5 Dry-run publish
pnpm -r publish --dry-run --access public
```

## Buoc 6: Setup cross-repo references

### Option A: npm link (dev)

```bash
# Trong mekong-cli, link sang agencyos-sdk packages
cd ~/Projects/agencyos-sdk/packages/core && pnpm link --global
cd ~/mekong-cli && pnpm link --global @mekong/core
```

### Option B: Git submodule (production)

```bash
# Trong mekong-cli, them agencyos-sdk nhu submodule
cd ~/mekong-cli
git submodule add git@github.com:longtho638-jpg/agencyos-sdk.git external/agencyos-sdk
# Import tu: external/agencyos-sdk/packages/core
```

### Option C: Published npm packages (recommended for production)

Sau khi publish len npm, mekong-cli chi can `pnpm add @mekong/core @mekong/raas`.
Day la option tot nhat — 2 repos hoan toan doc lap.

**Khuyen nghi:** Dev dung Option A, Production dung Option C.

---

## Danh sach PRIVATE (GIU trong mekong-cli)

| Path | Ly do |
|------|-------|
| `apps/openclaw-worker/` | CTO Brain — competitive advantage |
| `apps/algo-trader/` | Trading algorithms — proprietary |
| `apps/raas-gateway/` | Production gateway — internal |
| `apps/raas-gateway-cli/` | Gateway CLI — internal |
| `apps/analytics/` | Internal analytics |
| `apps/sophia-ai-factory/` | Client submodule |
| `apps/well/` | Client submodule |
| `apps/84tea/` | Client submodule |
| `apps/apex-os/` | Client submodule |
| `apps/anima119/` | Client submodule |
| `apps/com-anh-duong*/` | Client submodule |
| `apps/gemini-proxy-clone/` | Forked tool |
| `apps/antigravity-cli/` | Internal proxy CLI |
| `apps/antigravity-gateway/` | Internal proxy gateway |
| `packages/trading-core/` | Trading algorithms |
| `packages/vibe-arbitrage-engine/` | Arbitrage engine |
| `packages/mekong-engine/` | Internal engine |
| `packages/mekong-clawwork/` | Internal framework |
| `packages/mekong-moltbook/` | Internal tool |
| `packages/openclaw-agents/` | Internal agents |
| `antigravity/` | Proxy infra |
| `scripts/` | Internal scripts (215 files) |
| `tasks/` | Mission files |
| `factory-loop.sh` | Automation |
| `tom-hum/` | Daemon dir |
| `src/` (Python CLI) | CLI core — stays in mekong-cli |
| `.mekong/`, `.antigravity/` | Runtime state |
| `knowledge/` | Internal docs |

## Danh sach XOA (Phase 0B, KHONG lam o day)

Xem `phase-0b-prune.md` (chua tao). Bao gom:
- 35 hub-sdk stubs
- ~55 vibe-* stubs
- Legacy apps (admin, agentic-brain, landing, etc.)
- Rogue root dirs (frontend/ 555MB, backend/ 5.6MB, core/ 2.4MB, cli/ 284K)
- repomix-output.xml (83MB), .archive/ (848MB)

---

## Rui ro

| Risk | Muc do | Giam thieu |
|------|--------|------------|
| Secrets trong copied files | CAO | Grep `API_KEY\|SECRET\|sk-\|password` truoc khi commit |
| Broken imports after extract | TRUNG BINH | Build + test truoc khi push |
| packages/observability la Python | THAP | Giu la Python package, them pyproject.toml |
| @mekong/raas can tao tu dau (TS) | TRUNG BINH | Phase 0C xu ly chi tiet |

## Checklist

- [ ] Tao agencyos-sdk repo tren GitHub
- [ ] Copy 10 packages
- [ ] Copy 4 apps
- [ ] Copy docs (filter internal)
- [ ] Setup workspace config
- [ ] Grep secrets truoc khi commit
- [ ] pnpm install + build + test pass
- [ ] First commit + push
- [ ] Verify mekong-cli van build OK
- [ ] Setup cross-repo linking (dev)

## Cau hoi chua giai quyet

1. **Namespace:** Dung `@mekong/*` hay `@agencyos/*` cho npm packages? (Hien tai CLAUDE.md dung ca 2)
2. **packages/observability/** la Python — co nen convert sang TS cho consistency khong?
3. **packages/shared/** — co du content de extract hay merge vao core?
4. **apps/developers/** — co nen copy sang public khong? (hien tai khong trong danh sach)
5. **apps/starter-template/** — co nen la public template app?

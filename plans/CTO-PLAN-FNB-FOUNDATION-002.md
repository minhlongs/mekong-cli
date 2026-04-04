# CODING PLAN #002 — FnB Caffe Container Foundation Fix

> **Ngày tạo**: 2026-03-21
> **Priority**: P0 → P1
> **Agent assignment**: Claude Code CLI (TMUX worker panes)
> **Nguồn**: FnB Full Stack Discovery Report (2026-03-20)
> **App path**: `apps/fnb-caffe-container/`

---

## Objective

Thống nhất backend (chọn CF Worker + D1, loại bỏ Python API trùng lặp), migrate JSON data → D1, implement auth backend, setup CI/CD, refactor CSS/JS monolith, và đưa dự án về trạng thái production-ready.

## Context

- **15+ pages** frontend đã build xong
- **38 JS modules** hoạt động, nhưng `checkout.js` 32KB cần split
- **styles.css** 104KB monolith
- **Dual backend**: CF Worker + Python FastAPI → logic trùng lặp
- **Auth**: chỉ frontend, backend `auth/` folder trống
- **Data**: JSON files thay vì D1 database
- **CI/CD**: deploy thủ công bằng script

---

## PHASE 1 — Backend Unification (P0) ⭐

### Task 1.1 — Audit dual backend
```bash
cd /Users/mac/mekong-cli/apps/fnb-caffe-container
# List all Worker routes
grep -rn "router\|addEventListener\|fetch" worker/src/ --include="*.js"
# List all Python API routes  
grep -rn "@app\.\|@router\." src/ --include="*.py"
```
- **Goal**: Map ra tất cả routes trùng lặp giữa Worker và Python

### Task 1.2 — Consolidate to CF Worker + D1
- **Action**: Giữ CF Worker (`worker/src/`), archive Python API (`src/api/` → `src/api-legacy/`)
- **Routes cần giữ**: auth, menu, orders, reviews, payments, loyalty
- **Agent**: Claude Code Worker P0

```bash
# Archive Python API
mkdir -p src/api-legacy
git mv src/api/*.py src/api-legacy/ 2>/dev/null
git mv src/main.py src/api-legacy/ 2>/dev/null
```

### Task 1.3 — Migrate JSON → D1 Schema
- **Files**: `data/menu-data.json`, `data/loyalty-config.json`, `data/orders.json`, `data/carts.json`
- **Action**: Tạo D1 migration SQL từ JSON data

```bash
cd /Users/mac/mekong-cli/apps/fnb-caffe-container
# Create migrations folder
mkdir -p worker/migrations
```

- Create `worker/migrations/0001_seed_data.sql` với INSERT statements từ JSON
- Update Worker routes để đọc từ D1 thay vì JSON

### Task 1.4 — Commit Phase 1
```bash
git add -A
git commit -m "refactor(fnb): unify backend to CF Worker + D1, archive Python API"
```

---

## PHASE 2 — Auth & Security (P0)

### Task 2.1 — Implement CF Access auth
- **File**: `worker/src/auth.js` — enhance existing
- **Features**: Token-based auth, session management, role-based access (admin/staff/customer)
- **Agent**: Claude Code Worker P1

### Task 2.2 — Secure payment webhooks
- **Files**: `worker/src/orders.js`, payment handling
- Implement HMAC-SHA256 signature verification for VNPay/MoMo/PayOS callbacks
- Rate limiting trên tất cả API endpoints

### Task 2.3 — Remove demo credentials
```bash
cd /Users/mac/mekong-cli/apps/fnb-caffe-container
grep -rn "demo\|password.*123\|admin@\|test.*key" --include="*.html" --include="*.js" . | grep -v node_modules | grep -v .git
```

### Task 2.4 — Commit Phase 2
```bash
git add -A
git commit -m "security(fnb): implement CF Access auth, secure webhooks, remove demo creds"
```

---

## PHASE 3 — Code Quality Refactor (P1)

### Task 3.1 — Split styles.css (104KB → modules)
- **Agent**: Claude Code Worker P0
- Split into component files:

```
css/
├── base.css          # Reset, typography, variables
├── layout.css        # Grid, containers
├── components.css    # Buttons, cards, forms
├── menu.css          # Menu-specific styles
├── checkout.css      # Checkout-specific
├── loyalty.css       # Loyalty program
├── admin.css         # Admin dashboard
├── kds.css           # Kitchen display
├── animations.css    # Micro-animations
└── responsive.css    # Media queries
```

### Task 3.2 — Refactor checkout.js (32KB → modules)
- **Agent**: Claude Code Worker P1
- Extract into:

```
js/
├── checkout/
│   ├── index.js          # Entry point
│   ├── cart-manager.js   # Cart state (merge with existing cart.js)
│   ├── payment-flow.js   # Payment gateway logic
│   ├── validation.js     # Form validation
│   └── ui.js             # Checkout UI updates
```

### Task 3.3 — ESLint fix
```bash
cd /Users/mac/mekong-cli/apps/fnb-caffe-container
npx eslint . --fix --max-warnings=0
```

### Task 3.4 — Commit Phase 3
```bash
git add -A
git commit -m "refactor(fnb): split CSS monolith, refactor checkout.js, eslint cleanup"
```

---

## PHASE 4 — CI/CD & Deploy (P1)

### Task 4.1 — Setup GitHub Actions
- **Agent**: Claude Code Worker P0
- **File**: `.github/workflows/deploy.yml`

```yaml
name: Deploy FnB
on:
  push:
    branches: [main]
    paths: ['apps/fnb-caffe-container/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
        working-directory: apps/fnb-caffe-container
      - run: npm run lint
        working-directory: apps/fnb-caffe-container
      - run: npm test
        working-directory: apps/fnb-caffe-container
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          workingDirectory: apps/fnb-caffe-container
```

### Task 4.2 — Build optimization
```bash
cd /Users/mac/mekong-cli/apps/fnb-caffe-container
npm run build
# Verify Lighthouse score > 90
```

### Task 4.3 — Deploy to Cloudflare Pages
```bash
cd /Users/mac/mekong-cli/apps/fnb-caffe-container
npx wrangler pages deploy . --project-name=fnb-caffe-container
```

### Task 4.4 — Commit Phase 4
```bash
git add -A
git commit -m "ci(fnb): add GitHub Actions deploy pipeline, optimize build"
git push origin main
```

---

## Acceptance Criteria

- [ ] Python API archived → `src/api-legacy/`
- [ ] CF Worker handles ALL routes (auth, menu, orders, payments, loyalty)
- [ ] JSON data migrated to D1 schema
- [ ] Auth backend functional (token + session + roles)
- [ ] Payment webhooks secured (HMAC-SHA256)
- [ ] No demo credentials in codebase
- [ ] `styles.css` split into ≤10 component CSS files
- [ ] `checkout.js` refactored into 5+ modules
- [ ] ESLint passes with 0 warnings
- [ ] GitHub Actions deploy pipeline working
- [ ] Cloudflare Pages deployment successful
- [ ] `git status` clean after all commits

## Constraints

- **DO NOT** delete frontend pages — chỉ refactor backend + styling
- **DO NOT** thay đổi payment sandbox keys — production keys là Phase riêng
- Sử dụng `git mv` để giữ history
- Mỗi phase commit riêng để dễ rollback

## Estimated Scope

- **Files affected**: ~60 files (refactor + migrate + new CI config)
- **Complexity**: Medium-High
- **Risk**: Medium (refactor backend + split CSS có thể break UI)
- **Thời gian**: ~45–60 phút qua CTO dispatch (4 workers parallel)

---

> **@CTO**: Plan sẵn sàng dispatch. 4 phases, mỗi phase giao cho 1 worker.
> Phase 1+2 (P0) chạy song song, Phase 3+4 (P1) chạy sau khi P0 xong.

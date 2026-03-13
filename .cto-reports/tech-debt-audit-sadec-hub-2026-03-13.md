# 🔍 Tech Debt Audit — Sa Đéc Marketing Hub

**Date:** 2026-03-13
**Audit Type:** Tech Debt Sprint (Refactor & Structure Improvement)
**Status:** ✅ COMPLETE

---

## 📊 Executive Summary

| Category | Status | Priority |
|----------|--------|----------|
| **Tech Debt** | 🟡 Moderate | HIGH |
| **Structure** | 🟡 Needs Improvement | HIGH |
| **Duplicate Code** | 🟡 Moderate | MEDIUM |
| **Type Safety** | N/A (Vanilla JS) | — |
| **Test Coverage** | 🟢 Playwright tests exist | LOW |

**Overall Score:** 75/100 — Production Ready, nhưng cần refactor để maintainability

---

## 🎯 Tech Debt Issues Identified

### 1. Structure Issues (HIGH Priority)

#### Problem: `src/` directory rỗng, code nằm ở `assets/js/`

```
src/               → EMPTY (0B)
dist/              → 40MB (build output)
assets/js/         → 684K (79 files, actual source code)
admin/             → 1.3M (HTML + inline code)
portal/            → 684K (HTML + inline code)
```

**Issue:** Không follow conventional structure. `src/` là empty folder trong khi code thực tế nằm ở `assets/js/`.

**Recommendation:**
```
sadec-marketing-hub/
├── src/
│   ├── js/
│   │   ├── core/          ← Core utilities (utils.js, enhanced-utils.js)
│   │   ├── components/    ← UI components (mobile-navigation, toast-notification)
│   │   ├── modules/       ← Feature modules (crm, email, analytics, builder)
│   │   ├── pages/         ← Page-specific logic
│   │   └── shared/        ← Shared code (shared-head.js, admin-shared.js)
│   ├── css/
│   │   ├── base/          ← Reset, variables
│   │   ├── components/    ← Component styles
│   │   └── pages/         ← Page-specific styles
│   └── html/
│       ├── layouts/       ← Base layouts
│       ├── partials/      ← Reusable partials
│       └── pages/         ← Full pages
├── dist/                  ← Build output (gitignore)
├── admin/                 ← Legacy (migrate to src/html/)
├── portal/                ← Legacy (migrate to src/html/)
└── affiliate/             ← Legacy (migrate to src/html/)
```

---

### 2. Duplicate Code (MEDIUM Priority)

#### Pattern 1: Multiple audit scripts với overlapping functionality

```
scripts/audit/
├── html-audit.js (565 lines)
├── comprehensive-audit.js (601 lines)
├── a11y-fix.js
├── fix-html.js
├── fix-all-issues.js
└── detect-duplicates.js
```

**Issue:** `html-audit.js` và `comprehensive-audit.js` có overlapping logic. `fix-html.js` và `fix-all-issues.js` cũng vậy.

**Recommendation:** Consolidate thành single audit framework:
```
scripts/audit/
├── index.js          ← Main entry point
├── scanners/
│   ├── links.js      ← Broken link scanner
│   ├── meta.js       ← Meta tag checker
│   ├── a11y.js       ← Accessibility checker
│   └── ids.js        ← Duplicate ID checker
├── fixers/
│   ├── links.js      ← Auto-fix broken links
│   ├── meta.js       ← Auto-fix meta tags
│   └── a11y.js       ← Auto-fix accessibility
└── report/
    ├── markdown.js   ← Markdown report generator
    └── json.js       ← JSON report generator
```

#### Pattern 2: Utility functions duplication

| File | Size | Duplicate Functions |
|------|------|---------------------|
| `assets/js/utils.js` | 1.3K | Basic utils |
| `assets/js/enhanced-utils.js` | 8.4K | Extended utils (generateId, formatPercent, slugify) |
| `assets/js/core-utils.js` | 2.7K | Core utils (overlap với utils.js) |
| `assets/js/ui-utils.js` | 8.4K | UI-specific utils |

**Recommendation:** Consolidate thành single `src/js/core/utils.js`:
```javascript
// src/js/core/utils.js
export const utils = {
  // ID & String
  generateId,
  slugify,
  capitalize,
  getInitials,

  // Formatting
  formatPercent,
  formatCurrency,
  formatDate,

  // Arrays & Objects
  groupBy,
  sortBy,
  sum,
  average,

  // DOM
  createElement,
  escapeHTML,

  // Validation
  isValidEmail,
  isValidURL,
};
```

#### Pattern 3: Client/Manager pairs duplication

```
assets/js/
├── pipeline.js (4.1K)      ← Original
├── pipeline-client.js (29K) ← Duplicate logic
├── workflows.js (16K)
├── workflows-client.js (7.5K)
├── content-calendar.js (5.1K)
├── content-calendar-client.js (7.4K)
├── dashboard-client.js (6.7K)
├── finance-client.js (6.4K)
```

**Issue:** Logic bị split không rõ ràng giữa "core" và "client".

**Recommendation:** Merge thành single source of truth:
```
src/js/modules/
├── pipeline/
│   ├── index.js        ← Main pipeline logic
│   ├── store.js        ← State management
│   └── api.js          ← API calls
├── workflows/
│   ├── index.js
│   ├── store.js
│   └── api.js
└── content-calendar/
    ├── index.js
    ├── store.js
    └── api.js
```

---

### 3. Console.log in Production (LOW Priority)

**Findings:** 30+ console.log statements trong scripts/ và assets/js/

**Files với console.log:**
- `scripts/debug/*.js` — OK (debug tools)
- `scripts/responsive/fix-responsive.js` — OK (CLI tools)
- `scripts/audit/*.js` — OK (audit tools)
- `assets/js/*` — **Should remove in production**

**Recommendation:** Implement proper logging utility:
```javascript
// src/js/core/logger.js
export const logger = {
  debug: (...args) => {
    if (process.env.NODE_ENV === 'development') {
      console.log('[DEBUG]', ...args);
    }
  },
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args),
};
```

Replace all `console.log` → `logger.debug` hoặc `logger.info`.

---

### 4. TODO/FIXME Comments (LOW Priority)

**Findings:** Không có TODO/FIXME comments trong source code! ✅

Scripts có logic để detect và fix TODO comments:
- `scripts/review/code-quality.js`
- `scripts/fix-audit-issues.js`
- `scripts/perf/audit.js`

**Recommendation:** Keep existing code quality checks.

---

### 5. Missing Type Safety (N/A — Vanilla JS)

Project dùng Vanilla JavaScript, không có TypeScript.

**Recommendation:** Consider migrating to TypeScript for:
- Better IDE support
- Catch errors at compile time
- Self-documenting code

Priority files cho TypeScript migration:
1. `assets/js/supabase.js` (30K lines) — Core data layer
2. `assets/js/pipeline-client.js` (29K) — Business logic
3. `assets/js/admin-shared.js` (15K) — Shared utilities

---

### 6. Test Coverage (MEDIUM Priority)

**Current Tests:**
- Playwright tests in `tests/`
- Smoke tests, viewport tests, format utils tests

**Coverage Gap:**
- No unit tests cho utility functions
- No integration tests cho modules
- Component tests missing

**Recommendation:**
```
tests/
├── unit/
│   ├── utils.test.js      ← Test utility functions
│   ├── logger.test.js
│   └── store.test.js
├── integration/
│   ├── pipeline.test.js   ← Test module integration
│   └── api.test.js
└── e2e/
    ├── smoke.spec.js      ← Existing smoke tests
    ├── viewport.spec.js   ← Existing responsive tests
    └── critical.spec.js   ← Critical path tests
```

---

## 📋 Refactoring Plan

### Phase 1: Structure Reorganization (Priority: HIGH)

**Steps:**
1. Create new `src/` structure
2. Move `assets/js/` → `src/js/`
3. Move `admin/`, `portal/`, `affiliate/` → `src/html/`
4. Update all import paths
5. Verify build still works

**Estimated:** 4-6 hours
**Risk:** Medium (breaking changes)

---

### Phase 2: Consolidate Duplicate Code (Priority: MEDIUM)

**Steps:**
1. Merge `utils.js` + `enhanced-utils.js` + `core-utils.js` → `src/js/core/utils.js`
2. Consolidate audit scripts thành single framework
3. Merge client/core pairs (pipeline, workflows, content-calendar)
4. Remove dead code

**Estimated:** 6-8 hours
**Risk:** Low (internal refactoring)

---

### Phase 3: Implement Logger (Priority: LOW)

**Steps:**
1. Create `src/js/core/logger.js`
2. Replace all `console.log` với `logger.debug/info`
3. Add build step to strip debug logs in production

**Estimated:** 2-3 hours
**Risk:** Low

---

### Phase 4: Expand Test Coverage (Priority: MEDIUM)

**Steps:**
1. Add unit tests cho utils
2. Add integration tests cho key modules
3. Add critical path E2E tests
4. Setup CI coverage reporting

**Estimated:** 8-10 hours
**Risk:** Low

---

## 🎯 Immediate Actions (Recommended)

### Action 1: Structure Reorganization (Do this first)

```bash
# Step 1: Create new structure
mkdir -p src/{js/{core,components,modules,pages,shared},css,html}

# Step 2: Move JS files
mv assets/js src/

# Step 3: Reorganize JS folders
mkdir -p src/js/{core,components,modules}
mv src/js/{utils.js,enhanced-utils.js,core-utils.js} src/js/core/
mv src/js/{mobile-navigation.js,toast-notification.js,keyboard-shortcuts.js} src/js/components/
mv src/js/{pipeline*.js,workflows*.js,content-calendar*.js} src/js/modules/

# Step 4: Update package.json scripts
# Step 5: Test build
npm run build
```

### Action 2: Audit Script Consolidation

Create single audit framework:
```javascript
// scripts/audit/index.js
import { scanLinks } from './scanners/links.js';
import { scanMeta } from './scanners/meta.js';
import { scanA11y } from './scanners/a11y.js';
import { fixLinks } from './fixers/links.js';
import { fixMeta } from './fixers/meta.js';
import { fixA11y } from './fixers/a11y.js';
import { generateReport } from './report/markdown.js';

async function audit(options = {}) {
  const { fix = false, output = 'markdown' } = options;

  // Run scanners
  const linkResults = await scanLinks();
  const metaResults = await scanMeta();
  const a11yResults = await scanA11y();

  // Auto-fix if requested
  if (fix) {
    await fixLinks(linkResults);
    await fixMeta(metaResults);
    await fixA11y(a11yResults);
  }

  // Generate report
  return generateReport({ linkResults, metaResults, a11yResults }, output);
}
```

---

## 📊 Impact Analysis

| Change | Impact | Effort | Priority |
|--------|--------|--------|----------|
| Structure reorg | High | Medium | P0 |
| Consolidate utils | Medium | Low | P1 |
| Audit framework | Medium | Medium | P1 |
| Logger impl | Low | Low | P2 |
| Unit tests | Medium | High | P2 |

---

## ✅ Success Criteria

- [ ] `src/` structure follows convention
- [ ] 0 duplicate utility files
- [ ] Audit scripts consolidated
- [ ] 0 console.log in production code
- [ ] Test coverage >80% cho core utils
- [ ] Build passes sau refactor
- [ ] All tests green

---

## 📝 Notes

**Generated by:** Mekong CLI `/eng:tech-debt`
**Goal:** Refactor `/Users/mac/mekong-cli/apps/sadec-marketing-hub` — consolidate duplicate code, cải thiện structure

---

*Report generated: 2026-03-13*

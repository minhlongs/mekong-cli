# Tech Debt Audit Report - Sa Đéc Marketing Hub

**Date:** 2026-03-13
**Scope:** apps/sadec-marketing-hub
**Credits:** 20 estimated

---

## Executive Summary

| Metric | Value |
|--------|-------|
| JavaScript Files | 102 |
| CSS Files | 54 |
| Total JS Size | 1.1MB |
| Total CSS Size | 868KB |
| Node Modules | 52MB |
| Total LOC | ~5,300 (admin + portal JS) |

---

## Phase 1: Audit Findings

### 1. Duplicate Code Patterns 🔴

#### A. Repeated DOM Utilities

Found in multiple files:
- `admin/admin-utils.js` (208 lines)
- `portal/portal-utils.js` (143 lines)
- `ui-utils.js` (duplicated helpers)

**Functions duplicated:**
- `querySelector` / `querySelectorAll` wrappers
- `addEventListener` helpers
- Loading state toggles
- Toast/notification helpers

#### B. Repeated API Client Patterns

Each module has its own API client:
- `dashboard-client.js` (170 lines)
- `finance-client.js` (161 lines)
- `binh-phap-client.js` (152 lines)
- `workflows-client.js` (175 lines)
- `content-calendar-client.js`

**Common patterns:**
```javascript
document.addEventListener('DOMContentLoaded', async () => {
  // Same init pattern repeated 10+ times
});
```

#### C. CSS Duplication

Multiple CSS files with similar styles:
- `admin-unified.css`
- `admin-refactored.css`
- `admin-dashboard.css`
- Bundle files: `admin-common.css`, `admin-modules.css`

### 2. Console.log Statements 🟡

Found **50+ console.log** statements in:
- `scripts/debug/check-imports.js`
- `scripts/debug/broken-imports.js`
- `scripts/seo/add-seo-metadata.js`
- `scripts/audit/auto-fix.js`
- `assets/js/components/index.js`

### 3. Large Files 🟡

| File | Lines | Recommendation |
|------|-------|----------------|
| `admin/notification-bell.js` | 650 | Split into bell + panel |
| `admin/admin-ux-enhancements.js` | 621 | Split dark mode + shortcuts + skeleton |
| `admin/menu-manager.js` | 461 | Acceptable |
| `admin/admin-leads.js` | 341 | Acceptable |

### 4. TODO/FIXME Comments 🟢

Only **3 files** with technical debt markers:
- `scripts/review/code-quality.js`
- `scripts/perf/audit.js`
- `scripts/fix-audit-issues.js`

### 5. Missing Type Safety 🔴

- No TypeScript/JSDoc type annotations
- Implicit `any` types throughout
- No runtime validation for API responses

### 6. Test Coverage 🟡

| Test Suite | Coverage |
|------------|----------|
| Responsive Tests | ✅ 216 tests passing |
| E2E Tests | ⚠️ Partial (some failures) |
| Unit Tests | ❌ Missing |
| Component Tests | ⚠️ Limited |

---

## Phase 2: Prioritized Tech Debt

### P0 - Critical (Fix Now)

1. **Consolidate duplicate utilities** → Create shared module
2. **Remove console.log from production** → Clean up
3. **Extract repeated DOMContentLoaded patterns** → Create init helper

### P1 - High (This Sprint)

1. **Create shared API client** → Reduce duplication
2. **Split large files** → notification-bell.js, admin-ux-enhancements.js
3. **Add JSDoc type annotations** → Core utilities

### P2 - Medium (Next Sprint)

1. **CSS consolidation** → Remove unused styles
2. **Add unit tests** → Utility functions
3. **Bundle size optimization** → Code splitting

---

## Phase 3: Refactoring Plan

### Module Consolidation

```
assets/js/
├── shared/              # NEW: Consolidated utilities
│   ├── dom-utils.js     # DOM helpers (dedupe from 5 files)
│   ├── api-client.js    # Unified API client (dedupe from 10 files)
│   ├── format-utils.js  # Already exists
│   ├── guard-utils.js   # Already exists
│   └── ui-helpers.js    # Toast, loading, etc.
├── admin/
│   ├── admin-ux-enhancements.js → Split into:
│   │   ├── dark-mode.js
│   │   ├── keyboard-shortcuts.js
│   │   └── skeleton-loader.js
│   └── notification-bell.js → Split into:
│       ├── bell-component.js
│       └── notification-panel.js
├── portal/
│   └── (use shared modules)
└── init/                # NEW: Initialization patterns
    └── app-init.js      # Replace DOMContentLoaded pattern
```

### Code Quality Rules

1. **Max file size:** 300 lines
2. **Function max:** 50 lines
3. **Required:** JSDoc for public functions
4. **No console.log** in production code
5. **Single responsibility** per module

---

## Phase 4: Success Metrics

| Metric | Before | Target | After |
|--------|--------|--------|-------|
| Total JS files | 102 | 90 | TBD |
| Duplicate utils | 5 files | 1 file | TBD |
| Console.log count | 50+ | 0 | TBD |
| Files >500 lines | 2 | 0 | TBD |
| Test count | 216 | 250 | TBD |

---

## Estimated Credits

| Phase | Credits | Time |
|-------|---------|------|
| Audit | 2 | 5 min |
| Refactor | 12 | 25 min |
| Test | 6 | 10 min |
| **Total** | **20** | **40 min** |

---

**Status:** ✅ AUDIT COMPLETE
**Next:** Refactor phase

# Code Review: Utility Functions (formatting.ts)

**Date:** 2026-03-19
**Reviewer:** code-reviewer
**Files Reviewed:**
- `src/utils/formatting.ts` (130 lines)
- `src/utils/formatting.test.ts` (97 lines)

---

## Score: 6.5/10

---

## Overall Assessment

Utility functions demonstrate good structure and use of `Intl.NumberFormat` for locale-aware formatting. However, **4 TypeScript type errors** must be fixed before merging. Test coverage is solid but misses critical edge cases (NaN, Infinity, null/undefined).

---

## Critical Issues

### 1. TypeScript Type Errors — BLOCKING

**Location:** `formatting.ts:78-87`

```
src/utils/formatting.ts(78,39): error TS2339: Property 'locale' does not exist on type '{ minimumFractionDigits: number; maximumFractionDigits: number; style: "percent" | "decimal"; }'.
src/utils/formatting.ts(78,76): error TS2339: Property 'locale' does not exist on type '{ minimumFractionDigits: number; maximumFractionDigits: number; style: "percent" | "decimal"; }'.
src/utils/formatting.ts(87,37): error TS2339: Property 'locale' does not exist on type '{ minimumFractionDigits: number; maximumFractionDigits: number; style: "percent" | "decimal"; }'.
src/utils/formatting.ts(87,74): error TS2339: Property 'locale' does not exist on type '{ minimumFractionDigits: number; maximumFractionDigits: number; style: "percent" | "decimal"; }'.
```

**Problem:** `PercentageOptions` interface missing `locale` property, but code tries to access `opts.locale`.

**Fix:**
```typescript
export interface PercentageOptions {
  locale?: string;  // ADD THIS
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  style?: 'decimal' | 'percent';
}
```

---

## High Priority

### 2. Missing Edge Case Validation

**Risk:** Functions will throw or produce unexpected output with invalid inputs.

| Input | Current Behavior | Expected |
|-------|------------------|----------|
| `NaN` | `Intl.NumberFormat` returns `"NaN"` | Should throw or return `"N/A"` |
| `Infinity` | Returns `"∞"` | Should throw or clamp |
| `null` / `undefined` | TypeScript prevents, but runtime coercion possible | Explicit validation |
| Very large numbers | May lose precision | Document limits |

**Recommendation:**
```typescript
export function formatCurrency(amount: number, options: CurrencyOptions = {}): string {
  if (!Number.isFinite(amount)) {
    throw new Error(`Invalid amount: ${amount}. Must be a finite number.`);
  }
  // ... rest of implementation
}
```

### 3. Locale Handling Inconsistency

**Issue:** `formatPercentage` uses `opts.locale === 'auto' ? undefined : opts.locale`, but:
- `CurrencyOptions` has `locale?: string` with default `'en-US'`
- `NumberOptions` has `locale?: string` with default `'en-US'`
- `PercentageOptions` has NO `locale` property (see Critical #1)

**Inconsistency:** The `'auto'` magic string is undocumented and only used in `formatPercentage`.

**Recommendation:** Either:
1. Document `'auto'` behavior in all interfaces
2. Remove special handling and use `undefined` explicitly when needed
3. Use a dedicated flag: `autoLocale?: boolean`

---

## Medium Priority

### 4. Test Coverage Gaps

**Missing test cases:**

```typescript
// Edge cases not covered
describe('formatCurrency', () => {
  it('should throw on NaN', () => {
    expect(() => formatCurrency(NaN)).toThrow();
  });

  it('should throw on Infinity', () => {
    expect(() => formatCurrency(Infinity)).toThrow();
  });
});

describe('formatPercentage', () => {
  it('should handle values outside [0, 1] range', () => {
    expect(formatPercentage(1.5)).toBe('150.0%');  // Does it?
    expect(formatPercentage(-0.5)).toBe('-50.0%');
  });
});

describe('formatCompactNumber', () => {
  it('should handle negative numbers', () => {
    expect(formatCompactNumber(-1500)).toBe('-1.5K');
  });

  it('should handle zero', () => {
    expect(formatCompactNumber(0)).toBe('0');
  });
});
```

### 5. Currency Type Limitation

**Current:**
```typescript
currency?: 'USD' | 'VND' | 'EUR' | 'GBP';
```

**Problem:** `Intl.NumberFormat` supports 150+ currencies. Hardcoding limits flexibility.

**Recommendation:**
```typescript
type CurrencyCode = 'USD' | 'VND' | 'EUR' | 'GBP' | (string & {});
// Or simply:
currency?: string;  // Let Intl.NumberFormat validate
```

---

## Low Priority

### 6. Default Options Pattern

**Current:** Spread merge on every call
```typescript
const opts = { ...DEFAULT_CURRENCY_OPTIONS, ...options };
```

**More efficient:**
```typescript
function formatCurrency(amount: number, options: CurrencyOptions = {}): string {
  const {
    currency = 'USD',
    locale = 'en-US',
    minimumFractionDigits = 2,
    maximumFractionDigits = 2,
  } = options;

  return new Intl.NumberFormat(locale, { ... }).format(amount);
}
```

**Benefit:** Avoids object allocation, clearer defaults.

### 7. Documentation Gaps

**Missing JSDoc:**
- What happens with invalid inputs?
- What is the expected range for `formatPercentage`? (0-1 or any number?)
- What locales are supported?

**Add @throws annotations** for edge cases.

---

## Positive Observations

1. **Good use of Intl.NumberFormat** — Locale-aware, handles grouping automatically
2. **Well-structured interfaces** — Clear option types for each formatter
3. **Comprehensive happy-path tests** — 17 tests cover main use cases
4. **Exported via barrel index** — Clean module structure
5. **No security issues** — No user input concatenation, no eval

---

## Security & Performance

| Area | Status | Notes |
|------|--------|-------|
| **Security** | ✅ Clean | No injection vectors, no secrets |
| **Performance** | ✅ Good | `Intl.NumberFormat` is native and cached |
| **Type Safety** | ⚠️ Issues | 4 TS errors, missing `locale` in `PercentageOptions` |
| **Edge Cases** | ⚠️ Gaps | No NaN/Infinity handling |

---

## Recommended Actions

1. **[BLOCKING]** Fix TypeScript errors — Add `locale` to `PercentageOptions`
2. **[HIGH]** Add input validation for NaN/Infinity
3. **[HIGH]** Add missing edge case tests
4. **[MEDIUM]** Document or remove `'auto'` locale behavior
5. **[LOW]** Consider relaxing currency type constraint
6. **[LOW]** Refactor default options with destructuring

---

## Verdict: **APPROVE WITH COMMENTS** (pending fixes)

**Conditions for merge:**
- [ ] Fix 4 TypeScript type errors (Critical #1)
- [ ] Add input validation for NaN/Infinity
- [ ] Add at least 3 edge case tests

---

## Unresolved Questions

1. Should `formatPercentage` accept values outside [0, 1] range (e.g., `1.5` = 150%)?
2. Is the `'auto'` locale magic string documented elsewhere or should it be removed?
3. Are there performance requirements that justify optimizing the default options pattern?

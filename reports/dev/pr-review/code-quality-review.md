# PR Review Report — Sa Đéc Marketing Hub

**Date:** 2026-03-14
**Scope:** `/Users/mac/mekong-cli/apps/sadec-marketing-hub`
**Request:** Code quality review, patterns check, dead code detection

---

## 📊 Executive Summary

| Category | Status | Severity |
|----------|--------|----------|
| Code Quality | ⚠️ Needs Work | Medium |
| Type Safety | ⚠️ Moderate Issues | Medium |
| Security | ⚠️ Needs Review | High |
| Dead Code | ❌ Significant | High |
| Test Coverage | ✅ Good | — |

---

## 🔍 1. Code Quality Issues

### 1.1 Console.log trong Production Code

**Vấn đề:** Nhiều file production chứa `console.log` statements.

**Files bị ảnh hưởng:**
- `assets/js/services/payment-gateway.js` — Lines 90, 191, 314 (commented out)
- `assets/js/mobile-navigation.js` — Multiple console statements
- `assets/js/dashboard-client.js` — Debug logs
- `assets/js/finance-client.js` — Debug logs

**Khuyến nghị:**
```javascript
// ❌ BAD: console.log trong production
// [DEV] console.log('Payment Error:', error);

// ✅ GOOD: Sử dụng Logger utility
import { Logger } from './shared/logger.js';
Logger.error('[PaymentGateway]', 'Payment error', error);
```

**Hành động cần thiết:**
1. Thay thế tất cả `console.log` bằng Logger utility
2. Giữ lại `console.error` và `console.warn` cho error tracking
3. Cấu hình Logger level dựa trên environment (dev/prod)

---

### 1.2 TODO/FIXME Comments

**Status:** ✅ **KHÔNG tìm thấy** TODO/FIXME comments trong production code.

Đây là điểm tốt, cho thấy code đã được cleanup kỹ.

---

### 1.3 Type Safety (JavaScript)

**Vấn đề:** Project sử dụng JavaScript thuần (không TypeScript), nhưng có thể cải thiện type safety qua JSDoc.

**Files cần cải thiện:**

#### `assets/js/services/payment-gateway.js`
```javascript
// ❌ Currently:
class PaymentGateway {
    constructor(config) {
        this.config = config;
    }

    async createPaymentUrl(orderInfo) {
        // No type documentation
    }
}

// ✅ Should be:
/**
 * @typedef {Object} OrderInfo
 * @property {string} orderId
 * @property {number} amount
 * @property {string} [description]
 * @property {string} [invoiceId]
 */

/**
 * @param {OrderInfo} orderInfo
 * @returns {Promise<string>} Checkout URL
 */
async createPaymentUrl(orderInfo) { ... }
```

#### `assets/js/core/auth-service.js`
```javascript
// ❌ Currently:
async signIn(email, password) {
    // No validation
}

// ✅ Should be:
/**
 * @param {string} email - User email
 * @param {string} password - User password (min 8 chars)
 * @returns {Promise<{data: Object|null, error: Error|null}>}
 */
async signIn(email, password) {
    // Add input validation
    if (!email || !password) {
        throw new Error('Email và password là bắt buộc');
    }
}
```

---

## 🔒 2. Security Audit

### 2.1 Hardcoded Credentials

**⚠️ HIGH SEVERITY:** Placeholder credentials trong production code.

**File:** `assets/js/services/payment-gateway.js`

```javascript
// Lines 16-23:
const PAYMENT_CONFIG = {
    vnpay: {
        tmnCode: 'MEKONG01',
        hashSecret: 'YOUR_HASH_SECRET', // ⚠️ Placeholder
        url: 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
        // ...
    },
    momo: {
        partnerCode: 'MOMO_PARTNER_CODE', // ⚠️ Placeholder
        accessKey: 'YOUR_ACCESS_KEY',     // ⚠️ Placeholder
        secretKey: 'YOUR_SECRET_KEY',     // ⚠️ Placeholder
        // ...
    }
};
```

**Rủi ro:**
- Code với placeholder credentials có thể bị push lên production
- Developer có thể quên replace trước khi deploy
- Security audit sẽ fail

**Khuyến nghị:**
```javascript
// ✅ GOOD: Environment variables only
const PAYMENT_CONFIG = {
    vnpay: {
        tmnCode: window.__ENV__?.VNPAY_TMN_CODE,
        hashSecret: window.__ENV__?.VNPAY_HASH_SECRET,
        url: 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
    },
    // ...
};

// Validate at runtime
if (!PAYMENT_CONFIG.vnpay.hashSecret) {
    throw new Error('[PaymentGateway] VNPAY_HASH_SECRET is required');
}
```

---

### 2.2 Supabase Configuration

**File:** `assets/js/core/supabase-client.js`

```javascript
// Lines 10-11:
const SUPABASE_URL = 'https://pzcgvfhppglzfjavxuid.supabase.co';
// ⚠️ URL cứng, nên dùng environment variable
```

**Khuyến nghị:**
```javascript
// ✅ GOOD: Environment variable
const SUPABASE_URL = window.__ENV__?.SUPABASE_URL ||
                     'https://pzcgvfhppglzfjavxuid.supabase.co';
```

---

### 2.3 Input Validation

**⚠️ MEDIUM SEVERITY:** Thiếu input validation ở nhiều nơi.

**File:** `assets/js/core/auth-service.js`

```javascript
// ❌ No validation:
async signUp(email, password, metadata = {}) {
    const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: metadata }
    });
    return { data, error };
}

// ✅ Should validate:
async signUp(email, password, metadata = {}) {
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return { data: null, error: new Error('Email không hợp lệ') };
    }

    // Password strength
    if (password.length < 8) {
        return { data: null, error: new Error('Mật khẩu phải có ít nhất 8 ký tự') };
    }

    const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: metadata }
    });
    return { data, error };
}
```

---

## 🗑️ 3. Dead Code Detection

### 3.1 Unused Files

**Phát hiện:** Nhiều file trong `/scripts/` directory có vẻ là tooling scripts, không phải production code.

**Files có thể là dead code:**
```
scripts/debug/scan-console-errors.js
scripts/debug/check-imports.js
scripts/debug/broken-imports.js
scripts/refactor/consolidate-scroll-listeners.js
scripts/refactor/update-imports.js
scripts/perf/audit.js
scripts/fix-audit-issues.js
```

**Khuyến nghị:**
1. Di chuyển các scripts này sang `/tools/` hoặc `/dev-tools/` directory
2. Thêm documentation về cách sử dụng
3. Xóa các scripts không còn dùng đến

---

### 3.2 Duplicate Code

**Phát hiện:** Có dấu hiệu duplicate logic giữa các file.

#### Example: Payment handling

**File 1:** `index.html` (lines 680-767)
```javascript
async function createPayment(gateway, amount, packageName, invoiceId) {
    const isLocalhost = window.location.hostname === 'localhost' ||
                        window.location.hostname.includes('127.0.0.1');
    if (isLocalhost) {
        window.location.href = `/portal/payment-result.html?code=00&...`;
        return;
    }
    // ... payment logic
}
```

**File 2:** `assets/js/services/payment-gateway.js` (lines 279-321)
```javascript
async createPaymentUrl(orderInfo) {
    const isProd = window.location.hostname !== 'localhost' &&
                   !window.location.hostname.includes('127.0.0.1');
    if (isProd) {
        // ... payment logic
    } else {
        // Local simulation
        return `${this.config.returnUrl}?code=00&...`;
    }
}
```

**Vấn đề:** Logic xử lý payment bị duplicate giữa HTML inline script và payment-gateway.js module.

**Khuyến nghị:**
1. Remove inline script từ `index.html`
2. Sử dụng `paymentManager` từ `payment-gateway.js`
3. Import module trong HTML:
```html
<script type="module">
    import { paymentManager } from './assets/js/services/payment-gateway.js';

    async function openPaymentModal(packageName, amount) {
        const result = await paymentManager.processPayment('payos', {
            amount,
            description: packageName
        });
        if (result.success && result.type === 'redirect') {
            window.location.href = result.data;
        }
    }
</script>
```

---

### 3.3 Unused Imports

**Phát hiện:** Một số file import nhưng không sử dụng.

**Example:** `assets/js/core/supabase-client.js`
- Line 23: `import { Logger } from '../shared/logger.js';`
- Logger được sử dụng ở lines 62, 70, 215 ✅ (không phải dead code)

**Status:** ✅ Không tìm thấy unused imports nghiêm trọng.

---

## 🧪 4. Test Coverage

### 4.1 Test Files Present

**✅ GOOD:** Project có test suite khá đầy đủ.

**Test files found:**
```
tests/portal-payments.spec.ts          — Payment flow tests
tests/payment-modal.spec.ts            — Payment modal tests
tests/multi-gateway.spec.ts            — Multi-gateway tests
tests/payos-flow.spec.ts               — PayOS specific tests
tests/fixtures/auth.setup.ts           — Auth test fixtures
```

### 4.2 Test Patterns

**Good practices observed:**
```typescript
// tests/payos-flow.spec.ts — Well-structured test
test('should handle PayOS payment flow', async ({ page }) => {
    // Setup
    await page.goto('/#pricing');

    // Act
    await page.click('[data-package="growth"]');

    // Assert
    await expect(paymentModal).toBeVisible();
});
```

**Khuyến nghị:**
1. Thêm test cho payment-gateway.js service
2. Thêm unit tests cho auth-service.js
3. Setup CI/CD để chạy tests tự động

---

## 📋 5. Recommendations Summary

### Priority 1 — High (Fix Immediately)

| Issue | File | Action |
|-------|------|--------|
| Hardcoded credentials | `payment-gateway.js` | Replace với env vars |
| Missing input validation | `auth-service.js` | Add validation logic |
| Duplicate payment logic | `index.html` | Refactor to use module |

### Priority 2 — Medium (Fix Before Next Release)

| Issue | File | Action |
|-------|------|--------|
| Console.log statements | Multiple | Replace với Logger |
| Missing JSDoc types | Core services | Add type annotations |
| Hardcoded Supabase URL | `supabase-client.js` | Use env var |

### Priority 3 — Low (Tech Debt Cleanup)

| Issue | File | Action |
|-------|------|--------|
| Script organization | `/scripts/` | Reorganize to `/tools/` |
| Documentation | README | Add setup guide |
| Test coverage | `/tests/` | Add more unit tests |

---

## 🎯 Action Plan

### Week 1 — Security Fixes
- [ ] Replace hardcoded credentials với environment variables
- [ ] Add input validation cho auth-service.js
- [ ] Review và remove sensitive data từ code

### Week 2 — Code Quality
- [ ] Replace all console.log với Logger utility
- [ ] Add JSDoc type annotations
- [ ] Refactor duplicate payment logic

### Week 3 — Cleanup
- [ ] Reorganize scripts directory
- [ ] Remove dead code
- [ ] Add comprehensive documentation

---

## ✅ Quality Gate Checklist

| Gate | Status | Notes |
|------|--------|-------|
| 0 TODO/FIXME comments | ✅ Pass | Không tìm thấy |
| 0 console.log in production | ⚠️ Fail | ~10 instances found |
| 0 hardcoded secrets | ❌ Fail | Payment config has placeholders |
| Input validation | ⚠️ Partial | Auth service missing validation |
| Test coverage | ✅ Pass | Payment tests present |
| Type safety (JSDoc) | ⚠️ Partial | Needs improvement |

---

**Report generated by:** OpenClaw PR Review
**Time:** 2026-03-14
**Next Review:** After Priority 1 fixes

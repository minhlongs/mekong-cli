---
title: "Full PayPal Purge - All-In on Polar.sh"
description: "Complete removal of PayPal integration in favor of Polar.sh"
status: pending
priority: P1
effort: 4h
branch: master
tags: [payment, cleanup, polar, refactor]
created: 2026-02-07
---

# Full PayPal Purge - Implementation Plan

## 🎯 Objective

Complete removal of all PayPal-related code, dependencies, and configuration from the mekong-cli codebase. We are consolidating on **Polar.sh** as the sole payment provider.

## 📋 Context

After analysis of the codebase, PayPal integration exists in multiple layers:
- Backend API routes and webhook handlers
- PayPal SDK implementation (`api/core/finance/paypal_sdk/`)
- Payment service integrations
- Environment configuration
- Dependencies in requirements files

This purge will eliminate all PayPal code while ensuring Polar.sh handles all payment flows.

---

## 🔍 Discovery Summary

### Files to DELETE (Complete Removal)

**Backend Python Files:**
- `/api/payments/paypal.py` - PayPal checkout router
- `/api/webhooks/paypal_handler.py` - PayPal webhook handler
- `/api/core/finance/paypal_sdk/` - Entire PayPal SDK directory
  - `base.py`
  - `catalog.py`
  - `orders.py`
  - `payments.py`
  - `subscriptions.py`
  - `webhooks.py`
  - `__init__.py`

**Frontend Files (if exist):**
- `frontend/landing/app/components/PayPalCheckout.tsx`
- `frontend/landing/app/components/PayPalSmartButton.tsx`
- `frontend/landing/app/components/BraintreeCheckout.tsx`

### Files to MODIFY (Remove PayPal References)

**Backend:**
- `/api/main.py` - Remove PayPal handler router import/inclusion
- `/api/config.py` - Remove PayPal settings (PAYPAL_CLIENT_ID, etc.)
- `/api/services/payment_service.py` - Remove PayPal provider logic
- `/api/routers/payments.py` - Remove PayPal-related endpoints
- `/requirements.txt` - Remove PayPal-related dependencies (if any)
- `/pyproject.toml` - Remove PayPal-related dependencies

**Configuration:**
- `/.env.example` - Remove PAYPAL_* environment variables

**Apps (Sophia AI Factory):**
- Similar cleanup in `apps/sophia-ai-factory/` subdirectory

---

## 📐 Implementation Phases

### Phase 1: Backend Python Code Removal

**Priority:** P1 (Critical)
**Estimated Time:** 1.5h

#### 1.1 Delete PayPal SDK Directory
```bash
rm -rf /Users/macbookprom1/mekong-cli/api/core/finance/paypal_sdk/
```

#### 1.2 Delete PayPal Payment Routes
```bash
rm /Users/macbookprom1/mekong-cli/api/payments/paypal.py
```

#### 1.3 Delete PayPal Webhook Handler
```bash
rm /Users/macbookprom1/mekong-cli/api/webhooks/paypal_handler.py
```

#### 1.4 Update `api/main.py`
Remove:
```python
from api.webhooks import paypal_handler
app.include_router(paypal_handler.router)
```

#### 1.5 Update `api/config.py`
Remove PayPal settings:
```python
# PayPal
PAYPAL_CLIENT_ID: Optional[str] = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET: Optional[str] = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE: str = os.getenv("PAYPAL_MODE", "sandbox")
```

#### 1.6 Update `api/services/payment_service.py`
- Remove PayPal provider initialization
- Remove PayPal-specific methods (`verify_webhook`, `handle_webhook_event`)
- Remove PayPal imports

#### 1.7 Update `api/routers/payments.py`
- Remove PayPal-specific endpoints
- Update payment orchestrator logic to remove PayPal fallback

---

### Phase 2: Environment & Configuration Cleanup

**Priority:** P1 (Critical)
**Estimated Time:** 0.5h

#### 2.1 Update `.env.example`
Remove lines 1-5:
```bash
# REMOVE THESE LINES:
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_secret
PAYPAL_MODE=sandbox
PAYPAL_WEBHOOK_ID=your_webhook_id
```

#### 2.2 Update `requirements.txt`
- Remove PayPal SDK reference (currently noted as "implemented internally using requests")
- Verify no other PayPal dependencies exist

#### 2.3 Update `pyproject.toml`
- Check for PayPal-related dependencies
- Remove if present

---

### Phase 3: Frontend Components Removal

**Priority:** P2 (High)
**Estimated Time:** 1h

#### 3.1 Delete Frontend PayPal Components
```bash
# Root frontend (if exists)
rm -f /Users/macbookprom1/mekong-cli/frontend/landing/app/components/PayPalCheckout.tsx
rm -f /Users/macbookprom1/mekong-cli/frontend/landing/app/components/PayPalSmartButton.tsx
rm -f /Users/macbookprom1/mekong-cli/frontend/landing/app/components/BraintreeCheckout.tsx

# Sophia AI Factory frontend
rm -f /Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/frontend/landing/app/components/PayPalCheckout.tsx
rm -f /Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/frontend/landing/app/components/PayPalSmartButton.tsx
rm -f /Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/frontend/landing/app/components/BraintreeCheckout.tsx
```

#### 3.2 Update Checkout Page
- `/frontend/landing/app/checkout/page.tsx`
- Remove PayPal button/component imports and usage
- Update to use only Polar.sh checkout

#### 3.3 Remove PayPal from package.json
```bash
# Check and remove PayPal-related npm packages
grep -i paypal frontend/landing/package.json
grep -i paypal apps/sophia-ai-factory/frontend/landing/package.json
```

---

### Phase 4: Apps Subdirectory Cleanup

**Priority:** P2 (High)
**Estimated Time:** 1h

#### 4.1 Sophia AI Factory Backend
```bash
# Delete PayPal SDK
rm -rf /Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/api/core/finance/paypal_sdk/

# Delete PayPal routes and handlers
rm /Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/api/payments/paypal.py
rm /Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/api/webhooks/paypal_handler.py
rm /Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/api/routers/paypal_webhooks.py
```

#### 4.2 Update Sophia AI Factory Files
- `apps/sophia-ai-factory/api/services/payment_service.py`
- `apps/sophia-ai-factory/api/services/provisioning_service.py`
- `apps/sophia-ai-factory/api/routers/payments.py`
- `apps/sophia-ai-factory/api/routers/products.py`
- `apps/sophia-ai-factory/api/payments/core.py`
- `apps/sophia-ai-factory/requirements.txt`
- `apps/sophia-ai-factory/pyproject.toml`
- `apps/sophia-ai-factory/.env.example`

#### 4.3 Update Sophia AI Factory Frontend
- Remove PayPal components
- Update checkout flows
- Remove PayPal from i18n files (`packages/i18n/src/locales/{vi,en}.json`)

---

### Phase 5: Verification & Testing

**Priority:** P1 (Critical)
**Estimated Time:** 1h

#### 5.1 Import Verification
```bash
# Search for any remaining PayPal imports
grep -r "import.*paypal\|from.*paypal" /Users/macbookprom1/mekong-cli/api/ --include="*.py"
grep -r "import.*paypal\|from.*paypal" /Users/macbookprom1/mekong-cli/apps/ --include="*.py"
```

#### 5.2 Reference Verification
```bash
# Search for any PayPal string references
grep -ri "paypal" /Users/macbookprom1/mekong-cli/api/ --include="*.py" | grep -v ".pyc"
grep -ri "paypal" /Users/macbookprom1/mekong-cli/frontend/ --include="*.tsx" --include="*.ts"
```

#### 5.3 Build & Test
```bash
# Backend
cd /Users/macbookprom1/mekong-cli
python -m pytest api/tests/ -v

# Frontend (if applicable)
cd frontend/landing
npm run build
npm run lint
```

#### 5.4 Manual Testing
- [ ] API starts without errors
- [ ] Payment routes return 200/404 appropriately
- [ ] No PayPal references in `/docs` (FastAPI Swagger)
- [ ] Frontend builds successfully
- [ ] Checkout flow uses only Polar.sh

---

## 🔒 Risk Assessment

### High Risk
- **Breaking Payment Flows:** Ensure Polar.sh is fully configured before purge
- **Database References:** Check for `paypal_` columns in database schema
- **Active Subscriptions:** Verify no active PayPal subscriptions exist

### Medium Risk
- **Import Errors:** Circular imports or missed dependencies
- **Frontend Breakage:** Components referencing deleted PayPal code
- **Documentation:** Outdated docs mentioning PayPal

### Mitigation
1. **Backup First:** Create git branch before deletion
2. **Incremental Testing:** Test after each phase
3. **Rollback Plan:** Keep PayPal code in git history for emergency rollback

---

## ✅ Success Criteria

- [ ] Zero PayPal files remain in codebase
- [ ] Zero PayPal imports in Python files
- [ ] Zero PayPal dependencies in requirements.txt/pyproject.toml
- [ ] Zero PAYPAL_* env vars in .env.example
- [ ] API starts and runs without errors
- [ ] Frontend builds without errors
- [ ] Payment flow works with Polar.sh only
- [ ] All tests pass
- [ ] No console errors related to missing PayPal code

---

## 📝 Post-Purge Actions

1. **Update Documentation:**
   - Remove PayPal from payment integration docs
   - Update architecture diagrams
   - Update README.md payment section

2. **Database Migration (if needed):**
   - Check for `paypal_subscription_id` columns
   - Create migration to remove/archive PayPal-specific fields

3. **Monitor Production:**
   - Watch error logs for PayPal-related errors
   - Verify no webhook failures
   - Confirm Polar.sh handles all payment events

4. **Communication:**
   - Notify team of PayPal removal
   - Update deployment docs
   - Update environment setup guides

---

## 🔗 Related Files

**Primary Work Files:**
- `/api/main.py`
- `/api/config.py`
- `/api/services/payment_service.py`
- `/.env.example`
- `/requirements.txt`

**Deletion Targets:**
- `/api/core/finance/paypal_sdk/` (entire directory)
- `/api/payments/paypal.py`
- `/api/webhooks/paypal_handler.py`

**Frontend:**
- `/frontend/landing/app/components/PayPal*.tsx`
- `/frontend/landing/app/checkout/page.tsx`

---

## 📊 Effort Breakdown

| Phase | Task | Time |
|-------|------|------|
| 1 | Backend Python Code Removal | 1.5h |
| 2 | Environment & Config Cleanup | 0.5h |
| 3 | Frontend Components Removal | 1h |
| 4 | Apps Subdirectory Cleanup | 1h |
| 5 | Verification & Testing | 1h |
| **Total** | | **5h** |

---

## 🚀 Next Steps

1. **Create git branch:** `git checkout -b feat/paypal-purge-polar-only`
2. **Execute Phase 1:** Backend code removal
3. **Test after each phase:** Ensure no breakage
4. **Final verification:** Run full test suite
5. **Create PR:** With detailed changelog
6. **Deploy:** After approval and CI/CD green

---

**Plan Created:** 2026-02-07
**Author:** planner agent
**Work Context:** /Users/macbookprom1/mekong-cli

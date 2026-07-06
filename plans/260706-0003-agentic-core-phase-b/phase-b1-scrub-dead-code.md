# Phase B1: Dead Code Scrub (Steps 6-7)

## Goal
Remove dead scaffolding that creates confusion and slows navigation.

## Files to Delete

### src/zenpay/ (100KB+ dead scaffolding)
- `src/zenpay/__init__.py`
- `src/zenpay/config.py`
- `src/zenpay/models.py`
- `src/zenpay/kyc.py`
- `src/zenpay/stripe_client.py`
- `src/zenpay/api.py` (34KB — largest)
- `src/zenpay/exceptions.py`
- `src/zenpay/treasury.py`
- `src/zenpay/wallet.py`
- `src/zenpay/package.py`
- `src/zenpay/migrations/` (entire dir)
- `src/zenpay/tests/` (entire dir)

### src/metering/ (duplicated — merge into src/usage/ in B2)
- `src/metering/usage_tracker.py` (keep until B2 merge)
- `src/metering/usage_tracker.py.bak`
- `src/metering/usage-tracker.ts`

### Duplicate zenpay type stub
- `src/mekong/zenpay/types.py` (if exists)

## Verification
- `git ls-files src/zenpay/` should return nothing
- `git ls-files src/metering/` should return nothing
- No import errors in test collection
- Billing tests (zenpay/zenboard/billing) must not reference deleted files

## Risk: LOW (deletions only, no behavior change)

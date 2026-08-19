# RBAC DB Cross-Check Fix — 2026-08-19

## Defect

`src/auth/rbac.py:166-173` `_db_cross_check_role` imported
`LicenseRepository` via `get_repository()` and called `repo.get_user_role(user_id)`.
`LicenseRepository` has no such method — only `create_license`,
`get_license_by_key`, `get_license_by_key_id`. The `AttributeError` was swallowed
by a bare `except Exception: pass`, so the DB cross-check **never ran** and the
JWT role was trusted unconditionally.

This contradicted the module docstring: "JWT roles are cross-checked against
database roles on each request (Finding #65)."

## Root cause

Wrong repository. The `users.role` column is owned by
`src/auth/user_repository.py` → `UserRepository.get_user_with_role(user_id)`,
which returns `{"role": ...}`. `LicenseRepository` is for license-key records,
not users.

## Fix

| File | Change |
|------|--------|
| `src/auth/rbac.py` | `_db_cross_check_role` now uses `UserRepository().get_user_with_role(uuid.UUID(user_id))` and reads `db_user["role"]`. Bare `except Exception: pass` split into `except ValueError` (invalid UUID) and `except Exception` (DB failure), both logged via `logger.warning`. Added `import uuid`. |
| `tests/test_rbac.py` | New `TestDbCrossCheckRole` class — 6 tests: returns DB role, None when user not found, None when role missing, None for invalid UUID (DB never reached), None on DB exception (fail-open), None for empty user_id. |

## Verification

- `tests/test_rbac.py`: **103 passed** (was 97; +6 new)
- `tests/auth/`: **138 passed, 0 failed**
- CI-gated subset (`tests/core/ tests/cli/ tests/seed/ tests/commands/ tests/auth/ tests/unit/ tests/daemon/ tests/vn/`): **2242 passed, 0 failed** (matches baseline)
- `ruff check src/auth/rbac.py tests/test_rbac.py`: clean
- No regression; no public contract changed (`_db_cross_check_role` signature and
  return shape unchanged).

## Status

Verified, not committed.
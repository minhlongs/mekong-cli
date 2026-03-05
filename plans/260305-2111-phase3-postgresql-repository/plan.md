# Phase 3.3-3.6: PostgreSQL Repository Layer & Migration

**Date:** 2026-03-05
**Status:** In Progress
**Priority:** High

---

## Overview

Complete Phase 3 PostgreSQL migration with repository layer, migration scripts, and data migration from JSON to PostgreSQL.

---

## Phases

### Phase 3.3: Repository Layer ✅ In Progress
- Create `LicenseRepository` class with CRUD operations
- Methods: `create_license()`, `get_license()`, `update_license()`, `revoke_license()`, `record_usage()`, `get_usage()`

### Phase 3.4: Migration Scripts ✅ Blocked
- Create `src/db/migrate.py` to run schema on startup
- Add rollback support
- Migration versioning

### Phase 3.5: Update usage_meter.py ✅ Blocked
- Replace JSON file operations with PostgreSQL queries
- Use `LicenseRepository` for usage tracking

### Phase 3.6: Update license_generator.py ✅ Blocked
- Replace JSON revocation list with PostgreSQL queries
- Use `LicenseRepository` for revocation checks

---

## Files to Create

- `src/db/repository.py` - LicenseRepository class
- `src/db/migrate.py` - Migration runner

## Files to Modify

- `src/lib/usage_meter.py` - Use PostgreSQL
- `src/lib/license_generator.py` - Use PostgreSQL revocation

---

## Dependencies

- asyncpg installed (check pyproject.toml)
- PostgreSQL database available
- DATABASE_URL environment variable set

---

## Success Criteria

- [ ] All CRUD operations work with PostgreSQL
- [ ] Migration runs on startup
- [ ] No more JSON file dependencies for licenses/usage
- [ ] Tests pass with PostgreSQL

---
title: "Phase 1: Database Schema"
priority: P1
status: completed
effort: 1.5h
---

# Phase 1: Database Schema

## Context

- **Link to Plan:** [plan.md](plan.md)
- **Related Files:** `src/core/database.py`, `src/raas/`

## Overview

Create PostgreSQL schema for OAuth2 users, sessions, and RBAC roles.

## Key Insights

- Existing `licenses` table needs `role` column addition
- New `users` table stores OAuth2 provider metadata
- `user_sessions` table for JWT session management

## Requirements

### Functional
- Create `users` table with OAuth2 fields
- Add `role` column to `licenses` table
- Create `user_sessions` table for session management
- Migration scripts for existing databases

### Non-functional
- All tables use UUID primary keys
- Timestamps in UTC
- Indexes on frequently queried fields

## Architecture

```sql
-- New tables
users (id, email, oauth_provider, oauth_id, created_at, updated_at)
user_sessions (id, user_id, jwt_token, expires_at, created_at)

-- Modified table
licenses (+role: owner|admin|member|viewer)
```

## Implementation Steps

1. **Create migration file** `src/db/migrations/001_oauth2_schema.sql`
   ```sql
   -- Users table
   CREATE TABLE IF NOT EXISTS users (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       email TEXT UNIQUE NOT NULL,
       oauth_provider TEXT NOT NULL CHECK (oauth_provider IN ('google', 'github')),
       oauth_id TEXT NOT NULL,
       created_at TIMESTAMPTZ DEFAULT NOW(),
       updated_at TIMESTAMPTZ DEFAULT NOW(),
       UNIQUE(oauth_provider, oauth_id)
   );
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_id);

   -- User sessions table
   CREATE TABLE IF NOT EXISTS user_sessions (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID REFERENCES users(id) ON DELETE CASCADE,
       jwt_token TEXT NOT NULL,
       expires_at TIMESTAMPTZ NOT NULL,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
   CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
   CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);

   -- Add role to licenses table
   ALTER TABLE licenses
   ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'member'
   CHECK (role IN ('owner', 'admin', 'member', 'viewer'));
   CREATE INDEX idx_licenses_role ON licenses(role);
   ```

2. **Create migration runner** `src/db/migrations/run.py`
   - Read SQL files from `migrations/` directory
   - Execute in order
   - Track migration state in `schema_migrations` table

3. **Create SQLAlchemy models** `src/models/user.py`, `src/models/session.py`
   ```python
   class User(Base):
       __tablename__ = "users"
       id: Mapped[UUID] = mapped_column(primary=True)
       email: Mapped[str]
       oauth_provider: Mapped[str]
       oauth_id: Mapped[str]
   ```

## Todo List

- [x] Create `src/db/migrations/001_create_users_table.sql`
- [x] Create `src/db/migrations/002_add_roles_to_licenses.sql`
- [x] Create `src/db/migrations/003_create_user_sessions.sql`
- [x] Create `src/db/migrations/__init__.py`
- [x] Update `src/db/migrate.py` with OAuth2 migrations
- [x] Create `src/models/user.py` with User, UserSession, LicenseWithRole dataclasses
- [x] Create `src/auth/user_repository.py` with UserRepository

## Implementation Summary

Created files:
- `src/db/migrations/001_create_users_table.sql` - Users table with OAuth2 fields
- `src/db/migrations/002_add_roles_to_licenses.sql` - RBAC roles for licenses
- `src/db/migrations/003_create_user_sessions.sql` - Session management with token hash
- `src/models/user.py` - Dataclasses: User, UserSession, LicenseWithRole
- `src/auth/user_repository.py` - UserRepository with CRUD operations
- `src/auth/__init__.py` - Module exports
- `src/models/__init__.py` - Module exports
- `src/db/migrations/__init__.py` - Migration loader

## Success Criteria

- [x] Migration SQL files created with proper schema
- [x] All indexes defined for performance
- [x] Models can query database (UserRepository implemented)
- [x] Migration runner updated (migrate.py includes OAuth2 migrations)

## Risk Assessment

- **Risk:** Existing data in `licenses` table
- **Mitigation:** Use `ADD COLUMN IF NOT EXISTS` with default value

## Security Considerations

- OAuth IDs must be unique per provider
- Sessions have expiration timestamps
- CASCADE delete on user removal

## Next Steps

→ Phase 2: Implement OAuth2 providers (Google, GitHub)

# Database Migration Scripts

This directory contains scripts for database backup, restore, and migration operations.

## Scripts

### `db-backup.sh`

Creates a timestamped PostgreSQL backup.

**Usage:**
```bash
DATABASE_URL=postgresql://user:pass@host/db scripts/db-backup.sh /backup/dir [prefix]
```

**Examples:**
```bash
# Staging backup
DATABASE_URL=$STAGING_DB_URL scripts/db-backup.sh /tmp/backups staging

# Production backup with S3 upload
BACKUP_S3_BUCKET=my-company-backups \
DATABASE_URL=$PROD_DB_URL \
scripts/db-backup.sh /backups production
```

**Outputs:**
- Creates gzipped SQL dump: `prefix-db-timestamp-commit.sql.gz`
- Optionally uploads to S3 if `BACKUP_S3_BUCKET` is set
- Cleans up backups older than `BACKUP_RETENTION_DAYS` (default: 7)

### `db-restore.sh`

Restores a PostgreSQL database from a backup file.

**Usage:**
```bash
DATABASE_URL=postgresql://user:pass@host/db scripts/db-restore.sh /path/to/backup.sql.gz
```

**Examples:**
```bash
# Interactive restore (default)
DATABASE_URL=$PROD_DB_URL scripts/db-restore.sh /tmp/backups/production-*.sql.gz

# Non-interactive for automation
RESTORE_CONFIRM=true DATABASE_URL=$PROD_DB_URL scripts/db-restore.sh backup.sql.gz
```

**Safety features:**
- Requires explicit confirmation (can skip with `RESTORE_CONFIRM=true`)
- Verifies backup integrity before restore
- Optional connection disabling during restore (`DISABLE_CONNECTIONS=true`)

### `db-rollback.sh` (Lightweight)

Attempts to remove migration records from `schema_migrations` table.

**Note:** This does NOT reverse schema changes. Use `db-restore.sh` for true rollback.

**Usage:**
```bash
DATABASE_URL=postgresql://user:pass@host/db scripts/db-rollback.sh 014
# or
DATABASE_URL=postgresql://user:pass@host/db scripts/db-rollback.sh --last 1
```

## Python Migration Runner

The main migration functionality is in Python:

```bash
# Check status
python -m src.db.migrate status

# Apply migrations
python -m src.db.migrate migrate

# Rollback to specific version (removes from tracking only)
python -m src.db.migrate rollback 014
```

## GitHub Actions Workflow

The `.github/workflows/migrations.yml` workflow automates:

1. **migrate-staging** - Automatic daily and post-deploy migrations
2. **migrate-production** - Manual approval required, with auto-backup
3. **migration-health** - Daily health check for pending migrations

## Best Practices

1. **Always backup before migration** - The CI/CD pipeline does this automatically
2. **Test in staging first** - Verify migrations work before production
3. **Keep backups** - Retain at least 30 days of backups for critical data
4. **Monitor during migration** - Watch for long-running locks
5. **Have a restore plan** - Test restore procedure regularly
6. **Tag releases** - Correlate migrations with git tags

## Troubleshooting

### pg_dump not found
Install PostgreSQL client:
```bash
# Ubuntu/Debian
apt-get install postgresql-client

# macOS
brew install libpq
```

### Permission denied on backup
Ensure the database user has:
- CONNECT privilege on database
- SELECT privilege on all tables
- USAGE on sequences (for serial columns)

### Migration fails with duplicate relation
The migration was partially applied. Options:
1. Restore from backup and retry
2. Manually mark migration as applied (not recommended)
   ```sql
   INSERT INTO schema_migrations (version, name) VALUES ('014', 'my migration');
   ```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `BACKUP_S3_BUCKET` | S3 bucket for backups | No |
| `BACKUP_RETENTION_DAYS` | Days to keep local backups | No (default: 7) |
| `SKIP_BACKUP` | Skip backup creation (dangerous) | No |
| `RESTORE_CONFIRM` | Skip confirmation prompt | No |
| `DISABLE_CONNECTIONS` | Disable connections during restore | No |
| `MEKONG_VERSION` | Version string for backup naming | No |

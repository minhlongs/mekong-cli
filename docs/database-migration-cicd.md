# Database Migration CI/CD Pipeline

## Overview

The Migration CI/CD Pipeline provides automated, safe database schema changes with:

- **Automated staging migrations** - Runs on schedule and after successful deployments
- **Manual production migrations** - Requires explicit approval with safety checks
- **Automatic backups** - Creates timestamped backups before each migration
- **Health verification** - Post-migration health checks
- **Rollback capability** - Restore from backup if issues arise
- **Notifications** - Slack/PagerDuty alerts for failures

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  migrations.yml workflow                             │  │
│  │                                                       │  │
│  │  Jobs:                                                │  │
│  │  • migrate-staging (auto)                            │  │
│  │  • migrate-production (manual)                       │  │
│  │  • migration-health (daily)                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Migration Scripts                         │
│  • scripts/db-backup.sh   - Create backups                │
│  • scripts/db-restore.sh  - Restore from backup           │
│  • src/db/migrate.py      - Migration runner              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                       │
│  • schema_migrations table tracks applied versions        │
│  • Migrations in src/db/migrations/                       │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required Secrets

Configure in GitHub repository Settings → Secrets and variables → Actions:

| Secret | Description | Required For |
|--------|-------------|--------------|
| `STAGING_DATABASE_URL` | PostgreSQL connection string for staging | Staging migrations |
| `PRODUCTION_DATABASE_URL` | PostgreSQL connection string for production | Production migrations |
| `BACKUP_S3_BUCKET` | S3 bucket for offsite backups (optional) | Backup upload |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications (optional) | Alerts |
| `PAGERDUTY_INTEGRATION_KEY` | PagerDuty integration key (optional) | Critical alerts |
| `STAGING_GATEWAY_URL` | Staging API URL for health checks (optional) | Verification |
| `PRODUCTION_GATEWAY_URL` | Production API URL for health checks (optional) | Verification |

### Setting DATABASE_URL Format

```
postgresql://username:password@hostname:5432/database_name
```

Example:
```bash
postgresql://mekong_user:secure_password@db.example.com:5432/mekong_staging
```

## Usage

### Manual Migration Trigger

1. Go to GitHub repository → Actions → Database Migrations
2. Click "Run workflow"
3. Select environment:
   - `staging` - Runs immediately on staging database
   - `production` - Requires manual approval in GitHub environment
4. Optional: Enter target migration version (e.g., `014` to migrate to version 014)
5. Optional: For rollback, enter version in "Rollback mode" field (version to rollback TO)
6. Click "Run workflow"

### Automated Staging Migrations

Staging migrations run automatically:
- Daily at 2:00 AM UTC (health check)
- After successful staging deployments (if triggered via repository_dispatch)
- Manual dispatch

### Production Migrations

Production migrations require **manual approval**:
1. Trigger workflow with environment = production
2. GitHub will request approval via protected environment
3. Approver must confirm understanding of impact
4. Backup is automatically created before migration
5. Migration executes with verification
6. Success/failure notifications sent

## Migration Files

Migrations are located in `src/db/migrations/`:

```
src/db/migrations/
├── __init__.py       # Exports all migration SQL
├── 001_create_users_table.sql
├── 002_add_roles_to_licenses.sql
├── ...
└── 014_behavior_graph.sql
```

Migrations are tracked in `src/db/migrate.py`:

```python
MIGRATIONS = [
    ("001", "Initial schema", MIGRATION_001),
    ("002", "Webhook events table", MIGRATION_002),
    # ...
]
```

**Order matters** - migrations are applied in version order.

## Backup & Restore

### Automatic Backups

Backups are created automatically before migrations (unless disabled):

- Location: `/tmp/backups/` on the runner
- Naming: `mekong-{database}-{timestamp}-{commit}.sql.gz`
- Retention: 7 days (configurable via `BACKUP_RETENTION_DAYS`)
- Optional: Upload to S3 if `BACKUP_S3_BUCKET` is configured

### Manual Backup

```bash
DATABASE_URL=$STAGING_DATABASE_URL scripts/db-backup.sh /backup/path staging
```

Outputs backup file path on stdout.

### Restore from Backup

```bash
# Interactive restore with confirmation
DATABASE_URL=$PRODUCTION_DATABASE_URL scripts/db-restore.sh /backups/mekong-prod-20260620T120000Z-abcd1234.sql.gz

# Non-interactive (for automation)
RESTORE_CONFIRM=true DATABASE_URL=$PRODUCTION_DATABASE_URL scripts/db-restore.sh /path/to/backup.sql.gz
```

**Important**: Restoration is irreversible. Ensure you have a current backup of the current state before restoring.

### Rollback Strategy

The pipeline uses **backup-based rollback**:

1. Pre-migration backup created automatically
2. If migration fails or issues detected:
   ```bash
   # Restore the pre-migration backup
   DATABASE_URL=$PRODUCTION_DATABASE_URL scripts/db-restore.sh /path/to/pre-migration-backup.sql.gz
   ```
3. Verify application health after restore

## Rollback Procedures

### Full Database Rollback (Recommended)

1. Identify backup created before the problematic migration
   - Check workflow run logs for `backup_path` output
   - Backups stored in `/tmp/backups/` during migration
2. Restore from backup:
   ```bash
   DATABASE_URL=$PRODUCTION_DATABASE_URL scripts/db-restore.sh [backup_file]
   ```
3. Notify team of rollback completion
4. Investigate migration failure before retrying

### Schema-Only Rollback (Advanced)

The migration system supports forward-only migrations. True schema rollback requires:
1. Manual SQL to reverse changes, OR
2. Restore from backup (recommended)

## Monitoring & Alerts

### Health Checks

The pipeline verifies:
- Migration status (no pending migrations)
- Database connectivity
- Gateway API health (if `*_GATEWAY_URL` configured)

### Notifications

Slack notification example:

```json
{
  "text": "✅ Production database migration completed successfully",
  "attachments": [
    {
      "color": "good",
      "fields": [
        {"title": "Repo", "value": "mekong-cli/mekong-cli", "short": true},
        {"title": "Commit", "value": "abcd1234", "short": true},
        {"title": "Actor", "value": "username", "short": true}
      ]
    }
  ]
}
```

PagerDuty triggers on production failures with severity "critical".

## Troubleshooting

### Migration Fails with "relation already exists"

**Cause**: Migration was partially applied before failure.

**Resolution**:
```bash
# Check migration status
python -m src.db.migrate status

# Manually record skipped migration if safe
# Or restore from backup and re-run
```

### Connection Timeout

**Cause**: Database connection pool exhausted or network issue.

**Resolution**:
- Increase connection pool size in `src/db/database.py`
- Check database max_connections
- Verify network connectivity and firewall rules

### Backup Fails with "permission denied"

**Cause**: pg_dump not available or insufficient database permissions.

**Resolution**:
- Ensure `postgresql-client` is installed on runner
- Verify database user has CONNECT and SELECT privileges on all tables

### GitHub Runner Disk Space

**Cause**: Backups accumulating on runner.

**Resolution**:
- Backups auto-clean after 7 days via `find -mtime`
- S3 upload enabled to offload storage
- Consider larger runner or external backup storage

## Best Practices

1. **Always test migrations in staging first** - The pipeline enforces this by having separate staging/production jobs
2. **Keep migrations small and reversible** - One logical change per migration
3. **Add data migrations as separate files** - Don't mix schema and data changes
4. **Review migration SQL** - Ensure it's idempotent where possible
5. **Monitor migration duration** - Long locks can cause downtime
6. **Use maintenance windows** - Schedule production migrations during low-traffic periods
7. **Document breaking changes** - Update application code alongside migrations
8. **Tag releases** - Correlate migrations with git tags for traceability

## Integration with Deploy Pipeline

To trigger staging migrations automatically after deployment, add to `deploy.yml`:

```yaml
deploy-staging:
  # ... existing steps ...
  - name: Trigger Migration Workflow
    if: success()
    uses: peter-evans/repository-dispatch@v2
    with:
      token: ${{ secrets.GITHUB_TOKEN }}
      event-type: migrate-staging
      client-payload: '{"ref": "${{ github.ref }}", "sha": "${{ github.sha }}"}'
```

## Security Considerations

- Database URLs stored as GitHub Secrets (encrypted)
- S3 backups should use server-side encryption
- Slack webhook secret stored in GitHub Secrets
- Production environment requires manual approval (no auto-approval)
- Backup files contain sensitive data - handle with care
- Consider encryption at rest for backups
- Rotate database credentials regularly

## Reference

### Workflow Triggers

| Trigger | When | Environments |
|---------|------|--------------|
| `workflow_dispatch` | Manual | Staging, Production |
| `repository_dispatch` | From other workflows | Staging |
| `schedule` | Cron | Staging (health check) |

### Environment Protection

Configure in GitHub repository → Settings → Environments:
- `staging` - Auto-approve for CI
- `production` - Required reviewers, wait timer, branch restrictions

### Required IAM Permissions (for AWS/S3 backups)

If using S3:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::your-backup-bucket/backups/*"
    }
  ]
}
```

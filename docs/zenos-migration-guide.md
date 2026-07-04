# ZenOS Migration Guide

> Migrating from Tenant Model to Economic Particles with Constitutional AI

**Last Updated**: 2026-06-18  
**Target Version**: Mekong CLI v6.0+  
**Migration Type**: One-time architectural transformation

---

## Overview

ZenOS is the next-generation architecture for Mekong CLI, replacing the legacy tenant model with **Economic Particles** — atomic economic units that combine financial tracking, constitutional governance, and AI augmentation.

### What Changes

| Legacy System | ZenOS Replacement |
|---------------|-------------------|
| `tenants` table | `particles` table |
| Org-based isolation | Particle-based identity |
| Simple credit tracking | Treasury with multi-currency support |
| No governance | Constitution + amendment process |
| No founder profile | Encrypted Founder Genome |
| Monolithic agents | AI Cells (specialized per-particle) |

### Migration Path

```
┌─────────────────┐
│  Existing Users │
│  (tenants.db)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Run Migration Script               │
│  python3 scripts/                  │
│    migrate-tenants-to-particles.py │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Backwards Compatibility Layer      │
│  - Tenant APIs still work           │
│  - Auto-convert on access           │
│  - Deprecation warnings logged     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Full Particle Mode                 │
│  - New particle commands            │
│  - Constitution management          │
│  - Behavior Graph active            │
└─────────────────────────────────────┘
```

---

## Pre-Migration Checklist

### 1. Backup Everything

```bash
# Backup tenant database
cp ~/.mekong/raas/tenants.db ~/.mekong/raas/tenants.db.backup-$(date +%Y%m%d)

# Backup settings
cp ~/.mekong/settings.json ~/.mekong/settings.json.backup-$(date +%Y%m%d)

# Export tenant list for reference
sqlite3 ~/.mekong/raas/tenants.db "SELECT id, name, created_at FROM tenants" > ~/Desktop/tenants-export.csv
```

### 2. Verify Prerequisites

```bash
# Check Python version (3.11+ required)
python3 --version

# Check database exists
ls -la ~/.mekong/raas/tenants.db

# Check disk space (migration needs ~2x DB size)
df -h ~/.mekong/raas
```

### 3. Review Current Tenants

```bash
# List all tenants
python3 -m src.main raas tenant list

# Check for inactive tenants (these will be suspended, not active)
sqlite3 ~/.mekong/raas/tenants.db "SELECT name, is_active FROM tenants WHERE is_active = 0"
```

---

## Running the Migration

### Dry Run (Recommended First)

```bash
python3 scripts/migrate-tenants-to-particles.py --dry-run
```

Output example:
```
============================================================
TENANT TO PARTICLE MIGRATION
============================================================

Found 3 tenant(s) in /Users/you/.mekong/raas/tenants.db

Tenants to migrate:
  1. Acme Corp (id: a1b2c3d4...)
  2. Startup XYZ (id: e5f6g7h8...)
  3. My Shop (id: i9j0k1l2...)

Initializing particles database: /Users/you/.mekong/raas/particles.db

[DRY-RUN] Would migrate tenant 'Acme Corp' (a1b2c3d4...) to particle
[DRY-RUN] Would migrate tenant 'Startup XYZ' (e5f6g7h8...) to particle
[DRY-RUN] Would migrate tenant 'My Shop' (i9j0k1l2...) to particle

[DRY-RUN] Would set backwards compatibility flag in /Users/you/.mekong/settings.json

VERIFICATION
✓ Particle count matches tenant count
✓ Constitutions created for all particles
✓ Behavior graphs initialized
✓ Treasuries initialized

Migration Summary
Total tenants:  3
Successful:     3
Failed:         0

✓ Dry run completed successfully!
```

### Actual Migration

```bash
python3 scripts/migrate-tenants-to-particles.py
```

You'll be prompted for confirmation:
```
Proceed with migration of 3 tenant(s)? (yes/no): yes
```

#### Migration Output

```
============================================================
TENANT TO PARTICLE MIGRATION
============================================================

Found 3 tenant(s) in /Users/you/.mekong/raas/tenants.db

Tenants to migrate:
  1. Acme Corp (id: a1b2c3d4...)
  2. Startup XYZ (e5f6g7h8...)
  3. My Shop (i9j0k1l2...)

Initializing particles database: /Users/you/.mekong/raas/particles.db

MIGRATING...
✓ Migrated tenant 'Acme Corp' (a1b2c3d4...) to particle with constitution, behavior_graph, and treasury
✓ Migrated tenant 'Startup XYZ' (e5f6g7h8...) to particle with constitution, behavior_graph, and treasury
✓ Migrated tenant 'My Shop' (i9j0k1l2...) to particle with constitution, behavior_graph, and treasury

SETTING BACKWARDS COMPATIBILITY FLAG
✓ Set backwards compatibility flag in /Users/you/.mekong/settings.json

VERIFICATION
✓ All verifications passed
  - Particles: 3
  - Constitutions: 3
  - Behavior graphs: 3
  - Treasuries: 3

Migration Summary
Total tenants:  3
Successful:     3
Failed:         0

✓ Migration completed successfully!

Particles database: /Users/you/.mekong/raas/particles.db
Backwards compatibility enabled in settings.json

Next steps:
  1. Run tests: python3 -m pytest tests/ -k particle
  2. Verify API endpoints work with particle mode
  3. Update CLI commands to use particle commands
```

### Force Migration (Skip Confirmation)

```bash
python3 scripts/migrate-tenants-to-particles.py --force
```

### Migration with Rollback on Failure

If the migration fails partway through, you can rollback:

```bash
python3 scripts/migrate-tenants-to-particles.py --rollback
```

This will:
- Drop all particle tables
- Remove backwards compatibility flag
- Keep `tenants.db` intact

---

## What Gets Created

### 1. Particle Record

Each tenant becomes a particle with:

```json
{
  "id": "a1b2c3d4-...",
  "type": "opc",
  "name": "Acme Corp",
  "mission": null,
  "founder_id": null,
  "status": "active",
  "trust_score": 50.0,
  "created_at": "2025-06-01T10:30:00Z",
  "updated_at": "2025-06-18T15:45:00Z"
}
```

### 2. ZenOS Constitution

Every particle gets the default ZenOS Constitution (v1.0). The principle IDs match the runtime reviewer in `src/core/constitution.py`; descriptions preserve the ZenOS mission language.

```json
{
  "version": "1.0",
  "name": "ZenOS Constitution",
  "description": "Default constitutional framework for Economic Particles",
  "principles": [
    {
      "id": "safety",
      "priority": 1,
      "description": "Human wellbeing takes precedence over efficiency and profit"
    },
    {
      "id": "human_oversight",
      "priority": 2,
      "description": "AI systems serve humans, not the reverse"
    },
    {
      "id": "transparency",
      "priority": 3,
      "description": "All decisions affecting the particle must be explainable"
    },
    {
      "id": "privacy",
      "priority": 4,
      "description": "Particles may leave the ecosystem with their data"
    },
    {
      "id": "fairness",
      "priority": 5,
      "description": "No entity may extract value without fair compensation"
    },
    {
      "id": "beneficence",
      "priority": 6,
      "description": "Design decisions prioritize OPC and micro-enterprises"
    },
    {
      "id": "sustainability",
      "priority": 7,
      "description": "Revenue serves mission, not the reverse"
    },
    {
      "id": "accountability",
      "priority": 8,
      "description": "Multiple protocol jurisdictions may coexist"
    },
    {
      "id": "security",
      "priority": 9,
      "description": "Particles own and control their digital infrastructure"
    }
  ],
  "amendment_process": {
    "proposal_threshold": 0.1,
    "voting_period_days": 30,
    "quorum": 0.3,
    "pass_threshold": 0.666,
    "cooling_period_days": 7
  },
  "created_at": "2025-06-18T15:45:00Z",
  "source": "migration:default_zenos"
}
```

### 3. Empty Behavior Graph

```json
{
  "version": "1.0",
  "nodes": [],
  "edges": [],
  "metadata": {
    "created_at": "2025-06-18T15:45:00Z",
    "last_updated": "2025-06-18T15:45:00Z",
    "node_count": 0,
    "edge_count": 0
  }
}
```

### 4. Empty Treasury

Multi-currency ready with allocation rules:

```json
{
  "version": "1.0",
  "currency_balances": {},
  "allocation_rules": {
    "operating_reserve_percent": 0.30,
    "tax_reserve_percent": 0.25,
    "reinvestment_percent": 0.30,
    "founder_draw_percent": 0.15
  },
  "transactions": [],
  "metadata": {
    "created_at": "2025-06-18T15:45:00Z",
    "currency_support": ["VND", "USD", "EUR"],
    "self_custody_enabled": false
  }
}
```

---

## Backwards Compatibility

The migration enables **legacy tenant compatibility mode**. Existing APIs continue to work:

### Tenant API (Still Works)

```python
# These continue to function during transition
GET /v1/raas/tenant/{id}
POST /v1/raas/tenant/create
```

Behind the scenes, the gateway:
1. Receives tenant-based request
2. Looks up corresponding particle
3. Routes to particle service
4. Returns tenant-shaped response

### Disabling Compatibility

Once you're ready to go full particle mode:

```bash
# Edit settings.json
{
  "raas": {
    "legacy_tenant_compatibility": false,  // Change to false
    "migration_completed_at": "2025-06-18T15:45:00Z",
    "particle_mode": true
  }
}
```

Then update your integrations to use particle endpoints:
- `GET /v1/particle/{id}` instead of `/tenant/{id}`
- `POST /v1/particle/create` instead of `/tenant/create`

---

## Post-Migration Steps

### 1. Run Tests

```bash
# Run particle-specific tests
python3 -m pytest tests/zenos/test_particle_lifecycle.py -v

# Run migration tests
python3 -m pytest tests/zenos/test_migrate_tenants_to_particles.py -v

# Verify Vietnam workflows still work
python3 -m pytest tests/zenos/test_vietnam_feature_regression.py -v

# Full test suite (recommended)
python3 -m pytest -q
```

### 2. Verify API Endpoints

```bash
# List particles (new API)
mekong particle list

# Show particle details
mekong particle status <particle-id>

# Show constitution
mekong particle constitution <particle-id>
```

### 3. Test Constitution Review

```bash
# Check constitutional compliance of a command
mekong constitution review --action "finance:create-invoice" --amount 1000000
```

### 4. Initialize Founder Genome (Optional)

```bash
# Launch founder genome capture wizard
mekong genome init

# View existing genome
mekong genome view
```

### 5. Confirm Vietnam Features

Vietnam commands remain available and are particle-aware through the compatibility layer:

- `mekong ke-toan`
- `mekong thue-dnvn`
- `mekong zalo-oa`
- `mekong vietqr`

Run `tests/zenos/test_vietnam_feature_regression.py` after migration to confirm invoice, tax, Zalo OA, and VietQR behavior.

### 6. Update CLI Aliases (Optional)

If you want particle-first command experience:

```bash
# In your .zshrc or .bashrc
alias mekong-particle='mekong particle'
alias mekong-constitution='mekong constitution'
alias mekong-genome='mekong genome'
```

---

## API Changes

### New Particle Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/particle` | POST | Create new particle |
| `/v1/particle/{id}` | GET | Get particle details |
| `/v1/particle/{id}/constitution` | GET | Get particle's constitution |
| `/v1/particle/{id}/treasury/balance` | GET | Get treasury balance |
| `/v1/particle/{id}/behavior-graph/query` | POST | Query behavior graph |

### Deprecated Tenant Endpoints

These work in compatibility mode but will be removed in v7.0:

- `POST /v1/raas/tenant/create` → Use `POST /v1/particle`
- `GET /v1/raas/tenant/{id}` → Use `GET /v1/particle/{id}`
- `PUT /v1/raas/tenant/{id}/deactivate` → Use `POST /v1/particle/{id}/suspend`

---

## Troubleshooting

### Migration Fails: Database Locked

```bash
# Check for other processes using the DB
lsof ~/.mekong/raas/tenants.db

# Stop mekong gateway if running
sudo launchctl stop com.mekong.gateway

# Retry migration
python3 scripts/migrate-tenants-to-particles.py
```

### Verification Fails: Missing Constitution

```bash
# Check if constitutions were created
sqlite3 ~/.mekong/raas/particles.db "SELECT COUNT(*) FROM particle_constitutions"

# Should equal particle count. If not, run:
python3 scripts/migrate-tenants-to-particles.py --repair-constitutions
```

### Rollback Needed

```bash
# Full rollback
python3 scripts/migrate-tenants-to-particles.py --rollback

# Verify tenants still accessible
python3 -m src.main raas tenant list
```

### Compatibility Mode Not Working

Check `settings.json`:

```json
{
  "raas": {
    "legacy_tenant_compatibility": true,  // Must be true
    "particle_mode": true
  }
}
```

Restart gateway after changing:
```bash
sudo launchctl kickstart -k system/com.mekong.gateway
```

---

## Understanding the New Data Model

### Particle vs Tenant

| Aspect | Tenant (Legacy) | Particle (ZenOS) |
|--------|-----------------|------------------|
| Identity | UUID | UUID |
| Type | N/A | `opc`, `cooperative`, `micro_enterprise`, `creator` |
| Governance | None | Constitution + amendment process |
| Financial | Simple credit counter | Treasury with multi-currency |
| Identity | Tenant ID | `key_id` (license key) |
| Behavior | Not tracked | Behavior Graph (nodes/edges) |
| Founder | Not captured | Encrypted Founder Genome |

### Particle Lifecycle

```
birth (registration)
  ├─> active (normal operation)
  │    ├─> suspended (temporary pause)
  │    ├─> merged (combine with another particle)
  │    └─> split (create child particles)
  └─> dissolved (permanent termination)
```

---

## Next Steps After Migration

### 1. Read Constitutional AI Guide

See [`docs/constitutional-ai.md`](./constitutional-ai.md) to understand:

- The 9 constitutional principles
- How review scoring works
- Configuring enforcement modes

### 2. Explore Economic Particles

See [`docs/economic-particles.md`](./economic-particles.md) to learn:

- Particle types and use cases
- Treasury management
- Balance calculation mechanics

### 3. Capture Founder Genome

See [`docs/founder-genome.md`](./founder-genome.md) to discover:

- Genome wizard flow
- Trait definitions
- AI analysis capabilities

### 4. Update Your Integrations

If you have external systems integrating with Mekong:

| Integration | Old | New |
|-------------|-----|-----|
| API calls | `/v1/raas/tenant/*` | `/v1/particle/*` |
| Webhooks | `tenant.*` events | `particle.*` events |
| Database | `tenants` table | `particles` + `economic_particles` |
| SDK | `Tenant` class | `EconomicParticle` class |

SDK update:
```python
# Old
from mekong.raas import Tenant
tenant = Tenant.get_by_id("...")

# New
from mekong.models import EconomicParticle
particle = EconomicParticle.get_by_id("...")
```

---

## Support

- **Migration Issues**: Check `~/.mekong/logs/migration.log`
- **Compatibility Mode**: See `HARNESS.md` section on legacy modes
- **Full Documentation**: [`docs/`](./) directory
- **Community**: [mekongmind.com/guides](https://mekongmind.com/guides)

---

## Appendix: Database Schema

### New Tables

```sql
-- Particles (replaces tenants)
CREATE TABLE particles (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL DEFAULT 'opc',
    name TEXT NOT NULL,
    mission TEXT,
    founder_id TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    trust_score REAL DEFAULT 50.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Constitutions
CREATE TABLE particle_constitutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    particle_id TEXT NOT NULL UNIQUE,
    constitution_json TEXT NOT NULL,
    version TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (particle_id) REFERENCES particles(id) ON DELETE CASCADE
);

-- Behavior Graphs
CREATE TABLE behavior_graphs (
    particle_id TEXT PRIMARY KEY,
    graph_json TEXT NOT NULL,
    version TEXT NOT NULL,
    node_count INTEGER DEFAULT 0,
    edge_count INTEGER DEFAULT 0,
    last_updated TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (particle_id) REFERENCES particles(id) ON DELETE CASCADE
);

-- Treasuries
CREATE TABLE treasuries (
    particle_id TEXT PRIMARY KEY,
    treasury_json TEXT NOT NULL,
    version TEXT NOT NULL,
    currency_balances_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (particle_id) REFERENCES particles(id) ON DELETE CASCADE
);
```

### Legacy Tables (Preserved)

The `tenants` table is kept intact for backwards compatibility and rollback support.

---

**Migration Complete?** → Proceed to [`docs/constitutional-ai.md`](./constitutional-ai.md)

#!/usr/bin/env python3
"""Migration script: convert tenants to economic particles with ZenOS constitutions.

This script performs a one-time migration from the legacy tenant model to the
new Economic Particle architecture introduced in the ZenOS redesign.

Migration steps:
1. Read all tenants from ~/.mekong/raas/tenants.db
2. Create particle record for each tenant (copy id, name, created_at, status)
3. Create ZenOS constitution for each particle
4. Create empty behavior_graph (JSON placeholder)
5. Create empty treasury (multi-currency ready)
6. Set backwards compatibility flag in settings

Dependencies: Python 3.11+, sqlite3 (stdlib)

Usage:
    python3 scripts/migrate-tenants-to-particles.py [--dry-run] [--force]

Options:
    --dry-run    Show what would be migrated without making changes
    --force      Skip confirmation prompt (use with caution)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

# Migration constants
TENANTS_DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"
PARTICLES_DB_PATH = Path.home() / ".mekong" / "raas" / "particles.db"
SETTINGS_PATH = Path.home() / ".mekong" / "settings.json"

# Default ZenOS Constitution (v1.0)
# Runtime review uses src.core.constitution.Principle IDs. Descriptions preserve
# the ZenOS intent behind each guardrail.
DEFAULT_CONSTITUTION = {
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
        "proposal_threshold": 0.1,  # 10% trust score required to propose
        "voting_period_days": 30,
        "quorum": 0.3,  # 30% participation required
        "pass_threshold": 0.666,  # 2/3 majority
        "cooling_period_days": 7
    },
    "created_at": None,  # Filled during migration
    "source": "migration:default_zenos"
}

# Empty behavior graph placeholder
EMPTY_BEHAVIOR_GRAPH = {
    "version": "1.0",
    "nodes": [],
    "edges": [],
    "metadata": {
        "created_at": None,
        "last_updated": None,
        "node_count": 0,
        "edge_count": 0
    }
}

# Empty treasury placeholder (multi-currency ready)
EMPTY_TREASURY = {
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
        "created_at": None,
        "currency_support": ["VND", "USD", "USDT", "EUR"],
        "self_custody_enabled": False
    }
}

# Particle status mapping from tenant is_active
TENANT_STATUS_TO_PARTICLE = {
    1: "active",
    0: "suspended"
}


def connect_tenants() -> sqlite3.Connection:
    """Connect to the tenants database."""
    if not TENANTS_DB_PATH.exists():
        raise FileNotFoundError(f"Tenants database not found: {TENANTS_DB_PATH}")
    conn = sqlite3.connect(str(TENANTS_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_particles_db() -> sqlite3.Connection:
    """Initialize the particles database with required tables."""
    PARTICLES_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PARTICLES_DB_PATH))
    conn.row_factory = sqlite3.Row

    # Create particles table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS particles (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL DEFAULT 'opc',
            name TEXT NOT NULL,
            mission TEXT,
            founder_id TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            trust_score REAL DEFAULT 50.0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Create constitutions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS particle_constitutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            particle_id TEXT NOT NULL UNIQUE,
            constitution_json TEXT NOT NULL,
            version TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (particle_id) REFERENCES particles(id) ON DELETE CASCADE
        )
    """)

    # Create behavior_graphs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS behavior_graphs (
            particle_id TEXT PRIMARY KEY,
            graph_json TEXT NOT NULL,
            version TEXT NOT NULL,
            node_count INTEGER DEFAULT 0,
            edge_count INTEGER DEFAULT 0,
            last_updated TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (particle_id) REFERENCES particles(id) ON DELETE CASCADE
        )
    """)

    # Create treasuries table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS treasuries (
            particle_id TEXT PRIMARY KEY,
            treasury_json TEXT NOT NULL,
            version TEXT NOT NULL,
            currency_balances_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (particle_id) REFERENCES particles(id) ON DELETE CASCADE
        )
    """)

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_particles_status ON particles(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_particles_type ON particles(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_particles_founder ON particles(founder_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_constitutions_particle ON particle_constitutions(particle_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_treasuries_particle ON treasuries(particle_id)")

    conn.commit()
    return conn


def read_tenants(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """Read all tenants from the database."""
    cursor = conn.execute("SELECT * FROM tenants ORDER BY created_at ASC")
    return cursor.fetchall()


def migrate_tenant_to_particle(
    particle_conn: sqlite3.Connection,
    tenant: sqlite3.Row,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """Migrate a single tenant to a particle with all required substructures.

    Returns:
        (success, message) tuple
    """
    tenant_id = tenant["id"]
    tenant_name = tenant["name"]
    created_at = tenant["created_at"]
    _is_active = bool(tenant["is_active"])

    # Map tenant status to particle status
    particle_status = TENANT_STATUS_TO_PARTICLE.get(int(tenant["is_active"]), "active")
    particle_type = "opc"  # Default for migrated tenants

    now = datetime.now(timezone.utc).isoformat()

    try:
        if dry_run:
            return True, f"[DRY-RUN] Would migrate tenant '{tenant_name}' ({tenant_id}) to particle"

        # Begin transaction
        particle_conn.execute("BEGIN")

        # 1. Create particle
        particle_conn.execute("""
            INSERT INTO particles (id, type, name, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tenant_id, particle_type, tenant_name, particle_status, created_at, now))

        # 2. Create constitution (default ZenOS)
        constitution = DEFAULT_CONSTITUTION.copy()
        constitution["created_at"] = now
        constitution_json = json.dumps(constitution, ensure_ascii=False)

        particle_conn.execute("""
            INSERT INTO particle_constitutions (particle_id, constitution_json, version, created_at)
            VALUES (?, ?, ?, ?)
        """, (tenant_id, constitution_json, constitution["version"], now))

        # 3. Create empty behavior graph
        behavior_graph = EMPTY_BEHAVIOR_GRAPH.copy()
        behavior_graph["metadata"]["created_at"] = now
        behavior_graph["metadata"]["last_updated"] = now
        graph_json = json.dumps(behavior_graph, ensure_ascii=False)

        particle_conn.execute("""
            INSERT INTO behavior_graphs (particle_id, graph_json, version, node_count, edge_count, last_updated, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tenant_id, graph_json, behavior_graph["version"],
              behavior_graph["metadata"]["node_count"],
              behavior_graph["metadata"]["edge_count"],
              behavior_graph["metadata"]["last_updated"],
              now))

        # 4. Create empty treasury
        treasury = EMPTY_TREASURY.copy()
        treasury["metadata"]["created_at"] = now
        treasury_json = json.dumps(treasury, ensure_ascii=False)
        currency_balances_json = json.dumps(treasury["currency_balances"], ensure_ascii=False)

        particle_conn.execute("""
            INSERT INTO treasuries (particle_id, treasury_json, version, currency_balances_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tenant_id, treasury_json, treasury["version"], currency_balances_json, now, now))

        particle_conn.commit()
        return True, f"Migrated tenant '{tenant_name}' ({tenant_id}) to particle with constitution, behavior_graph, and treasury"

    except sqlite3.Error as e:
        particle_conn.rollback()
        return False, f"Failed to migrate tenant {tenant_id}: {e}"


def set_backwards_compatibility_flag(settings_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """Set the backwards compatibility flag in settings.json.

    The flag enables legacy org/tenant API compatibility during transition.
    """
    try:
        settings = {}
        if settings_path.exists():
            with open(settings_path, "r") as f:
                settings = json.load(f)

        # Ensure raas section exists
        if "raas" not in settings:
            settings["raas"] = {}

        # Set the compatibility flag
        settings["raas"]["legacy_tenant_compatibility"] = True
        settings["raas"]["migration_completed_at"] = datetime.now(timezone.utc).isoformat()
        settings["raas"]["particle_mode"] = True

        if dry_run:
            return True, f"[DRY-RUN] Would set backwards compatibility flag in {settings_path}"

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

        return True, f"Set backwards compatibility flag in {settings_path}"

    except Exception as e:
        return False, f"Failed to set compatibility flag: {e}"


def verify_migration(particle_conn: sqlite3.Connection, tenant_count: int) -> List[str]:
    """Verify that all tenants were migrated successfully."""
    issues = []

    cursor = particle_conn.execute("SELECT COUNT(*) FROM particles")
    particle_count = cursor.fetchone()[0]

    if particle_count != tenant_count:
        issues.append(f"Particle count ({particle_count}) does not match tenant count ({tenant_count})")

    # Verify constitutions
    cursor = particle_conn.execute("SELECT COUNT(*) FROM particle_constitutions")
    constitution_count = cursor.fetchone()[0]
    if constitution_count != particle_count:
        issues.append(f"Constitution count ({constitution_count}) does not match particle count ({particle_count})")

    # Verify behavior graphs
    cursor = particle_conn.execute("SELECT COUNT(*) FROM behavior_graphs")
    graph_count = cursor.fetchone()[0]
    if graph_count != particle_count:
        issues.append(f"Behavior graph count ({graph_count}) does not match particle count ({particle_count})")

    # Verify treasuries
    cursor = particle_conn.execute("SELECT COUNT(*) FROM treasuries")
    treasury_count = cursor.fetchone()[0]
    if treasury_count != particle_count:
        issues.append(f"Treasury count ({treasury_count}) does not match particle count ({particle_count})")

    # Check for empty graphs/treasuries
    cursor = particle_conn.execute("""
        SELECT COUNT(*) FROM behavior_graphs
        WHERE json_extract(graph_json, '$.nodes') IS NULL
           OR json_extract(graph_json, '$.edges') IS NULL
    """)
    if cursor.fetchone()[0] > 0:
        issues.append("Some behavior graphs have null nodes/edges")

    cursor = particle_conn.execute("""
        SELECT COUNT(*) FROM treasuries
        WHERE json_extract(treasury_json, '$.currency_balances') IS NULL
    """)
    if cursor.fetchone()[0] > 0:
        issues.append("Some treasuries have null currency_balances")

    return issues


def rollback_migration(particle_conn: sqlite3.Connection) -> Tuple[bool, str]:
    """Rollback the migration by dropping all particle tables."""
    try:
        particle_conn.execute("BEGIN")
        particle_conn.execute("DROP TABLE IF EXISTS treasuries")
        particle_conn.execute("DROP TABLE IF EXISTS behavior_graphs")
        particle_conn.execute("DROP TABLE IF EXISTS particle_constitutions")
        particle_conn.execute("DROP TABLE IF EXISTS particles")
        particle_conn.commit()

        # Remove backwards compatibility flag
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, "r") as f:
                settings = json.load(f)
            if "raas" in settings:
                settings["raas"].pop("legacy_tenant_compatibility", None)
                settings["raas"].pop("migration_completed_at", None)
                settings["raas"].pop("particle_mode", None)
            with open(SETTINGS_PATH, "w") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

        # Optionally delete the particles.db (commented out for safety)
        # if PARTICLES_DB_PATH.exists():
        #     PARTICLES_DB_PATH.unlink()

        return True, "Migration rolled back successfully"

    except Exception as e:
        return False, f"Rollback failed: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Migrate tenants to economic particles with ZenOS constitutions"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be migrated without making changes")
    parser.add_argument("--force", action="store_true",
                        help="Skip confirmation prompt")
    parser.add_argument("--rollback", action="store_true",
                        help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        print("ROLLBACK MODE")
        confirm = args.force or input("Rollback migration? This will delete all particle data. (yes/no): ") == "yes"
        if not confirm:
            print("Rollback cancelled.")
            return 0

        try:
            if PARTICLES_DB_PATH.exists():
                conn = sqlite3.connect(str(PARTICLES_DB_PATH))
                success, msg = rollback_migration(conn)
                conn.close()
                print(f"\033[32m✓ {msg}\033[0m" if success else f"\033[31m✗ {msg}\033[0m")
                return 0 if success else 1
            else:
                print("Particles database not found, nothing to rollback.")
                return 0
        except Exception as e:
            print(f"\033[31m✗ Rollback failed: {e}\033[0m")
            return 1

    print("=" * 60)
    print("TENANT TO PARTICLE MIGRATION")
    print("=" * 60)

    # Check prerequisites
    if not TENANTS_DB_PATH.exists():
        print(f"\033[31m✗ Tenants database not found: {TENANTS_DB_PATH}\033[0m")
        return 1

    if args.dry_run:
        print("\033[33mDRY RUN MODE - No changes will be made\033[0m")

    try:
        # Connect to tenants DB
        tenants_conn = connect_tenants()
        tenants = read_tenants(tenants_conn)
        tenant_count = len(tenants)

        print(f"\nFound {tenant_count} tenant(s) in {TENANTS_DB_PATH}")

        if tenant_count == 0:
            print("\033[33mNo tenants to migrate.\033[0m")
            return 0

        # Show sample tenants
        print("\nTenants to migrate:")
        for i, tenant in enumerate(tenants[:5], 1):
            print(f"  {i}. {tenant['name']} (id: {tenant['id'][:8]}...)")
        if tenant_count > 5:
            print(f"  ... and {tenant_count - 5} more")

        # Initialize particles DB
        print(f"\nInitializing particles database: {PARTICLES_DB_PATH}")
        if not args.dry_run:
            particle_conn = init_particles_db()
        else:
            particle_conn = None

        # Confirm
        if not args.force and not args.dry_run:
            confirm = input(f"\nProceed with migration of {tenant_count} tenant(s)? (yes/no): ") != "yes"
            if confirm:
                print("Migration cancelled.")
                return 0

        # Perform migration
        print("\n" + "=" * 60)
        print("MIGRATING...")
        print("=" * 60)

        success_count = 0
        failure_count = 0

        for tenant in tenants:
            if args.dry_run:
                success, msg = True, f"[DRY-RUN] Would migrate tenant {tenant['name']}"
            else:
                success, msg = migrate_tenant_to_particle(particle_conn, tenant, dry_run=args.dry_run)

            if success:
                print(f"\033[32m✓ {msg}\033[0m")
                success_count += 1
            else:
                print(f"\033[31m✗ {msg}\033[0m")
                failure_count += 1

        # Set backwards compatibility flag
        if not args.dry_run:
            print("\n" + "-" * 60)
            print("SETTING BACKWARDS COMPATIBILITY FLAG")
            print("-" * 60)
            success, msg = set_backwards_compatibility_flag(SETTINGS_PATH, dry_run=args.dry_run)
            if success:
                print(f"\033[32m✓ {msg}\033[0m")
            else:
                print(f"\033[31m✗ {msg}\033[0m")

        # Verification (only for real migrations)
        if not args.dry_run and particle_conn:
            print("\n" + "=" * 60)
            print("VERIFICATION")
            print("=" * 60)
            issues = verify_migration(particle_conn, tenant_count)
            if issues:
                print("\033[31m✗ Verification failed:\033[0m")
                for issue in issues:
                    print(f"  - {issue}")
                return 1
            else:
                print("\033[32m✓ All verifications passed\033[0m")
                print(f"  - Particles: {success_count}")
                print(f"  - Constitutions: {success_count}")
                print(f"  - Behavior graphs: {success_count}")
                print(f"  - Treasuries: {success_count}")

        # Summary
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total tenants:  {tenant_count}")
        print(f"Successful:     {success_count}")
        print(f"Failed:         {failure_count}")

        if failure_count > 0:
            print("\n\033[31m⚠ Some migrations failed. Check logs above.\033[0m")
            return 1
        else:
            print("\n\033[32m✓ Migration completed successfully!\033[0m")
            if not args.dry_run:
                print(f"\nParticles database: {PARTICLES_DB_PATH}")
                print("Backwards compatibility enabled in settings.json")
                print("\nNext steps:")
                print("  1. Run tests: python3 -m pytest tests/ -k particle")
                print("  2. Verify API endpoints work with particle mode")
                print("  3. Update CLI commands to use particle commands")
            return 0

    except Exception as e:
        print(f"\033[31m✗ Migration failed: {e}\033[0m")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

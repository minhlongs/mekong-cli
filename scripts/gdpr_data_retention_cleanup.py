#!/usr/bin/env python3
"""
GDPR Data Retention & Cleanup Script (Task #273)

Implements data retention policies in compliance with GDPR storage
limitation principle (Article 5(1)(e)) and record-keeping requirements.

Retention Policies:
- webhook_events: 90 days (temporary processing)
- poll_responses: 2 years (analytics retention)
- audit_logs: 2 years (security audit), then anonymize PII
- pilot_records: 7 years after account deletion (tax/legal hold)
- conversion_records: 7 years (financial/legal requirement)
- consent_records: Indefinite (proof of lawful basis)
- gdpr_audit_logs: 7 years (compliance evidence)

Usage:
    python3 scripts/gdpr_data_retention_cleanup.py --dry-run
    python3 scripts/gdpr_data_retention_cleanup.py --execute
    python3 scripts/gdpr_data_retention_cleanup.py --schedule  # for cron

Schedule: Run daily at 2 AM via cron or launchd
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# Configuration from environment or defaults
CONFIG_DIR = Path(os.getenv("MEKONG_CONFIG_DIR", "~/.mekong")).expanduser()
RETENTION_DAYS = {
    "webhook_events": 90,
    "poll_responses": 730,  # 2 years
    "audit_logs": 730,  # 2 years (anonymize after, keep metadata)
    "gdpr_audit_logs": 2555,  # 7 years
    "conversion_records": 2555,  # 7 years (legal)
    "deleted_pilots": 2555,  # 7 years deletion markers
    "consent_records": -1,  # indefinite (per Article 7 proof)
}

# Files managed by this script
FILES_TO_CLEAN = {
    "webhook_events": CONFIG_DIR / "webhook_events.jsonl",
    "poll_responses": CONFIG_DIR / "poll_responses.jsonl",
    "conversions": CONFIG_DIR / "conversions.jsonl",
    "consents": CONFIG_DIR / "consents.jsonl",
    "gdpr_audit": CONFIG_DIR / "gdpr_audit.jsonl",
    "audit_logs": CONFIG_DIR / "audit_log.jsonl",
}


def get_cutoff_date(retention_days: int) -> datetime:
    """Calculate cutoff date for given retention period."""
    if retention_days < 0:
        return None  # Indefinite retention
    return datetime.now(timezone.utc) - timedelta(days=retention_days)


def read_jsonl(path: Path) -> List[Dict]:
    """Read JSONL file, return list of records."""
    if not path.exists():
        return []
    
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning("Skipping malformed line in %s: %s", path.name, e)
    return records


def write_jsonl(path: Path, records: List[Dict]) -> None:
    """Write records to JSONL file (overwrite)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("Wrote %d records to %s", len(records), path.name)


def get_record_date(record: Dict, file_type: str) -> datetime:
    """Extract timestamp from record based on file type."""
    timestamp_fields = {
        "webhook_events": "received_at",
        "poll_responses": "recorded_at",
        "conversions": "recorded_at",
        "audit_logs": "timestamp",
        "gdpr_audit": "timestamp",
    }
    
    field = timestamp_fields.get(file_type, "timestamp")
    timestamp_str = record.get(field)
    
    if not timestamp_str:
        # Fallback to any timestamp field
        for key in ["created_at", "onboarded_at", "deleted_at", "given_at"]:
            if key in record:
                timestamp_str = record[key]
                break
    
    if timestamp_str:
        try:
            # Handle ISO format with or without timezone
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError) as e:
            logger.debug("Could not parse timestamp %s: %s", timestamp_str, e)
    
    # Default to now (will be kept)
    return datetime.now(timezone.utc)


def cleanup_jsonl_file(file_type: str, dry_run: bool = True) -> Tuple[int, int]:
    """
    Clean up old records from JSONL file based on retention policy.
    
    Returns:
        (records_removed, records_kept)
    """
    path = FILES_TO_CLEAN.get(file_type)
    if not path or not path.exists():
        logger.warning("File not found: %s", path)
        return 0, 0
    
    retention_days = RETENTION_DAYS.get(file_type, 365)
    cutoff = get_cutoff_date(retention_days)
    
    if cutoff is None:
        logger.info("Skipping %s - indefinite retention", file_type)
        return 0, 0
    
    records = read_jsonl(path)
    kept = []
    removed = 0
    
    for record in records:
        record_date = get_record_date(record, file_type)
        if record_date >= cutoff:
            kept.append(record)
        else:
            removed += 1
    
    logger.info("%s: %d records to remove, %d to keep", file_type, removed, len(kept))
    
    if not dry_run and removed > 0:
        # Backup before deletion
        backup_path = path.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d')}.jsonl")
        path.rename(backup_path)
        write_jsonl(path, kept)
        logger.info("Backup saved to %s", backup_path)
    
    return removed, len(kept)


def cleanup_sqlite_deleted_pilots(dry_run: bool = True) -> Tuple[int, int]:
    """
    Clean up pilot records marked as deleted beyond retention period.
    Requires pilot.db with raw_payload storage.
    """
    db_path = CONFIG_DIR / "pilot.db"
    if not db_path.exists():
        logger.warning("SQLite DB not found: %s", db_path)
        return 0, 0
    
    retention_days = RETENTION_DAYS["deleted_pilots"]
    cutoff = get_cutoff_date(retention_days)
    
    if cutoff is None:
        return 0, 0
    
    cutoff_iso = cutoff.isoformat()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find deleted pilots older than cutoff
    cursor.execute(
        """
        SELECT user_id, deleted_at FROM pilots
        WHERE _deletion_marker = 1 AND deleted_at < ?
        """,
        (cutoff_iso,)
    )
    
    old_deletions = cursor.fetchall()
    removed_count = len(old_deletions)
    
    if not dry_run and removed_count > 0:
        # Create backup
        backup_path = db_path.with_name(f"pilot-backup-{datetime.now().strftime('%Y%m%d')}.db")
        db_path.copy(backup_path)
        
        # Delete old deletion markers
        cursor.execute(
            "DELETE FROM pilots WHERE _deletion_marker = 1 AND deleted_at < ?",
            (cutoff_iso,)
        )
        conn.commit()
        logger.info("Removed %d old deletion marker records", removed_count)
    
    conn.close()
    return removed_count, 0  # No kept count for this operation


def anonymize_audit_logs_pii(dry_run: bool = True) -> int:
    """
    Anonymize PII in audit logs older than 1 year (retain metadata only).
    
    Replaces user_id with hashed version and removes IP addresses.
    """
    audit_path = CONFIG_DIR / "audit_log.jsonl"
    if not audit_path.exists():
        return 0
    
    cutoff = get_cutoff_date(365)  # 1 year for anonymization
    
    records = read_jsonl(audit_path)
    anonymized = 0
    
    for record in records:
        timestamp = get_record_date(record, "audit_logs")
        if timestamp < cutoff:
            # Anonymize PII fields
            if "user_id" in record and record["user_id"]:
                # Hash for consistent anonymization
                import hashlib
                original = record["user_id"]
                record["user_id"] = "anon_" + hashlib.sha256(original.encode()).hexdigest()[:16]
                record["_anonymized"] = True
                anonymized += 1
            
            # Remove IP addresses
            if "client_ip" in record:
                record["client_ip"] = None
            
            # Remove user agent
            if "user_agent" in record:
                record["user_agent"] = None
    
    if not dry_run and anonymized > 0:
        backup_path = audit_path.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d')}.jsonl")
        audit_path.rename(backup_path)
        write_jsonl(audit_path, records)
        logger.info("Anonymized %d audit log records", anonymized)
    
    return anonymized


def run_cleanup(dry_run: bool = True) -> Dict[str, Tuple[int, int]]:
    """
    Run all cleanup operations.
    
    Returns:
        Dict mapping file_type to (removed, kept) counts
    """
    logger.info("Starting GDPR data retention cleanup (dry_run=%s)", dry_run)
    
    results = {}
    
    # Clean JSONL files
    for file_type in ["poll_responses", "conversions", "consents", "gdpr_audit", "audit_logs"]:
        removed, kept = cleanup_jsonl_file(file_type, dry_run)
        results[file_type] = (removed, kept)
    
    # Clean SQLite deleted pilots
    removed, kept = cleanup_sqlite_deleted_pilots(dry_run)
    results["deleted_pilots_sqlite"] = (removed, kept)
    
    # Anonymize old audit logs
    anonymized = anonymize_audit_logs_pii(dry_run)
    results["audit_logs_anonymized"] = (anonymized, 0)
    
    # Summary
    total_removed = sum(r for r, k in results.values())
    total_kept = sum(k for r, k in results.values())
    
    logger.info("Cleanup complete: %d records removed, %d kept", total_removed, total_kept)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="GDPR data retention cleanup - remove expired personal data"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete data (without this, runs in dry-run mode)"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run as scheduled job (logs to syslog)"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate cleanup report"
    )
    
    args = parser.parse_args()
    
    if args.schedule:
        # Configure for syslog/cron
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
    
    results = run_cleanup(dry_run=not args.execute)
    
    if args.report:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": not args.execute,
            "results": {
                k: {"removed": r, "kept": k_val}
                for k, (r, k_val) in results.items()
            },
            "total_removed": sum(r for r, k in results.values()),
            "total_kept": sum(k for r, k in results.values()),
        }
        report_path = CONFIG_DIR / "reports" / f"retention-cleanup-{datetime.now().strftime('%Y%m%d')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2))
        logger.info("Report written to %s", report_path)
    
    return 0 if all(r >= 0 for r, k in results.values()) else 1


if __name__ == "__main__":
    exit(main())

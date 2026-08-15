#!/usr/bin/env python3
"""
GDPR Incident Forensic Collection Script

Preserves evidence for security incident investigation:
- Database snapshots
- Application logs (last 48 hours)
- Memory dumps (if applicable)
- Network captures
- System configurations
- Cloudflare logs (if applicable)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def ensure_directory(path: str) -> Path:
    """Create directory if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def backup_database(incident_id: str, output_dir: Path) -> Dict[str, Any]:
    """Create database snapshot for forensic analysis."""
    db_backup_dir = output_dir / 'database'
    ensure_directory(str(db_backup_dir))

_timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_file = db_backup_dir / f'db_snapshot_{timestamp}.sql'

    result = {
        'backup_file': str(backup_file),
        'success': False,
        'error': None,
        'tables_backed_up': [],
        'row_counts': {}
    }

    try:
        # Get database connection from environment/config
        db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/mekong')

        # Use pg_dump for consistent snapshot
        cmd = [
            'pg_dump',
            '--no-acl',
            '--no-owner',
            '--format=plain',
            '--section=pre-data',
            db_url,
            '-f', str(backup_file)
        ]

        print(f"[*] Creating database snapshot: {backup_file}")
        subprocess.run(cmd, check=True, capture_output=True)

        # Get table row counts
        tables_cmd = [
            'psql', db_url, '-c',
            "SELECT schemaname, tablename, n_tup_ins+n_tup_upd+n_tup_del as estimate FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"
        ]
        tables_output = subprocess.run(tables_cmd, capture_output=True, text=True, check=True)
        result['row_counts'] = {'raw': tables_output.stdout}

        # List of important tables to document
        important_tables = [
            'users', 'licenses', 'usage_records', 'audit_logs',
            'consents', 'founder_genomes', 'pilots', 'plugins',
            'api_keys', 'sessions'
        ]
        result['tables_backed_up'] = important_tables

        result['success'] = True
        print(f"[+] Database snapshot created: {backup_file}")

    except subprocess.CalledProcessError as e:
        result['error'] = f"Database backup failed: {e.stderr.decode() if e.stderr else str(e)}"
        print(f"[!] {result['error']}")
    except Exception as e:
        result['error'] = f"Database backup error: {str(e)}"
        print(f"[!] {result['error']}")

    return result


def collect_application_logs(incident_id: str, output_dir: Path, hours: int = 48) -> Dict[str, Any]:
    """Collect application logs from last N hours."""
    logs_dir = output_dir / 'logs'
    ensure_directory(str(logs_dir))

    result = {
        'logs_collected': [],
        'success': False,
        'error': None
    }

    try:
        # Define log sources
        log_sources = {
            'gateway': '/var/log/mekong/gateway.log',
            'api': '/var/log/mekong/api.log',
            'security': '/var/log/mekong/security.log',
            'agent': '/var/log/mekong/agent.log',
            'postgres': '/var/log/postgresql/postgresql-*.log',
            'nginx': '/var/log/nginx/access.log',
            'cloudflare': '/var/log/mekong/cloudflare.log'
        }

        # Check which logs exist
    _timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        for log_type, log_path in log_sources.items():
            # Use find to get recent logs
            cmd = [
                'find', log_path.split('*')[0] + '*',
                '-mtime', f'-{hours // 24 + 1}',
                '-type', 'f'
            ]

            try:
                log_files = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if log_files.stdout.strip():
                    for log_file in log_files.stdout.strip().split('\n'):
                        if log_file:
                            dest = logs_dir / f"{log_type}_{Path(log_file).name}"
                            subprocess.run(['cp', log_file, str(dest)], check=True)
                            result['logs_collected'].append(str(dest))
                            print(f"[+] Collected log: {log_file} -> {dest}")
            except Exception as e:
                print(f"[!] Could not collect {log_type} logs: {e}")

        # Also collect from ~/.mekong/logs if exists
        mekong_logs = Path.home() / '.mekong' / 'logs'
        if mekong_logs.exists():
            for log_file in mekong_logs.glob('*.log'):
                dest = logs_dir / f"mekong_{log_file.name}"
                subprocess.run(['cp', str(log_file), str(dest)], check=True)
                result['logs_collected'].append(str(dest))

        result['success'] = len(result['logs_collected']) > 0
        print(f"[+] Collected {len(result['logs_collected'])} log files")

    except Exception as e:
        result['error'] = f"Log collection error: {str(e)}"
        print(f"[!] {result['error']}")

    return result


def collect_memory_dumps(incident_id: str, output_dir: Path) -> Dict[str, Any]:
    """Collect memory dumps of critical processes."""
    dumps_dir = output_dir / 'memory'
    ensure_directory(str(dumps_dir))

    result = {
        'dumps_created': [],
        'success': False,
        'error': None
    }

    try:
        # Critical processes to dump
        processes = [
            ('gateway', 'mekong-gateway'),
            ('api', 'uvicorn'),
            ('worker', 'celery')
        ]

    _timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        for name, pattern in processes:
            # Find process IDs
            cmd = ['pgrep', '-f', pattern]
            pids = subprocess.run(cmd, capture_output=True, text=True)

            if pids.stdout.strip():
                for pid in pids.stdout.strip().split('\n'):
                    if pid:
                        dump_file = dumps_dir / f"{name}_pid{pid}_{timestamp}.dmp"
                        # Use gcore if available (gdb)
                        try:
                            subprocess.run(['gcore', '-o', str(dumps_dir / f"{name}_pid{pid}"), pid],
                                         capture_output=True, check=False)
                            if dump_file.exists():
                                result['dumps_created'].append(str(dump_file))
                                print(f"[+] Memory dump: {dump_file}")
                        except FileNotFoundError:
                            print(f"[!] gcore not available, skipping memory dump for {name} (PID {pid})")

        result['success'] = len(result['dumps_created']) > 0
        print(f"[+] Created {len(result['dumps_created'])} memory dumps")

    except Exception as e:
        result['error'] = f"Memory dump error: {str(e)}"
        print(f"[!] {result['error']}")

    return result


def capture_network_traffic(incident_id: str, output_dir: Path, duration: int = 300) -> Dict[str, Any]:
    """Capture network traffic for analysis."""
    capture_dir = output_dir / 'network'
    ensure_directory(str(capture_dir))

    result = {
        'capture_file': None,
        'success': False,
        'error': None,
        'duration_seconds': duration
    }

    try:
    _timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        capture_file = capture_dir / f"network_capture_{timestamp}.pcap"

        print(f"[*] Starting network capture (duration: {duration}s)...")

        # Use tcpdump if available
        subprocess.run([
            'tcpdump', '-i', 'any', '-w', str(capture_file),
            '-s', '0', '--immediate-mode'
        ], timeout=duration, capture_output=True, check=False)

        if capture_file.exists() and capture_file.stat().st_size > 0:
            result['capture_file'] = str(capture_file)
            result['success'] = True
            print(f"[+] Network capture saved: {capture_file} ({capture_file.stat().st_size} bytes)")
        else:
            result['error'] = "No packets captured (tcpdump may require sudo)"

    except subprocess.TimeoutExpired:
        # Expected - capture runs for duration then times out
        if capture_file.exists():
            result['success'] = True
            result['capture_file'] = str(capture_file)
            print(f"[+] Network capture completed: {capture_file}")
    except FileNotFoundError:
        result['error'] = "tcpdump not available"
    except Exception as e:
        result['error'] = f"Network capture error: {str(e)}"

    return result


def backup_system_configs(incident_id: str, output_dir: Path) -> Dict[str, Any]:
    """Backup system configuration files."""
    configs_dir = output_dir / 'configs'
    ensure_directory(str(configs_dir))

    result = {
        'configs_backed_up': [],
        'success': False,
        'error': None
    }

    config_files = [
        '/etc/nginx/nginx.conf',
        '/etc/cloudflare/cloudflare.cfg',
        '/etc/postgresql/postgresql.conf',
        '/app/.env',
        '/app/config.yaml',
        '~/.mekong/config.yaml'
    ]

    try:
        for config_path in config_files:
            path = Path(config_path).expanduser()
            if path.exists():
                dest = configs_dir / path.name
                subprocess.run(['cp', str(path), str(dest)], check=True)
                result['configs_backed_up'].append(str(dest))
                print(f"[+] Backed up config: {path} -> {dest}")

        result['success'] = len(result['configs_backed_up']) > 0

    except Exception as e:
        result['error'] = f"Config backup error: {str(e)}"

    return result


def collect_cloudflare_logs(incident_id: str, output_dir: Path) -> Dict[str, Any]:
    """Fetch recent Cloudflare logs via API if credentials available."""
    cf_dir = output_dir / 'cloudflare'
    ensure_directory(str(cf_dir))

    result = {
        'logs_fetched': [],
        'success': False,
        'error': None
    }

    cf_api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
    if not cf_api_token:
        result['error'] = "CLOUDFLARE_API_TOKEN not set"
        return result

    try:
        import requests

        zone_id = os.environ.get('CLOUDFLARE_ZONE_ID')
        if not zone_id:
            # Get zones
            zones_resp = requests.get(
                'https://api.cloudflare.com/client/v4/zones',
                headers={'Authorization': f'Bearer {cf_api_token}'}
            )
            zones = zones_resp.json().get('result', [])
            if zones:
                zone_id = zones[0]['id']

        if zone_id:
            # Fetch logs for last 24 hours
        _timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            logs_resp = requests.get(
                f'https://api.cloudflare.com/client/v4/zones/{zone_id}/logs/requests',
                headers={'Authorization': f'Bearer {cf_api_token}'},
                params={'start': timestamp, 'end': timestamp}
            )

            if logs_resp.status_code == 200:
                log_file = cf_dir / f"cloudflare_logs_{datetime.utcnow().strftime('%Y%m%d')}.json"
                with open(log_file, 'w') as f:
                    json.dump(logs_resp.json(), f, indent=2)
                result['logs_fetched'].append(str(log_file))
                result['success'] = True
                print(f"[+] Fetched Cloudflare logs: {log_file}")

    except ImportError:
        result['error'] = "requests library not available"
    except Exception as e:
        result['error'] = f"Cloudflare logs error: {str(e)}"

    return result


def generate_evidence_index(incident_id: str, output_dir: Path, collection_results: Dict[str, Any]) -> str:
    """Generate evidence index manifest."""
    index_file = output_dir / 'EVIDENCE_INDEX.md'

    with open(index_file, 'w') as f:
        f.write(f"""# Evidence Index - Incident {incident_id}

**Collection Date:** {datetime.utcnow().isoformat()}Z
**Collected By:** Forensic Collection Script

## Evidence Inventory

### 1. Database Snapshot
""")

        if collection_results.get('database', {}).get('success'):
            f.write(f"- Backup file: `{collection_results['database']['backup_file']}`\n")
            f.write(f"- Tables: {', '.join(collection_results['database']['tables_backed_up'])}\n")
        else:
            f.write("- **FAILED**\n")

        f.write("""
### 2. Application Logs
""")
        logs = collection_results.get('logs', {}).get('logs_collected', [])
        for log in logs:
            f.write(f"- `{log}`\n")
        if not logs:
            f.write("- **No logs collected**\n")

        f.write("""
### 3. Memory Dumps
""")
        dumps = collection_results.get('memory', {}).get('dumps_created', [])
        for dump in dumps:
            f.write(f"- `{dump}`\n")
        if not dumps:
            f.write("- **No memory dumps created**\n")

        f.write("""
### 4. Network Capture
""")
        capture = collection_results.get('network', {}).get('capture_file')
        if capture:
            f.write(f"- `{capture}`\n")
            f.write(f"- Duration: {collection_results['network'].get('duration_seconds', 0)}s\n")
        else:
            f.write("- **No capture collected**\n")

        f.write("""
### 5. System Configurations
""")
        configs = collection_results.get('configs', {}).get('configs_backed_up', [])
        for config in configs:
            f.write(f"- `{config}`\n")
        if not configs:
            f.write("- **No configs backed up**\n")

        f.write("""
### 6. Cloudflare Logs
""")
        if collection_results.get('cloudflare', {}).get('success'):
            for log in collection_results['cloudflare'].get('logs_fetched', []):
                f.write(f"- `{log}`\n")
        else:
            f.write("- **Not available** (no API token or error)\n")

        f.write("""

## Chain of Custody

All evidence files must have SHA256 checksums recorded:

```bash
# Generate checksums
find . -type f -exec sha256sum {} \\> checksums.sha256
```

## Access Control

Evidence directory should be:
- Read-only for investigators
- Not modified after collection
- Backed up to secure storage
- Access logged (who accessed, when)

""")

    print(f"[+] Evidence index generated: {index_file}")
    return str(index_file)


def main():
    parser = argparse.ArgumentParser(
        description='Collect forensic evidence for security incident investigation'
    )
    parser.add_argument('--incident-id', required=True, help='Incident identifier (e.g., INC-2026-XXXXX)')
    parser.add_argument('--output', default='/incidents/{incident_id}/forensics',
                       help='Output directory (use {incident_id} placeholder)')
    parser.add_argument('--systems', help='Comma-separated list of affected systems')
    parser.add_argument('--skip-network', action='store_true', help='Skip network capture')
    parser.add_argument('--skip-memory', action='store_true', help='Skip memory dumps')

    args = parser.parse_args()

    # Resolve output path
    output_path = args.output.format(incident_id=args.incident_id)
    output_dir = ensure_directory(output_path)

    print(f"\n[*] Forensic Collection for Incident: {args.incident_id}")
    print(f"[*] Output directory: {output_dir}")
    print(f"[*] Collection started: {datetime.utcnow().isoformat()}Z\n")

    collection_results = {}

    # 1. Database snapshot
    print("\n[1/6] Database Snapshot")
    collection_results['database'] = backup_database(args.incident_id, output_dir)

    # 2. Application logs
    print("\n[2/6] Application Logs")
    collection_results['logs'] = collect_application_logs(args.incident_id, output_dir)

    # 3. Memory dumps
    if not args.skip_memory:
        print("\n[3/6] Memory Dumps")
        collection_results['memory'] = collect_memory_dumps(args.incident_id, output_dir)
    else:
        collection_results['memory'] = {'success': False, 'dumps_created': []}
        print("[3/6] Memory dumps skipped")

    # 4. Network capture
    if not args.skip_network:
        print("\n[4/6] Network Capture (5 minutes)")
        collection_results['network'] = capture_network_traffic(args.incident_id, output_dir, duration=300)
    else:
        collection_results['network'] = {'success': False}
        print("[4/6] Network capture skipped")

    # 5. System configs
    print("\n[5/6] System Configurations")
    collection_results['configs'] = backup_system_configs(args.incident_id, output_dir)

    # 6. Cloudflare logs
    print("\n[6/6] Cloudflare Logs")
    collection_results['cloudflare'] = collect_cloudflare_logs(args.incident_id, output_dir)

    # Generate evidence index
    print("\n[*] Generating evidence index...")
    generate_evidence_index(args.incident_id, output_dir, collection_results)

    # Summary
    print("\n" + "="*60)
    print("FORENSIC COLLECTION COMPLETE")
    print("="*60)
    print(f"\nEvidence stored at: {output_dir}")
    print("\nNext steps:")
    print("1. Verify checksums of all collected files")
    print("2. Secure the evidence (read-only, access control)")
    print("3. Begin forensic analysis")
    print("4. Document chain of custody")

    success_count = sum(1 for r in [
        collection_results.get('database', {}).get('success', False),
        collection_results.get('logs', {}).get('success', False),
        collection_results.get('memory', {}).get('success', False),
        collection_results.get('network', {}).get('success', False),
        collection_results.get('configs', {}).get('success', False)
    ] if r)

    print(f"\nSuccessful collections: {success_count}/5")
    print("="*60)

    return 0 if success_count >= 3 else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
GDPR Incident Initial Triage Script

Performs initial assessment of a security alert to determine:
- If PII is potentially involved
- Preliminary severity estimate
- Immediate containment actions
- IRT escalation requirements
"""

import argparse
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    from src.core.telemetry_consent import get_consent_records_by_user
    from src.config import get_settings
except ImportError:
    # Mock for standalone execution
    def get_consent_records_by_user(*args):
        return []
    def get_settings():
        return None


def assess_pii_involvement(alert_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Determine if PII is potentially involved based on alert data.
    Returns: (has_pii, pii_types)
    """
    pii_types = []
    has_pii = False

    # Check affected systems
    systems = alert_data.get('systems', [])
    for system in systems:
        if 'database' in system.lower() and 'user' in system.lower():
            has_pii = True
            pii_types.append('user database records')

        if 'log' in system.lower():
            has_pii = True
            pii_types.append('log data (may contain PII)')

    # Check alert type
    alert_type = alert_data.get('type', '').lower()
    if 'sql' in alert_type or 'injection' in alert_type:
        has_pii = True
        pii_types.append('potential database exfiltration')

    if 'exfiltration' in alert_type or 'data_leak' in alert_type:
        has_pii = True
        pii_types.append('data exfiltration')

    if 'authentication' in alert_type:
        has_pii = True
        pii_types.append('authentication data')

    return has_pii, list(set(pii_types))


def estimate_record_count(alert_data: Dict[str, Any]) -> int:
    """Estimate approximate number of records affected."""
    # Default estimate based on severity indicators
    severity = alert_data.get('severity', '').lower()

    if 'critical' in severity or 'high' in severity:
        return 10000  # Default high estimate
    elif 'medium' in severity:
        return 1000
    elif 'low' in severity:
        return 50

    return 100  # Conservative default


def determine_containment_actions(alert_data: Dict[str, Any], systems: List[str]) -> List[str]:
    """Recommend immediate containment actions."""
    actions = []

    for system in systems:
        if 'api' in system.lower() or 'gateway' in system.lower():
            actions.append('Rate limit affected API endpoints')
            actions.append('Enable WAF rule to block attack pattern')

        if 'database' in system.lower() or 'postgres' in system.lower():
            actions.append('Enable read-only mode for affected tables')
            actions.append('Review database audit logs')

        if 'plugin' in system.lower():
            actions.append('Disable affected plugin via plugin manager')
            actions.append('Isolate plugin in sandbox')

    if 'credentials' in alert_data.get('type', '').lower():
        actions.append('Force password reset for affected users')
        actions.append('Revoke all active sessions')

    actions.append('Preserve logs (last 48 hours)')
    actions.append('Create forensic snapshot')

    return list(set(actions))


def generate_triage_report(alert_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive triage report."""
    has_pii, pii_types = assess_pii_involvement(alert_data)
    systems = alert_data.get('systems', ['unknown'])
    record_count = estimate_record_count(alert_data)
    containment_actions = determine_containment_actions(alert_data, systems)

    # Determine escalation required
    escalate = has_pii or alert_data.get('severity', '').lower() in ['critical', 'high']

    report = {
        'alert_id': alert_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'assessment': {
            'has_pii_potential': has_pii,
            'pii_types_identified': pii_types,
            'estimated_records_affected': record_count,
            'severity_estimate': alert_data.get('severity', 'unknown'),
            'affected_systems': systems,
            'is_ongoing': alert_data.get('ongoing', True)
        },
        'recommended_actions': {
            'containment': containment_actions,
            'escalate_to_irt': escalate,
            'notify_dpo': escalate and has_pii
        },
        'next_steps': [
            'Preserve all logs (do not clear/rotate)',
            'Isolate affected systems if breach confirmed',
            'Notify DPO within 1 hour if PII confirmed',
            'Begin evidence collection'
        ]
    }

    return report


def print_summary(report: Dict[str, Any]):
    """Print human-readable summary."""
    print('\n' + '='*60)
    print('INCIDENT TRIAGE REPORT')
    print('='*60)
    print(f"\nAlert ID: {report['alert_id']}")
    print(f"Timestamp: {report['timestamp']}")
    print("\n--- Assessment ---")
    print(f"PII Involvement: {'YES' if report['assessment']['has_pii_potential'] else 'NO'}")
    if report['assessment']['pii_types_identified']:
        print(f"PII Types: {', '.join(report['assessment']['pii_types_identified'])}")
    print(f"Estimated Records: {report['assessment']['estimated_records_affected']:,}")
    print(f"Severity: {report['assessment']['severity_estimate']}")
    print(f"Affected Systems: {', '.join(report['assessment']['affected_systems'])}")

    print("\n--- Escalation ---")
    print(f"IRT Escalation Required: {'YES' if report['recommended_actions']['escalate_to_irt'] else 'No'}")
    print(f"DPO Notification Required: {'YES' if report['recommended_actions']['notify_dpo'] else 'No'}")

    print("\n--- Containment Actions ---")
    for action in report['recommended_actions']['containment']:
        print(f"  - {action}")

    print("\n--- Next Steps ---")
    for step in report['next_steps']:
        print(f"  - {step}")

    print('\n' + '='*60)

    if report['recommended_actions']['notify_dpo']:
        print('\n*** DPO MUST BE NOTIFIED WITHIN 1 HOUR ***')
        print('Contact: [DPO_EMAIL] | Phone: [DPO_PHONE]')
    print()


def main():
    parser = argparse.ArgumentParser(
        description='GDPR Incident Initial Triage - Assess security alerts for PII involvement'
    )
    parser.add_argument('--alert-id', required=True, help='Unique alert identifier')
    parser.add_argument('--alert-json', help='JSON file with alert data (optional)')
    parser.add_argument('--output', help='Output file for full JSON report (optional)')

    args = parser.parse_args()

    # Build alert data from args or stdin
    if args.alert_json:
        with open(args.alert_json) as f:
            alert_data = json.load(f)
    else:
        # Read from stdin if no file provided
        try:
            alert_data = json.load(sys.stdin)
        except json.JSONDecodeError:
            # Build from command-line provided fields
            alert_data = {
                'type': os.environ.get('ALERT_TYPE', 'unknown'),
                'severity': os.environ.get('ALERT_SEVERITY', 'medium'),
                'systems': os.environ.get('ALERT_SYSTEMS', '').split(','),
                'ongoing': os.environ.get('ALERT_ONGOING', 'true').lower() == 'true'
            }

    # Ensure required fields
    alert_data.setdefault('severity', 'medium')
    alert_data.setdefault('systems', [])
    alert_data.setdefault('ongoing', True)

    # Generate triage report
    report = generate_triage_report(args.alert_id, alert_data)

    # Print summary to stdout
    print_summary(report)

    # Write full JSON report if output specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report written to: {args.output}")

    # Exit with appropriate code for automation
    if report['recommended_actions']['notify_dpo']:
        sys.exit(2)  # PII confirmed, DPO notification required
    elif report['recommended_actions']['escalate_to_irt']:
        sys.exit(1)  # Escalate to IRT
    else:
        sys.exit(0)  # No PII, no escalation needed


if __name__ == '__main__':
    main()

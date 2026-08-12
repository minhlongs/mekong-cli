#!/usr/bin/env python3
"""
Precise license gate audit: check which API route files actually
use the license_gate middleware vs just happen to mention it.
"""
from pathlib import Path

ROOT = Path('/Users/macbook/mekong-cli')
API_DIR = ROOT / 'src/api'
CORE_DIR = ROOT / 'src/core'

# Sensitive route files to check (both src/api/ and src/core/ variants)
SENSITIVE_FILES = [
    # src/api/ routes
    'src/api/billing_routes.py',
    'src/api/org_routes.py',
    'src/api/constitutional_middleware.py',
    'src/api/coupon_router.py',
    'src/api/gateway_models.py',
    'src/api/graph_router.py',
    'src/api/metrics_routes.py',
    'src/api/openclaw_daemon_service.py',
    'src/api/quota_status_endpoints.py',
    'src/api/raas_router.py',
    'src/api/tier_config_routes.py',
    'src/api/vn_payments_routes.py',
    'src/api/vn_pilot_routes.py',
    'src/api/vn_pricing_routes.py',
    # src/core/ routes
    'src/core/gateway/gateway_mission_routes.py',
    'src/core/gateway/gateway_webhook_mcu_routes.py',
    'src/core/gateway/gateway_main.py',
    'src/core/gateway/metrics_routes.py',
    'src/middleware/license_gate.py',
    'src/middleware/license_server.py',
    'src/services/raas_billing_service.py',
    'src/services/raas_billing_middleware.py',
    'src/services/raas_auth_middleware.py',
    'src/commands/vn_pilot_billing.py',
    'src/commands/vn_pilot_auth.py',
]

print("=" * 70)
print("PRECISE LICENSE GATE AUDIT")
print("=" * 70)

results = {"protected": [], "custom_auth": [], "no_gate": [], "not_found": []}

for rel_path in SENSITIVE_FILES:
    fpath = ROOT / rel_path
    if not fpath.exists():
        results["not_found"].append(rel_path)
        continue

    src = fpath.read_text()

    # ACTUAL usage: the function is called, not just imported
    actual_usage = any(p in src for p in [
        'Depends(license_gate)',
        'Depends(LicenseGate)',
        'license_gate(',
        'app.add_middleware(LicenseGate',
        'app.add_middleware(license_gate',
    ])

    # Also referenced (imported but maybe not yet wired)
    imported = 'license_gate' in src or 'LicenseGate' in src

    # Has its own auth mechanism
    has_custom_auth = any(p in src for p in [
        'Bearer', 'JWT', 'jwt.decode', 'authorization',
        'get_current_user', 'auth_header'
    ])

    # Has router definition (exposes endpoints)
    has_router = 'APIRouter' in src or 'FastAPI(' in src

    if actual_usage:
        status = "PROTECTED"
        results["protected"].append(rel_path)
    elif has_custom_auth:
        status = "CUSTOM_AUTH"
        results["custom_auth"].append(rel_path)
    elif imported:
        status = "IMPORTED_NOT_WIRED"
        results["no_gate"].append(rel_path)
    else:
        status = "NO_GATE"
        results["no_gate"].append(rel_path)

    exposure = "ROUTER" if has_router else "INTERNAL"
    print(f"  [{status:18s}] {exposure:8s} {rel_path}")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  ✅  Protected (license_gate wired):        {len(results['protected'])}")
print(f"  ⚠️  Custom auth (verify equivalence):       {len(results['custom_auth'])}")
print(f"  ❌  No protection detected:                {len(results['no_gate'])}")
print(f"  ➖  Not found:                             {len(results['not_found'])}")

if results["no_gate"]:
    print()
    print("FILES NEEDING ATTENTION:")
    for f in results["no_gate"]:
        print(f"  - {f}")

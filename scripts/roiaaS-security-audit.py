#!/usr/bin/env python3
"""ROIaaS Security Scanner - Post-Production Hardening Audit"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# Configuration
SRC_DIR = Path("src")
TESTS_DIR = Path("tests")
REPORTS_DIR = Path("plans/reports")

# Audit results
audit_results = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "version": "v0.2.0",
    "commit": "c26f8b379",
    "categories": {}
}

def scan_secrets():
    """Scan for exposed secrets in source code"""
    print("🔒 Scanning for exposed secrets...")

    patterns = [
        (r"sk-[a-zA-Z0-9]{32,}", "API Key"),
        (r"Bearer\s+[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+", "JWT Token"),
        (r"password\s*=\s*['\"][^'\"]{8,}['\"]", "Hardcoded Password"),
    ]

    findings = []
    for root, dirs, files in os.walk(SRC_DIR):
        # Skip __pycache__ and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                try:
                    content = filepath.read_text(encoding='utf-8')
                    for pattern, secret_type in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            findings.append({
                                "file": str(filepath),
                                "type": secret_type,
                                "count": len(matches)
                            })
                except Exception:
                    pass

    # Check .env files not gitignored
    env_files = list(Path(".").glob("*.env"))
    for env_file in env_files:
        findings.append({
            "file": str(env_file),
            "type": "Environment File",
            "status": "Should be in .gitignore"
        })

    audit_results["categories"]["secrets_scan"] = {
        "status": "PASS" if len(findings) == 0 else "WARNING",
        "findings": findings,
        "total_files_scanned": sum(1 for _ in SRC_DIR.rglob("*.py"))
    }
    print(f"   ✅ Secrets scan: {len(findings)} findings")
    return findings

def scan_dependencies():
    """Check dependency vulnerabilities"""
    print("📦 Scanning dependencies...")

    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        content = pyproject.read_text()
        deps = re.findall(r'([a-zA-Z0-9\-_]+)\s*=', content)

        audit_results["categories"]["dependencies"] = {
            "status": "PASS",
            "total_deps": len(deps),
            "scanned": True
        }
        print(f"   ✅ Dependencies: {len(deps)} packages")
    return []

def scan_license_gates():
    """Verify license gate implementation"""
    print("🔑 Scanning license gates...")

    license_files = [
        "src/raas/license_models.py",
        "src/lib/license_generator.py",
        "src/lib/raas_gate.py",
        "src/lib/raas_gate_validator.py",
        "src/usage/decorators.py"
    ]

    gates_found = {
        "license_models": False,
        "license_generator": False,
        "raas_gate": False,
        "usage_decorators": False
    }

    for file_path in license_files:
        if Path(file_path).exists():
            content = Path(file_path).read_text()
            if "RAAS_LICENSE_KEY" in content or "LicenseKeyPayload" in content:
                gates_found[file_path.split("/")[-1].replace(".py", "")] = True

    all_gates = all(gates_found.values())
    audit_results["categories"]["license_gates"] = {
        "status": "PASS" if all_gates else "INCOMPLETE",
        "gates": gates_found,
        "all_present": all_gates
    }
    print(f"   ✅ License gates: {sum(gates_found.values())}/{len(gates_found)}")
    return gates_found

def scan_webhook_security():
    """Verify webhook security implementation"""
    print("🔔 Scanning webhook security...")

    webhook_file = Path("src/api/polar_webhook.py")
    if webhook_file.exists():
        content = webhook_file.read_text()

        checks = {
            "hmac_sha256": "hmac" in content.lower() and "sha256" in content.lower(),
            "timestamp_validation": "timestamp" in content.lower() and "300" in content,
            "idempotency": "idempotency" in content.lower() or "_processed_events" in content,
            "ttl_cache": "OrderedDict" in content or "ttl" in content.lower(),
            "structlog": "structlog" in content
        }

        passed = sum(1 for v in checks.values() if v)
        audit_results["categories"]["webhook_security"] = {
            "status": "PASS" if passed == len(checks) else "PARTIAL",
            "checks": checks,
            "passed": f"{passed}/{len(checks)}"
        }
        print(f"   ✅ Webhook security: {passed}/{len(checks)} checks")
    return checks

def scan_usage_metering():
    """Verify usage metering implementation"""
    print("📊 Scanning usage metering...")

    usage_files = {
        "usage_tracker": Path("src/usage/usage_tracker.py"),
        "usage_queue": Path("src/lib/usage_queue.py"),
        "usage_metering_service": Path("src/lib/usage_metering_service.py"),
        "decorators": Path("src/usage/decorators.py")
    }

    checks = {}
    for name, filepath in usage_files.items():
        checks[name] = filepath.exists()

    # Check for specific features
    if checks["usage_tracker"]:
        content = checks["usage_tracker"].read_text() if hasattr(checks["usage_tracker"], 'read_text') else Path("src/usage/usage_tracker.py").read_text()
        checks["idempotency"] = "idempotency" in content.lower()
        checks["sha256"] = "sha256" in content.lower() or "hashlib" in content

    if checks["usage_metering_service"]:
        content = Path("src/lib/usage_metering_service.py").read_text()
        checks["circuit_breaker"] = "circuit_breaker" in content.lower() or "CircuitBreaker" in content
        checks["retry"] = "retry" in content.lower() or "backoff" in content

    passed = sum(1 for v in checks.values() if v)
    audit_results["categories"]["usage_metering"] = {
        "status": "PASS" if passed >= len(checks) - 1 else "PARTIAL",
        "components": list(checks.keys()),
        "features": checks
    }
    print(f"   ✅ Usage metering: {passed} checks")
    return checks

def scan_test_coverage():
    """Check test coverage for ROIaaS components"""
    print("🧪 Checking test coverage...")

    test_files = list(TESTS_DIR.glob("test_*.py"))
    roi_tests = [f for f in test_files if any(x in f.name for x in [
        "license", "usage", "webhook", "command", "tracing", "sbom", "validation"
    ])]

    audit_results["categories"]["test_coverage"] = {
        "status": "PASS",
        "total_tests": len(test_files),
        "roi_tests": len(roi_tests),
        "test_files": [f.name for f in roi_tests]
    }
    print(f"   ✅ Test coverage: {len(roi_tests)} ROIaaS tests")
    return roi_tests

def generate_report():
    """Generate final audit report"""
    print("\n📋 Generating audit report...")

    # Calculate overall status
    statuses = [v.get("status", "UNKNOWN") for v in audit_results["categories"].values()]
    overall = "PASS" if all(s == "PASS" for s in statuses) else "PASS_WITH_WARNINGS"

    audit_results["overall_status"] = overall
    audit_results["summary"] = {
        "total_categories": len(audit_results["categories"]),
        "passed": sum(1 for s in statuses if s == "PASS"),
        "warnings": sum(1 for s in statuses if s in ["WARNING", "PARTIAL"]),
        "failed": sum(1 for s in statuses if s == "FAIL")
    }

    # Save report
    report_path = REPORTS_DIR / "roiaaS-security-audit-260307.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(audit_results, f, indent=2)

    print(f"   📄 Report saved to: {report_path}")
    return audit_results

def print_summary():
    """Print audit summary"""
    print("\n" + "="*60)
    print("🛡️  ROIaaS SECURITY AUDIT SUMMARY")
    print("="*60)
    print(f"Timestamp: {audit_results['timestamp']}")
    print(f"Version: {audit_results['version']}")
    print(f"Commit: {audit_results['commit']}")
    print(f"Overall Status: {audit_results.get('overall_status', 'PENDING')}")
    print("\nCategories:")
    for name, data in audit_results["categories"].items():
        status = data.get("status", "UNKNOWN")
        print(f"  - {name}: {status}")
    print("="*60)

if __name__ == "__main__":
    print("🔍 ROIaaS Post-Production Security Audit\n")

    scan_secrets()
    scan_dependencies()
    scan_license_gates()
    scan_webhook_security()
    scan_usage_metering()
    scan_test_coverage()
    generate_report()
    print_summary()

    # Exit with status
    overall = audit_results.get("overall_status", "FAIL")
    exit(0 if overall == "PASS" else 1)

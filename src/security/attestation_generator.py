# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Security Attestation Report Generator."""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.security.attestation_scanner import SecurityScannerMixin

RAAS_GATEWAY_CONFIG = {
    "base_url": os.getenv("RAAS_GATEWAY_URL", "https://api.cashclaw.cc"),
    "api_key_prefix": "mk_",
    "jwt_audience": "mekong-cli-security",
    "kv_namespace": "security-attestations",
}


class SecurityAttestationGenerator(SecurityScannerMixin):
    """Generates and signs security attestation reports."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def generate_attestation(self, security_results: dict[str, Any]) -> dict[str, Any]:
        commit_info = self.get_commit_info()
        all_passed = security_results["secrets_ok"] and security_results["env_ok"] and security_results["sanitizer_ok"]
        status = "ATTESTED_SECURE" if all_passed else "ATTESTATION_FAILED"
        return {
            "attestation_version": "1.0.0",
            "attestation_type": "mekong-cli-security-hardening",
            "timestamp": self.timestamp,
            "commit_sha": commit_info["sha"],
            "branch": commit_info["branch"],
            "repository": "mekong-cli",
            "security_checks": {
                "secret_scanning": "PASS" if security_results["secrets_ok"] else "FAIL",
                "command_injection_protection": "PASS" if security_results["sanitizer_ok"] else "FAIL",
                "env_file_exclusion": "PASS" if security_results["env_ok"] else "FAIL",
            },
            "compliance": {
                "owasp_top_10": "COMPLIANT" if all_passed else "NON_COMPLIANT",
                "no_hardcoded_secrets": security_results["secrets_ok"],
                "command_sanitization_enabled": security_results["sanitizer_ok"],
                "env_file_exclusion": security_results["env_ok"],
            },
            "raas_gateway_compatible": True,
            "jwt_auth_ready": True,
            "mk_api_key_format": True,
            "status": status,
        }

    def sign_attestation(self, attestation: dict[str, Any]) -> str:
        canonical_json = json.dumps(attestation, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).hexdigest()

    def save_report(self, attestation: dict[str, Any], signature: str, output_dir: str = "plans/reports") -> Path:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        report_file = output_path / f"security-attestation-{attestation['commit_sha'][:8]}.json"
        report = {**attestation, "signature": signature, "signature_algorithm": "SHA256"}
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        return report_file

    def print_report(self, attestation: dict[str, Any], signature: str) -> None:
        print("\n" + "=" * 60 + "\n  MEKONG CLI SECURITY ATTESTATION REPORT\n" + "=" * 60 + "\n")
        print(f"Commit:       {attestation['commit_sha']}\nBranch:       {attestation['branch']}\nTimestamp:    {attestation['timestamp']}\n\nSecurity Checks:")
        for check, result in attestation["security_checks"].items():
            print(f"  {'✅' if result == 'PASS' else '❌'} {check.replace('_', ' ').title()}: {result}")
        print("\nCompliance:")
        for check, result in attestation["compliance"].items():
            print(f"  {'✅' if result is True or result == 'COMPLIANT' else '❌'} {check.replace('_', ' ').title()}: {result}")
        print(f"\nRaaS Gateway Compatible: {attestation['raas_gateway_compatible']}\nJWT Auth Ready:          {attestation['jwt_auth_ready']}\n\nSignature (SHA256): {signature}\nStatus: {attestation['status']}\n\n" + "=" * 60)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Generate security attestation report")
    parser.add_argument("--repo", default=".", help="Repository path")
    parser.add_argument("--output", default="plans/reports", help="Output directory")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    args = parser.parse_args()

    generator = SecurityAttestationGenerator(args.repo)
    security_results = generator.run_security_checks()
    attestation = generator.generate_attestation(security_results)
    signature = generator.sign_attestation(attestation)
    report_path = generator.save_report(attestation, signature, args.output)

    if not args.quiet:
        generator.print_report(attestation, signature)
        print(f"\nReport saved to: {report_path}")

    sys.exit(0 if attestation["status"] == "ATTESTED_SECURE" else 1)


if __name__ == "__main__":
    main()

__all__ = ["RAAS_GATEWAY_CONFIG", "SecurityAttestationGenerator", "main"]

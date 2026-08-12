#!/usr/bin/env python3
"""
Export OpenAPI specifications from running Mekong services.

This script connects to running services and fetches their OpenAPI schemas,
then writes them to the docs/api/ directory.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Literal

import httpx

# Service configurations
SERVICES = {
    "agent-forest": {
        "url": "http://localhost:8000/openapi.json",
        "output": "docs/api/agent-forest-openapi.json",
    },
    "mekongd": {
        "url": "http://localhost:8001/openapi.json",
        "output": "docs/api/mekongd-openapi.json",
    },
}


def export_service(service: str, timeout: float = 5.0) -> bool:
    """Export OpenAPI spec for a single service."""
    config = SERVICES[service]

    try:
        resp = httpx.get(config["url"], timeout=timeout)
        resp.raise_for_status()
    except httpx.RequestError as exc:
        print(f"ERROR: Could not connect to {service} at {config['url']}: {exc}")
        return False
    except httpx.HTTPStatusError as exc:
        print(f"ERROR: {service} returned {exc.response.status_code}")
        return False

    output_path = Path(config["output"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Pretty-print the JSON
    schema = resp.json()
    output_path.write_text(json.dumps(schema, indent=2))

    print(f"✓ Exported {service} to {output_path}")
    return True


def export_all(timeout: float = 5.0) -> tuple[int, int]:
    """Export all services, return (success_count, failure_count)."""
    successes = 0
    failures = 0

    for service in SERVICES:
        if export_service(service, timeout):
            successes += 1
        else:
            failures += 1

    return successes, failures


def start_service(service: Literal["agent-forest", "mekongd"]) -> None:
    """Start a service in the background."""
    pkg_dir = Path("packages") / service
    if not pkg_dir.exists():
        print(f"ERROR: Package {service} not found at {pkg_dir}")
        sys.exit(1)

    print(f"Starting {service}...")
    cmd = [
        "poetry",
        "run",
        "python",
        "-m",
        f"{service}.cli" if service == "agent-forest" else "mekongd.cli",
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=pkg_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"Started {service} (PID: {proc.pid})")
    print("Wait a moment for the service to be ready...")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export OpenAPI specs from running Mekong services"
    )
    parser.add_argument(
        "--service",
        choices=list(SERVICES) + ["all"],
        default="all",
        help="Service to export (default: all)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start services before exporting",
    )

    args = parser.parse_args()

    if args.start:
        if args.service == "all":
            start_service("agent-forest")
            start_service("mekongd")
        else:
            start_service(args.service)  # type: ignore
        print()
        input("Press Enter when services are ready to export...")

    services = list(SERVICES.keys()) if args.service == "all" else [args.service]
    successes = 0

    for service in services:
        if export_service(service, args.timeout):
            successes += 1

    failures = len(services) - successes

    print(f"\nExport complete: {successes} succeeded, {failures} failed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

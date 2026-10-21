# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Security command - Audit, scan, and secure applications"""

from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, List, Optional, Union

from rich.console import Console
from rich.table import Table
import typer

from src.commands.security_audit_helpers import (
    audit_config,
    generate_report,
    harden,
)
from src.commands.security_scanners import (
    display_scan_results,
    scan_with_bandit,
    scan_with_safety,
    scan_with_semgrep,
)

app = typer.Typer()
console = Console()


@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to scan"),
    tool: str = typer.Option("auto", "--tool", "-t", help="Tool to use: bandit, semgrep, safety, auto"),
    format_output: str = typer.Option("table", "--format", "-f", help="Output format: table, json, sarif"),
    severity: str = typer.Option("all", "--severity", "-s", help="Severity level: low, medium, high, critical, all"),
    exclude: Optional[str] = typer.Option(None, "--exclude", "-e", help="Exclude patterns"),
) -> None:
    """Scan project for security vulnerabilities."""
    console.print(f"[bold]🔍 Scanning {path} for security vulnerabilities...[/bold]")

    scan_results = []

    if tool in ("auto", "bandit"):
        bandit_results = scan_with_bandit(path, severity)
        if bandit_results:
            scan_results.extend(bandit_results)

    if tool in ("auto", "safety"):
        safety_results = scan_with_safety(path)
        if safety_results:
            scan_results.extend(safety_results)

    if tool in ("auto", "semgrep"):
        semgrep_results = scan_with_semgrep(path, severity)
        if semgrep_results:
            scan_results.extend(semgrep_results)

    if format_output == "json":
        output_json = {
            "timestamp": datetime.now().isoformat(),
            "path": path,
            "tool": tool,
            "results": scan_results,
            "summary": {
                "total": len(scan_results),
                "critical": len([r for r in scan_results if r.get("severity") == "CRITICAL"]),
                "high": len([r for r in scan_results if r.get("severity") == "HIGH"]),
                "medium": len([r for r in scan_results if r.get("severity") == "MEDIUM"]),
                "low": len([r for r in scan_results if r.get("severity") == "LOW"]),
            },
        }
        console.print_json(data=output_json)
    else:
        display_scan_results(scan_results)


@app.command()
def scan_secrets(
    path: str = typer.Argument(".", help="Path to scan for secrets"),
    include_filenames: bool = typer.Option(False, "--include-filenames", help="Include filenames in output"),
    entropy_threshold: float = typer.Option(4.5, "--entropy", help="Entropy threshold for detection"),
):
    """Scan for hardcoded secrets and credentials"""
    console.print(f"[bold]🔑 Scanning {path} for hardcoded secrets...[/bold]")

    secrets_found = []
    secret_patterns = [
        r'["\'](?:password|passwd|pwd|secret|token|key|api_key|api-key)["\'][\s:]=[\s\'"]*[^\'"\s]{8,}',
        r'(?:api_key|secret_key|aws_access|aws_secret|client_secret|private_key)[\s:]=[\s\'"]*[^\'"\s]{8,}',
        r'https?://[^\s\'"]*:[^\s\'"@]*@[^\s\'"]*',
        r"BEGIN (?:RSA |EC |DSA |PGP |SSH )?(?:PRIVATE|PUBLIC) KEY",
    ]

    for file_path in Path(path).rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in [".py", ".js", ".ts", ".json", ".yml", ".yaml", ".env", ".txt"]:
            try:
                file_content = file_path.read_text(encoding="utf-8")
                for pattern in secret_patterns:
                    for match in re.finditer(pattern, file_content, re.IGNORECASE):
                        secrets_found.append({
                            "file": str(file_path),
                            "line_num": file_content[: match.start()].count("\n") + 1,
                            "match": match.group()[:50] + "..." if len(match.group()) > 50 else match.group(),
                            "pattern": pattern,
                        })
            except (UnicodeDecodeError, PermissionError):
                continue

    if secrets_found:
        console.print(f"[red]❌ Found {len(secrets_found)} potential secrets![/red]")
        secrets_table = Table(title="Potential Secrets Found")
        secrets_table.add_column("File", style="cyan")
        secrets_table.add_column("Line", style="magenta", justify="right")
        secrets_table.add_column("Match", style="yellow")

        for secret in secrets_found:
            secrets_table.add_row(
                secret["file"] if include_filenames else Path(secret["file"]).name,
                str(secret["line_num"]),
                secret["match"],
            )

        console.print(secrets_table)
        console.print("\n[yellow]⚠️  IMPORTANT: Rotate these credentials and DO NOT commit them to version control![/yellow]")
    else:
        console.print("[green]✅ No obvious secrets found![/green]")


app.command()(audit_config)
app.command()(generate_report)
app.command()(harden)

__all__ = [
    "Dict", "List", "Optional", "Union", "app", "audit_config", "console",
    "display_scan_results", "generate_report", "harden", "json", "scan",
    "scan_secrets", "scan_with_bandit", "scan_with_safety", "scan_with_semgrep",
    "subprocess", "sys",
]

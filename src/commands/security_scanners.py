# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Scanner and display helpers for Security command."""

import json
import sys
from typing import Dict, List, Union

from rich.table import Table


def _facade():
    return sys.modules["src.commands.security"]


def scan_with_bandit(path: str, severity: str) -> List[Dict[str, Union[str, int]]]:
    """Scan with Bandit (Python security scanner)"""
    f = _facade()
    try:
        result = f.subprocess.run(
            [f.sys.executable, "-m", "bandit", "-r", path, "-f", "json"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode in (0, 1):
            data = json.loads(result.stdout)
            bandit_results = []
            sev_map = {"LOW": "LOW", "MEDIUM": "MEDIUM", "HIGH": "HIGH"}
            for issue in data.get("results", []):
                issue_severity = sev_map.get(issue.get("issue_severity", "").upper(), "MEDIUM")
                if severity == "all" or issue_severity.lower() == severity.lower():
                    bandit_results.append({
                        "tool": "Bandit",
                        "file": issue.get("filename", ""),
                        "line": issue.get("line_number", 0),
                        "severity": issue_severity,
                        "code": issue.get("test_id", ""),
                        "message": issue.get("issue_text", ""),
                        "confidence": issue.get("issue_confidence", ""),
                    })
            return bandit_results
        f.console.print(f"[yellow]⚠️  Bandit scan failed: {result.stderr}[/yellow]")
        return []
    except FileNotFoundError:
        f.console.print("[dim]Bandit not found. Install with: pip install bandit[/dim]")
        return []
    except json.JSONDecodeError:
        f.console.print("[yellow]⚠️  Bandit output format not recognized[/yellow]")
        return []


def scan_with_safety(path: str) -> List[Dict[str, Union[str, int]]]:
    """Scan dependencies with Safety (dependency vulnerability scanner)."""
    f = _facade()
    try:
        req_files = (
            list(f.Path(path).glob("**/requirements*.txt"))
            + list(f.Path(path).glob("**/Pipfile"))
            + list(f.Path(path).glob("**/pyproject.toml"))
        )
        if not req_files:
            f.console.print("[yellow]⚠️  No dependency files found, skipping Safety scan[/yellow]")
            return []

        req_file = str(req_files[0])
        result = f.subprocess.run(
            [f.sys.executable, "-m", "safety", "check", "-r", req_file, "--format", "json"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode in (0, 1):
            try:
                issues = json.loads(result.stdout)
                safety_results = []
                for issue in issues:
                    vulns = issue.get("analyzed_version", {}).get("vulnerabilities", [])
                    sev = vulns[0].get("cvssv3", {}).get("base_severity", "HIGH") if vulns else "MEDIUM"
                    msg = issue.get("vulnerabilities", [{}])[0].get("description", "") if issue.get("vulnerabilities") else ""
                    safety_results.append({
                        "tool": "Safety", "file": req_file, "line": 0, "severity": sev,
                        "code": issue.get("name", ""), "message": msg, "confidence": "HIGH",
                    })
                return safety_results
            except json.JSONDecodeError:
                f.console.print("[yellow]⚠️  Safety output format not recognized[/yellow]")
                return []
        f.console.print(f"[yellow]⚠️  Safety scan failed: {result.stderr}[/yellow]")
        return []
    except FileNotFoundError:
        f.console.print("[dim]Safety not found. Install with: pip install safety[/dim]")
        return []


def scan_with_semgrep(path: str, severity: str) -> List[Dict[str, Union[str, int]]]:
    """Scan with Semgrep (static analysis tool)."""
    f = _facade()
    try:
        result = f.subprocess.run(
            ["semgrep", "--config=auto", "--json", path],
            capture_output=True, text=True, check=False,
        )
        if result.returncode in (0, 1):
            data = json.loads(result.stdout)
            semgrep_results = []
            for issue in data.get("results", []):
                sev = issue.get("extra", {}).get("severity", "MEDIUM").upper()
                if severity == "all" or sev.lower() == severity.lower():
                    semgrep_results.append({
                        "tool": "Semgrep",
                        "file": issue.get("path", ""),
                        "line": issue.get("start", {}).get("line", 0),
                        "severity": sev,
                        "code": issue.get("check_id", ""),
                        "message": issue.get("extra", {}).get("message", ""),
                        "confidence": issue.get("extra", {}).get("confidence", "MEDIUM"),
                    })
            return semgrep_results
        f.console.print(f"[yellow]⚠️  Semgrep scan failed: {result.stderr}[/yellow]")
        return []
    except FileNotFoundError:
        f.console.print("[dim]Semgrep not found. Install with: pip install semgrep[/dim]")
        return []
    except json.JSONDecodeError:
        f.console.print("[yellow]⚠️  Semgrep output format not recognized[/yellow]")
        return []


def display_scan_results(results: List[Dict[str, Union[str, int]]]) -> None:  # type: ignore[misc]
    """Display scan results in a table."""
    f = _facade()
    if not results:
        f.console.print("[green]✅ No security issues found![/green]")
        return

    f.console.print(f"[bold]📊 Found {len(results)} security issues:[/bold]")
    summary_table = Table(title="Security Issues Summary")
    summary_table.add_column("Severity", style="cyan")
    summary_table.add_column("Count", style="magenta", justify="right")

    for sev, label in [("CRITICAL", "🔴 CRITICAL"), ("HIGH", "🟠 HIGH"), ("MEDIUM", "🟡 MEDIUM"), ("LOW", "🔵 LOW")]:
        items = [r for r in results if r["severity"] == sev]
        if items:
            summary_table.add_row(label, str(len(items)))
    f.console.print(summary_table)

    results_table = Table(title="Security Issues Detail")
    for col, st in [("Tool", "cyan"), ("Severity", "magenta"), ("File:Line", "yellow"), ("Issue", "dim")]:
        results_table.add_column(col, style=st)

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    for res in sorted(results, key=lambda x: severity_order.get(str(x["severity"]), 4)):
        sev_str = str(res["severity"])
        severity_style = {"CRITICAL": "red bold", "HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}.get(sev_str, "white")
        msg = str(res["message"])
        results_table.add_row(
            str(res["tool"]),
            f"[{severity_style}]{sev_str}[/{severity_style}]",
            f"{res['file']}:{res['line']}",
            msg[:60] + "..." if len(msg) > 60 else msg,
        )
    f.console.print(results_table)

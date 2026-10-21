# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Audit, report, and hardening helpers for Security command."""

from datetime import datetime
import json
import sys

from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.security"]


def audit_config() -> None:
    """Audit configuration files for security issues."""
    f = _facade()
    f.console.print("[bold]🛡️  Auditing configuration files for security issues...[/bold]")

    findings = []
    config_files = (
        list(f.Path(".").glob("**/{settings,config,configuration}.py"))
        + list(f.Path(".").glob("**/config.json"))
        + list(f.Path(".").glob("**/appsettings.json"))
        + list(f.Path(".").glob("**/application.properties"))
        + list(f.Path(".").glob("**/.env*"))
        + list(f.Path(".").glob("**/docker-compose*.yml"))
        + list(f.Path(".").glob("**/docker-compose*.yaml"))
    )

    for config_file in config_files:
        content = config_file.read_text()

        if config_file.suffix == ".py" and "DEBUG = True" in content:
            findings.append({
                "file": str(config_file),
                "issue": "DEBUG mode enabled in production",
                "severity": "HIGH",
                "recommendation": "Set DEBUG = False for production",
            })

        if "SECRET_KEY =" in content and ("changeme" in content or "your-secret-key" in content or "dev-key" in content):
            findings.append({
                "file": str(config_file),
                "issue": "Weak or default SECRET_KEY detected",
                "severity": "HIGH",
                "recommendation": "Use a strong, randomly generated secret key",
            })

        if "docker-compose" in config_file.name and ("password:" in content or "secret:" in content) and "${" not in content:
            findings.append({
                "file": str(config_file),
                "issue": "Credentials exposed in Docker Compose file",
                "severity": "HIGH",
                "recommendation": "Use environment variables or Docker secrets",
            })

    if findings:
        f.console.print(f"[red]❌ Found {len(findings)} security misconfigurations![/red]")

        config_table = Table(title="Configuration Issues")
        for col, st in [("File", "cyan"), ("Severity", "magenta"), ("Issue", "yellow"), ("Recommendation", "dim")]:
            config_table.add_column(col, style=st)

        severity_colors = {"LOW": "blue", "MEDIUM": "yellow", "HIGH": "red", "CRITICAL": "red bold"}

        for finding in findings:
            severity_color = severity_colors.get(finding["severity"], "white")
            config_table.add_row(
                f.Path(finding["file"]).name,
                f"[{severity_color}]{finding['severity']}[/{severity_color}]",
                finding["issue"],
                finding["recommendation"],
            )

        f.console.print(config_table)
    else:
        f.console.print("[green]✅ No configuration security issues found![/green]")


def generate_report(output_file: str = typer.Option("security-report.json", "--output", "-o", help="Output file for report")):
    """Generate comprehensive security report"""
    f = _facade()
    f.console.print(f"[bold]📜 Generating security report: {output_file}...[/bold]")

    report_data = {
        "generated_at": datetime.now().isoformat(),
        "project_root": str(f.Path(".").absolute()),
        "report_type": "Security Assessment",
        "sections": {},
    }

    try:
        result = f.subprocess.run([f.sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
        report_data["sections"]["dependencies"] = result.stdout.split("\n")
    except Exception:
        report_data["sections"]["dependencies"] = ["Could not retrieve dependency list"]

    perms_info = []
    for file_path in f.Path(".").glob("**/*.py"):
        if file_path.is_file():
            stat = file_path.stat()
            perms_info.append({
                "file": str(file_path),
                "size": stat.st_size,
                "permissions": oct(stat.st_mode)[-3:],
            })

    report_data["sections"]["file_permissions"] = perms_info[:20]

    if f.Path(".git").exists():
        try:
            result = f.subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, check=True)
            report_data["sections"]["git_remotes"] = result.stdout
        except Exception:
            report_data["sections"]["git_remotes"] = "Could not retrieve git remotes"

    with open(output_file, "w") as fh:
        json.dump(report_data, fh, indent=2)

    f.console.print(f"[green]✅ Security report generated: {output_file}[/green]")


def harden() -> None:
    """Suggest security hardening measures"""
    f = _facade()
    f.console.print("[bold]🔒 Security Hardening Recommendations:[/bold]")

    recommendations = [
        ("Update Dependencies", "Regularly update all dependencies to patch known vulnerabilities", "pip install --upgrade --upgrade-strategy eager"),
        ("Enable Two-Factor Authentication", "Add 2FA to all accounts and services", "Configure with your authentication provider"),
        ("Use Environment Variables", "Store sensitive data in environment variables, not code", "export SECRET_KEY='...'"),
        ("Implement Input Validation", "Validate all user inputs to prevent injection attacks", "Use validation libraries like Joi or express-validator"),
        ("Configure HTTPS", "Enforce HTTPS encryption for all connections", "Set up SSL/TLS certificates"),
        ("Enable Rate Limiting", "Protect against abuse and brute-force attacks", "Implement rate limiting middleware"),
        ("Minimize Attack Surface", "Disable unused services and close unnecessary ports", "Audit running services regularly"),
        ("Secure Session Management", "Implement secure session handling", "Use secure cookies with HttpOnly flag"),
        ("Log Security Events", "Maintain audit trails of security-relevant events", "Set up centralized logging"),
        ("Regular Security Testing", "Perform ongoing security assessments", "Schedule automated scans"),
    ]

    rec_table = Table(title="Hardening Recommendations")
    rec_table.add_column("Area", style="cyan", width=20)
    rec_table.add_column("Recommendation", style="magenta", width=40)
    rec_table.add_column("Implementation", style="dim", width=30)

    for area, rec, impl in recommendations:
        rec_table.add_row(area, rec, impl)

    f.console.print(rec_table)
    f.console.print("\n[bold]🔍 Project-Specific Checks:[/bold]")

    checks = []
    if f.Path("requirements.txt").exists():
        checks.append(("✅", "Dependencies tracked in requirements.txt"))
    else:
        checks.append(("❌", "Create requirements.txt with: pip freeze > requirements.txt"))

    if f.Path(".gitignore").exists():
        gitignore_content = f.Path(".gitignore").read_text()
        if ".env" in gitignore_content or "*.env" in gitignore_content:
            checks.append(("✅", ".env file properly ignored"))
        else:
            checks.append(("⚠️", "Add .env to .gitignore to prevent credential leaks"))

    if f.Path("requirements.txt").exists():
        req_content = f.Path("requirements.txt").read_text().lower()
        if "django" in req_content and "django-cors-headers" not in req_content:
            checks.append(("⚠️", "Consider adding django-cors-headers for CORS security"))

    check_table = Table()
    check_table.add_column("Status", style="cyan")
    check_table.add_column("Issue", style="magenta")
    for st, issue in checks:
        check_table.add_row(st, issue)

    f.console.print(check_table)

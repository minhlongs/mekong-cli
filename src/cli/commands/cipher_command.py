"""
CLI command group for Vietnamese National Cryptography, State Cipher & Civil Cryptography Suite.
Governed by Law on Cryptography 2011 (Law No. 05/2011/QH13) & Decree No. 58/2016/NĐ-CP.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.cipher_engine import (
    VALID_BRANCH_TYPES,
    VALID_EQUIPMENT_TYPES,
    VALID_KEY_STATUS,
    VALID_KEY_TYPES,
    VALID_LICENSE_STATUS,
    VALID_LICENSE_TYPES,
    VALID_PRODUCT_CATEGORIES,
    VALID_SECURITY_LEVELS,
    VALID_SEVERITY_LEVELS,
    VALID_SYSTEM_STATUS,
    VALID_TAMPER_LEVELS,
    CipherEngine,
)

app = typer.Typer(
    name="cipher",
    help="Vietnamese National Cryptography, State Cipher & Civil Cryptography Suite (Luật Cơ yếu 2011 & Nghị định 58/2016/NĐ-CP).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def cipher_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of State Cipher Networks, Key Lifecycles, Civil Crypto Licenses, and Incident Posture.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = CipherEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    inc_color = "green" if telemetry["unresolved_incidents"] == 0 else "red"

    overview_text = (
        f"[bold cyan]Active Operational State Cipher Systems (Hệ thống mật mã chuyên dùng đang hoạt động):[/bold cyan] {telemetry['active_operational_systems']} networks\n"
        f"[bold cyan]Active Valid Cryptographic Keys (Khóa mật mã chuyên dùng hợp lệ):[/bold cyan] {telemetry['active_valid_keys']} keys\n"
        f"[bold cyan]Certified Cryptographic Hardware / HSM (Trang thiết bị mật mã đã kiểm định đạt chuẩn):[/bold cyan] {telemetry['certified_equipment_count']} appliances\n"
        f"[bold cyan]Active Civil Cryptography Licenses (Giấy phép kinh doanh mật mã dân sự có hiệu lực):[/bold cyan] {telemetry['active_civil_licenses']} enterprises\n"
        f"[bold cyan]Cryptographic Incidents / Tamper Alerts (Sự cố an toàn mật mã / cảnh báo xâm phạm):[/bold cyan] {telemetry['total_cryptographic_incidents']} cases ([{inc_color}]{telemetry['unresolved_incidents']} unresolved[/{inc_color}])"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]BAN CƠ YẾU CHÍNH PHỦ — TRUNG TÂM GIÁM SÁT MẬT MÃ QUỐC GIA (LUẬT CƠ YẾU 2011)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    systems_by_branch = telemetry.get("systems_by_branch", {})
    if systems_by_branch:
        branch_table = Table(title="Phân bổ Hệ thống Mật mã theo Tổ chức Lực lượng Cơ yếu", box=box.SIMPLE_HEAVY)
        branch_table.add_column("Cipher Branch (Hệ thống Cơ yếu)", style="cyan")
        branch_table.add_column("Active Networks", justify="right", style="green")
        for branch, cnt in systems_by_branch.items():
            branch_table.add_row(branch, str(cnt))
        console.print(branch_table)


@app.command("system")
def register_system_cmd(
    id_: str = typer.Option(..., "--id", help="System unique ID (e.g. SYS-GOV-01)."),
    name: str = typer.Option(..., "--name", "-n", help="Cipher system network name."),
    branch: str = typer.Option("PARTY_GOVERNMENT", "--branch", "-b", help="PARTY_GOVERNMENT, MILITARY_DEFENSE, PUBLIC_SECURITY, DIPLOMATIC_FOREIGN."),
    level: str = typer.Option("TUYET_MAT_TOP_SECRET", "--level", "-l", help="TUYET_MAT_TOP_SECRET, TOI_MAT_SECRET, MAT_CONFIDENTIAL."),
    location: str = typer.Option(..., "--location", help="Deployment location / data center."),
    algo: str = typer.Option("TCVN-7142-GOV", "--algo", help="Cryptographic standard or algorithm."),
    date: Optional[str] = typer.Option(None, "--date", help="Commissioning date (YYYY-MM-DD)."),
    status: str = typer.Option("ACTIVE_OPERATIONAL", "--status", help="ACTIVE_OPERATIONAL, STANDBY_BACKUP, MAINTENANCE_KEY_ROTATION, DECOMMISSIONED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a state cryptographic system protecting state secrets (Article 11 Law 05/2011/QH13).
    """
    engine = CipherEngine()
    try:
        res = engine.register_system(
            system_id=id_,
            system_name=name,
            branch_type=branch,
            security_level=level,
            deployment_location=location,
            algorithm_standard=algo,
            commission_date=date,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering cipher system:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký Hệ thống Mật mã Chuyên dùng thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("key")
def issue_key_cmd(
    id_: str = typer.Option(..., "--id", help="Cryptographic key ID (e.g. KEY-2026-A1)."),
    system: str = typer.Option(..., "--system", "-s", help="Target cipher system ID."),
    type_: str = typer.Option("MASTER_ROOT_KEY", "--type", "-t", help="MASTER_ROOT_KEY, SESSION_TRANSPORT_KEY, DATA_ENCRYPTION_KEY, SIGNING_AUTH_KEY."),
    officer: str = typer.Option(..., "--officer", help="Custodian cipher officer name."),
    bits: int = typer.Option(256, "--bits", help="Key length in bits (min 128)."),
    fingerprint: Optional[str] = typer.Option(None, "--fingerprint", help="SHA-256 fingerprint hash (auto-generated if omitted)."),
    interval: int = typer.Option(90, "--interval", help="Key rotation interval in days."),
    expire: Optional[str] = typer.Option(None, "--expire", help="Expiration date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue and record a cryptographic key lifecycle record (Article 15 Law 05/2011/QH13).
    """
    engine = CipherEngine()
    try:
        res = engine.issue_key(
            key_id=id_,
            system_id=system,
            key_type=type_,
            custodian_officer=officer,
            key_length_bits=bits,
            key_fingerprint=fingerprint,
            rotation_interval_days=interval,
            expiration_date=expire,
        )
    except Exception as e:
        console.print(f"[bold red]Error issuing cryptographic key:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Khởi tạo Khóa Mật mã Chuyên dùng thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("license")
def register_license_cmd(
    id_: str = typer.Option(..., "--id", help="Civil crypto license ID (e.g. LIC-MMDS-2026-001)."),
    enterprise: str = typer.Option(..., "--enterprise", "-e", help="Licensed commercial enterprise name."),
    tax_id: str = typer.Option(..., "--tax-id", help="Enterprise Tax Identification Number (MST)."),
    type_: str = typer.Option("PRODUCT_TRADING", "--type", "-t", help="PRODUCT_TRADING, SERVICE_PROVISION, IMPORT_EXPORT_PERMIT."),
    category: str = typer.Option("HARDWARE_HSM", "--category", "-c", help="HARDWARE_HSM, SECURITY_IP_VPN, PKI_SMART_CARD, SECURE_MESSAGING_APP, ENCRYPTED_STORAGE."),
    authority: str = typer.Option("Ban Cơ yếu Chính phủ - Cục QLMMDS", "--authority", help="Licensing authority."),
    valid_from: Optional[str] = typer.Option(None, "--from", help="Start validity date (YYYY-MM-DD)."),
    valid_until: Optional[str] = typer.Option(None, "--until", help="Expiration date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue or register a civil cryptography license (Decree 58/2016/NĐ-CP & Decree 53/2018/NĐ-CP).
    """
    engine = CipherEngine()
    try:
        res = engine.register_civil_license(
            license_id=id_,
            enterprise_name=enterprise,
            enterprise_tax_id=tax_id,
            license_type=type_,
            product_category=category,
            issuing_authority=authority,
            valid_from=valid_from,
            valid_until=valid_until,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering civil crypto license:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Giấy phép Kinh doanh Mật mã Dân sự (Nghị định 58/2016/NĐ-CP)", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("equipment")
def register_equipment_cmd(
    id_: str = typer.Option(..., "--id", help="Equipment unique ID (e.g. EQ-HSM-2026-01)."),
    serial: str = typer.Option(..., "--serial", "-s", help="Hardware serial number."),
    model: str = typer.Option(..., "--model", "-m", help="Cryptographic hardware model."),
    type_: str = typer.Option("HSM_APPLIANCE", "--type", "-t", help="DEDICATED_ENCRYPTOR, HSM_APPLIANCE, SECURE_ROUTER_VPN, TOKEN_CARD."),
    tamper: str = typer.Option("PHYSICAL_ZEROIZE_SENSITIVE", "--tamper", help="PHYSICAL_ZEROIZE_SENSITIVE, TAMPER_EVIDENT, TAMPER_RESISTANT, COGNITIVE_SHIELDED."),
    unit: str = typer.Option(..., "--unit", "-u", help="Assigned custodial unit / government agency."),
    status: str = typer.Option("CERTIFIED_PASSED", "--status", help="CERTIFIED_PASSED, INSPECTION_PENDING, QUARANTINED, FAILED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register and verify dedicated cryptographic hardware or HSM appliance (Article 12 Law 05/2011/QH13).
    """
    engine = CipherEngine()
    try:
        res = engine.register_equipment(
            equipment_id=id_,
            serial_number=serial,
            model_name=model,
            equipment_type=type_,
            tamper_resistance_level=tamper,
            assigned_unit=unit,
            inspection_status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering cryptographic equipment:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký & Kiểm định Thiết bị Mật mã Chuyên dùng", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("incident")
def report_incident_cmd(
    id_: str = typer.Option(..., "--id", help="Incident ID (e.g. INC-CIPHER-2026-01)."),
    target: str = typer.Option(..., "--target", "-t", help="Affected system or key ID."),
    severity: str = typer.Option("HIGH_TAMPER_DETECTED", "--severity", help="CRITICAL_KEY_COMPROMISE, HIGH_TAMPER_DETECTED, MEDIUM_FIRMWARE_ANOMALY, LOW_PROTOCOL_MISMATCH."),
    desc: str = typer.Option(..., "--desc", help="Incident description details."),
    actions: str = typer.Option(..., "--actions", help="Containment and zeroization actions taken."),
    officer: str = typer.Option(..., "--officer", help="Reporting cipher officer name."),
    date: Optional[str] = typer.Option(None, "--date", help="Reported date (YYYY-MM-DD)."),
    resolved: bool = typer.Option(False, "--resolved", help="Whether incident is fully contained and resolved."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Report a cryptographic security incident, tamper alert, or key breach (Article 20 Law 05/2011/QH13).
    """
    engine = CipherEngine()
    try:
        res = engine.report_incident(
            incident_id=id_,
            affected_system_or_key=target,
            severity_level=severity,
            incident_description=desc,
            containment_actions=actions,
            reporting_officer=officer,
            reported_date=date,
            resolved=resolved,
        )
    except Exception as e:
        console.print(f"[bold red]Error reporting cryptographic incident:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Báo cáo Sự cố An toàn Mật mã & Xử lý Khẩn cấp", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="systems, keys, licenses, equipment, incidents, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List cipher systems, keys, civil licenses, certified equipment, and incident reports.
    """
    engine = CipherEngine()
    records = engine.list_records(record_type=record_type, limit=limit)

    if json_output:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    for category, items in records.items():
        table = Table(title=f"Danh mục {category.upper()} ({len(items)} bản ghi)", box=box.ROUNDED)
        if not items:
            console.print(f"[dim]No {category} found.[/dim]")
            continue

        columns = list(items[0].keys())
        for col in columns[:6]:
            table.add_column(col, style="cyan")
        for item in items:
            table.add_row(*[str(item.get(c, "")) for c in columns[:6]])
        console.print(table)


@app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Get aggregate telemetry metrics on national cipher network readiness, key health, and civil crypto compliance.
    """
    engine = CipherEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Vận hành Hệ thống Mật mã Quốc gia & Mật mã Dân sự", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if isinstance(v, dict):
            table.add_row(str(k), f"{len(v)} sub-branches")
        else:
            table.add_row(str(k), str(v))
    console.print(table)

"""
CLI command group for Vietnamese National Identification, Electronic Identity (VNeID),
Biometrics & Population Database Suite.
Governed by:
- Law on Identification 2023 (Law No. 26/2023/QH15 — Luật Căn cước 2023)
- Decree No. 69/2024/NĐ-CP (Electronic Identification and Authentication)
- Decree No. 70/2024/NĐ-CP (Guiding Implementation of Law on Identification 2023)
- Circular No. 16/2024/TT-BCA & Circular No. 17/2024/TT-BCA
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.identity_engine import (
    VALID_BIOMETRIC_TYPES,
    VALID_CARD_STATUS,
    VALID_COLLECTION_TYPES,
    VALID_GENDERS,
    VALID_VERIFY_METHODS,
    VALID_VNEID_LEVELS,
    VALID_VNEID_STATUS,
    IdentityEngine,
)

app = typer.Typer(
    name="identity",
    help="Vietnamese National Identification & Electronic Identity (VNeID) Suite (Luật Căn cước 2023 & NĐ 69/2024/NĐ-CP).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def identity_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of Vietnamese National Identity, VNeID, Biometrics, and Verification Audits.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = IdentityEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    success_color = "green" if telemetry["verification_success_rate_percent"] >= 95.0 else "yellow"

    overview_text = (
        f"[bold cyan]National Identity Cards (Thẻ Căn cước 12 số - Luật 26/2023/QH15):[/bold cyan] {telemetry['total_identity_cards']} cards ([green]{telemetry['active_identity_cards']} active valid[/green])\n"
        f"[bold cyan]Electronic Identity Accounts (Định danh điện tử VNeID - NĐ 69/2024/NĐ-CP):[/bold cyan] {telemetry['total_vneid_accounts']} accounts ([green]{telemetry['vneid_level2_active']} Level-2 activated[/green])\n"
        f"[bold cyan]Biometrics Repository (Cơ sở dữ liệu sinh trắc học quốc gia - Điều 15 & 16):[/bold cyan] {telemetry['total_biometrics_enrolled']} profiles ([yellow]{telemetry['iris_scans_enrolled']} iris scans[/yellow], [cyan]{telemetry['dna_profiles_enrolled']} DNA profiles[/cyan])\n"
        f"[bold cyan]Vietnamese Origin Certificates (Giấy chứng nhận căn cước người gốc VN - Điều 30):[/bold cyan] {telemetry['total_origin_certificates']} issued ([green]{telemetry['active_origin_certificates']} active valid[/green])\n"
        f"[bold cyan]Population Database Verifications (Xác thực KYC & kiểm tra thẻ căn cước):[/bold cyan] {telemetry['total_verification_audits']} requests ([bold {success_color}]{telemetry['verification_success_rate_percent']}% success rate[/bold {success_color}])"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold red]BỘ CÔNG AN — HỆ THỐNG CĂN CƯỚC & ĐỊNH DANH ĐIỆN TỬ QUỐC GIA (VNeID)[/bold red]",
            box=box.ROUNDED,
            border_style="red",
        )
    )


@app.command("card")
def issue_card_cmd(
    card_id: str = typer.Option(..., "--id", "-i", help="12-digit personal identification number (Số định danh cá nhân / số thẻ căn cước)."),
    name: str = typer.Option(..., "--name", "-n", help="Full name of citizen (Họ và tên)."),
    dob: str = typer.Option(..., "--dob", "-d", help="Date of birth in YYYY-MM-DD format (Ngày tháng năm sinh)."),
    gender: str = typer.Option("MALE", "--gender", "-g", help="Gender: MALE, FEMALE, OTHER."),
    pob: str = typer.Option(..., "--pob", help="Place of birth registration (Nơi đăng ký khai sinh)."),
    por: str = typer.Option(..., "--por", help="Place of residence (Nơi cư trú thường trú / tạm trú)."),
    ethnicity: str = typer.Option("Kinh", "--ethnicity", "-e", help="Ethnicity (Dân tộc)."),
    nationality: str = typer.Option("VIETNAM", "--nationality", help="Nationality (Quốc tịch)."),
    status: str = typer.Option("ACTIVE_VALID", "--status", "-s", help="Card status: ACTIVE_VALID, EXPIRED_RENEWAL_DUE, REVOKED_INVALIDATED, REPLACED_REISSUED."),
    issue_date: Optional[str] = typer.Option(None, "--issue-date", help="Issue date in YYYY-MM-DD format (defaults to today)."),
    expiry_date: Optional[str] = typer.Option(None, "--expiry-date", help="Expiry date (computed automatically per Article 21 Law 26/2023 if omitted)."),
    authority: str = typer.Option("C06_BCA", "--authority", help="Issuing authority (Cục C06 Bộ Công an)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue or register an Identity Card (Thẻ Căn cước) under the Law on Identification 2023.
    """
    engine = IdentityEngine()
    try:
        res = engine.issue_identity_card(
            card_id=card_id,
            full_name=name,
            date_of_birth=dob,
            gender=gender,
            place_of_birth=pob,
            place_of_residence=por,
            ethnicity=ethnicity,
            nationality=nationality,
            card_status=status,
            issue_date=issue_date,
            expiry_date=expiry_date,
            issuing_authority=authority,
        )
    except Exception as e:
        console.print(f"[bold red]Error issuing identity card:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]✓ Successfully issued Identity Card {card_id} for {name}![/bold green]")
    console.print(f"  Validity: {res['issue_date']} -> [bold cyan]{res['expiry_date']}[/bold cyan] | Status: {res['card_status']}")


@app.command("vneid")
def provision_vneid_cmd(
    card_id: str = typer.Option(..., "--id", "-i", help="Citizen 12-digit identity card number."),
    phone: str = typer.Option(..., "--phone", "-p", help="Registered citizen mobile phone number."),
    level: str = typer.Option("LEVEL_2", "--level", "-l", help="Account level: LEVEL_1, LEVEL_2."),
    email: Optional[str] = typer.Option(None, "--email", help="Citizen email address."),
    docs: Optional[str] = typer.Option(None, "--docs", help="Comma-separated integrated documents (e.g. 'GPLX,BHYT,BHXH,MA_SO_THUE')."),
    status: str = typer.Option("ACTIVATED", "--status", "-s", help="Activation status: ACTIVATED, PENDING_ACTIVATION, LOCKED_SECURITY, DEACTIVATED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Provision or update an Electronic Identity (VNeID) account under Decree 69/2024/NĐ-CP.
    """
    engine = IdentityEngine()
    integrated_docs_list = [d.strip() for d in docs.split(",") if d.strip()] if docs else None

    try:
        res = engine.provision_vneid_account(
            card_id=card_id,
            phone_number=phone,
            account_level=level,
            email=email,
            integrated_docs=integrated_docs_list,
            activation_status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error provisioning VNeID account:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]✓ VNeID Account {res['account_id']} configured successfully![/bold green]")
    console.print(f"  Level: [cyan]{res['account_level']}[/cyan] | Status: [green]{res['activation_status']}[/green] | Docs: {res['integrated_docs']}")


@app.command("biometric")
def enroll_biometric_cmd(
    card_id: str = typer.Option(..., "--id", "-i", help="Citizen 12-digit identity card number."),
    bio_type: str = typer.Option(..., "--type", "-t", help="Biometric type: IRIS_SCAN, FACIAL_PORTRAIT, FINGERPRINT_TEN_PRINT, DNA_PROFILE, VOICE_SAMPLE."),
    collection: str = typer.Option("MANDATORY_STATUTORY", "--collection", "-c", help="Collection type: MANDATORY_STATUTORY, VOLUNTARY_CITIZEN_REQUEST, PROCEDURAL_CRIMINAL_JUSTICE."),
    score: float = typer.Option(95.0, "--score", help="Biometric quality score (0.0 to 100.0)."),
    officer: str = typer.Option("BCA-C06-001", "--officer", help="Collecting police officer badge."),
    payload: Optional[str] = typer.Option(None, "--payload", help="Raw biometric template data to hash."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Enroll biometric data (Iris, Face, Fingerprint, DNA, Voice) under Articles 15 & 16 Law 26/2023/QH15.
    """
    engine = IdentityEngine()
    try:
        res = engine.enroll_biometrics(
            card_id=card_id,
            biometric_type=bio_type,
            collection_type=collection,
            raw_payload_or_template=payload,
            quality_score=score,
            collecting_officer_badge=officer,
        )
    except Exception as e:
        console.print(f"[bold red]Error enrolling biometric data:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]✓ Enrolled {res['biometric_type']} for Card {card_id} successfully![/bold green]")
    console.print(f"  Biometric ID: {res['biometric_id']} | Hash: {res['data_hash'][:16]}... | Quality: {res['quality_score']}%")


@app.command("cert")
def issue_certificate_cmd(
    name: str = typer.Option(..., "--name", "-n", help="Full name of person of Vietnamese origin."),
    dob: str = typer.Option(..., "--dob", "-d", help="Date of birth in YYYY-MM-DD format."),
    gender: str = typer.Option("MALE", "--gender", "-g", help="Gender: MALE, FEMALE, OTHER."),
    origin: str = typer.Option(..., "--origin", help="Place of origin / ancestral homeland (Quê quán / Nơi sinh)."),
    residence: str = typer.Option(..., "--residence", help="Current residence in Vietnam (Nơi sinh sống hiện tại)."),
    cert_id: Optional[str] = typer.Option(None, "--cert-id", help="Optional specific certificate number."),
    validity: int = typer.Option(2, "--validity", help="Validity period in years (default 2 years per Article 30 Law 26/2023)."),
    unit: str = typer.Option("CONG_AN_CAP_HUYEN", "--unit", help="Issuing district/provincial police unit."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue an Identity Certificate (Giấy chứng nhận căn cước) to a person of Vietnamese origin without nationality.
    """
    engine = IdentityEngine()
    try:
        res = engine.issue_identity_certificate(
            full_name=name,
            date_of_birth=dob,
            gender=gender,
            place_of_origin=origin,
            current_residence=residence,
            cert_id=cert_id,
            validity_years=validity,
            issuing_unit=unit,
        )
    except Exception as e:
        console.print(f"[bold red]Error issuing identity certificate:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]✓ Issued Identity Certificate {res['cert_id']} for {name}![/bold green]")
    console.print(f"  Valid until: [cyan]{res['valid_until']}[/cyan] | Issuing unit: {res['issuing_unit']}")


@app.command("verify")
def verify_identity_cmd(
    target_id: str = typer.Option(..., "--id", "-i", help="12-digit card number or certificate ID to verify."),
    agency: str = typer.Option(..., "--agency", "-a", help="Verifying institution or agency (e.g. Ngân hàng, Phòng Công chứng, Cổng DVC)."),
    method: str = typer.Option("QR_CODE_SCAN", "--method", "-m", help="Verification method: QR_CODE_SCAN, NFC_CHIP_READ, VNEID_APP_AUTH, BIOMETRIC_MATCH_IRIS, BIOMETRIC_MATCH_FACE."),
    sample: Optional[str] = typer.Option(None, "--sample", help="Optional biometric payload/sample for biometric matching."),
    bypass_offline: bool = typer.Option(False, "--bypass-offline", help="Allow fallback verification if offline."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Verify identity card or certificate against the National Database under Decree 69/2024/NĐ-CP.
    """
    engine = IdentityEngine()
    try:
        res = engine.verify_identity(
            card_or_cert_id=target_id,
            verifier_agency=agency,
            verification_method=method,
            biometric_sample=sample,
            bypass_offline=bypass_offline,
        )
    except Exception as e:
        console.print(f"[bold red]Error executing verification:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_color = "bold green" if res["is_verified"] else "bold red"
    console.print(f"[{status_color}]Verification Result: {res['verification_result']} (Score: {res['matched_score']}%)[/{status_color}]")
    console.print(f"  Target: {target_id} | Agency: {agency} | Method: {method} | Audit ID: {res['audit_id']}")
    if res["document_details"]:
        d = res["document_details"]
        console.print(f"  Citizen Name: [bold]{d.get('full_name')}[/bold] | DOB: {d.get('date_of_birth')} | Residence: {d.get('place_of_residence', d.get('current_residence'))}")


@app.command("list")
def list_records_cmd(
    category: str = typer.Option("all", "--category", "-c", help="Category: cards, vneid, biometrics, certificates, audits, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum records to retrieve."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List records from the National Identification database.
    """
    engine = IdentityEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_output:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    # Render cards table
    if "cards" in records and records["cards"]:
        table = Table(title="National Identity Cards (Thẻ Căn cước)", box=box.SIMPLE)
        table.add_column("Card ID", style="cyan")
        table.add_column("Full Name", style="bold")
        table.add_column("DOB", style="dim")
        table.add_column("Gender")
        table.add_column("Residence")
        table.add_column("Expiry Date", style="yellow")
        table.add_column("Status", style="green")

        for c in records["cards"]:
            table.add_row(
                c["card_id"],
                c["full_name"],
                c["date_of_birth"],
                c["gender"],
                c["place_of_residence"][:25] + ("..." if len(c["place_of_residence"]) > 25 else ""),
                c["expiry_date"],
                c["card_status"],
            )
        console.print(table)

    # Render VNeID table
    if "vneid" in records and records["vneid"]:
        table = Table(title="Electronic Identity Accounts (VNeID)", box=box.SIMPLE)
        table.add_column("Account ID", style="cyan")
        table.add_column("Card ID")
        table.add_column("Level", style="bold")
        table.add_column("Phone")
        table.add_column("Integrated Docs")
        table.add_column("Status", style="green")

        for v in records["vneid"]:
            docs_str = ", ".join(v.get("integrated_docs", []))
            table.add_row(
                v["account_id"],
                v["card_id"],
                v["account_level"],
                v["phone_number"],
                docs_str,
                v["activation_status"],
            )
        console.print(table)

    # Render Biometrics table
    if "biometrics" in records and records["biometrics"]:
        table = Table(title="Biometrics Records (Dữ liệu sinh trắc học)", box=box.SIMPLE)
        table.add_column("Biometric ID", style="cyan")
        table.add_column("Card ID")
        table.add_column("Type", style="bold")
        table.add_column("Collection")
        table.add_column("Score", style="magenta")
        table.add_column("Enrolled Date")

        for b in records["biometrics"]:
            table.add_row(
                b["biometric_id"],
                b["card_id"],
                b["biometric_type"],
                b["collection_type"],
                f"{b['quality_score']}%",
                b["enrolled_date"],
            )
        console.print(table)

    # Render Certificates table
    if "certificates" in records and records["certificates"]:
        table = Table(title="Vietnamese Origin Certificates (Giấy chứng nhận căn cước)", box=box.SIMPLE)
        table.add_column("Cert ID", style="cyan")
        table.add_column("Full Name", style="bold")
        table.add_column("DOB")
        table.add_column("Origin")
        table.add_column("Valid Until", style="yellow")
        table.add_column("Status", style="green")

        for cert in records["certificates"]:
            table.add_row(
                cert["cert_id"],
                cert["full_name"],
                cert["date_of_birth"],
                cert["place_of_origin"],
                cert["valid_until"],
                cert["status"],
            )
        console.print(table)

    # Render Audits table
    if "audits" in records and records["audits"]:
        table = Table(title="Identity Verification Audits (Nhật ký xác thực)", box=box.SIMPLE)
        table.add_column("Audit ID", style="cyan")
        table.add_column("Target ID")
        table.add_column("Verifier Agency")
        table.add_column("Method")
        table.add_column("Result")
        table.add_column("Score")

        for a in records["audits"]:
            res_style = "bold green" if a["verification_result"] == "MATCH_SUCCESS_VERIFIED" else "bold red"
            table.add_row(
                a["audit_id"],
                a["card_or_cert_id"],
                a["verifier_agency"],
                a["verification_method"],
                f"[{res_style}]{a['verification_result']}[/{res_style}]",
                f"{a['matched_score']}%",
            )
        console.print(table)


@app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Display telemetry metrics for National Identity, VNeID, and Biometrics databases.
    """
    engine = IdentityEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="National Identity Telemetry & Population Database Status", box=box.ROUNDED)
    table.add_column("Indicator", style="bold cyan")
    table.add_column("Value", style="bold green")

    for k, v in telemetry.items():
        table.add_row(k.replace("_", " ").title(), str(v))

    console.print(table)

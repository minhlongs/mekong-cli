# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia AI Video Factory — CLI Command Surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.sophia_video_script_resolver import resolve_script_content
from src.commands.sophia_video_catalog import (
    avatars_command, cost_command, templates_command, voices_command,
)
from src.services.sophia_video_service import (
    AspectRatio, LeadingChannel, SophiaVideoService, VideoRenderRequest,
    sanitize_script, validate_identifier, validate_job_id,
)

app = typer.Typer(
    name="video", help="Sophia AI Video Factory — RaaS video generation engine for Vietnam",
    no_args_is_help=True, add_completion=False, rich_markup_mode="rich",
)
console = Console()
_service = SophiaVideoService()


_resolve_script_content = resolve_script_content


@app.command(name="render")
@app.command(name="create")
def render_command(
    script: Annotated[str, typer.Argument(..., help="Script narration text or path to .txt/.md file")],
    title: Annotated[str, typer.Option("--title", "-t", help="Video title or slug")] = "Sophia Video",
    avatar: Annotated[str, typer.Option("--avatar", "-a", help="Avatar presenter ID")] = "sophia-anchor-vi-01",
    leading: Annotated[
        str,
        typer.Option(
            "--leading",
            help="Channel that carries meaning: voice_leading | image_leading | dual_lock (RULE-P1, required)",
        ),
    ] = "voice_leading",
    voice: Annotated[str, typer.Option("--voice", "-v", help="Voice model ID")] = "elevenlabs-vi-hoang-01",
    ratio: Annotated[str, typer.Option("--ratio", "-r", help="Aspect ratio: 9:16, 16:9, 1:1")] = "9:16",
    template: Annotated[str, typer.Option("--template", help="Composition template ID")] = "news_anchor",
    dna: Annotated[str | None, typer.Option("--dna", help="Approved Design DNA name to style captions & colors")] = None,
    tenant: Annotated[str, typer.Option("--tenant", help="Tenant ID for quota and billing")] = "default",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Simulate generation without invoking external APIs")] = False,
    no_subtitles: Annotated[bool, typer.Option("--no-subtitles", help="Disable dynamic subtitles")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output result as JSON")] = False,
) -> None:
    """Render an AI avatar video from a script with brand Design DNA and voice synthesis."""
    try:
        sanitized_script = sanitize_script(_resolve_script_content(script))
        try:
            aspect_ratio_enum = AspectRatio(ratio)
        except ValueError:
            console.print(f"[red]❌ Unsupported aspect ratio: '{ratio}'. Supported: 9:16, 16:9, 1:1[/red]")
            raise typer.Exit(code=1)

        try:
            leading_channel = LeadingChannel(leading)
        except ValueError:
            console.print(
                f"[red]❌ Unsupported leading channel: '{leading}'. "
                "Supported: voice_leading, image_leading, dual_lock[/red]"
            )
            raise typer.Exit(code=1)

        req = VideoRenderRequest(
            title=title, script=sanitized_script, avatar_id=avatar, voice_id=voice,
            aspect_ratio=aspect_ratio_enum, template=template, design_dna_name=dna,
            leading_channel=leading_channel, tenant_id=tenant, dry_run=dry_run,
            subtitles_enabled=not no_subtitles,
        )
        if not json_output:
            console.print(f"[bold cyan]🎬 Initiating Sophia Video Render: '{title}'...[/bold cyan]")
            if dry_run:
                console.print("[yellow]🧪 DRY-RUN MODE: Simulating video generation[/yellow]")

        result = _service.render_video(req)
        if json_output:
            typer.echo(result.model_dump_json(indent=2))
            return

        console.print(Panel(
            f"[green]✅ Video Render Completed Successfully![/green]\n\n"
            f"[bold]Job ID:[/bold] {result.job_id}\n[bold]Status:[/bold] {result.status.value}\n"
            f"[bold]Duration:[/bold] {result.duration_seconds:.1f}s\n[bold]Credits Used:[/bold] {result.credits_used} MCU\n"
            f"[bold]Aspect Ratio:[/bold] {result.aspect_ratio}\n[bold]Presenter:[/bold] {result.avatar_id} ({result.voice_id})\n"
            f"[bold]Design DNA:[/bold] {result.design_dna_applied or 'Default'}\n"
            f"[bold]Artifact:[/bold] {result.local_artifact_path or result.video_url}",
            title="Sophia Video Generation Result", border_style="green",
        ))
    except typer.Exit:
        raise
    except ValueError as val_err:
        console.print(f"[red]❌ Validation Error: {val_err}[/red]")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[red]❌ Sophia Video Generation Failed: {exc}[/red]")
        raise typer.Exit(code=1)


@app.command(name="status")
def status_command(
    job_id: Annotated[str, typer.Argument(..., help="Job ID to check (e.g. sophia-...)")],
    json_output: Annotated[bool, typer.Option("--json", help="Output result as JSON")] = False,
) -> None:
    """Check status and metadata of a video render job."""
    try:
        clean_id = validate_job_id(job_id)
        result = _service.get_job_status(clean_id)
        if json_output:
            typer.echo(result.model_dump_json(indent=2))
            return
        console.print(Panel(result.to_summary(), title=f"Sophia Job Status: {result.job_id}", border_style="cyan"))
    except FileNotFoundError:
        console.print(f"[red]❌ Job not found: {job_id}[/red]")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]❌ Invalid Job ID: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[red]❌ Error checking job status: {exc}[/red]")
        raise typer.Exit(code=1)


@app.command(name="list")
def list_command(
    tenant: Annotated[str, typer.Option("--tenant", help="Tenant ID filter (use 'all' for all tenants)")] = "default",
    limit: Annotated[int, typer.Option("--limit", "-l", help="Maximum jobs to return")] = 20,
    json_output: Annotated[bool, typer.Option("--json", help="Output result as JSON")] = False,
) -> None:
    """List recent video generation jobs."""
    try:
        jobs = _service.list_jobs(tenant_id=tenant, limit=limit)
        if json_output:
            typer.echo(json.dumps([j.model_dump() for j in jobs], indent=2))
            return
        if not jobs:
            console.print(f"[yellow]No video jobs found for tenant '{tenant}'.[/yellow]")
            return

        table = Table(title=f"Sophia Video Jobs (Tenant: {tenant})")
        for col, st in [("Job ID", "cyan"), ("Title", "bold"), ("Status", "green"), ("Duration", None), ("Ratio", None), ("Avatar", None), ("Created At", "dim")]:
            table.add_column(col, style=st) if st else table.add_column(col)
        for job in jobs:
            table.add_row(job.job_id, job.title[:24], job.status.value, f"{job.duration_seconds:.1f}s", job.aspect_ratio, job.avatar_id, job.created_at[:19])
        console.print(table)
    except ValueError as e:
        console.print(f"[red]❌ Validation Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[red]❌ Failed to list video jobs: {exc}[/red]")
        raise typer.Exit(code=1)


app.command(name="avatars")(avatars_command)
app.command(name="voices")(voices_command)
app.command(name="templates")(templates_command)
app.command(name="cost")(cost_command)

__all__ = [
    "AspectRatio", "SophiaVideoService", "VideoRenderRequest", "_resolve_script_content",
    "_service", "app", "avatars_command", "console", "cost_command", "list_command",
    "render_command", "sanitize_script", "status_command", "templates_command",
    "validate_identifier", "validate_job_id", "voices_command",
]

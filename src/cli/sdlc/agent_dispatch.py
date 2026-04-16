"""
src/cli/sdlc/agent_dispatch.py — Shared dispatch logic for SDLC phase commands.

Responsibilities:
- Resolve .mekong/ output paths (global or per-feature)
- Load prior phase output (with missing-file guard)
- Construct agent prompt from CLAUDE.<phase>.md contract
- Print agent instructions for manual invocation (MVP: no Task tool coupling)
- Write/overwrite output file with template scaffold when --scaffold flag used

Each phase CLI module calls one function from this module.
No direct Task tool import — agents are invoked by the user running the CLI.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()

# Root of .mekong/ directory (relative to cwd or repo root)
_MEKONG_DIR_NAME = ".mekong"
_PHASES_DIR_NAME = "phases"
_TEMPLATES_DIR_NAME = "templates"


def _mekong_root(cwd: Optional[Path] = None) -> Path:
    """Return the .mekong/ directory, searching up from cwd."""
    base = cwd or Path.cwd()
    for parent in [base, *base.parents]:
        candidate = parent / _MEKONG_DIR_NAME
        if candidate.is_dir():
            return candidate
    # Fallback: create in cwd
    fallback = base / _MEKONG_DIR_NAME
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _output_dir(feature: str, mekong_root: Path) -> Path:
    """
    Return the directory where phase outputs are written.

    Default: .mekong/  (global, overwritten each feature)
    With MEKONG_FEATURE_DIR=1: .mekong/features/<feature>/
    """
    if os.environ.get("MEKONG_FEATURE_DIR") == "1":
        feature_dir = mekong_root / "features" / feature
        feature_dir.mkdir(parents=True, exist_ok=True)
        return feature_dir
    return mekong_root


def _phases_dir(mekong_root: Path) -> Path:
    """Return .mekong/phases/ where CLAUDE.*.md contracts live."""
    return mekong_root / _PHASES_DIR_NAME


def _templates_dir(mekong_root: Path) -> Path:
    """Return .mekong/phases/templates/ where blank templates live."""
    return _phases_dir(mekong_root) / _TEMPLATES_DIR_NAME


def load_prior_output(
    filename: str,
    feature: str,
    mekong_root: Path,
    required: bool = True,
) -> Optional[str]:
    """
    Load content of a prior phase output file.

    Args:
        filename: e.g. "SPEC_OUTPUT.md"
        feature: feature slug (used for error message)
        mekong_root: resolved .mekong/ path
        required: if True, exit with error when file missing

    Returns:
        File content string, or None if not required and missing.
    """
    out_dir = _output_dir(feature, mekong_root)
    path = out_dir / filename
    if not path.exists():
        if required:
            phase_map = {
                "SPEC_OUTPUT.md": f"mekong spec new {feature}",
                "DESIGN_OUTPUT.md": f"mekong design {feature}",
                "TASKS.todo": f"mekong code {feature}",
            }
            hint = phase_map.get(filename, f"mekong spec new {feature}")
            console.print(
                f"[red]Missing:[/red] {path}\n"
                f"Run [bold cyan]{hint}[/bold cyan] first."
            )
            raise typer.Exit(code=1)
        return None
    return path.read_text(encoding="utf-8")


def scaffold_output(
    template_name: str,
    output_filename: str,
    feature: str,
    mekong_root: Path,
    overwrite: bool = True,
) -> Path:
    """
    Copy a blank template to the output path, substituting {{feature}}.

    Args:
        template_name: filename in templates/ e.g. "SPEC_OUTPUT.template.md"
        output_filename: target filename e.g. "SPEC_OUTPUT.md"
        feature: slug used for substitution
        mekong_root: resolved .mekong/ path
        overwrite: if False, skip if output already exists

    Returns:
        Path to the written output file.
    """
    tmpl_path = _templates_dir(mekong_root) / template_name
    out_dir = _output_dir(feature, mekong_root)
    out_path = out_dir / output_filename

    if out_path.exists() and not overwrite:
        return out_path

    if tmpl_path.exists():
        content = tmpl_path.read_text(encoding="utf-8")
        content = content.replace("{{feature}}", feature)
        out_path.write_text(content, encoding="utf-8")
    else:
        # Template missing — write minimal placeholder
        out_path.write_text(
            f"# {output_filename.replace('.md', '')}: {feature}\n"
            f"<!-- Template not found: {tmpl_path} -->\n"
            f"<!-- Fill in manually then re-run the next phase command -->\n",
            encoding="utf-8",
        )
    return out_path


def print_agent_instructions(
    phase: str,
    feature: str,
    contract_path: Path,
    output_path: Path,
    agent_name: str,
    prior_output_path: Optional[Path] = None,
) -> None:
    """
    Print instructions for the agent to execute this phase.

    MVP: prints to terminal. The user copies the prompt to their agent session
    or runs `claude` / `mekong-opus` interactively.
    """
    console.print(f"\n[bold cyan]Phase:[/bold cyan] {phase.upper()}")
    console.print(f"[bold]Feature:[/bold] {feature}")
    console.print(f"[bold]Agent:[/bold] {agent_name}")
    console.print(f"[bold]Contract:[/bold] {contract_path}")
    console.print(f"[bold]Output:[/bold] {output_path}")
    if prior_output_path:
        console.print(f"[bold]Prior output:[/bold] {prior_output_path}")

    console.print("\n[bold yellow]--- Agent Prompt (copy to agent session) ---[/bold yellow]")
    prompt_lines = [
        f"You are the {agent_name} agent executing the {phase} phase.",
        f"Feature: {feature}",
        "",
        f"1. Read your contract: {contract_path}",
    ]
    if prior_output_path:
        prompt_lines.append(f"2. Read prior phase output: {prior_output_path}")
        prompt_lines.append(f"3. Write your output to: {output_path}")
    else:
        prompt_lines.append(f"2. Write your output to: {output_path}")
    prompt_lines.append("")
    prompt_lines.append("Follow all instructions in the contract. Do not skip sections.")

    console.print("\n".join(prompt_lines))
    console.print("[bold yellow]--- End Prompt ---[/bold yellow]\n")


def resolve_context(feature: str) -> tuple[Path, Path, Path]:
    """
    Resolve (mekong_root, output_dir, phases_dir) for a given feature slug.

    Returns:
        Tuple of (mekong_root, output_dir, phases_dir) as Path objects.
    """
    root = _mekong_root()
    out = _output_dir(feature, root)
    phases = _phases_dir(root)
    return root, out, phases

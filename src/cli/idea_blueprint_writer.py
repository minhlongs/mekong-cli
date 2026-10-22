# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Blueprint rendering and writing for `mk idea`.

Kept out of `idea_commands.py` so the command stays a thin orchestration layer and the
rendered blueprint cannot drift from what the command prints.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def blueprint_files(
    idea_text: str, validation: dict[str, Any], bmc: dict[str, Any], prd: dict[str, Any], handoff: dict[str, Any]
) -> dict[str, str]:
    """Render the pipeline stages into a file set, keyed relative to the output directory.

    Content is derived from the same dicts the command prints, so stdout and disk agree.
    """
    audit_section = ""
    contract = validation.get("contract")
    if contract:
        audit_section = (
            "\n## Live readiness evidence\n\n"
            f"- verdict: `{contract.get('readiness_verdict')}`\n"
            f"- safe_for_public_github: `{contract.get('safe_for_public_github')}`\n"
            f"- saas_paywall_active: `{contract.get('saas_paywall_active')}`\n"
            f"- contract_digest: `{contract.get('contract_digest')}`\n"
        )

    framework = "\n".join(
        [
            "# Company blueprint",
            "",
            f"**Idea:** {idea_text}",
            "",
            f"**Stage:** {validation.get('stage', 'unknown')}",
            "",
            f"**Archetype:** {bmc.get('archetype', 'unknown')}",
            "",
            "## Business model blocks",
            "",
            *[f"- **{name}:** {value}" for name, value in bmc.get("blocks", {}).items()],
            "",
            "## MVP features",
            "",
            *[f"- {item}" for item in prd.get("mvp_features", [])],
            "",
            "## Non-functional requirements",
            "",
            *[f"- {item}" for item in prd.get("non_functional", [])],
            "",
            f"**Tech stack:** {prd.get('tech_stack', 'unknown')}",
            audit_section.rstrip("\n"),
            "",
            "## Next commands",
            "",
            *[f"- `{cmd}`" for cmd in handoff.get("next_commands", [])],
            "",
        ]
    )

    features = "\n".join(
        [f"# MVP features for: {idea_text}", "", *[f"- {i}" for i in prd.get("mvp_features", [])], ""]
    )
    return {
        "00-framework.md": framework,
        "company.json": json.dumps(
            {
                "name": idea_text[:80],
                "stage": validation.get("stage", "zero"),
                "model": bmc.get("archetype", "unknown"),
                "agents": {},
                "next_commands": handoff.get("next_commands", []),
                "source": "mk idea",
            },
            indent=2,
            ensure_ascii=False,
        ),
        "mvp-scope.md": features,
    }


def write_blueprint(files: dict[str, str], output_dir: Path, dry_run: bool) -> list[str]:
    """Write the blueprint under `output_dir`, or report what would be written."""
    if dry_run:
        return sorted(files)
    written: list[str] = []
    for rel_path, content in sorted(files.items()):
        destination = output_dir / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        written.append(str(destination))
    return written


def run_deep_engine(idea_text: str, repo_root: Path, dry_run: bool) -> dict[str, Any] | None:
    """Hand the idea to the autopilot loop, or return None when it cannot be driven here."""
    try:
        from mekong.autopilot import IdeaLoop, RunOptions
    except ImportError:
        return None
    loop = IdeaLoop(RunOptions(idea=idea_text, dry_run=dry_run, worktree=False))
    result = loop.run()
    audit = getattr(loop, "audit_path", None)
    return {
        "run_id": result.run_id,
        "ok": result.ok,
        "reason": result.reason,
        "iterations": result.iterations,
        "files_touched": sorted(result.files_touched),
        "audit_log": str(audit) if audit is not None else None,
    }


def stage_validate(idea: str, deep: bool = False) -> dict[str, Any]:
    return {"stage": "zero", "valid": True, "raw_input": idea, "deep_mode": deep, "tri_layer_applied": True}


def stage_bmc(validation: dict[str, Any], is_opencore: bool = False) -> dict[str, Any]:
    return {
        "archetype": "Open-Core MIT + Cloud SaaS/RaaS (B2B/Solo-Founder)" if is_opencore else "SaaS B2B",
        "stage": validation.get("stage", "zero"),
        "blocks": {
            "channel": "Public GitHub PLG / CLI-first / API Gateway" if is_opencore else "Direct / API-first",
            "revenue": "Tiered SaaS (BASIC/PREMIUM/ENTERPRISE/MASTER) + MCU HTTP 402 + PayOS VietQR" if is_opencore else "Subscription",
            "cost": "Local BYOK (0 cloud cost for OSS) + Metered Cloud Workers",
        },
    }


def stage_prd(bmc: dict[str, Any], is_opencore: bool = False) -> dict[str, Any]:
    mvp = (
        [
            "Phase 1: Git Secret Purge & OSS/EE Directory Split (Steps 1-5)",
            "Phase 2: Provider-Neutral CapabilityBus & Local BYOK (Steps 6-10)",
            "Phase 3: FastAPI HS256 JWT License Gate & MCU HTTP 402 Billing (Steps 11-15)",
            "Phase 4: Multi-Tenant RBAC, SHA-256 AuditLedger & PayOS Webhook (Steps 16-20)",
            "Phase 5: 60s Quickstart, CLI Upsell Banner, CI LOC/Leak Gate & CLA (Steps 21-25)",
        ]
        if is_opencore
        else ["Auth", "Core workflow", "API"]
    )
    return {
        "mvp_features": mvp,
        "non_functional": ["<200ms p95", "99.9% uptime", "<=185 LOC/module", "0 leaked secrets"],
        "tech_stack": "Python 3.9+ / Typer / FastAPI / SQLite MCU / PayOS VietQR",
    }


def stage_handoff(prd: dict[str, Any], bmc: dict[str, Any], deep: bool = False) -> dict[str, Any]:
    cmds = ["/ak:brainstorm", "/ak:plan", "/ak:cook", "/ak:test", "/ak:code-review"] if deep else ["/ck:plan", "/ck:cook", "/ck:test", "/ck:code-review"]
    return {"next_commands": cmds, "execution_order": bmc.get("blocks", {}), "mvp_scope": prd.get("mvp_features", [])}

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Spec, plan.md, and SDD artifact generators for `mekong plan from-init`."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Optional

from src.cli.commands.plan.spec_templates import (
    render_data_model,
    render_quickstart,
    render_research,
)


def _slug(text: str) -> str:
    """Return a URL-safe slug; preserves spaces (already lowercased)."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _load_company(base_dir: Path) -> Optional[dict]:
    p = base_dir / ".mekong" / "company.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _generate_spec(company: dict, outlines: list[str], lang: str) -> str:
    """Return SPEC_OUTPUT.md content (deterministic template)."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    is_vi = lang == "vi"

    header = "# Product Spec\n\n" if not is_vi else "# Đặc tả sản phẩm\n\n"
    meta = (
        f"**Company:** {company.get('company_name', '?')}  \n"
        f"**Product Type:** {company.get('product_type', '?')}  \n"
        f"**Generated:** {now}\n\n"
    )
    separator = "---\n\n"

    overview_title = "## Overview\n\n" if not is_vi else "## Tổng quan\n\n"
    context = (
        f"Auto-generated from `mekong company init` for **{company.get('product_type', '?')}** product.  \n"
        f"Scenario: `{company.get('scenario', '?')}` | Budget: `{company.get('budget_tier', '?')}`.\n\n"
    )

    domains_title = "## Domains\n\n" if not is_vi else "## Lĩnh vực\n\n"
    domains = "".join(f"- `{d}`\n" for d in outlines) + "\n"

    return header + meta + separator + overview_title + context + separator + domains_title + domains


def _generate_plan_md(
    company: dict,
    outlines: list[str],
    lang: str,
) -> tuple[str, Path]:
    """Return (plan_content, plan_dir)."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    slug = _slug(company.get("company_name", "project"))

    plan_dir = Path("plans") / f"{slug}-{date_str}"
    plan_dir.mkdir(parents=True, exist_ok=True)

    is_vi = lang == "vi"
    phases = [
        {"key": "research", "title": "Nghiên cứu" if is_vi else "Research"},
        {"key": "implement", "title": "Triển khai" if is_vi else "Implement"},
        {"key": "test", "title": "Kiểm thử" if is_vi else "Test"},
        {"key": "review", "title": "Đánh giá" if is_vi else "Review"},
        {"key": "deploy", "title": "Triển khai" if is_vi else "Deploy"},
    ]

    phase_links = [f"[phase-{idx + 1:02d}](phase-{idx + 1:02d}-{p['key']}.md)" for idx, p in enumerate(phases)]
    dep_lines = [f"- phase-{idx:02d} -> phase-{idx + 1:02d}" for idx in range(1, len(phases))]
    ac_lines = [f"{i}. **{outline}** — implemented, tested, reviewed" for i, outline in enumerate(outlines, 1)]

    title_line = "# Plan\n" if not is_vi else "# Kế hoạch\n"
    meta = (
        f"**Company:** {company.get('company_name', '?')}  \n"
        f"**Product:** {company.get('product_type', '?')}  \n"
        f"**Status:** planned  \n"
        f"**Created:** {date_str}\n\n"
    )

    phases_list = "\n".join(
        f"- **{p['title']}** ([{link}]({link.split('](')[1].rstrip(')')}))"
        for p, link in zip(phases, phase_links)
    ) + "\n\n"
    deps_content = "\n".join(dep_lines) + "\n\n" if dep_lines else "Sequential — no parallel track required.\n\n"
    ac_content = "\n".join(ac_lines) + "\n"

    plan_content = f"{title_line}{meta}---\n\n## Phases\n\n{phases_list}## Dependencies\n\n{deps_content}## Acceptance Criteria\n\n{ac_content}"
    (plan_dir / "plan.md").write_text(plan_content, encoding="utf-8")

    phase_stub_templates = {
        "research": "## Context links\n\n## Requirements\n\n## Files to modify/create/delete\n\n## Implementation steps\n\n## Tests or validation\n\n## Risks and rollback notes\n",
        "implement": "## Context links\n\n## Requirements\n\n## Files to modify/create/delete\n\n## Implementation steps\n\n## Tests or validation\n\n## Risks and rollback notes\n",
        "test": "## Context links\n\n## Test plan\n\n## Coverage targets\n\n## CI requirements\n",
        "review": "## Context links\n\n## Review checklist\n\n## Security audit\n\n## Approvals\n",
        "deploy": "## Context links\n\n## Pre-flight checks\n\n## Deployment steps\n\n## Smoke tests\n\n## Rollback plan\n",
    }

    for idx, phase in enumerate(phases):
        phase_file = plan_dir / f"phase-{idx + 1:02d}-{phase['key']}.md"
        body = phase_stub_templates.get(phase["key"], "\n")
        stub = f"# Phase {idx + 1:02d}: {phase['title']}\n\n**Acceptance:** {phase.get('acceptance', 'TBD')}\n\n{body}"
        phase_file.write_text(stub, encoding="utf-8")

    return plan_content, plan_dir


def _write_artifacts(plan_dir: Path, company: dict, lang: str) -> None:
    """Write 4 supplementary SDD artifacts. Each write independently guarded."""
    try:
        api_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": company.get("company_name", "Project"),
                "version": "0.1.0",
                "description": "Auto-generated API skeleton.",
            },
            "paths": {},
        }
        (plan_dir / "contracts").mkdir(exist_ok=True)
        (plan_dir / "contracts" / "api-spec.json").write_text(
            json.dumps(api_spec, indent=2), encoding="utf-8",
        )
    except OSError:
        pass

    md_artifacts = {
        "data-model.md": render_data_model,
        "quickstart.md": render_quickstart,
        "research.md": render_research,
    }
    for filename, render_fn in md_artifacts.items():
        try:
            (plan_dir / filename).write_text(render_fn(company, lang), encoding="utf-8")
        except OSError:
            pass

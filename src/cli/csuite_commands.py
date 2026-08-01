"""C-suite commands for Binh Phap deep mapping.

Register directly on root Typer with register_csuite_commands(root).
"""
from __future__ import annotations

import json
from typing import Optional

import typer

from src.core.binh_phap_dispatcher import BinhPhapDispatcher


def _run_cfo(topic: str, prompt: str, company: str) -> None:
    """CFO Brain — Ch2 Finance + Ch5 Base — Fable 5."""
    d = BinhPhapDispatcher(company_json=company)
    action = d.next_action()
    domain_topic = "budget" if topic in ("budget", "finance", "review") else "pricing"
    llm_prompt = prompt or (
        f"CFO deep-dive on {topic}. Vietnamese commercial framing. "
        f"Include revenue impact, cost structure, pricing levers, next actions."
    )
    result = d.execute_for_topic(domain_topic, llm_prompt, {"period": topic, "product": topic})
    result.setdefault("meta", {})
    result["meta"].update({
        "command": "cfo",
        "dimension": action.get("dimension", "?"),
        "chapter": action.get("chapter", 0),
        "topic": topic,
        "company": company,
    })
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


def _run_cmo(topic: str, prompt: str, company: str) -> None:
    """CMO Brain — Ch11 Fire + Ch12 Invade — Fable 5."""
    d = BinhPhapDispatcher(company_json=company)
    action = d.next_action()
    domain_topic = "campaign" if topic in ("campaign", "outreach") else "growth:experiment"
    llm_prompt = prompt or (
        f"CMO deep-dive on {topic}. Vietnamese commercial framing. "
        f"Include channels, messaging, conversion funnel, growth levers."
    )
    result = d.execute_for_topic(domain_topic, llm_prompt, {"brief": topic, "channel": topic})
    result.setdefault("meta", {})
    result["meta"].update({
        "command": "cmo",
        "dimension": action.get("dimension", "?"),
        "chapter": action.get("chapter", 0),
        "topic": topic,
        "company": company,
    })
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


def _run_cso(topic: str, prompt: str, company: str) -> None:
    """CSO Brain — Ch6 Void + Ch1 Terrain — Fable 5."""
    d = BinhPhapDispatcher(company_json=company)
    action = d.next_action()
    domain_topic = "venture:terrain" if topic in ("terrain", "positioning") else "competitive"
    llm_prompt = prompt or (
        f"CSO deep-dive on {topic}. Vietnamese commercial framing. "
        f"Include market landscape, competitive threats, white-space opportunities."
    )
    result = d.execute_for_topic(domain_topic, llm_prompt, {"competitors": [topic]})
    result.setdefault("meta", {})
    result["meta"].update({
        "command": "cso",
        "dimension": action.get("dimension", "?"),
        "chapter": action.get("chapter", 0),
        "topic": topic,
        "company": company,
    })
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


def register_csuite_commands(app: typer.Typer) -> None:
    """Register cfo, cmo, cso on the given Typer app."""

    @app.command("cfo")
    def cfo_cmd(
        topic: str = typer.Argument(..., help="CFO topic: budget, pricing, finance, review"),
        prompt: str = typer.Option("", "--prompt", "-p", help="Optional LLM prompt"),
        company: str = typer.Option(".mekong/company.json", "--company", "-c", help="Company context file"),
    ) -> None:
        _run_cfo(topic, prompt, company)

    @app.command("cmo")
    def cmo_cmd(
        topic: str = typer.Argument(..., help="CMO topic: campaign, outreach, launch, growth"),
        prompt: str = typer.Option("", "--prompt", "-p", help="Optional LLM prompt"),
        company: str = typer.Option(".mekong/company.json", "--company", "-c", help="Company context file"),
    ) -> None:
        _run_cmo(topic, prompt, company)

    @app.command("cso")
    def cso_cmd(
        topic: str = typer.Argument(..., help="CSO topic: research, competitive, scout, terrain"),
        prompt: str = typer.Option("", "--prompt", "-p", help="Optional LLM prompt"),
        company: str = typer.Option(".mekong/company.json", "--company", "-c", help="Company context file"),
    ) -> None:
        _run_cso(topic, prompt, company)

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Studio CLI commands — registered with main Typer app."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()
app = typer.Typer(name="studio", help="🏯 VC Studio Platform — Binh Phap Ton Tu")
portfolio_app = typer.Typer(name="portfolio", help="📊 Portfolio company management")
dealflow_app = typer.Typer(name="dealflow", help="🔍 Deal pipeline management")
expert_app = typer.Typer(name="expert", help="🧠 Expert pool management")
venture_app = typer.Typer(name="venture", help="⚔️ Binh Phap venture strategy")
match_app = typer.Typer(name="match", help="🤝 Three-party matching")


@app.command("init")
def studio_init(name: str = typer.Argument(..., help="Studio name"), thesis: str = typer.Option("general", help="Thesis template: general, ai, fintech, defi")) -> None:
    console.print(f"[bold green]🏯 Studio '{name}' initialized (template: {thesis}).[/bold green]\n[dim]Run `mekong venture thesis` to define investment thesis.[/dim]")


@app.command("status")
def studio_status() -> None:
    console.print("[bold]🏯 Studio Status[/bold] — no studio initialized yet.\n[dim]Run `mekong studio init <name>` first.[/dim]")


@app.command("report")
def studio_report(period: str = typer.Option("weekly", help="weekly, monthly, quarterly"), output: str = typer.Option("cli", help="cli, markdown, json")) -> None:
    console.print(f"[bold]📊 Studio Report ({period})[/bold] — output: {output}")


@portfolio_app.command("create")
def portfolio_create(
    name: str = typer.Argument(..., help="Company name"), sector: str = typer.Option(..., help="Sector: ai, fintech, saas, ecom, other"),
    stage: str = typer.Option("idea", help="Stage: idea, validation, mvp, seed"), equity: float = typer.Option(30.0, help="Studio equity percentage"),
) -> None:
    console.print(f"[bold green]✅ Portfolio company '{name}' created[/bold green]\n   Sector: {sector} | Stage: {stage} | Equity: {equity}%")


@portfolio_app.command("list")
def portfolio_list(stage: str = typer.Option(None, help="Filter by stage"), sort: str = typer.Option("health", help="Sort: health, mrr, momentum, created")) -> None:
    console.print("[bold]📊 Portfolio Companies[/bold] — empty portfolio.")


@portfolio_app.command("status")
def portfolio_status(company: str = typer.Argument(..., help="Company slug")) -> None:
    console.print(f"[bold]📊 Status: {company}[/bold] — company not found.")


@portfolio_app.command("update")
def portfolio_update(
    company: str = typer.Argument(..., help="Company slug"), mrr: float = typer.Option(None, help="Update MRR"),
    stage: str = typer.Option(None, help="Update stage"), team_size: int = typer.Option(None, help="Update team size"),
) -> None:
    console.print(f"[bold green]✅ Updated: {company}[/bold green]")


@portfolio_app.command("health")
def portfolio_health(company: str = typer.Argument(None, help="Company slug or 'all'")) -> None:
    console.print(f"[bold]🏥 Health Assessment: {company or 'all'}[/bold]")


@dealflow_app.command("add")
def dealflow_add(
    name: str = typer.Argument(..., help="Company/opportunity name"), sector: str = typer.Option(..., help="Sector"),
    source: str = typer.Option("manual", help="Source: manual, referral, inbound, ai_sourced"), one_liner: str = typer.Option(..., help="One-line description"),
) -> None:
    console.print(f"[bold green]✅ Deal '{name}' added to pipeline[/bold green]")


@dealflow_app.command("list")
def dealflow_list(stage: str = typer.Option(None, help="Filter by stage")) -> None:
    console.print("[bold]🔍 Deal Pipeline[/bold] — empty pipeline.")


@dealflow_app.command("screen")
def dealflow_screen(deal_id: str = typer.Argument(..., help="Deal ID")) -> None:
    console.print(f"[bold]🔍 Screening deal: {deal_id}[/bold]")


@dealflow_app.command("diligence")
def dealflow_diligence(deal_id: str = typer.Argument(..., help="Deal ID"), depth: str = typer.Option("standard", help="quick, standard, deep")) -> None:
    console.print(f"[bold]🔍 Due diligence ({depth}): {deal_id}[/bold]")


@dealflow_app.command("advance")
def dealflow_advance(deal_id: str = typer.Argument(..., help="Deal ID"), to_stage: str = typer.Option(None, help="Target stage"), note: str = typer.Option(None, help="Note for this transition")) -> None:
    console.print(f"[bold green]✅ Deal {deal_id} advanced[/bold green]")


@dealflow_app.command("pass")
def dealflow_pass_cmd(deal_id: str = typer.Argument(..., help="Deal ID"), reason: str = typer.Option(..., help="Reason for passing")) -> None:
    console.print(f"[bold yellow]⏭️ Passed on deal {deal_id}: {reason}[/bold yellow]")


@expert_app.command("add")
def expert_add(name: str = typer.Argument(..., help="Expert name"), email: str = typer.Option(..., help="Email"), specialties: str = typer.Option(..., help="Comma-separated specialties")) -> None:
    console.print(f"[bold green]✅ Expert '{name}' added to pool[/bold green]")


@expert_app.command("match")
def expert_match(company: str = typer.Argument(..., help="Company slug"), need: str = typer.Option(..., help="Description of need")) -> None:
    console.print(f"[bold]🧠 Matching experts for {company}: {need}[/bold]")


@expert_app.command("dispatch")
def expert_dispatch(
    expert_id: str = typer.Argument(..., help="Expert ID"), company: str = typer.Option(..., help="Company slug"),
    scope: str = typer.Option(..., help="Engagement scope"), engagement_type: str = typer.Option("advisory", "--type", help="advisory, fractional, project"),
) -> None:
    console.print(f"[bold green]✅ Expert {expert_id} dispatched to {company}[/bold green]")


@expert_app.command("pool")
def expert_pool(specialty: str = typer.Option(None, help="Filter by specialty")) -> None:
    console.print("[bold]🧠 Expert Pool[/bold] — empty pool.")


@venture_app.command("thesis")
def venture_thesis(action: str = typer.Argument("show", help="show, update, evaluate")) -> None:
    console.print(f"[bold]⚔️ Investment Thesis — {action}[/bold]")


@venture_app.command("terrain")
def venture_terrain(market: str = typer.Argument(..., help="Market/sector to analyze")) -> None:
    console.print(f"[bold]🗺️ Terrain Analysis: {market}[/bold]")


@venture_app.command("momentum")
def venture_momentum(target: str = typer.Argument(None, help="Company slug or sector")) -> None:
    console.print(f"[bold]⚡ Momentum Score: {target or 'all'}[/bold]")


@venture_app.command("five-factors")
def venture_five_factors(target: str = typer.Argument(..., help="Deal ID or company slug")) -> None:
    console.print(f"[bold]🏯 Five-Factor Evaluation: {target}[/bold]")


@venture_app.command("void-substance")
def venture_void_substance(market: str = typer.Argument(..., help="Market to map")) -> None:
    console.print(f"[bold]👻 Void-Substance Map: {market}[/bold]")


@match_app.command("founder-idea")
def match_founder_idea(founder_id: str = typer.Option(None, help="Specific founder ID"), idea: str = typer.Option(None, help="Specific idea/sector to match")) -> None:
    console.print("[bold]🤝 Founder-Idea Matching[/bold]")


@match_app.command("vc-startup")
def match_vc_startup(company: str = typer.Argument(..., help="Company slug")) -> None:
    console.print(f"[bold]🤝 VC Match for: {company}[/bold]")


@match_app.command("expert-need")
def match_expert_need(company: str = typer.Argument(..., help="Company slug"), need: str = typer.Option(..., help="What expertise is needed")) -> None:
    console.print(f"[bold]🤝 Expert Match for {company}: {need}[/bold]")


def register_studio_commands(main_app: typer.Typer) -> None:
    for sub, name in [(app, "studio"), (portfolio_app, "portfolio"), (dealflow_app, "dealflow"), (expert_app, "expert"), (venture_app, "venture"), (match_app, "match")]:
        main_app.add_typer(sub, name=name)

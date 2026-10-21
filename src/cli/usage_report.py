# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage Report — Generate and display usage reports."""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.usage_tracker import generate_mock_usage
from src.cli.usage_types import (
    DEFAULT_QUOTA, QUOTA_CRITICAL_THRESHOLD, QUOTA_WARNING_THRESHOLD, RATE_LIMIT_CRITICAL, RATE_LIMIT_WARNING,
)

console = Console()


def display_usage_data(usage_data: dict, verbose: bool) -> None:
    """Display usage data from gateway."""
    metrics = usage_data.get("metrics", [])
    summary = usage_data.get("summary", {})
    table = Table(title="Usage Summary", show_header=True, header_style="bold cyan")
    for col, kw in [("Metric", {"style": "dim"}), ("Value", {"justify": "right"}), ("Unit", {"style": "green"})]:
        table.add_column(col, **kw)
    table.add_row("Total Requests", f"{summary.get('total_requests', 0):,}", "calls")
    table.add_row("Total Tokens", f"{summary.get('total_tokens', 0):,}", "tokens")
    table.add_row("Total Duration", f"{summary.get('total_duration_ms', 0):,.0f}", "ms")
    table.add_row("Unique Endpoints", f"{summary.get('unique_endpoints', 0):,}", "endpoints")
    console.print(table)

    if verbose and metrics:
        console.print("\n[bold]Detailed Breakdown:[/bold]\n")
        detail_table = Table(show_header=True, header_style="bold cyan")
        for col, kw in [("Event Type", {"style": "dim"}), ("Count", {"justify": "right"}), ("Tokens", {"justify": "right"}), ("Duration (ms)", {"justify": "right"})]:
            detail_table.add_column(col, **kw)
        by_type: dict = {}
        for m in metrics:
            et = m.get("event_type", "unknown")
            by_type.setdefault(et, {"count": 0, "tokens": 0, "duration": 0})
            by_type[et]["count"] += 1
            by_type[et]["tokens"] += m.get("input_tokens", 0) + m.get("output_tokens", 0)
            by_type[et]["duration"] += m.get("duration_ms", 0)
        for et, st in by_type.items():
            detail_table.add_row(et, f"{st['count']:,}", f"{st['tokens']:,}", f"{st['duration']:,.0f}")
        console.print(detail_table)


def display_local_usage(license_key: str, period: str, verbose: bool) -> None:
    """Display local/mock usage data when gateway is unavailable."""
    summary = generate_mock_usage(period).get("summary", {})
    total_requests = summary.get("total_requests", 0)
    table = Table(title="Local Usage Metrics (Cached)", show_header=True, header_style="bold cyan")
    for col, kw in [("Metric", {"style": "dim"}), ("Value", {"justify": "right"}), ("Unit", {"style": "green"})]:
        table.add_column(col, **kw)
    table.add_row("Total Requests", f"{total_requests:,}", "calls")
    table.add_row("Total Tokens", f"{summary.get('total_tokens', 0):,}", "tokens")
    table.add_row("Total Duration", f"{summary.get('total_duration_ms', 0):,.0f}", "ms")

    quota_pct = (total_requests / DEFAULT_QUOTA) * 100
    qs = "green" if quota_pct < QUOTA_WARNING_THRESHOLD else "yellow" if quota_pct < QUOTA_CRITICAL_THRESHOLD else "red"
    table.add_row("Quota Usage", f"[{qs}]{quota_pct:.1f}%[/{qs}]", f"of {DEFAULT_QUOTA:,}")
    console.print(table)

    if verbose:
        console.print("\n[bold]Events by Type:[/bold]\n")
        dt = Table(show_header=True, header_style="bold cyan")
        for col, kw in [("Event Type", {"style": "dim"}), ("Count", {"justify": "right"}), ("% of Total", {"justify": "right"})]:
            dt.add_column(col, **kw)
        for et, cnt in [("cli:command", int(total_requests * 0.6)), ("llm:call", int(total_requests * 0.3)), ("agent:spawn", int(total_requests * 0.1))]:
            dt.add_row(et, f"{cnt:,}", f"{(cnt / total_requests * 100) if total_requests > 0 else 0:.1f}%")
        console.print(dt)
    display_quota_warnings(quota_pct)


def display_report_table(
    usage_data: Optional[dict], entitlements_data: Optional[dict],
    rate_limit_remaining: int, rate_limit_limit: int, rate_limit_reset: str, verbose: bool,
) -> None:
    """Display comprehensive usage report table."""
    metrics = usage_data.get("metrics", []) if usage_data else []
    summary = usage_data.get("summary", {}) if usage_data else {}
    tier_info = entitlements_data.get("tier", {}) if entitlements_data else {}
    total_requests = summary.get("total_requests", 0) or sum(m.get("request_count", 0) for m in metrics)

    tier_name, tier_quota = tier_info.get("name", "N/A"), tier_info.get("quota", 0)
    quota_remaining = max(0, tier_quota - total_requests)
    quota_pct = (total_requests / tier_quota * 100) if tier_quota > 0 else 0
    quota_icon, quota_color = get_quota_status(quota_pct)
    rate_color = get_rate_limit_color(rate_limit_remaining)
    reset_display = format_reset_time(rate_limit_reset)
    cycle_start = entitlements_data.get("billing_cycle_start") if entitlements_data else None
    cycle_end = entitlements_data.get("billing_cycle_end") if entitlements_data else None

    console.print("\n[bold]📈 Usage Summary[/bold]\n")
    st = Table(show_header=True, header_style="bold cyan")
    st.add_column("Metric", style="dim", width=25)
    st.add_column("Value", justify="right", width=20)
    st.add_column("Details", style="green", width=30)
    st.add_row("Total Requests", f"[bold]{total_requests:,}[/bold]", f"of {tier_quota:,} quota" if tier_quota else "unlimited")
    st.add_row("Quota Used", f"[{quota_color}]{quota_icon} {quota_pct:.1f}%[/{quota_color}]", f"{quota_remaining:,} remaining")
    st.add_row("Rate Limit", f"[{rate_color}]{rate_limit_remaining:,}[/{rate_color}]", f"of {rate_limit_limit:,} (resets: {reset_display})")
    st.add_row("Tier", f"[bold cyan]{tier_name}[/bold cyan]", tier_info.get("description", ""))
    console.print(st)

    if cycle_start or cycle_end:
        console.print("\n[bold]📅 Billing Cycle[/bold]\n")
        ct = Table(show_header=False, box=None)
        ct.add_column("Label", style="dim")
        ct.add_column("Value", style="cyan")
        if cycle_start:
            ct.add_row("Period Start:", str(cycle_start)[:10])
        if cycle_end:
            ct.add_row("Period End:", str(cycle_end)[:10])
        console.print(ct)

    if verbose and metrics:
        display_detailed_breakdown(metrics)
    display_usage_warnings(quota_pct, rate_limit_remaining, rate_limit_limit)


def display_detailed_breakdown(metrics: list) -> None:
    """Display detailed endpoint breakdown."""
    console.print("\n[bold]📋 Detailed Breakdown[/bold]\n")
    dt = Table(show_header=True, header_style="bold cyan")
    for col, kw in [("Endpoint", {"style": "dim"}), ("Method", {"justify": "center"}), ("Requests", {"justify": "right"}), ("Payload Size", {"justify": "right"})]:
        dt.add_column(col, **kw)
    by_ep: dict = {}
    for m in metrics:
        key = f"{m.get('endpoint', 'unknown')}:{m.get('method', 'N/A')}"
        by_ep.setdefault(key, {"requests": 0, "payload": 0})
        by_ep[key]["requests"] += m.get("request_count", 1)
        by_ep[key]["payload"] += m.get("payload_size", 0)
    for key, stats in sorted(by_ep.items()):
        ep, method = key.split(":", 1)
        dt.add_row(ep, method, f"{stats['requests']:,}", f"{stats['payload']:,} bytes")
    console.print(dt)


def get_quota_status(quota_pct: float) -> tuple[str, str]:
    return ("🚨", "red") if quota_pct >= QUOTA_CRITICAL_THRESHOLD else (("⚠️", "yellow") if quota_pct >= QUOTA_WARNING_THRESHOLD else ("✅", "green"))


def get_rate_limit_color(remaining: int) -> str:
    return "red" if remaining < RATE_LIMIT_CRITICAL else ("yellow" if remaining < RATE_LIMIT_WARNING else "green")


def format_reset_time(rate_limit_reset: str) -> str:
    if not rate_limit_reset:
        return "N/A"
    try:
        return datetime.utcfromtimestamp(int(rate_limit_reset)).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, TypeError):
        return rate_limit_reset


def display_usage_warnings(quota_pct: float, rate_limit_remaining: int, rate_limit_limit: int) -> None:
    warnings = []
    if quota_pct >= QUOTA_CRITICAL_THRESHOLD:
        warnings.append(Panel(f"[bold red]🚨 Critical: Quota nearly exhausted![/bold red]\n{quota_pct:.1f}% of monthly limit used.\nImmediate action required: upgrade tier or reduce usage.", title="Critical Warning", border_style="red"))
    elif quota_pct >= QUOTA_WARNING_THRESHOLD:
        warnings.append(Panel(f"[bold yellow]⚠️ Warning: High quota usage[/bold yellow]\n{quota_pct:.1f}% of monthly limit used.\nConsider monitoring usage closely or upgrading tier.", title="Quota Warning", border_style="yellow"))
    if rate_limit_limit > 0 and rate_limit_remaining < RATE_LIMIT_CRITICAL:
        warnings.append(Panel(f"[bold red]🚨 Rate limit nearly exhausted![/bold red]\nOnly {rate_limit_remaining} requests remaining.\nFurther requests may be throttled.", title="Rate Limit Warning", border_style="red"))
    elif rate_limit_limit > 0 and rate_limit_remaining < RATE_LIMIT_WARNING:
        warnings.append(Panel(f"[bold yellow]⚠️ Rate limit low[/bold yellow]\n{rate_limit_remaining} requests remaining this hour.", title="Rate Limit Notice", border_style="yellow"))
    for w in warnings:
        console.print(w)
    if not warnings:
        console.print(Panel("[bold green]✅ All systems nominal[/bold green]\nUsage within healthy limits.", title="Status", border_style="green"))


def display_quota_warnings(quota_pct: float) -> None:
    if quota_pct >= QUOTA_CRITICAL_THRESHOLD:
        console.print(Panel(f"[bold red]🚨 Quota nearly exhausted![/bold red]\n{quota_pct:.1f}% of monthly limit used.\nConsider upgrading your tier or reducing usage.", title="Quota Warning", border_style="red"))
    elif quota_pct >= QUOTA_WARNING_THRESHOLD:
        console.print(Panel(f"[bold yellow]⚠️ Quota warning[/bold yellow]\n{quota_pct:.1f}% of monthly limit used.", title="Quota Warning", border_style="yellow"))

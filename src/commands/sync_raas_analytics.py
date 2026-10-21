# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Analytics cache, fetch, and display helpers for RaaS Gateway Synchronization."""

import json
import sys
from typing import Dict, Optional

from rich.panel import Panel
from rich.table import Table


def _facade():
    return sys.modules["src.commands.sync_raas"]


def _get_cache() -> Optional[Dict]:
    """Get cached analytics data if it's still valid."""
    f = _facade()
    if not f.CACHE_FILE.exists():
        return None
    try:
        with open(f.CACHE_FILE, "r") as fh:
            cache_data = json.load(fh)
        if f.time.time() - cache_data.get("timestamp", 0) > f.CACHE_TTL:
            f.CACHE_FILE.unlink(missing_ok=True)
            return None
        return cache_data.get("data")
    except Exception as e:
        f.console.print(Panel(
            f"[bold yellow]⚠️ Cache Error: {str(e)}[/bold yellow]\n\nWill fetch fresh data from API.",
            title="⚠️ Cache Error", border_style="yellow",
        ))
        return None


def _save_cache(data: Dict):
    """Save analytics data to cache."""
    f = _facade()
    f.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(f.CACHE_FILE, "w") as fh:
            json.dump({"timestamp": int(f.time.time()), "data": data}, fh)
    except Exception as e:
        f.console.print(Panel(
            f"[bold yellow]⚠️ Cache Save Error: {str(e)}[/bold yellow]\n\nData will not be cached.",
            title="⚠️ Cache Error", border_style="yellow",
        ))


def fetch_analytics(license_key: str, use_cache: bool = True) -> Optional[dict]:
    """Fetch real-time analytics from RaaS Analytics dashboard API with caching."""
    f = _facade()
    if use_cache:
        cached_data = f._get_cache()
        if cached_data:
            f.console.print(Panel(
                "[bold blue]📊 Using cached analytics data[/bold blue]\n\nData will be refreshed in 5 minutes.",
                title="✅ Cached Data", border_style="blue",
            ))
            return cached_data

    try:
        response = f.requests.get(f.ANALYTICS_ENDPOINT, headers={"Authorization": f"Bearer {license_key}"}, timeout=10)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            f.console.print(Panel(
                f"[bold yellow]⚠️ Rate Limited[/bold yellow]\n\nPlease retry after {retry_after} seconds.",
                title="⚠️ Rate Limiting", border_style="yellow",
            ))
            return None
        if response.status_code == 200:
            data = response.json()
            f._save_cache(data)
            return data
        f.console.print(Panel(
            f"[bold yellow]⚠️ Analytics Fetch Failed: {response.status_code}[/bold yellow]\n\n[dim]{response.text}[/dim]",
            title="⚠️ Analytics Error", border_style="yellow",
        ))
        return None
    except f.requests.exceptions.RequestException as e:
        f.console.print(Panel(
            f"[bold yellow]⚠️ Analytics Connection Error[/bold yellow]\n\n[dim]{str(e)}[/dim]",
            title="⚠️ Network Error", border_style="yellow",
        ))
        return None


def display_analytics(analytics: dict):
    """Display detailed analytics in formatted tables with key metrics."""
    f = _facade()
    f.console.print("\n[bold blue]📊 RaaS Gateway Analytics Dashboard[/bold blue]")

    if "usage" in analytics:
        usage = analytics["usage"]
        usage_table = Table(show_header=True, header_style="bold green")
        usage_table.add_column("Metric", style="dim")
        usage_table.add_column("Value")
        for key, label in [
            ("total_commands", "Total Commands"), ("commands_today", "Commands Today"),
            ("commands_this_month", "Commands This Month"), ("avg_commands_per_day", "Avg Commands/Day"),
            ("daily_active_users", "Daily Active Users (DAU)"), ("monthly_active_users", "Monthly Active Users (MAU)"),
            ("unique_projects", "Unique Projects"),
        ]:
            if key in usage:
                usage_table.add_row(label, f"{usage[key]:.1f}" if key == "avg_commands_per_day" else str(usage[key]))
        f.console.print(usage_table)

    if "quota" in analytics:
        quota = analytics["quota"]
        quota_table = Table(show_header=True, header_style="bold blue")
        for col, st in [("Resource", "dim"), ("Used", None), ("Total", None), ("Remaining", None), ("Usage %", None)]:
            quota_table.add_column(col, style=st) if st else quota_table.add_column(col)
        for key, label in [("commands", "Commands"), ("api_calls", "API Calls"), ("storage", "Storage (MB)"), ("email_sends", "Email Sends")]:
            if key in quota:
                used, total = quota[key].get("used", 0), quota[key].get("total", 0)
                quota_table.add_row(label, str(used), str(total), str(total - used), f"{(used / total) * 100 if total > 0 else 0:.1f}%")
        f.console.print("\n[bold blue]📊 Quota Consumption[/bold blue]")
        f.console.print(quota_table)

    if analytics.get("features"):
        features = analytics["features"]
        f.console.print("\n[bold blue]🎯 Feature Usage[/bold blue]")
        feature_table = Table(show_header=True, header_style="bold purple")
        for col in ("Feature", "Usage Count", "Usage %"):
            feature_table.add_column(col)
        total = sum(feat["count"] for feat in features)
        for feat in sorted(features, key=lambda x: x["count"], reverse=True)[:10]:
            feature_table.add_row(feat.get("name", "Unknown"), str(feat.get("count", 0)), f"{(feat['count'] / total) * 100 if total > 0 else 0:.1f}%")
        f.console.print(feature_table)

    if analytics.get("projects"):
        f.console.print("\n[bold blue]📁 Active Projects[/bold blue]")
        project_table = Table(show_header=True, header_style="bold green")
        for col in ("Project ID", "Name", "Commands", "Last Activity"):
            project_table.add_column(col)
        for proj in analytics["projects"][:5]:
            project_table.add_row(proj.get("id", "N/A"), proj.get("name", "N/A"), str(proj.get("command_count", 0)), proj.get("last_activity", "N/A"))
        f.console.print(project_table)

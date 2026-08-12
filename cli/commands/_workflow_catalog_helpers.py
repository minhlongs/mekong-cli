"""Domain inference + table rendering for `mekong workflow` commands.

Shared by list/show/domains subcommands. Single source of truth for hint
rules and group-build logic, keeping commands/testability separate from UI.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.command_fabric.catalog import build_command_catalog

console = Console()

# ---------------------------------------------------------------------------
# Domain inference — contract layer (authoritative), then keyword hints.
# ---------------------------------------------------------------------------
_DOMAIN_RULES: list[tuple[str, tuple[str, str], tuple[str, ...]]] = [
    (
        "founder",
        ("👑 Founder / Nhà sáng lập", "Annual plan / OKR / fundraising / boards / investors"),
        ("annual", "okr", "fundraise", "pitch", "swot", "board-", "cap-table", "ipo",
         "bmd", "biz-angel", "investor-pitch", "vc-"),
    ),
    (
        "business",
        ("💼 Business / Kinh doanh", "Sales / finance / marketing / brand / pricing / revenue"),
        ("sales", "marketing", "finance", "pricing", "brand", "hiring", "revenue",
         "business-", "financial", "invoice", "crm", "edp", "acquire", "outreach",
         "client-", "cpo-"),
    ),
    (
        "product",
        ("🎯 Product / Sản phẩm", "Planning / roadmaps / sprints / scopes / ideation"),
        ("roadmap", "brainstorm", "scope", "product-", "ideation", "sprint",
         "plan-", "requirements", "pm-"),
    ),
    (
        "engineering",
        ("⚙️ Engineering / Kỹ thuật", "Build / code / test / deploy / review / CI&CD"),
        ("cook", "fix", "code", "test", "deploy", "review", "backend-", "devops",
         "engineering", "build-", "database", "saas", "docker", "ci/cd",
         "performance", "frontend-", "react-"),
    ),
    (
        "ops",
        ("🔧 Ops / Vận hành", "Security / audit / health / monitoring / compliance / triage"),
        ("audit", "health", "security", "clean", "compliance", "trail", "itgc",
         "sox", "diagnostic", "status", "triage", "dead-code", "paging", "incident",
         "ops-"),
    ),
    (
        "studio",
        ("🏯 Studio", "Studio: dealflow / venture / expert"),
        ("studio", "dealflow", "venture", "expert", "studio-pm"),
    ),
    (
        "strategy",
        ("🎪 Strategy / Chiến lược", "Binh Phap / strategic analysis / forecasting"),
        ("binh-phap", "strategy", "analyze", "forecast", "rewrite", "analysis-",
         "competitive"),
    ),
    (
        "content",
        ("✍️ Content / Nội dung", "Copy / video / transcript / content generation"),
        ("content", "tweet", "email", "landing", "video-", "transcript",
         "copywriting", "multimodal", "design-"),
    ),
    (
        "agent",
        ("🤖 Agent / Tác nhân", "Memory / autonomous / governance / LLM runtime"),
        ("agent", "memory", "autonomous", "particle", "governance",
         "model-selector", "llm-choice", "llm-optimize"),
    ),
    (
        "docs",
        ("📚 Docs / Tài liệu", "Documentation generation / maintenance"),
        ("docs-", "update-docs", "generate-docs", "documentation"),
    ),
    (
        "legal",
        ("⚖️ Legal / Pháp chế", "Contracts / NDA / legal review"),
        ("legal", "contract", "nda"),
    ),
]
_DOMAIN_ORDER: list[str] = [r[0] for r in _DOMAIN_RULES]
_DOMAIN_BY_ID: dict[str, tuple[str, str]] = {r[0]: r[1] for r in _DOMAIN_RULES}
_DOMAIN_SCOPES: dict[str, str] = {
    "founder": "Annual / OKR / fundraising / kế hoạch niên / gọi vốn",
    "business": "Sales / finance / marketing / bán hàng / marketing / tài chính",
    "product": "Planning / roadmaps / sprints / kế hoạch / sprint / roadmap",
    "engineering": "Build / code / test / deploy / code / test / deploy",
    "ops": "Security / audit / health / bảo mật / audit / theo dõi",
    "studio": "Studio-specific workflow / studio đặc thù",
    "strategy": "Binh Phap / strategic analysis / chiến lược",
    "content": "Copy / video / transcript / nội dung",
    "agent": "Memory / autonomous / governance / bộ nhớ / tự chủ",
    "docs": "Documentation generation / tạo tài liệu",
    "legal": "Contracts / NDA / pháp chế",
    "general": "Other skills / chưa phân loại",
}


# ---------------------------------------------------------------------------
# Public helpers (used by workflow.py commands)
# ---------------------------------------------------------------------------

def infer_domain(name: str, description: str = "", layer: str | None = None) -> str:
    """Return canonical domain id for a command record."""
    if layer:
        layer_map = {
            "founder": "founder", "business": "business", "product": "product",
            "engineering": "engineering", "ops": "ops", "studio": "studio",
            "docs": "docs",
        }
        mapped = layer_map.get(layer.strip().lower())
        if mapped:
            return mapped
    haystack = f"{name} {description}".lower()
    for domain_id, _label, hints in _DOMAIN_RULES:
        if any(h in haystack for h in hints):
            return domain_id
    return "general"


def get_domain_groups(records: Sequence) -> dict[str, list]:
    """Return {domain_id: [records...]} from an iterable of CommandRecords."""
    grouped: dict[str, list] = defaultdict(list)
    for rec in records:
        grouped[infer_domain(rec.name, rec.description, rec.layer)].append(rec)
    return grouped


def render_domain_table(records: Sequence, title: str, *, compact: bool = False) -> None:
    table = Table(
        title=title,
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
        expand=True,
        show_lines=False,
    )
    table.add_column("name / tên", style="bold", no_wrap=True, min_width=22)
    if not compact:
        table.add_column("description / mô tả", style="dim", min_width=40)
    table.add_column("source / nguồn", style="dim", no_wrap=True, min_width=28)
    for rec in sorted(records, key=lambda r: r.name):
        row = [rec.name]
        if not compact:
            row.append(rec.description[:90] if rec.description else "—")
        row.append(rec.source)
        table.add_row(*row)
    console.print(table)


def render_summary(count: int, domain_count: int) -> str:
    return (
        f"[bold]{count}[/] skills / kỹ năng across "
        f"[bold]{domain_count}[/] domain(s) / lĩnh vực\n"
        f"[dim]Source / nguồn:[/dim] [cyan].claude/commands/[/cyan] · "
        f"[dim]Schema:[/dim] [cyan]mekong.command_fabric.v1[/cyan]"
    )

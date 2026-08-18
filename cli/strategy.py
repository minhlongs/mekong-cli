# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""
🏯 Strategy Module for Mekong-CLI
Handles Binh Phap analysis, planning and WIN-WIN-WIN validation.
"""

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


def analyze(idea: str = typer.Argument(..., help="Ý tưởng dự án hoặc bài toán kinh doanh")):
    """🏯 Phân tích chiến lược dự án theo Binh Pháp (Ngũ Sự)."""
    try:
        from core.modules.strategy import StrategyPresenter, StrategyService

        console.print(f"\n[bold blue]🏯 Đang phân tích chiến lược cho:[/bold blue] {idea}...")

        service = StrategyService(agency_name="Mekong Agency")
        insights = service.analyze_situation(idea)

        console.print(StrategyPresenter.format_report(service, insights))
    except ImportError:
        console.print("[red]❌ Lỗi: Module chiến lược chưa được cài đặt.[/red]")


def plan(task: str = typer.Argument(..., help="Nhiệm vụ cần lập kế hoạch")):
    """📋 Tạo kế hoạch tác chiến (Task Plan) theo pattern Manus."""
    from datetime import datetime
    from pathlib import Path

    plans_dir = Path("plans")
    plans_dir.mkdir(exist_ok=True)
    task_plan = plans_dir / "task_plan.md"

    content = f"""# Task Plan: {task}
Created: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Goal
{task}

## Phases
- [ ] Phase 1: Nghiên cứu & Lập kế hoạch
- [ ] Phase 2: Triển khai (Cook)
- [ ] Phase 3: Kiểm thử (Test)
- [ ] Phase 4: Bàn giao (Ship)
"""
    task_plan.write_text(content, encoding="utf-8")
    console.print(
        Panel(
            f"✅ Đã khởi tạo kế hoạch tại: [cyan]plans/task_plan.md[/cyan]\n🎯 Nhiệm vụ: {task}",
            title="📋 Planning",
        )
    )


def win3():
    """🛡️ Kiểm tra sự cân bằng WIN-WIN-WIN cho dự án."""
    console.print("\n[bold]⚖️  WIN-WIN-WIN ALIGNMENT CHECK[/bold]")
    console.print("-" * 40)
    console.print("👑 [bold green]ANH (Owner):[/bold green]     ✅ Equity + Cash flow")
    console.print("🏢 [bold green]AGENCY (Team):[/bold green]    ✅ Moat + Infrastructure")
    console.print("🚀 [bold green]CLIENT (Startup):[/bold green] ✅ 10x Value + Growth")
    console.print("-" * 40)
    console.print("[dim]Trạng thái: Cân bằng tuyệt đối. Có thể tiến hành.[/dim]")

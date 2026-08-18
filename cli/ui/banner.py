# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""
Banner UI component for CLI.
Displays the main application banner.
"""

from rich.console import Console

from cli.theme import TOKENS, get_theme


def print_banner() -> None:
    """Print main banner."""
    console = Console(theme=get_theme())
    banner_text = """
[bold primary]╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🏯 AGENCY OS - COMMAND CENTER                          ║
║                                                           ║
║   The One-Person Unicorn Operating System                ║
║   "Không đánh mà thắng" - Win Without Fighting           ║
║                                                           ║
║   🌐 agencyos.network                                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝[/bold primary]
    """
    console.print(banner_text)

"""
Binh Pháp CLI Commands
"""

import typer
from src.binh_phap.immortal_loop import main as run_immortal_loop

app = typer.Typer(help="Binh Pháp Strategy: Infinite loops & Standards")


@app.command()
def immortal():
    """
    🌀 The Immortal Loop: Infinite Supervisor for RaaS & OSS Standards.
    Runs continuously, audits, calculates score, and delegates fixes.
    """
    run_immortal_loop()


@app.command()
def monitor():
    """
    Alias for immortal.
    """
    run_immortal_loop()

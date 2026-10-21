# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Paper trading CLI command — run prediction loop with simulated fills."""

from __future__ import annotations

import logging
import signal
import sys
import time

import typer
from rich.console import Console
from rich.panel import Panel

from src.polymarket.capital_tiers import get_progress_report
from src.polymarket.kelly_position_sizer import KellyPositionSizer
from src.polymarket.market_scanner import MarketScanner, ScannerFilters
from src.polymarket.paper_exchange import PaperExchange
from src.polymarket.prediction_loop import (
    DecisionLogger,
    EnsembleEstimator,
    LoopConfig,
    PredictionLoop,
    TemperatureScaler,
)
from src.polymarket.risk_manager import RiskManager
from src.polymarket.types import Market, Signal

logger = logging.getLogger(__name__)
console = Console()


def _build_dashboard(
    exchange: PaperExchange, cycle: int, signals: list[Signal], risk_mgr: RiskManager, db_path: str,
) -> Panel:
    """Build terminal dashboard panel."""
    port, progress = exchange.get_portfolio(), get_progress_report(db_path)
    lines = [
        f"Capital: ${port.capital:.2f}  |  P&L: ${port.total_pnl:+.2f}",
        f"Trades: {port.total_trades}  |  Win Rate: {port.win_rate * 100:.0f}%",
        f"Open: {exchange.open_position_count}  |  Cycle: {cycle}",
        f"Tier: {progress.tier.level} (${progress.tier.max_capital})  |  Days: {progress.days_completed}/{progress.tier.min_dry_run_days}",
        "",
    ]
    if signals:
        lines.append("Last Signals:")
        for sig in signals[:5]:
            lines.append(f"  {sig.prediction.market_id[:12]}  {sig.prediction.direction.value} ${sig.position_size_usd:.2f}  edge: {sig.prediction.edge * 100:+.1f}%")
    else:
        lines.append("No signals this cycle")
    lines += ["", f"Circuit Breaker: {risk_mgr.state.circuit_breaker.value}"]
    return Panel("\n".join(lines), title=f"CashClaw Paper Trading — Cycle {cycle}", border_style="cyan")


def register_paper_command(app: typer.Typer) -> None:
    """Register the paper trading command."""

    @app.command()
    def paper(
        capital: float = typer.Option(200.0, help="Initial capital in USDC"),
        cycles: int = typer.Option(0, help="Max cycles (0=infinite)"),
        interval: float = typer.Option(60.0, help="Seconds between cycles"),
        db_path: str = typer.Option("data/algo-trade.db", help="SQLite database path"),
        ensemble_n: int = typer.Option(3, help="Ensemble vote count"),
        verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose logging"),
    ) -> None:
        """Run paper trading loop — scan, predict, size, simulate fills."""
        logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
        console.print(Panel(
            f"Capital: ${capital:.2f}\nEnsemble: N={ensemble_n}\nInterval: {interval}s\nDB: {db_path}\nMode: PAPER (no real trades)",
            title="CashClaw Paper Trading", border_style="green",
        ))

        scanner, estimator, scaler = MarketScanner(ScannerFilters()), EnsembleEstimator(n_votes=ensemble_n), TemperatureScaler()
        decision_logger, sizer = DecisionLogger(db_path), KellyPositionSizer()
        exchange, risk_mgr = PaperExchange(initial_capital=capital), RiskManager(capital=capital)
        config = LoopConfig(cycle_interval_sec=interval, ensemble_n=ensemble_n, db_path=db_path, paper_trading=True)
        last_signals: list[Signal] = []

        loop = PredictionLoop(
            scanner=scanner, estimator=estimator, scaler=scaler, logger_db=decision_logger,
            config=config, on_signal=lambda sig: last_signals.append(sig),
        )

        def handle_sigint(signum: int, frame: object) -> None:
            console.print("\n[yellow]Shutting down...[/yellow]")
            loop.stop()
            port = exchange.get_portfolio()
            console.print(Panel(
                f"Total Trades: {port.total_trades}\nWin Rate: {port.win_rate * 100:.0f}%\nFinal P&L: ${port.total_pnl:+.2f}\nCapital: ${port.capital_with_pnl:.2f}",
                title="Final Report", border_style="green",
            ))
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_sigint)
        console.print("[green]Paper trading started. Ctrl+C to stop.[/green]")

        cycle = 0
        max_cycles = cycles if cycles > 0 else float("inf")
        while cycle < max_cycles:
            cycle += 1
            last_signals.clear()
            try:
                markets: list[Market] = []
                signals = loop.run_cycle(markets)
                for sig in signals:
                    sized = sizer.size_signal(sig.prediction, exchange.portfolio.capital)
                    sig.kelly_fraction, sig.position_size_usd = sized.kelly_fraction, sized.position_size_usd
                    if risk_mgr.check_trade(sig).allowed:
                        exchange.execute_signal(sig)
                if cycle % 5 == 0 or cycle == 1:
                    console.print(_build_dashboard(exchange, cycle, last_signals, risk_mgr, db_path))
                time.sleep(config.cycle_interval_sec)
            except KeyboardInterrupt:
                handle_sigint(0, None)
            except Exception:
                logger.exception("Error in paper trading cycle %d", cycle)
                time.sleep(config.cycle_interval_sec)

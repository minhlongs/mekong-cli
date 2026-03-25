"""Paper trading CLI command — run prediction loop with simulated fills."""

from __future__ import annotations

import signal
import sys
import logging

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
    exchange: PaperExchange,
    cycle: int,
    signals: list[Signal],
    risk_mgr: RiskManager,
    db_path: str,
) -> Panel:
    """Build terminal dashboard panel."""
    port = exchange.get_portfolio()
    progress = get_progress_report(db_path)

    # Main stats
    lines = [
        f"Capital: ${port.capital:.2f}  |  P&L: ${port.total_pnl:+.2f}",
        f"Trades: {port.total_trades}  |  Win Rate: {port.win_rate * 100:.0f}%",
        f"Open: {exchange.open_position_count}  |  Cycle: {cycle}",
        f"Tier: {progress.tier.level} (${progress.tier.max_capital})  |  "
        f"Days: {progress.days_completed}/{progress.tier.min_dry_run_days}",
        "",
    ]

    # Last signals
    if signals:
        lines.append("Last Signals:")
        for sig in signals[:5]:
            direction = sig.prediction.direction.value
            edge_pct = sig.prediction.edge * 100
            lines.append(
                f"  {sig.prediction.market_id[:12]}  "
                f"{direction} ${sig.position_size_usd:.2f}  "
                f"edge: {edge_pct:+.1f}%"
            )
    else:
        lines.append("No signals this cycle")

    # Risk state
    lines.append("")
    breaker = risk_mgr.state.circuit_breaker.value
    lines.append(f"Circuit Breaker: {breaker}")

    return Panel(
        "\n".join(lines),
        title=f"CashClaw Paper Trading — Cycle {cycle}",
        border_style="cyan",
    )


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
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        console.print(Panel(
            f"Capital: ${capital:.2f}\n"
            f"Ensemble: N={ensemble_n}\n"
            f"Interval: {interval}s\n"
            f"DB: {db_path}\n"
            f"Mode: PAPER (no real trades)",
            title="CashClaw Paper Trading",
            border_style="green",
        ))

        # Initialize components
        scanner = MarketScanner(ScannerFilters())
        estimator = EnsembleEstimator(n_votes=ensemble_n)
        scaler = TemperatureScaler()
        decision_logger = DecisionLogger(db_path)
        sizer = KellyPositionSizer()
        exchange = PaperExchange(initial_capital=capital)
        risk_mgr = RiskManager(capital=capital)

        config = LoopConfig(
            cycle_interval_sec=interval,
            ensemble_n=ensemble_n,
            db_path=db_path,
            paper_trading=True,
        )

        last_signals: list[Signal] = []

        def on_signal(sig: Signal) -> None:
            last_signals.append(sig)

        loop = PredictionLoop(
            scanner=scanner,
            estimator=estimator,
            scaler=scaler,
            logger_db=decision_logger,
            config=config,
            on_signal=on_signal,
        )

        # Graceful shutdown
        def handle_sigint(signum: int, frame: object) -> None:
            console.print("\n[yellow]Shutting down...[/yellow]")
            loop.stop()
            port = exchange.get_portfolio()
            console.print(Panel(
                f"Total Trades: {port.total_trades}\n"
                f"Win Rate: {port.win_rate * 100:.0f}%\n"
                f"Final P&L: ${port.total_pnl:+.2f}\n"
                f"Capital: ${port.capital_with_pnl:.2f}",
                title="Final Report",
                border_style="green",
            ))
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_sigint)

        # Mock market source (in production, calls Polymarket API)
        def market_source() -> list[Market]:
            """Placeholder — returns empty list until API is wired."""
            return []

        console.print("[green]Paper trading started. Ctrl+C to stop.[/green]")

        cycle = 0
        max_cycles = cycles if cycles > 0 else float("inf")
        import time

        while cycle < max_cycles:
            cycle += 1
            last_signals.clear()

            try:
                markets = market_source()
                signals = loop.run_cycle(markets)

                # Size signals
                for sig in signals:
                    sized = sizer.size_signal(sig.prediction, exchange.portfolio.capital)
                    sig.kelly_fraction = sized.kelly_fraction
                    sig.position_size_usd = sized.position_size_usd

                    # Risk check before execution
                    check = risk_mgr.check_trade(sig)
                    if check.allowed:
                        exchange.execute_signal(sig)

                # Dashboard every 5 cycles
                if cycle % 5 == 0 or cycle == 1:
                    dashboard = _build_dashboard(
                        exchange, cycle, last_signals, risk_mgr, db_path
                    )
                    console.print(dashboard)

                time.sleep(config.cycle_interval_sec)

            except KeyboardInterrupt:
                handle_sigint(0, None)
            except Exception:
                logger.exception("Error in paper trading cycle %d", cycle)
                time.sleep(config.cycle_interval_sec)

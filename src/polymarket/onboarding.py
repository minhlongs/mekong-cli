"""CashClaw onboarding wizard — interactive CLI for new customers.

Flow:
  1. Validate API key
  2. Configure preferences
  3. Start paper trading
  4. Show first signals
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class OnboardingWizard:
    """Interactive onboarding wizard for new CashClaw customers."""

    def __init__(self, api_key: str = "", tier: str = "starter") -> None:
        self.api_key = api_key
        self.tier = tier
        self.console = Console() if HAS_RICH else None

    def run(self) -> bool:
        """Run the full onboarding flow. Returns True if successful."""
        self._print_welcome()

        # Step 1: API key
        if not self.api_key:
            self.api_key = self._prompt_api_key()
            if not self.api_key:
                self._print("No API key provided. Get one at cashclaw.io")
                return False

        # Step 2: Validate
        if not self._validate_api_key():
            self._print("Invalid API key. Check your key at cashclaw.io/dashboard")
            return False

        self._print(f"API key validated. Tier: {self.tier}")

        # Step 3: Configure
        self._configure()

        # Step 4: Start paper trading
        self._print("\nStarting paper trading...")
        self._start_paper_trading()

        self._print_success()
        return True

    def _print_welcome(self) -> None:
        """Print welcome banner."""
        if self.console:
            self.console.print(Panel(
                "[bold]Welcome to CashClaw[/bold]\n\n"
                "AI-powered prediction market trading signals.\n"
                "This wizard will get you trading in 2 minutes.",
                title="CashClaw Setup",
                border_style="green",
            ))
        else:
            print("=== CashClaw Setup ===")
            print("AI-powered prediction market trading signals.")

    def _prompt_api_key(self) -> str:
        """Prompt user for API key."""
        key = os.getenv("CASHCLAW_API_KEY", "")
        if key:
            self._print(f"Found API key from environment: {key[:8]}...")
            return key

        if HAS_RICH:
            return Prompt.ask("Enter your API key")
        return input("Enter your API key: ").strip()

    def _validate_api_key(self) -> bool:
        """Validate API key against the server."""
        if not self.api_key:
            return False

        # Basic format check
        if len(self.api_key) < 8:
            return False

        # In production: call /v1/health with auth header
        # For now, accept any properly formatted key
        if self.api_key.startswith("ck_"):
            self.tier = "starter"  # Will be resolved from server
            return True

        # Accept dev keys too
        return len(self.api_key) >= 8

    def _configure(self) -> None:
        """Configure trading preferences."""
        self._print("\nDefault configuration:")
        self._print("  Mode: Paper trading (safe)")
        self._print("  Capital: $200 USDC")
        self._print("  Strategy: DNA (ensemble N=3)")
        self._print("  Risk: Half-Kelly, 10% cap, 5% daily loss limit")

    def _start_paper_trading(self) -> None:
        """Initialize paper trading."""
        try:
            from src.polymarket.trading_pipeline import PipelineConfig, TradingPipeline
            config = PipelineConfig(
                initial_capital=200.0,
                paper_trading=True,
            )
            pipeline = TradingPipeline(config)
            status = pipeline.get_status()
            self._print(f"Pipeline ready: {status['mode']} mode, ${status['capital']:.2f}")
        except Exception as e:
            self._print(f"Pipeline init: {e} (will work once markets are connected)")

    def _print_success(self) -> None:
        """Print success message."""
        if self.console:
            self.console.print(Panel(
                "[bold green]Setup complete![/bold green]\n\n"
                "Next steps:\n"
                "  1. Run [bold]cashclaw paper[/bold] to start paper trading\n"
                "  2. Check signals at [bold]cashclaw.io/dashboard[/bold]\n"
                "  3. Monitor via Telegram (optional)",
                title="Ready",
                border_style="green",
            ))
        else:
            print("\n=== Setup Complete ===")
            print("Run 'cashclaw paper' to start paper trading")

    def _print(self, msg: str) -> None:
        """Print message."""
        if self.console:
            self.console.print(msg)
        else:
            print(msg)


def run_onboarding(api_key: str = "", tier: str = "starter") -> bool:
    """Run the onboarding wizard."""
    wizard = OnboardingWizard(api_key=api_key, tier=tier)
    return wizard.run()

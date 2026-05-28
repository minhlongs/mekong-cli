"""Config loader — pydantic-settings from env + TOML."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import tomli
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_PATH = Path.home() / ".mekongd" / "config.toml"


class PolicyConfig(BaseModel):
    """Routing policy — regex patterns decide local vs cloud."""

    local_patterns: list[str] = Field(
        default_factory=lambda: [
            r"(?i)^(read|search|grep|find|list|explore)",
            r"(?i)reformat|rename|rewrite|summarize",
        ]
    )
    cloud_patterns: list[str] = Field(
        default_factory=lambda: [
            r"(?i)^(plan|architect|design|review|verify)",
        ]
    )
    default_destination: str = Field(default="local", pattern=r"^(local|cloud)$")


class MekongdConfig(BaseSettings):
    """Top-level daemon config."""

    model_config = SettingsConfigDict(
        env_prefix="MEKONGD_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Model + runtime
    model_name: str = "Qwen/Qwen3.6-35B-A3B-MLX-4bit"
    mlx_path: Optional[str] = None  # override for local path
    local_api_url: str = "http://127.0.0.1:11437/v1"
    local_api_key: str = "mlx"

    # Proxy server
    api_host: str = "127.0.0.1"
    api_port: int = 8765

    # Cloud fallback (Anthropic)
    anthropic_fallback_url: str = "https://api.anthropic.com"
    anthropic_api_key: Optional[str] = None

    # Stats SQLite
    stats_db_path: Path = Path.home() / ".mekongd" / "stats.sqlite"

    # Cost estimation (USD per million tokens — Sonnet 4.6 default)
    cloud_input_usd_per_mtok: float = 3.0
    cloud_output_usd_per_mtok: float = 15.0

    # Optional daily cloud-spend cap (USD, UTC day). None = no enforcement.
    # Set via env MEKONGD_CLOUD_DAILY_BUDGET_USD.
    cloud_daily_budget_usd: Optional[float] = None

    # Cap max_tokens for local requests. Claude Code sends 8192 by default
    # which wastes KV cache on Qwen-35B. Set via MEKONGD_LOCAL_MAX_TOKENS.
    local_max_tokens: int = 2048

    # Policy
    policy: PolicyConfig = Field(default_factory=PolicyConfig)


def load_config(config_path: Optional[Path] = None) -> MekongdConfig:
    """Load config from TOML file + env vars. Env vars take precedence."""
    path = config_path or DEFAULT_CONFIG_PATH
    toml_data: dict = {}
    if path.exists():
        with open(path, "rb") as f:
            toml_data = tomli.load(f)
    return MekongdConfig(**toml_data)

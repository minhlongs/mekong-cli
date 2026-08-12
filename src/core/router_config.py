"""Mekong CLI - Provider Router Config Loader.

Loads and parses provider configuration from YAML with environment variable resolution.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from .provider_router import (
    ProviderConfig,
    RoutingConfig,
    MetricsConfig,
    RoutingStrategy,
    load_provider_configs,
)
from .load_balancer import LoadBalancerConfig, LoadBalancerType

logger = logging.getLogger(__name__)


@dataclass
class RouterConfig:
    """Complete router configuration."""
    providers: list[ProviderConfig]
    routing: RoutingConfig
    metrics: MetricsConfig

    @property
    def enabled_providers(self) -> list[ProviderConfig]:
        """Get only enabled providers."""
        return [p for p in self.providers if p.enabled]


def load_router_config(config_path: Optional[str] = None) -> RouterConfig:
    """Load router configuration from YAML file with environment variable resolution."""
    if config_path is None:
        # Default to providers.yaml in config directory
        config_path = str(Path(__file__).parent.parent / "config" / "providers.yaml")

    if not os.path.exists(config_path):
        logger.warning("Config file not found: %s, using defaults", config_path)
        return _default_config()

    with open(config_path, "r") as f:
        # Load with environment variable substitution
        content = f.read()
        content = _substitute_env_vars(content)
        data = yaml.safe_load(content)

    # Parse providers
    providers = []
    for p in data.get("providers", []):
        # Resolve base_url from env if needed
        if p.get("base_url_env") and not p.get("base_url"):
            p["base_url"] = os.getenv(p["base_url_env"], "")
        # Resolve api_key from env if needed
        if p.get("api_key_env") and not p.get("api_key"):
            p["api_key"] = os.getenv(p["api_key_env"], "")

        providers.append(ProviderConfig(**p))

    # Parse routing config
    routing_data = data.get("routing", {})
    load_balancer_data = routing_data.get("load_balancer", {})
    routing_config = RoutingConfig(
        strategy=RoutingStrategy(routing_data.get("strategy", "adaptive")),
        fallback_chain=routing_data.get("fallback_chain", []),
        load_balancer=LoadBalancerConfig(
            type=LoadBalancerType(load_balancer_data.get("type", "weighted")),
            health_check_interval_sec=load_balancer_data.get("health_check_interval_sec", 30),
            unhealthy_threshold=load_balancer_data.get("unhealthy_threshold", 3),
            sticky_sessions=load_balancer_data.get("sticky_sessions", False),
            warmup_requests=load_balancer_data.get("warmup_requests", 0),
        ),
        failover=routing_data.get("failover", {}),
        circuit_breaker=routing_data.get("circuit_breaker", {}),
        health_monitor=routing_data.get("health_monitor", {}),
        cost_optimizer=routing_data.get("cost_optimizer", {}),
    )

    # Parse metrics config
    metrics_data = data.get("metrics", {})
    metrics_config = MetricsConfig(
        enabled=metrics_data.get("enabled", True),
        collection_interval_sec=metrics_data.get("collection_interval_sec", 10),
        retention_hours=metrics_data.get("retention_hours", 24),
        export=metrics_data.get("export", {}),
        track=metrics_data.get("track", []),
    )

    return RouterConfig(
        providers=providers,
        routing=routing_config,
        metrics=metrics_config,
    )


def _substitute_env_vars(content: str) -> str:
    """Substitute ${VAR} or $VAR with environment variables."""
    import re

    def replace(match: re.Match) -> str:
        var_name = match.group(1) or match.group(2)
        return os.getenv(var_name, match.group(0))

    # Match ${VAR} or $VAR
    pattern = r"\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)"
    return re.sub(pattern, replace, content)


def _default_config() -> RouterConfig:
    """Create default configuration when file not found."""
    from .provider_router import ProviderConfig
    from .load_balancer import LoadBalancerConfig, LoadBalancerType

    # Minimal default providers from environment
    default_providers = []

    # OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        default_providers.append(ProviderConfig(
            name="openrouter",
            type="openai_compatible",
            enabled=True,
            priority=10,
            weight=100,
            base_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
            default_model="openrouter/auto",
            models=["openrouter/auto"],
        ))

    # AgentRouter
    if os.getenv("AGENTROUTER_API_KEY"):
        default_providers.append(ProviderConfig(
            name="agentrouter",
            type="openai_compatible",
            enabled=True,
            priority=20,
            weight=80,
            base_url="https://agentrouter.mercury.ai/v1",
            api_key_env="AGENTROUTER_API_KEY",
            default_model="agentrouter/auto",
            models=["agentrouter/auto"],
        ))

    # DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        default_providers.append(ProviderConfig(
            name="deepseek",
            type="openai_compatible",
            enabled=True,
            priority=30,
            weight=70,
            base_url="https://api.deepseek.com/v1",
            api_key_env="DEEPSEEK_API_KEY",
            default_model="deepseek-chat",
            models=["deepseek-chat"],
        ))

    # Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        default_providers.append(ProviderConfig(
            name="anthropic",
            type="anthropic",
            enabled=True,
            priority=40,
            weight=50,
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_API_KEY",
            default_model="claude-3-5-sonnet-20241022",
            models=["claude-3-5-sonnet-20241022"],
        ))

    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        default_providers.append(ProviderConfig(
            name="openai",
            type="openai_compatible",
            enabled=True,
            priority=50,
            weight=50,
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            default_model="gpt-4o",
            models=["gpt-4o"],
        ))

    # Gemini
    if os.getenv("GOOGLE_API_KEY"):
        default_providers.append(ProviderConfig(
            name="gemini",
            type="gemini",
            enabled=True,
            priority=60,
            weight=40,
            base_url="https://generativelanguage.googleapis.com",
            api_key_env="GOOGLE_API_KEY",
            default_model="gemini-2.0-flash-exp",
            models=["gemini-2.0-flash-exp"],
        ))

    # Local MLX
    if os.getenv("LOCAL_LLM_URL"):
        default_providers.append(ProviderConfig(
            name="local-mlx",
            type="openai_compatible",
            enabled=True,
            priority=70,
            weight=30,
            base_url_env="LOCAL_LLM_URL",
            api_key_env="LOCAL_LLM_API_KEY",
            default_model="mlx-community/llama-3.2-3b-instruct-4bit",
            models=["mlx-community/llama-3.2-3b-instruct-4bit"],
        ))

    # Ollama
    if os.getenv("OLLAMA_BASE_URL"):
        default_providers.append(ProviderConfig(
            name="ollama",
            type="openai_compatible",
            enabled=True,
            priority=80,
            weight=20,
            base_url_env="OLLAMA_BASE_URL",
            default_model="llama3.2:3b",
            models=["llama3.2:3b"],
        ))

    # If no providers configured, add offline
    if not default_providers:
        default_providers.append(ProviderConfig(
            name="offline",
            type="offline",
            enabled=True,
            priority=100,
            weight=10,
            default_model="offline",
            models=["offline"],
        ))

    return RouterConfig(
        providers=default_providers,
        routing=RoutingConfig(
            strategy=RoutingStrategy.ADAPTIVE,
            fallback_chain=[p.name for p in default_providers],
            load_balancer=LoadBalancerConfig(type=LoadBalancerType.ADAPTIVE),
        ),
        metrics=MetricsConfig(),
    )


def create_provider_factory():
    """Create provider factory function for router."""
    from .providers import (
        LLMProvider,
        OpenAICompatibleProvider,
        GeminiProvider,
        OfflineProvider,
        AnthropicProvider,
    )

    def factory(config: ProviderConfig) -> LLMProvider:
        if config.type == "openai_compatible":
            return OpenAICompatibleProvider(
                name=config.name,
                base_url=config.resolve_base_url(),
                api_key=config.resolve_api_key(),
                default_model=config.default_model,
                timeout=config.timeout_sec,
                max_retries=config.max_retries,
            )
        elif config.type == "gemini":
            return GeminiProvider(
                api_key=config.resolve_api_key(),
                model=config.default_model,
            )
        elif config.type == "anthropic":
            return AnthropicProvider(
                api_key=config.resolve_api_key(),
                model=config.default_model,
            )
        elif config.type == "offline":
            return OfflineProvider()
        else:
            logger.warning("Unknown provider type %s, using offline", config.type)
            return OfflineProvider()

    return factory


__all__ = [
    "RouterConfig",
    "load_router_config",
    "create_provider_factory",
]
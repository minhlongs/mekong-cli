"""Mekong CLI - Provider Registry.

Multi-provider LLM registry (inspired by AI SDK provider pattern).
Manages multi-provider LLM routing with colon-separated model refs.
Example: "gemini:gemini-2.5-pro", "openai:gpt-4o", "proxy:gemini-3-pro-high"
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True)
class ProviderHealth:
    consecutive_failures: int = 0
    last_failure_at: float = 0.0
    last_success_at: float = 0.0
    state: CircuitState = CircuitState.CLOSED


@dataclass
class ProviderCircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0
    _health: dict[str, ProviderHealth] = field(default_factory=dict, repr=False)

    def _key(self, provider_name: str, model_ref: str) -> str:
        return f"{provider_name}:{model_ref}"

    def health(self, provider_name: str, model_ref: str) -> ProviderHealth:
        return self._health.get(self._key(provider_name, model_ref), ProviderHealth())

    def record_success(self, provider_name: str, model_ref: str) -> None:
        key = self._key(provider_name, model_ref)
        previous = self._health.get(key)
        self._health[key] = ProviderHealth(
            consecutive_failures=0,
            last_success_at=__import__("time").time(),
            state=CircuitState.CLOSED,
            last_failure_at=previous.last_failure_at if previous else 0.0,
        )

    def record_failure(self, provider_name: str, model_ref: str) -> None:
        key = self._key(provider_name, model_ref)
        previous = self._health.get(key, ProviderHealth())
        failures = previous.consecutive_failures + 1
        state = CircuitState.OPEN if failures >= self.failure_threshold else CircuitState.CLOSED
        now = __import__("time").time()
        self._health[key] = ProviderHealth(
            consecutive_failures=failures,
            last_failure_at=now,
            state=state,
            last_success_at=previous.last_success_at,
        )
        logger.warning(
            "provider=%s model=%s failure=%s state=%s",
            provider_name,
            model_ref,
            failures,
            state.value,
        )

    def can_attempt(self, provider_name: str, model_ref: str) -> bool:
        key = self._key(provider_name, model_ref)
        current = self._health.get(key, ProviderHealth())
        if current.state is CircuitState.CLOSED:
            return True
        if current.state is CircuitState.HALF_OPEN:
            return True
        age = __import__("time").time() - current.last_failure_at
        if age >= self.recovery_timeout_seconds:
            self._health[key] = ProviderHealth(
                consecutive_failures=current.consecutive_failures,
                last_failure_at=current.last_failure_at,
                last_success_at=current.last_success_at,
                state=CircuitState.HALF_OPEN,
            )
            logger.info(
                "provider=%s model=%s promoting to HALF_OPEN",
                provider_name,
                model_ref,
            )
            return True
        return False

    def should_degrade(self, provider_name: str, model_ref: str) -> bool:
        return not self.can_attempt(provider_name, model_ref)

    def reset(self, provider_name: str, model_ref: str) -> None:
        key = self._key(provider_name, model_ref)
        self._health[key] = ProviderHealth()
        logger.info(
            "provider=%s model=%s circuit reset",
            provider_name,
            model_ref,
        )


@runtime_checkable
class ProviderSpec(Protocol):
    """Protocol for LLM provider implementations.

    Each provider implements: provider name, supported models, and generate.
    """

    @property
    def provider_name(self) -> str:
        """Unique provider identifier (e.g., 'gemini', 'openai', 'proxy')."""
        ...

    @property
    def supported_models(self) -> list[str]:
        """List of model IDs this provider serves."""
        ...

    def get_capabilities(self, model_id: str) -> dict[str, bool]:
        """Return model capabilities (tools, structured_output, streaming)."""
        ...


@runtime_checkable
class RoutingStrategy(Protocol):
    """Protocol for registry routing strategies (Strategy Registry).

    Implementations decide which provider:model pair is returned for a
    given model reference. Default behavior is exact provider lookup.
    """

    def select(
        self,
        registry: "ProviderRegistry",
        model_ref: str,
        *,
        tier: str | None = None,
        fallback: bool = False,
    ) -> ResolvedModel:
        """Return selected ResolvedModel for the request."""
        ...


@dataclass
class DefaultRoutingStrategy:
    """Default routing: straightforward provider:model resolution.

    Delegates to ``ProviderRegistry.resolve`` so alias expansion,
    default-model fallback, and capability resolution all behave the
    same way whether the caller uses the strategy layer or the registry
    directly.
    """

    def select(
        self,
        registry: "ProviderRegistry",
        model_ref: str,
        *,
        tier: str | None = None,
        fallback: bool = False,
    ) -> ResolvedModel:
        if ":" in model_ref:
            resolved_ref = model_ref
        else:
            provider_name = registry.default_provider or next(iter(registry._providers), "openai")
            resolved_ref = f"{provider_name}:{model_ref}"
        return registry.resolve(resolved_ref)


@dataclass
class ResolvedModel:
    """Result of resolving a model reference string."""

    provider_name: str
    model_id: str
    capabilities: dict[str, bool] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Configuration for a registered provider."""

    name: str
    factory: Callable[..., "ProviderSpec"]
    default_model: str = ""
    aliases: dict[str, str] = field(default_factory=dict)


class ProviderRegistry:
    """Central registry for LLM providers.

    Central provider registry with colon-separated model refs.
    Supports colon-separated model refs: "provider:model-id"
    """


    def __init__(self) -> None:
        self._providers: dict[str, ProviderConfig] = {}
        self._instances: dict[str, ProviderSpec] = {}
        self._default_provider: str = ""
        self._breaker = ProviderCircuitBreaker()
        self._provider_model_map: dict[str, list[str]] = {}

    def record_failure(self, provider_name: str, model_ref: str) -> None:
        self._breaker.record_failure(provider_name, model_ref)

    def record_success(self, provider_name: str, model_ref: str) -> None:
        self._breaker.record_success(provider_name, model_ref)

    def register(
        self,
        name: str,
        factory: Callable[..., "ProviderSpec"],
        default_model: str = "",
        aliases: dict[str, str] | None = None,
    ) -> None:
        """Register a provider with lazy initialization.

        Args:
            name: Provider identifier (e.g., 'gemini', 'openai')
            factory: Callable that creates provider instance
            default_model: Default model when only provider name given
            aliases: Model alias mappings (e.g., {"fast": "gemini-2.0-flash"})

        """
        self._providers[name] = ProviderConfig(
            name=name,
            factory=factory,
            default_model=default_model,
            aliases=aliases or {},
        )
        if not self._default_provider:
            self._default_provider = name

    def set_default(self, provider_name: str) -> None:
        """Set the default provider for unqualified model refs.

        Args:
            provider_name: Name of registered provider

        """
        if provider_name not in self._providers:
            msg = f"Provider not registered: {provider_name}"
            raise ValueError(msg)
        self._default_provider = provider_name

    def resolve(self, model_ref: str) -> ResolvedModel:
        """Resolve a model reference string to provider + model.

        Supports formats:
        - "gemini:gemini-2.5-pro" → (gemini, gemini-2.5-pro)
        - "openai:gpt-4o" → (openai, gpt-4o)
        - "fast" → resolve alias from default provider
        - "gemini-2.5-pro" → use default provider

        Args:
            model_ref: Colon-separated or plain model reference

        Returns:
            ResolvedModel with provider_name, model_id, capabilities

        """
        if ":" in model_ref:
            parts = model_ref.split(":", 1)
            provider_name, model_id = parts[0], parts[1]
        else:
            provider_name = self._default_provider
            model_id = model_ref

        if provider_name not in self._providers:
            msg = (
                f"Unknown provider '{provider_name}'. "
                f"Registered: {list(self._providers.keys())}"
            )
            raise ValueError(
                msg,
            )

        config = self._providers[provider_name]

        # Check aliases
        if model_id in config.aliases:
            model_id = config.aliases[model_id]

        # Use default model if empty
        if not model_id and config.default_model:
            model_id = config.default_model

        # Get capabilities from provider instance
        instance = self._get_instance(provider_name)
        capabilities = {}
        if instance:
            capabilities = instance.get_capabilities(model_id)

        return ResolvedModel(
            provider_name=provider_name,
            model_id=model_id,
            capabilities=capabilities,
        )

    def _get_instance(self, provider_name: str) -> ProviderSpec | None:
        """Lazy-initialize and cache provider instance.

        Args:
            provider_name: Registered provider name

        Returns:
            Provider instance or None if initialization fails

        """
        if provider_name in self._instances:
            return self._instances[provider_name]

        config = self._providers.get(provider_name)
        if not config:
            return None

        try:
            instance = config.factory()
            self._instances[provider_name] = instance
            return instance
        except Exception as e:
            logger.warning("Failed to instantiate provider '%s': %s", provider_name, e)
            return None

    def list_providers(self) -> list[str]:
        """Return names of all registered providers."""
        return list(self._providers.keys())

    def list_models(self, provider_name: str) -> list[str]:
        """Return supported models for a provider.

        Args:
            provider_name: Provider to query

        Returns:
            List of model IDs

        """
        instance = self._get_instance(provider_name)
        if instance:
            return instance.supported_models
        return []


# Built-in provider specs


class OpenAICompatProvider:
    """Provider for any OpenAI-compatible endpoint (LLM_BASE_URL configured)."""

    @property
    def provider_name(self) -> str:
        return "proxy"

    @property
    def supported_models(self) -> list[str]:
        return [
            "gemini-3-pro-high",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "claude-sonnet-4-6",
            "claude-opus-4-6",
        ]

    def get_capabilities(self, model_id: str) -> dict[str, bool]:
        return {
            "tools": True,
            "structured_output": True,
            "streaming": True,
            "system_message": True,
        }


class GeminiProvider:
    """Provider for Google Gemini (direct API via google-genai SDK)."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def supported_models(self) -> list[str]:
        return [
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-3-pro-preview",
        ]

    def get_capabilities(self, model_id: str) -> dict[str, bool]:
        return {
            "tools": True,
            "structured_output": True,
            "streaming": True,
            "system_message": True,
        }


class OpenAIProvider:
    """Provider for OpenAI (direct API)."""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def supported_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"]

    def get_capabilities(self, model_id: str) -> dict[str, bool]:
        is_reasoning = model_id.startswith("o")
        return {
            "tools": not is_reasoning,
            "structured_output": True,
            "streaming": True,
            "system_message": not is_reasoning,
        }


def create_default_registry() -> ProviderRegistry:
    """Create registry with built-in providers pre-registered.

    Returns:
        ProviderRegistry with proxy, gemini, openai providers

    """
    registry = ProviderRegistry()

    registry.register(
        "proxy",
        factory=OpenAICompatProvider,
        default_model="gemini-3-pro-high",
        aliases={"fast": "gemini-2.0-flash", "best": "gemini-3-pro-high"},
    )
    registry.register(
        "gemini",
        factory=GeminiProvider,
        default_model="gemini-2.5-pro",
        aliases={"fast": "gemini-2.0-flash", "pro": "gemini-2.5-pro"},
    )
    registry.register(
        "openai",
        factory=OpenAIProvider,
        default_model="gpt-4o",
        aliases={"fast": "gpt-4o-mini", "best": "gpt-4o"},
    )

    return registry


__all__ = [
    "DefaultRoutingStrategy",
    "OpenAICompatProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "ProviderConfig",
    "ProviderRegistry",
    "ProviderSpec",
    "ResolvedModel",
    "RoutingStrategy",
    "create_default_registry",
]

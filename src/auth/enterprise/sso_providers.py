"""Enterprise SSO/SAML provider stubs.

Additive-only: no route mutation, no callback breakage.
"""
from __future__ import annotations

from typing import Dict, Optional


class SSOProviderError(Exception):
    """Raised when an SSO provider is misconfigured or verification fails."""


class SAMLProvider:
    """Minimal SAML placeholder — does not perform real SAML flows yet."""

    def __init__(self, config: Dict[str, object]) -> None:
        self.provider_id: str = config.get("provider_id", "")
        self.entity_id: str = config.get("entity_id", "")
        self.sso_url: str = config.get("sso_url", "")
        self.x509_cert: str = config.get("x509_cert", "")
        self.name_id_format: str = config.get(
            "name_id_format",
            "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        )
        self.attribute_mapping: Dict[str, str] = config.get(
            "attribute_mapping",
            {"email": "email", "name": "displayName", "role": "role"},
        )

    def build_auth_request(self, relay_state: Optional[str] = None) -> Dict[str, str]:
        raise SSOProviderError("SAML auth request not implemented yet")

    def verify_response(self, response: Dict[str, object]) -> Dict[str, object]:
        raise SSOProviderError("SAML response verification not implemented yet")


_registry: Dict[str, Dict[str, object]] = {}


def register_provider(
    provider_id: str,
    provider_type: str = "saml",
    config: Optional[Dict[str, object]] = None,
) -> None:
    config = config or {}
    config["provider_id"] = provider_id
    config["provider_type"] = provider_type
    _registry[provider_id] = config


def get_sso_provider(provider_id: str) -> Dict[str, object]:
    if provider_id not in _registry:
        raise KeyError(f"SSO provider not found: {provider_id}")
    return _registry[provider_id]


def list_sso_providers() -> Dict[str, Dict[str, object]]:
    return dict(_registry)


def create_sso_provider(
    provider_id: str,
    config: Dict[str, object],
) -> Dict[str, object]:
    register_provider(provider_id=provider_id, config=config)
    return get_sso_provider(provider_id)


def update_sso_provider(
    provider_id: str,
    config: Dict[str, object],
) -> Dict[str, object]:
    existing = get_sso_provider(provider_id)
    existing.update(config)
    _registry[provider_id] = existing
    return existing


def delete_sso_provider(provider_id: str) -> None:
    _registry.pop(provider_id, None)


def build_saml_auth_request(
    provider_id: str,
    relay_state: Optional[str] = None,
) -> Dict[str, str]:
    provider = get_sso_provider(provider_id)
    if provider.get("provider_type") != "saml":
        raise SSOProviderError(
            f"Provider {provider_id} is not SAML: {provider.get('provider_type')}"
        )
    return SAMLProvider(provider).build_auth_request(relay_state=relay_state)


def verify_saml_response(
    provider_id: str,
    response: Dict[str, object],
) -> Dict[str, object]:
    provider = get_sso_provider(provider_id)
    if provider.get("provider_type") != "saml":
        raise SSOProviderError(
            f"Provider {provider_id} is not SAML: {provider.get('provider_type')}"
        )
    return SAMLProvider(provider).verify_response(response)


def configure_from_env() -> None:
    import os as _os

    provider_type = _os.getenv("MEKONG_SSO_TYPE", "saml")
    provider_id = _os.getenv("MEKONG_SSO_PROVIDER_ID")
    if not provider_id:
        return

    register_provider(
        provider_id,
        provider_type=provider_type,
        config={
            "provider_type": provider_type,
            "enabled": _os.getenv("MEKONG_SSO_ENABLED", "false").lower() == "true",
            "entity_id": _os.getenv("MEKONG_SSO_ENTITY_ID", ""),
            "sso_url": _os.getenv("MEKONG_SSO_SSO_URL", ""),
            "x509_cert": _os.getenv("MEKONG_SSO_X509_CERT", ""),
            "name_id_format": _os.getenv("MEKONG_SSO_NAMEID_FORMAT", ""),
            "attribute_mapping": {
                "email": _os.getenv("MEKONG_SSO_ATTR_EMAIL", "email"),
                "name": _os.getenv("MEKONG_SSO_ATTR_NAME", "displayName"),
                "role": _os.getenv("MEKONG_SSO_ATTR_ROLE", "role"),
            },
        },
    )

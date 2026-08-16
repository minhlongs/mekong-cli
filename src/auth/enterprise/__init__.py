# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Enterprise tier — SSO/SAML provider config (additive, no route mutation)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SSOProviderConfig:
    provider_id: str
    provider_type: str = "saml"
    enabled: bool = False
    entity_id: str = ""
    sso_url: str = ""
    x509_cert: str = ""
    name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    attribute_mapping: Dict[str, str] = field(default_factory=dict)
    default_role: str = "member"
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class EnterpriseConfig:
    sso_providers: Dict[str, SSOProviderConfig] = field(default_factory=dict)
    audit_retention_days: int = 90
    support_channel: str = ""
    sla_response_hours: int = 4
    custom_domain: Optional[str] = None


_providers: Dict[str, SSOProviderConfig] = {}
_enterprise = EnterpriseConfig()


def register_provider(config: SSOProviderConfig) -> None:
    _providers[config.provider_id] = config
    _enterprise.sso_providers = dict(_providers)


def get_provider(provider_id: str) -> Optional[SSOProviderConfig]:
    return _providers.get(provider_id)


def list_providers() -> List[SSOProviderConfig]:
    return list(_providers.values())


def get_enterprise_config() -> EnterpriseConfig:
    return _enterprise


def configure_from_env() -> None:
    import os
    ptype = os.getenv("MEKONG_SSO_TYPE", "saml")
    pid = os.getenv("MEKONG_SSO_PROVIDER_ID", "default-saml")
    if not pid:
        return
    register_provider(
        SSOProviderConfig(
            provider_id=pid,
            provider_type=ptype,
            enabled=os.getenv("MEKONG_SSO_ENABLED", "false").lower() == "true",
            entity_id=os.getenv("MEKONG_SSO_ENTITY_ID", ""),
            sso_url=os.getenv("MEKONG_SSO_SSO_URL", ""),
            x509_cert=os.getenv("MEKONG_SSO_X509_CERT", ""),
            name_id_format=os.getenv("MEKONG_SSO_NAMEID_FORMAT", ""),
            attribute_mapping={
                "email": os.getenv("MEKONG_SSO_ATTR_EMAIL", "email"),
                "name": os.getenv("MEKONG_SSO_ATTR_NAME", "displayName"),
                "role": os.getenv("MEKONG_SSO_ATTR_ROLE", "role"),
            },
            default_role=os.getenv("MEKONG_SSO_DEFAULT_ROLE", "member"),
        )
    )
    _enterprise.support_channel = os.getenv("MEKONG_SUPPORT_CHANNEL", "")
    _enterprise.sla_response_hours = int(os.getenv("MEKONG_SLA_HOURS", "4"))

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Credential declaration schema for plugin manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CredentialRequirement:
    """One credential a plugin needs from a provider."""

    provider: str
    env_fallback: Optional[str] = None
    required: bool = True
    scope: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PluginCredentials:
    """All credential requirements for a plugin."""

    requirements: List[CredentialRequirement] = field(default_factory=list)

    def provider_names(self) -> List[str]:
        return [r.provider for r in self.requirements]

    def required_providers(self) -> List[str]:
        return [r.provider for r in self.requirements if r.required]

    def optional_providers(self) -> List[str]:
        return [r.provider for r in self.requirements if not r.required]

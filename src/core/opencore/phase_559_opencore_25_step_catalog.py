"""25-Step Open-Core Public GitHub + SaaS Monetization Catalog (Phase 559)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OpenCorePhase(str, Enum):
    PHASE_1_SPLIT_AND_HYGIENE = "PHASE_1_SPLIT_AND_HYGIENE"
    PHASE_2_PLUGIN_AND_SEAMS = "PHASE_2_PLUGIN_AND_SEAMS"
    PHASE_3_CLOUD_CONTROL_PLANE = "PHASE_3_CLOUD_CONTROL_PLANE"
    PHASE_4_ENTERPRISE_MONETIZATION = "PHASE_4_ENTERPRISE_MONETIZATION"
    PHASE_5_PLG_GROWTH_AND_GOVERNANCE = "PHASE_5_PLG_GROWTH_AND_GOVERNANCE"


@dataclass(frozen=True)
class OpenCoreStepSpec:
    step_number: int
    phase: OpenCorePhase
    slug: str
    oss_public_surface: str
    saas_monetized_surface: str


TWENTY_FIVE_OPENCORE_STEPS: tuple[OpenCoreStepSpec, ...] = (
    OpenCoreStepSpec(1, OpenCorePhase.PHASE_1_SPLIT_AND_HYGIENE, "git-history-secret-purge", "Clean commit history", "Zero leaked prod keys"),
    OpenCoreStepSpec(2, OpenCorePhase.PHASE_1_SPLIT_AND_HYGIENE, "oss-vs-ee-directory-split", "src/core + src/cli (MIT)", "apps/ + billing/ isolated"),
    OpenCoreStepSpec(3, OpenCorePhase.PHASE_1_SPLIT_AND_HYGIENE, "gitignore-quarantine-lock", ".gitignore guardrails", "Private tenant data blocked"),
    OpenCoreStepSpec(4, OpenCorePhase.PHASE_1_SPLIT_AND_HYGIENE, "env-example-byok-template", ".env.example template", "Managed cloud env vault"),
    OpenCoreStepSpec(5, OpenCorePhase.PHASE_1_SPLIT_AND_HYGIENE, "mit-license-and-sbom", "MIT LICENSE + SBOM", "Commercial SLA terms"),
    OpenCoreStepSpec(6, OpenCorePhase.PHASE_2_PLUGIN_AND_SEAMS, "capability-bus-interfaces", "CapabilityBus protocol", "Managed cloud providers"),
    OpenCoreStepSpec(7, OpenCorePhase.PHASE_2_PLUGIN_AND_SEAMS, "byok-local-adapters", "User-supplied API keys", "Zero-config hosted inference"),
    OpenCoreStepSpec(8, OpenCorePhase.PHASE_2_PLUGIN_AND_SEAMS, "cloud-bridge-webhooks", "WatcherBridge client stub", "Hosted webhook ingestion"),
    OpenCoreStepSpec(9, OpenCorePhase.PHASE_2_PLUGIN_AND_SEAMS, "local-sandbox-runtime", "Single-operator CLI", "Multi-region cloud workers"),
    OpenCoreStepSpec(10, OpenCorePhase.PHASE_2_PLUGIN_AND_SEAMS, "versioned-openapi-sdk", "Public SDK & schemas", "Metered API gateway"),
    OpenCoreStepSpec(11, OpenCorePhase.PHASE_3_CLOUD_CONTROL_PLANE, "jwt-license-gate", "Local bypass in pytest", "FastAPI HS256 license_gate"),
    OpenCoreStepSpec(12, OpenCorePhase.PHASE_3_CLOUD_CONTROL_PLANE, "mcu-credit-metering", "Mock local credit ledger", "MCUBilling + HTTP 402 recharge"),
    OpenCoreStepSpec(13, OpenCorePhase.PHASE_3_CLOUD_CONTROL_PLANE, "tiered-rate-limiting", "FREE tier defaults", "STARTER/PRO/ENTERPRISE/MASTER"),
    OpenCoreStepSpec(14, OpenCorePhase.PHASE_3_CLOUD_CONTROL_PLANE, "managed-worker-queues", "In-memory queue", "Redis Cluster + Durable Objects"),
    OpenCoreStepSpec(15, OpenCorePhase.PHASE_3_CLOUD_CONTROL_PLANE, "encrypted-key-vault", "Local dotenv storage", "KMS encrypted tenant keys"),
    OpenCoreStepSpec(16, OpenCorePhase.PHASE_4_ENTERPRISE_MONETIZATION, "multi-tenant-rbac-isolation", "Single local profile", "Tenant isolator + RBAC/SSO"),
    OpenCoreStepSpec(17, OpenCorePhase.PHASE_4_ENTERPRISE_MONETIZATION, "compliance-audit-ledger", "Stdout structured logs", "Immutable TT78/SOC2 vault"),
    OpenCoreStepSpec(18, OpenCorePhase.PHASE_4_ENTERPRISE_MONETIZATION, "always-on-cloud-daemon", "Foreground CLI run", "24/7 autonomous daemon + SLA"),
    OpenCoreStepSpec(19, OpenCorePhase.PHASE_4_ENTERPRISE_MONETIZATION, "strategy-recipe-marketplace", "Community recipes", "Verified alpha marketplace cut"),
    OpenCoreStepSpec(20, OpenCorePhase.PHASE_4_ENTERPRISE_MONETIZATION, "payment-webhook-activation", "PaymentProvider interface", "PayOS / NOWPayments / Polar IPN"),
    OpenCoreStepSpec(21, OpenCorePhase.PHASE_5_PLG_GROWTH_AND_GOVERNANCE, "sixty-second-quickstart", "git clone + mekong", "1-click cloud workspace"),
    OpenCoreStepSpec(22, OpenCorePhase.PHASE_5_PLG_GROWTH_AND_GOVERNANCE, "cli-to-cloud-upsell-prompt", "Quota warning banner", "Seamless recharge_url upgrade"),
    OpenCoreStepSpec(23, OpenCorePhase.PHASE_5_PLG_GROWTH_AND_GOVERNANCE, "ci-leak-and-loc-gate", "Pre-commit ruff + pytest", "Automated boundary enforcement"),
    OpenCoreStepSpec(24, OpenCorePhase.PHASE_5_PLG_GROWTH_AND_GOVERNANCE, "public-benchmark-trust-badge", "Reproducible test suite", "Enterprise trust verification"),
    OpenCoreStepSpec(25, OpenCorePhase.PHASE_5_PLG_GROWTH_AND_GOVERNANCE, "cla-and-trademark-policy", "Open PR contributions", "Protected brand & SaaS rights"),
)

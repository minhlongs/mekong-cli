"""Company Init Wizard — /company init backend.

5-question wizard that generates 12 config files for a new solo agentic company.
Supports both CLI (interactive) and API (dict input) modes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.core.mcu_gate import MCUGate

logger = logging.getLogger(__name__)

# Type aliases
Scenario = Literal["local_first", "hybrid", "api_only", "apple_silicon"]
BudgetTier = Literal["zero", "minimal", "hybrid", "unlimited"]
Language = Literal["vi", "en", "both"]
ProductType = Literal["saas", "digital", "api_service", "consulting"]

PRODUCT_MAP = {"1": "saas", "2": "digital", "3": "api_service", "4": "consulting"}
SCENARIO_MAP = {"1": "local_first", "2": "hybrid", "3": "api_only", "4": "apple_silicon"}
BUDGET_MAP = {"1": "zero", "2": "minimal", "3": "hybrid", "4": "unlimited"}
LANGUAGE_MAP = {"1": "vi", "2": "en", "3": "both"}

TIER_MCU_SEED = {"starter": 100, "growth": 500, "premium": 2000}

COST_ESTIMATES = {
    "local_first": "~$27/mo (Ollama only + minimal API)",
    "hybrid": "~$52-65/mo",
    "api_only": "~$145/mo",
    "apple_silicon": "~$35/mo (Metal acceleration)",
}


@dataclass
class CompanyConfig:
    """Wizard output — all 5 answers."""

    company_name: str
    product_type: ProductType
    scenario: Scenario
    budget_tier: BudgetTier
    primary_language: Language


def _resolve_model(scenario: str, role: str, tier: str) -> str:
    """Pick model for an agent role based on scenario."""
    local_available = scenario in ("local_first", "hybrid", "apple_silicon")

    routing: dict[str, dict[str, str]] = {
        "cto": {
            "complex": "claude-opus-4-6" if scenario != "local_first" else "ollama:deepseek-coder-v2:33b",
            "standard": "claude-sonnet-4-6",
            "simple": "claude-haiku-4-5",
        },
        "cmo": {"any": "gemini-2.0-flash"},
        "coo": {"any": "ollama:llama3.2:3b" if local_available else "claude-haiku-4-5"},
        "cfo": {"any": "ollama:qwen2.5:7b" if local_available else "gemini-2.0-flash"},
        "cs": {"any": "claude-haiku-4-5"},
        "sales": {"any": "claude-haiku-4-5"},
        "editor": {"any": "gemini-2.0-flash"},
        "data": {"any": "ollama:qwen2.5:7b" if local_available else "gemini-2.0-flash"},
    }
    return routing.get(role, {"any": "gemini-2.0-flash"})


# Agent prompt templates keyed by role
AGENT_PROMPTS: dict[str, str] = {
    "cto": (
        "You are the CTO of {company_name}.\n"
        "Language: {lang}\n"
        "Focus: Architecture, code quality, security, performance.\n"
        "Never create code with placeholders or TODOs.\n"
        "Always write tests for new functionality.\n"
        "Apply Jidoka: stop immediately if touching schema/auth/billing."
    ),
    "cmo": (
        "You are the CMO of {company_name}.\n"
        "Language: {lang}\n"
        "Focus: Marketing copy, brand voice, campaigns, SEO.\n"
        "Every piece of content must have a clear CTA.\n"
        "Tone: professional but approachable.\n"
        "Always write in the language specified by the task."
    ),
    "coo": (
        "You are the COO of {company_name}.\n"
        "Language: {lang}\n"
        "Focus: Operations, workflows, infra setup, process optimization.\n"
        "Apply Toyota TPS: minimize waste, standardize processes.\n"
        "Every operation must be idempotent and have rollback plan."
    ),
    "cfo": (
        "You are the CFO of {company_name}.\n"
        "Language: {lang}\n"
        "Focus: Revenue tracking, cost analysis, MCU billing reconciliation.\n"
        "Never share financial data with external APIs.\n"
        "Always include margin calculations in reports."
    ),
    "cs": (
        "You are the Customer Success Manager of {company_name}.\n"
        "Language: {lang}\n"
        "Focus: Customer support, retention, satisfaction.\n"
        "Response tone: empathetic, solution-focused, fast.\n"
        "Escalate to CTO if issue is technical. Escalate to CFO if billing dispute."
    ),
    "sales": (
        "You are the Sales Agent of {company_name}.\n"
        "Language: {lang}\n"
        "Focus: Lead nurturing, upsell, conversion.\n"
        "Never make promises that can't be delivered.\n"
        "Personalize every outreach based on usage data."
    ),
    "editor": (
        "You are the Content Editor of {company_name}.\n"
        "Language: {lang}\n"
        "Focus: Long-form writing, documentation, blog posts, newsletters.\n"
        "Maintain consistent voice across all content.\n"
        "Minimum 300 words for blog posts, 150 words for newsletters."
    ),
    "data": (
        "You are the Data Analyst of {company_name}.\n"
        "Language: {lang}\n"
        "Focus: Metrics, reporting, business intelligence.\n"
        "Always cite data sources. Never fabricate numbers.\n"
        "Every report ends with 3 actionable recommendations.\n"
        "Run locally — do not send raw data to external APIs."
    ),
}

AGENT_ROLES = list(AGENT_PROMPTS.keys())


def validate_config(config: CompanyConfig) -> list[str]:
    """Validate wizard answers. Returns list of error messages."""
    errors: list[str] = []
    if not config.company_name or not config.company_name.strip():
        errors.append("company_name is required")
    if config.product_type not in ("saas", "digital", "api_service", "consulting"):
        errors.append(f"Invalid product_type: {config.product_type}")
    if config.scenario not in ("local_first", "hybrid", "api_only", "apple_silicon"):
        errors.append(f"Invalid scenario: {config.scenario}")
    if config.budget_tier not in ("zero", "minimal", "hybrid", "unlimited"):
        errors.append(f"Invalid budget_tier: {config.budget_tier}")
    if config.primary_language not in ("vi", "en", "both"):
        errors.append(f"Invalid primary_language: {config.primary_language}")
    return errors


def generate_config_files(
    config: CompanyConfig,
    base_dir: str | Path = ".",
    mcu_gate: MCUGate | None = None,
) -> dict[str, str]:
    """Generate all 12 config files from wizard answers.

    Args:
        config: Validated CompanyConfig from wizard.
        base_dir: Project root directory.
        mcu_gate: Optional MCUGate for seeding balance (uses file fallback if None).

    Returns:
        Dict mapping relative file paths to their content.
    """
    errors = validate_config(config)
    if errors:
        raise ValueError(f"Invalid config: {'; '.join(errors)}")

    now = datetime.now(timezone.utc).isoformat()
    files: dict[str, str] = {}

    # File 1: .mekong/company.json
    company_json = {
        "company_name": config.company_name,
        "product_type": config.product_type,
        "scenario": config.scenario,
        "budget_tier": config.budget_tier,
        "primary_language": config.primary_language,
        "created_at": now,
        "version": "1.0",
    }
    files[".mekong/company.json"] = json.dumps(company_json, indent=2, ensure_ascii=False)

    # File 2: .openclaw/config.json
    openclaw_config = {
        "routing_rules": {},
        "fallback_chain": {
            "claude-opus-4-6": ["claude-sonnet-4-6", "gemini-2.0-flash"],
            "claude-sonnet-4-6": ["claude-haiku-4-5", "gemini-2.0-flash"],
            "ollama:llama3.2:3b": ["claude-haiku-4-5"],
        },
        "cost_override": {"budget_tier": config.budget_tier},
    }
    # Build per-role routing
    for role in AGENT_ROLES:
        openclaw_config["routing_rules"][role] = _resolve_model(
            config.scenario, role, ""
        )
    files[".openclaw/config.json"] = json.dumps(openclaw_config, indent=2, ensure_ascii=False)

    # Files 3-10: .mekong/agents/{role}.md
    lang = config.primary_language
    for role in AGENT_ROLES:
        template = AGENT_PROMPTS[role]
        content = template.format(company_name=config.company_name, lang=lang)
        files[f".mekong/agents/{role}.md"] = content

    # File 11: company section for CLAUDE.md
    claude_section = (
        f"# {config.company_name} — AgencyOS Configuration\n\n"
        f"## Company\n"
        f"- Name: {config.company_name}\n"
        f"- Product: {config.product_type}\n"
        f"- Language: {config.primary_language}\n"
        f"- LLM Scenario: {config.scenario}\n\n"
        f"## Active Agents\n"
        f"CTO · CMO · COO · CFO · CS · Sales · Editor · Data\n\n"
        f"## Rules\n"
        f"- All tasks route through hybrid_router\n"
        f"- MCU must be deducted for every agent execution\n"
        f"- Memory auto-saved after every successful task\n"
        f"- Jidoka: stop on schema/auth/billing changes\n"
    )
    files[".mekong/claude_company_section.md"] = claude_section

    # File 12: .mekong/mcu_balance.json
    mcu_balance = {
        "balance": TIER_MCU_SEED["starter"],
        "locked": 0,
        "lifetime_used": 0,
        "tier": "starter",
        "last_updated": now,
    }
    files[".mekong/mcu_balance.json"] = json.dumps(mcu_balance, indent=2)

    return files


def write_config_files(
    files: dict[str, str], base_dir: str | Path = "."
) -> list[str]:
    """Write generated config files to disk.

    Returns list of written file paths.
    """
    base = Path(base_dir)
    written: list[str] = []

    for rel_path, content in files.items():
        full_path = base / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        written.append(str(rel_path))
        logger.info("Written: %s", rel_path)

    return written


def seed_mcu_balance(
    tenant_id: str,
    tier: str = "starter",
    mcu_gate: MCUGate | None = None,
) -> int:
    """Seed initial MCU balance for a new tenant.

    Returns the amount seeded.
    """
    amount = TIER_MCU_SEED.get(tier, 100)

    if mcu_gate:
        mcu_gate.seed_balance(tenant_id, amount, reason=f"company_init_{tier}")

    return amount


def init_company(
    config: CompanyConfig,
    base_dir: str | Path = ".",
    mcu_gate: MCUGate | None = None,
    tenant_id: str = "default",
) -> dict:
    """Full init pipeline: validate → generate → write → seed MCU.

    Returns summary dict with all created files and MCU status.
    """
    # Check if already initialized
    base = Path(base_dir)
    company_file = base / ".mekong" / "company.json"
    if company_file.exists():
        existing = json.loads(company_file.read_text(encoding="utf-8"))
        raise FileExistsError(
            f"Company already setup: {existing.get('company_name', 'unknown')}. "
            f"Use --reset to reconfigure."
        )

    # Generate and write
    files = generate_config_files(config, base_dir, mcu_gate)
    written = write_config_files(files, base_dir)

    # Seed MCU
    mcu_seeded = seed_mcu_balance(tenant_id, "starter", mcu_gate)

    cost_est = COST_ESTIMATES.get(config.scenario, "unknown")

    return {
        "company_name": config.company_name,
        "scenario": config.scenario,
        "budget_tier": config.budget_tier,
        "primary_language": config.primary_language,
        "files_created": len(written),
        "files": written,
        "mcu_seeded": mcu_seeded,
        "cost_estimate": cost_est,
    }

"""Founder Legal — /founder legal backend.

Legal foundation kit: incorporation checklists (VN/US/SG), IP protection,
contract templates (ToS, Privacy, Contractor, Advisor), and compliance
checklists (GDPR, PDPA).

DISCLAIMER: Not legal advice. Always consult a licensed attorney.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

Jurisdiction = Literal["vietnam", "us_delaware", "singapore", "other"]
LegalStage = Literal["incorporation", "ip", "contracts", "compliance"]


# ── Data Models ──────────────────────────────────────────────────────


@dataclass
class ChecklistItem:
    """A single legal checklist item."""

    task: str
    priority: str  # high | medium | low
    cost: str = ""
    timeline: str = ""
    notes: str = ""
    done: bool = False


@dataclass
class IncorporationChecklist:
    """Incorporation checklist for a jurisdiction."""

    jurisdiction: Jurisdiction
    entity_type: str
    items: list[ChecklistItem]
    post_incorporation: list[ChecklistItem]


@dataclass
class IPChecklist:
    """IP protection checklist."""

    code_items: list[ChecklistItem]
    trademark_items: list[ChecklistItem]
    domain_items: list[ChecklistItem]
    trade_secret_items: list[ChecklistItem]


@dataclass
class ContractTemplate:
    """A contract template reference."""

    name: str
    type: str  # tos | privacy | contractor | advisor | employment
    sections: list[str]
    notes: str = ""


@dataclass
class ComplianceChecklist:
    """Compliance requirement checklist."""

    framework: str  # GDPR | PDPA | SOC2 | PCI
    items: list[ChecklistItem]
    when_needed: str


@dataclass
class LegalKit:
    """Complete legal foundation kit."""

    incorporation: IncorporationChecklist
    ip: IPChecklist
    contracts: list[ContractTemplate]
    compliance: list[ComplianceChecklist]
    disclaimer: str = (
        "All generated documents are STARTING POINTS only. "
        "Have a licensed attorney review before using."
    )


# ── Incorporation ────────────────────────────────────────────────────

JURISDICTION_CONFIGS: dict[Jurisdiction, dict] = {
    "vietnam": {
        "entity_type": "Cong ty TNHH MTV (1 member LLC)",
        "items": [
            ChecklistItem("Company name check (dangkykinhdoanh.gov.vn)", "high"),
            ChecklistItem("Office address (virtual ~500K VND/mo)", "high", "500K VND/mo"),
            ChecklistItem("Charter capital (recommend 100-500M VND)", "high"),
            ChecklistItem("Business registration code selection", "high"),
            ChecklistItem("Registration documents (CCCD + forms)", "high"),
            ChecklistItem("Submit to Dept of Planning & Investment", "high", "~1M VND", "3-5 business days"),
            ChecklistItem("Open business bank account", "high", "", "After registration"),
        ],
    },
    "us_delaware": {
        "entity_type": "Delaware C-Corp",
        "items": [
            ChecklistItem("Stripe Atlas registration", "high", "$500 all-in"),
            ChecklistItem("EIN application at IRS.gov", "high", "Free", "After incorporation"),
            ChecklistItem("Registered agent setup", "high", "~$50/yr (included in Atlas)"),
            ChecklistItem("83(b) election filing", "high", "Free", "Within 30 days of equity"),
            ChecklistItem("Bank account (Mercury/Brex)", "high", "Free", "After EIN"),
        ],
    },
    "singapore": {
        "entity_type": "Singapore Pte Ltd",
        "items": [
            ChecklistItem("Nominee director (if no SG resident)", "high", "~SGD 2K/yr"),
            ChecklistItem("ACRA filing", "high", "~SGD 300"),
            ChecklistItem("Corppass digital filing setup", "medium"),
            ChecklistItem("Bank account (DBS/OCBC/Aspire)", "high", "", "After registration"),
        ],
    },
    "other": {
        "entity_type": "Local LLC equivalent",
        "items": [
            ChecklistItem("Research local entity types", "high"),
            ChecklistItem("Consult local attorney", "high"),
            ChecklistItem("Register business", "high"),
            ChecklistItem("Open business bank account", "high"),
        ],
    },
}

POST_INCORPORATION_UNIVERSAL = [
    ChecklistItem("Founders agreement signed", "high"),
    ChecklistItem("IP assignment agreement signed by all founders", "high"),
    ChecklistItem("Vesting schedule: 4-year, 1-year cliff", "high"),
    ChecklistItem("Cap table created (Carta free tier or spreadsheet)", "medium"),
]


def build_incorporation_checklist(
    jurisdiction: Jurisdiction,
) -> IncorporationChecklist:
    """Build incorporation checklist for jurisdiction."""
    config = JURISDICTION_CONFIGS.get(jurisdiction, JURISDICTION_CONFIGS["other"])

    return IncorporationChecklist(
        jurisdiction=jurisdiction,
        entity_type=config["entity_type"],
        items=[ChecklistItem(**i) if isinstance(i, dict) else i for i in config["items"]],
        post_incorporation=list(POST_INCORPORATION_UNIVERSAL),
    )


# ── IP Protection ────────────────────────────────────────────────────


def build_ip_checklist() -> IPChecklist:
    """Build IP protection checklist."""
    return IPChecklist(
        code_items=[
            ChecklistItem("All code in private repo", "high"),
            ChecklistItem(".gitignore protects secrets", "high"),
            ChecklistItem("No personal paths in code", "medium"),
            ChecklistItem("License chosen: MIT / Proprietary / Dual", "high"),
            ChecklistItem("All contributors signed IP assignment", "high"),
        ],
        trademark_items=[
            ChecklistItem("Search USPTO.gov (US) / IP Vietnam / IPOS (SG)", "medium"),
            ChecklistItem("File trademark when revenue > $5K/mo", "low", "$250-350/class (US)"),
            ChecklistItem("File in primary market first", "medium", "", "8-12 months to registration"),
        ],
        domain_items=[
            ChecklistItem("Primary .com registered", "high", "~$10/yr"),
            ChecklistItem("Defensive: .io, .co, .ai registrations", "low", "$10-50/yr each"),
            ChecklistItem("Privacy protection enabled (WHOIS)", "medium"),
        ],
        trade_secret_items=[
            ChecklistItem("NDA for all employees/contractors before code access", "high"),
            ChecklistItem("IP assignment for all employees/contractors", "high"),
            ChecklistItem("Customer data access logged and limited", "medium"),
        ],
    )


# ── Contracts ────────────────────────────────────────────────────────


def build_contract_templates() -> list[ContractTemplate]:
    """Build contract template references."""
    return [
        ContractTemplate(
            "Terms of Service", "tos",
            [
                "Acceptable use policy",
                "Payment + refund terms",
                "Data ownership (customer owns their data)",
                "Limitation of liability",
                "Dispute resolution",
            ],
            "Required for any SaaS product",
        ),
        ContractTemplate(
            "Privacy Policy", "privacy",
            [
                "What data you collect",
                "How you use it",
                "Who you share with (disclose LLM providers!)",
                "Retention period",
                "User rights (access, delete, export)",
                "Contact for data requests",
            ],
            "Required for any user data collection. Disclose AI provider usage.",
        ),
        ContractTemplate(
            "Contractor Agreement", "contractor",
            [
                "Scope of work",
                "Payment terms",
                "IP assignment (all work belongs to company)",
                "Confidentiality",
                "Termination clause",
            ],
        ),
        ContractTemplate(
            "Advisor Agreement", "advisor",
            [
                "Equity: 0.1-0.5%, 2-year vest, no cliff",
                "FAST agreement (standard Silicon Valley)",
                "Scope of advisory services",
                "Term and termination",
            ],
        ),
        ContractTemplate(
            "Employment Offer Letter", "employment",
            [
                "Job title + description",
                "Salary + bonus structure",
                "Start date",
                "Probation period (typically 60 days)",
                "Reference to company internal policies",
                "NDA + IP assignment attached",
            ],
            "For Vietnam: must include probation details per labor code",
        ),
    ]


# ── Compliance ───────────────────────────────────────────────────────


def build_compliance_checklists() -> list[ComplianceChecklist]:
    """Build compliance checklists for common frameworks."""
    return [
        ComplianceChecklist(
            "GDPR",
            [
                ChecklistItem("Privacy policy updated", "high"),
                ChecklistItem("Cookie consent banner implemented", "high"),
                ChecklistItem("Data processing agreements with sub-processors", "high"),
                ChecklistItem("Right to be forgotten process documented", "medium"),
                ChecklistItem("DPO designated or documented why not required", "medium"),
                ChecklistItem("Breach notification process (72h to authority)", "high"),
            ],
            "When serving EU users",
        ),
        ComplianceChecklist(
            "PDPA Vietnam (Nghi dinh 13/2023)",
            [
                ChecklistItem("Privacy policy in Vietnamese", "high"),
                ChecklistItem("Consent collection documented", "high"),
                ChecklistItem("Data localization considered", "medium"),
                ChecklistItem("Breach notification within 72h", "high"),
            ],
            "When operating in Vietnam or processing VN user data",
        ),
        ComplianceChecklist(
            "SOC 2",
            [
                ChecklistItem("Document security policies", "low"),
                ChecklistItem("Access controls documented", "low"),
                ChecklistItem("Logging and monitoring setup", "low"),
            ],
            "When enterprise customers require it (~$100K ARR)",
        ),
        ComplianceChecklist(
            "PCI DSS",
            [
                ChecklistItem("Don't store raw card data — use Stripe/Polar", "high"),
                ChecklistItem("Compliance inherited from payment processor", "high"),
            ],
            "If handling payment data (usually handled by processor)",
        ),
        ComplianceChecklist(
            "General Security",
            [
                ChecklistItem("All API keys in env vars, not in code", "high"),
                ChecklistItem("All secrets in .env not committed to git", "high"),
                ChecklistItem("Database backups automated", "high"),
                ChecklistItem("Employee/contractor offboarding process", "medium"),
                ChecklistItem("2FA on all critical services", "high"),
                ChecklistItem("Incident response plan documented", "medium"),
            ],
            "Always — baseline security for any startup",
        ),
    ]


# ── Full Kit Assembly ────────────────────────────────────────────────


def build_legal_kit(
    jurisdiction: Jurisdiction = "vietnam",
) -> LegalKit:
    """Build complete legal foundation kit."""
    return LegalKit(
        incorporation=build_incorporation_checklist(jurisdiction),
        ip=build_ip_checklist(),
        contracts=build_contract_templates(),
        compliance=build_compliance_checklists(),
    )


# ── File I/O ─────────────────────────────────────────────────────────


def save_legal_kit(base_dir: str, kit: LegalKit) -> list[str]:
    """Save legal kit to .mekong/legal/."""
    legal_dir = Path(base_dir) / ".mekong" / "legal"
    legal_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []

    # Incorporation
    path = legal_dir / "incorporation-checklist.json"
    path.write_text(json.dumps(asdict(kit.incorporation), indent=2, ensure_ascii=False))
    saved.append(str(path))

    # IP
    path = legal_dir / "ip-checklist.json"
    path.write_text(json.dumps(asdict(kit.ip), indent=2, ensure_ascii=False))
    saved.append(str(path))

    # Contracts
    contracts_dir = legal_dir / "contracts"
    contracts_dir.mkdir(exist_ok=True)
    for contract in kit.contracts:
        slug = contract.type.replace(" ", "-")
        path = contracts_dir / f"{slug}-template.json"
        path.write_text(json.dumps(asdict(contract), indent=2, ensure_ascii=False))
        saved.append(str(path))

    # Compliance
    path = legal_dir / "compliance-checklist.json"
    path.write_text(json.dumps(
        [asdict(c) for c in kit.compliance],
        indent=2, ensure_ascii=False,
    ))
    saved.append(str(path))

    return saved

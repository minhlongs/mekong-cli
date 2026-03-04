"""
🧬 Agency DNA Engine
===================

Core logic for managing agency identity, voice, and service catalog.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from typing_extensions import TypedDict

from .models import PricingTier, Service, Tone

# Configure logging
logger = logging.getLogger(__name__)


class AgencyIdentityDict(TypedDict):
    name: str
    niche: str
    location: str
    tagline: str
    voice: str


class AgencyConfigDict(TypedDict):
    tone: str
    tier: str
    capabilities: List[str]


class AgencyServiceDict(TypedDict):
    name: str
    price_usd: float
    price_vnd: int
    duration: int


class AgencyDNADict(TypedDict):
    """Full serialized representation of Agency DNA"""
    identity: AgencyIdentityDict
    configuration: AgencyConfigDict
    services: List[AgencyServiceDict]
    contact: Dict[str, str]


@dataclass
class AgencyDNA:
    """
    🧬 Agency DNA

    The single source of truth for agency identity.
    Used by AI agents to personalize content, proposals, and communication.
    """

    name: str = "Unicorn Agency"
    niche: str = "Full-stack Automation"
    location: str = "Ho Chi Minh City"
    region: str = "South"
    tone: Tone = Tone.FRIENDLY
    tier: PricingTier = PricingTier.GROWTH

    # Core specializations
    capabilities: List[str] = field(default_factory=lambda: ["AI Automation", "Lead Gen"])

    # Service Catalog
    services: List[Service] = field(default_factory=list)

    # Contact & Identity
    contact: Dict[str, str] = field(
        default_factory=lambda: {
            "email": "",
            "phone": "",
            "website": "",
            "zalo": "",
            "telegram": "",
        }
    )

    # Social Handles
    social: Dict[str, str] = field(default_factory=dict)

    def add_service(
        self, name: str, description: str, price_usd: float, duration: int = 7
    ) -> Service:
        """Appends a new service to the agency's catalog."""
        service = Service(
            name=name, description=description, price_usd=price_usd, duration_days=duration
        )
        self.services.append(service)
        logger.info(f"Service added to DNA: {name} (${price_usd})")
        return service

    def get_localized_voice(self) -> str:
        """Returns a description of the agent's voice for prompting."""
        profiles = {
            Tone.MIEN_TAY: "Chân thành, mộc mạc, dùng từ ngữ ấm áp như 'nghen', 'hen', 'tui'.",
            Tone.MIEN_BAC: "Trang trọng, chỉn chu, lễ phép, dùng từ 'vâng', 'ạ', 'xin phép'.",
            Tone.MIEN_TRUNG: "Thẳng thắn, kiên cường, mộc mạc, đậm chất miền Trung.",
            Tone.FRIENDLY: "Modern, approachable, and supportive tone.",
            Tone.PROFESSIONAL: "Authoritative, data-driven, and corporate tone.",
        }
        return profiles.get(self.tone, "Standard professional tone.")

    def get_tagline(self) -> str:
        """Generates a contextual tagline for marketing materials."""
        if self.tone == Tone.MIEN_TAY:
            return f"Đồng hành cùng {self.niche} - Trọn tình miền Tây"
        elif self.tone == Tone.MIEN_BAC:
            return f"Giải pháp {self.niche} tinh hoa - Đẳng cấp Thủ đô"
        elif self.tone == Tone.MIEN_TRUNG:
            return f"{self.niche} bền vững - Vững chãi miền Trung"

        return f"Elite {self.niche} Experts | {self.location}"

    def to_dict(self) -> AgencyDNADict:
        """Serializable dictionary for frontend and agent injection."""
        return {
            "identity": {
                "name": self.name,
                "niche": self.niche,
                "location": self.location,
                "tagline": self.get_tagline(),
                "voice": self.get_localized_voice(),
            },
            "configuration": {
                "tone": self.tone.value,
                "tier": self.tier.value,
                "capabilities": self.capabilities,
            },
            "services": [
                {
                    "name": s.name,
                    "price_usd": s.price_usd,
                    "price_vnd": s.price_vnd,
                    "duration": s.duration_days,
                }
                for s in self.services
            ],
            "contact": self.contact,
        }


def create_starter_dna(agency_name: str, niche: str) -> AgencyDNA:
    """Factory for bootstrapping a new agency DNA."""
    dna = AgencyDNA(name=agency_name, niche=niche)
    dna.add_service("MVP Launch", "Quick market validation", 499.0, 14)
    dna.add_service("Agency OS Setup", "Full automation implementation", 1999.0, 30)
    return dna

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Founder Genome Model - Encrypted founder profile data for AI analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class FounderGenome:
    """Model for storing encrypted founder genome data.

    The genome captures a founder's:
    - Risk tolerance and decision patterns
    - Leadership style and team dynamics
    - Growth philosophy and execution approach
    - Market context and competitive positioning
    - Financial behavior and capital strategy
    """

    id: Optional[int] = None
    founder_id: str = ""  # Unique identifier (email or UUID)
    encrypted_data: bytes = b""  # AES-256-GCM encrypted JSON payload
    encryption_key_id: str = ""  # Key identifier for rotation
    genome_hash: str = ""  # SHA-256 hash of raw data for deduplication
    analysis_summary: Optional[str] = None  # AI-generated insights
    confidence_score: Optional[float] = None  # 0.00-1.00
    trait_scores: Dict[str, float] = field(default_factory=dict)  # Extracted traits
    cluster_id: Optional[int] = None  # For similarity grouping
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Raw genome fields (stored unencrypted in encrypted_data)
    raw_genome: Optional[Dict[str, Any]] = field(default=None, repr=False)

    # Genome trait definitions
    TRAIT_DEFINITIONS = {
        "risk_tolerance": "Willingness to take calculated risks (0-1)",
        "execution_speed": "Bias toward rapid iteration vs. careful planning (0-1)",
        "capital_efficiency": "Ability to achieve more with less capital (0-1)",
        "vision_clarity": "Clarity and persuasiveness of long-term vision (0-1)",
        "team_building": "Skill at recruiting, retaining, and elevating talent (0-1)",
        "customer_obsession": "Depth of customer understanding and empathy (0-1)",
        "adaptability": "Ability to pivot and learn from failure (0-1)",
        "resilience": "Capacity to endure setbacks and pressure (0-1)",
        "strategic_thinking": "Ability to see patterns and plan multiple moves ahead (0-1)",
        "founder_market_fit": "Alignment between founder skills and market needs (0-1)",
    }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FounderGenome":
        """Create FounderGenome from database row dict."""
        return cls(
            id=data.get("id"),
            founder_id=data["founder_id"],
            encrypted_data=data.get("encrypted_data", b""),
            encryption_key_id=data.get("encryption_key_id", ""),
            genome_hash=data.get("genome_hash", ""),
            analysis_summary=data.get("analysis_summary"),
            confidence_score=float(data["confidence_score"]) if data.get("confidence_score") is not None else None,
            trait_scores=data.get("trait_scores") or {},
            cluster_id=data.get("cluster_id"),
            created_at=data.get("created_at") or datetime.utcnow(),
            updated_at=data.get("updated_at") or datetime.utcnow(),
        )

    def to_dict(self, include_encrypted: bool = True) -> Dict[str, Any]:
        """Convert FounderGenome to dict for database operations."""
        result: Dict[str, Any] = {
            "founder_id": self.founder_id,
            "encryption_key_id": self.encryption_key_id,
            "genome_hash": self.genome_hash,
            "analysis_summary": self.analysis_summary,
            "confidence_score": self.confidence_score,
            "trait_scores": self.trait_scores,
            "cluster_id": self.cluster_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_encrypted:
            result["encrypted_data"] = self.encrypted_data
        return result

    def get_trait(self, trait_name: str, default: float = 0.5) -> float:
        """Get a specific trait score."""
        return self.trait_scores.get(trait_name, default)

    def set_trait(self, trait_name: str, value: float) -> None:
        """Set a trait score (clamped 0-1)."""
        self.trait_scores[trait_name] = max(0.0, min(1.0, value))

    def dominant_traits(self, top_n: int = 3) -> List[tuple[str, float]]:
        """Get the top N dominant traits."""
        sorted_traits = sorted(
            self.trait_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_traits[:top_n]

    def is_complete_profile(self) -> bool:
        """Check if all trait definitions have been scored."""
        return all(trait in self.trait_scores for trait in self.TRAIT_DEFINITIONS)

    def overall_rating(self) -> float:
        """Calculate overall founder rating from trait scores."""
        if not self.trait_scores:
            return 0.0
        # Weighted average - core traits have higher weight
        weights = {
            "founder_market_fit": 1.5,
            "execution_speed": 1.2,
            "adaptability": 1.2,
            "resilience": 1.2,
            "customer_obsession": 1.0,
            "team_building": 1.0,
            "vision_clarity": 1.0,
            "strategic_thinking": 1.0,
            "capital_efficiency": 0.9,
            "risk_tolerance": 0.8,
        }
        weighted_sum = sum(
            self.trait_scores.get(trait, 0) * weights.get(trait, 1.0)
            for trait in self.TRAIT_DEFINITIONS
        )
        total_weight = sum(weights.get(trait, 1.0) for trait in self.TRAIT_DEFINITIONS)
        return weighted_sum / total_weight if total_weight > 0 else 0.0


@dataclass
class GenomeAnalysisRequest:
    """Request structure for AI genome analysis."""

    founder_id: str
    raw_responses: Dict[str, Any]  # Raw questionnaire/input data
    analysis_type: str = "full"  # full, quick, traits_only
    include_recommendations: bool = True
    context: Optional[Dict[str, Any]] = None  # Industry, stage, etc.

    def to_prompt_context(self) -> str:
        """Convert request to context string for LLM prompt."""
        context_lines = [f"Founder ID: {self.founder_id}"]
        if self.context:
            for key, value in self.context.items():
                context_lines.append(f"{key.replace('_', ' ').title()}: {value}")
        context_lines.append("\nResponses:")
        for key, value in self.raw_responses.items():
            context_lines.append(f"- {key}: {value}")
        return "\n".join(context_lines)


@dataclass
class GenomeMatch:
    """Result of finding similar founders."""

    founder_genome: FounderGenome
    similarity_score: float  # 0.0-1.0
    matching_traits: List[str]
    divergent_traits: List[str]
    insights: str

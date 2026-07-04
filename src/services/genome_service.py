"""Founder Genome Service - Storage, encryption, and AI analysis for founder profiles."""

from __future__ import annotations

import json
import hashlib
import hmac
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import asdict
import asyncio

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

from src.models.founder_genome import FounderGenome, GenomeAnalysisRequest, GenomeMatch

logger = __import__("logging").getLogger(__name__)


class GenomeServiceError(Exception):
    """Base exception for genome service errors."""
    pass


class EncryptionError(GenomeServiceError):
    """Encryption/decryption error."""
    pass


class GenomeNotFoundError(GenomeServiceError):
    """Genome not found error."""
    pass


class FounderGenomeRepository:
    """Repository for storing and retrieving founder genomes with encryption."""

    # AI Analysis Prompts
    ANALYSIS_PROMPTS = {
        "full_analysis": """
You are a founder genome analyst. Analyze the following founder profile data and provide:

1. EXECUTIVE SUMMARY (2-3 paragraphs)
   - Overall founder profile and strengths
   - Key patterns in decision-making
   - Primary growth opportunities

2. TRAIT SCORES (normalized 0-1)
   For each trait, score based on responses:
   - risk_tolerance: Willingness to take calculated risks
   - execution_speed: Bias toward rapid iteration vs. careful planning
   - capital_efficiency: Ability to achieve more with less capital
   - vision_clarity: Clarity and persuasiveness of long-term vision
   - team_building: Skill at recruiting, retaining, and elevating talent
   - customer_obsession: Depth of customer understanding
   - adaptability: Ability to pivot and learn from failure
   - resilience: Capacity to endure setbacks
   - strategic_thinking: Ability to see patterns and plan ahead
   - founder_market_fit: Alignment between founder skills and market

3. CLUSTER ASSIGNMENT
   Which founder cluster does this profile match?
   - Serial Entrepreneur (high execution, high resilience)
   - Visionary (high vision clarity, high strategic thinking)
   - Operator (high capital efficiency, high team building)
   - Experimenter (high adaptability, medium risk tolerance)
   - Specialist (high founder-market fit, niche focus)
   - Challenger (high risk tolerance, high resilience)

4. CONFIDENCE SCORE (0.00-1.00)
   How confident are you in this analysis based on data completeness?

5. KEY INSIGHTS
   - 3-5 specific, actionable observations
   - Potential blind spots or risks
   - Recommended focus areas

6. MATCHES AND COMPLEMENTARY TRAITS
   - Which founder types would complement this founder?
   - What co-founder qualities would balance weaknesses?

Format response as JSON:
{
    "executive_summary": "...",
    "trait_scores": {"risk_tolerance": 0.xx, ...},
    "cluster": "Cluster Name",
    "confidence": 0.xx,
    "insights": ["...", "..."],
    "complementary_founders": ["type1", "type2"],
    "blind_spots": ["...", "..."]
}
""",

        "quick_traits": """
Extract trait scores from founder responses. Score each 0-1 based on evidence:

Traits to score (be conservative, default to 0.5):
- risk_tolerance
- execution_speed
- capital_efficiency
- vision_clarity
- team_building
- customer_obsession
- adaptability
- resilience
- strategic_thinking
- founder_market_fit

For each score, provide a brief justification (1-2 sentences).

Respond with JSON only:
{
    "trait_scores": {"trait_name": 0.xx, ...},
    "justifications": {"trait_name": "explanation", ...},
    "data_completeness": 0.xx
}
""",

        "cluster_analysis": """
Given these trait scores, determine the founder cluster:

Clusters:
1. Serial Entrepreneur: execution_speed > 0.7, resilience > 0.7, multiple_ventures = true
2. Visionary: vision_clarity > 0.8, strategic_thinking > 0.7, market_size_focus = true
3. Operator: capital_efficiency > 0.7, team_building > 0.7, operations_experience = true
4. Experimenter: adaptability > 0.8, risk_tolerance 0.4-0.7, pivots >= 2
5. Specialist: founder_market_fit > 0.8, domain_experience >= 5 years
6. Challenger: risk_tolerance > 0.8, resilience > 0.8, competitive_background = true

Respond with JSON:
{
    "cluster": "Cluster Name",
    "cluster_description": "...",
    "match_confidence": 0.xx,
    "alternative_clusters": [{"name": "...", "confidence": 0.xx}],
    "key_indicators": ["...", "..."]
}
""",

        "recommendations": """
Based on this founder's genome profile, provide specific recommendations for:

1. CO-FOUNDER MATCHES
   - 2-3 ideal co-founder archetypes to balance gaps
   - Specific traits each would bring

2. INVESTOR FIT
   - Which investor types would align best?
   - What signals should they highlight?

3. HIRING PRIORITIES
   - First 10 hires: what roles and why?
   - Traits to look for in early team

4. GROWTH STRATEGY
   - Organic vs. paid growth recommendation
   - Market entry approach (niche-first vs. broad)
   - Capital strategy (bootstrap vs. raise)

5. RISK MITIGATION
   - Top 3 risks based on trait profile
   - Specific mitigations for each

Respond with JSON:
{
    "cofounder_matches": [{"archetype": "...", "balances": ["..."]}],
    "investor_fit": ["...", "..."],
    "hiring_priorities": [{"role": "...", "reason": "..."}],
    "growth_strategy": {"approach": "...", "rationale": "..."},
    "risk_mitigations": [{"risk": "...", "mitigation": "..."}]
}
""",

        "similarity_search": """
You are a founder similarity matcher. Given a target founder's trait scores and a list of other founders, calculate similarity scores.

Consider:
- Direct trait score differences (Euclidean distance)
- Cluster alignment (same cluster = +0.2 bonus)
- Complementary trait patterns (high resilience + high adaptability = synergy)

For each candidate, provide:
- similarity_score (0.0-1.0)
- matching_traits (traits where both > 0.7 or both < 0.3)
- divergent_traits (traits with > 0.5 difference)
- partnership_insight (brief note on potential dynamics)

Respond with JSON array:
[
    {
        "founder_id": "...",
        "similarity_score": 0.xx,
        "matching_traits": ["...", "..."],
        "divergent_traits": ["...", "..."],
        "partnership_insight": "..."
    }
]
""",
    }

    def __init__(self, config_dir: Optional[Path] = None, use_aesgcm: bool = False):
        """
        Initialize genome repository.

        Args:
            config_dir: Directory for storing encryption keys and data
            use_aesgcm: Use AES-256-GCM instead of Fernet (more secure but less portable)
        """
        self.config_dir = config_dir or (Path.home() / ".mekong" / "genomes")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self.config_dir / "data"
        self.data_dir.mkdir(exist_ok=True)

        self.use_aesgcm = use_aesgcm
        self._init_encryption_key()

    def _init_encryption_key(self) -> None:
        """Initialize or load encryption key."""
        if self.use_aesgcm:
            # AES-256-GCM requires 32-byte key
            key_file = self.config_dir / ".aesgcm_key"
        else:
            # Fernet uses 32-byte base64-encoded key
            key_file = self.config_dir / ".fernet_key"

        if key_file.exists():
            self.encryption_key = key_file.read_bytes()
        else:
            if self.use_aesgcm:
                self.encryption_key = secrets.token_bytes(32)
            else:
                self.encryption_key = Fernet.generate_key()
            key_file.write_bytes(self.encryption_key)
            os.chmod(key_file, 0o600)

        logger.debug("Encryption key initialized at %s", key_file)

    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of genome data for deduplication."""
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _encrypt(self, data: Dict[str, Any]) -> bytes:
        """Encrypt genome data."""
        try:
            json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

            if self.use_aesgcm:
                # AES-256-GCM: 12-byte nonce + ciphertext + 16-byte tag
                nonce = secrets.token_bytes(12)
                aesgcm = AESGCM(self.encryption_key)
                ciphertext = aesgcm.encrypt(nonce, json_data, None)
                return nonce + ciphertext
            else:
                # Fernet: URL-safe base64, includes timestamp and IV
                fernet = Fernet(self.encryption_key)
                return fernet.encrypt(json_data)
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}") from e

    def _decrypt(self, ciphertext: bytes) -> Dict[str, Any]:
        """Decrypt genome data."""
        try:
            if self.use_aesgcm:
                nonce = ciphertext[:12]
                encrypted_data = ciphertext[12:]
                aesgcm = AESGCM(self.encryption_key)
                decrypted = aesgcm.decrypt(nonce, encrypted_data, None)
            else:
                fernet = Fernet(self.encryption_key)
                decrypted = fernet.decrypt(ciphertext)

            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}") from e

    async def save_genome_async(
        self,
        founder_id: str,
        raw_genome: Dict[str, Any],
        analysis_summary: Optional[str] = None,
        confidence_score: Optional[float] = None,
        trait_scores: Optional[Dict[str, float]] = None,
        cluster_id: Optional[int] = None,
    ) -> FounderGenome:
        """
        Save a founder genome with encryption (async).

        Args:
            founder_id: Unique founder identifier
            raw_genome: Raw genome data (will be encrypted)
            analysis_summary: AI-generated analysis
            confidence_score: AI confidence 0.00-1.00
            trait_scores: Extracted trait scores
            cluster_id: Cluster assignment for similarity search

        Returns:
            Saved FounderGenome instance
        """
        # Calculate hash for deduplication
        genome_hash = self._calculate_hash(raw_genome)

        # Encrypt the data
        encrypted_data = self._encrypt(raw_genome)

        # Generate key identifier for rotation support
        key_id = hashlib.sha256(self.encryption_key).hexdigest()[:16]

        # Create genome record
        genome = FounderGenome(
            founder_id=founder_id,
            encrypted_data=encrypted_data,
            encryption_key_id=key_id,
            genome_hash=genome_hash,
            analysis_summary=analysis_summary,
            confidence_score=confidence_score,
            trait_scores=trait_scores or {},
            cluster_id=cluster_id,
            raw_genome=raw_genome,
        )

        # Save to database
        await self._save_to_database_async(genome)

        logger.info("Saved genome for founder %s (hash: %s)", founder_id, genome_hash[:16])
        return genome

    async def _save_to_database_async(self, genome: FounderGenome) -> None:
        """Save genome to PostgreSQL database (async)."""
        try:
            from src.db.repository import get_general_repository
            repo = get_general_repository()

            # Convert to dict for database
            data = genome.to_dict(include_encrypted=True)

            # Check if exists
            existing = await repo.fetch_one(
                "SELECT id FROM founder_genomes WHERE founder_id = $1",
                (genome.founder_id,)
            )

            if existing:
                # Update
                await repo.execute(
                    """
                    UPDATE founder_genomes SET
                        encrypted_data = $1,
                        encryption_key_id = $2,
                        genome_hash = $3,
                        analysis_summary = $4,
                        confidence_score = $5,
                        trait_scores = $6,
                        cluster_id = $7,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE founder_id = $8
                    """,
                    (
                        data["encrypted_data"],
                        data["encryption_key_id"],
                        data["genome_hash"],
                        data["analysis_summary"],
                        data["confidence_score"],
                        json.dumps(data["trait_scores"]),
                        data["cluster_id"],
                        genome.founder_id,
                    )
                )
                genome.id = existing["id"]
            else:
                # Insert
                result = await repo.fetch_one(
                    """
                    INSERT INTO founder_genomes
                    (founder_id, encrypted_data, encryption_key_id, genome_hash,
                     analysis_summary, confidence_score, trait_scores, cluster_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                    """,
                    (
                        genome.founder_id,
                        data["encrypted_data"],
                        data["encryption_key_id"],
                        data["genome_hash"],
                        data["analysis_summary"],
                        data["confidence_score"],
                        json.dumps(data["trait_scores"]),
                        data["cluster_id"],
                    )
                )
                genome.id = result["id"] if result else None

            logger.debug("Saved genome %s to database", genome.id)

        except Exception as e:
            logger.error("Failed to save genome to database: %s", e)
            raise GenomeServiceError(f"Database save failed: {e}") from e

    async def load_genome_async(self, founder_id: str) -> Optional[FounderGenome]:
        """
        Load and decrypt a founder genome (async).

        Args:
            founder_id: Founder identifier

        Returns:
            FounderGenome if found, None otherwise
        """
        try:
            from src.db.repository import get_general_repository
            repo = get_general_repository()

            row = await repo.fetch_one(
                "SELECT * FROM founder_genomes WHERE founder_id = $1",
                (founder_id,)
            )

            if not row:
                return None

            # Decrypt the data
            decrypted_data = self._decrypt(row["encrypted_data"])

            # Create genome with raw data
            genome = FounderGenome.from_dict(dict(row))
            genome.raw_genome = decrypted_data

            # If trait_scores is empty, try to extract from decrypted data
            if not genome.trait_scores and "trait_scores" in decrypted_data:
                genome.trait_scores = decrypted_data["trait_scores"]

            return genome

        except EncryptionError as e:
            logger.error("Failed to decrypt genome for %s: %s", founder_id, e)
            raise
        except Exception as e:
            logger.error("Failed to load genome for %s: %s", founder_id, e)
            raise GenomeServiceError(f"Load failed: {e}") from e

    async def find_similar_genomes_async(
        self,
        trait_scores: Dict[str, float],
        limit: int = 10,
        exclude_founder_id: Optional[str] = None
    ) -> List[GenomeMatch]:
        """
        Find genomes with similar trait profiles (async).

        Args:
            trait_scores: Target trait scores to match
            limit: Maximum number of matches to return
            exclude_founder_id: Exclude this founder from results

        Returns:
            List of GenomeMatch sorted by similarity
        """
        try:
            from src.db.repository import get_general_repository
            repo = get_general_repository()

            # Load all genomes with trait scores
            rows = await repo.fetch_all(
                """
                SELECT id, founder_id, trait_scores, cluster_id, analysis_summary
                FROM founder_genomes
                WHERE trait_scores IS NOT NULL
                """
            )

            matches = []
            for row in rows:
                if exclude_founder_id and row["founder_id"] == exclude_founder_id:
                    continue

                other_traits = row.get("trait_scores") or {}

                # Calculate Euclidean distance-based similarity
                all_traits = set(trait_scores.keys()) | set(other_traits.keys())
                if not all_traits:
                    continue

                squared_diff = 0
                for trait in all_traits:
                    score1 = trait_scores.get(trait, 0.5)
                    score2 = other_traits.get(trait, 0.5)
                    squared_diff += (score1 - score2) ** 2

                # Normalize to 0-1 (1 = identical)
                max_distance = (len(all_traits) * 1.0) ** 0.5
                similarity = 1.0 - (squared_diff ** 0.5 / max_distance if max_distance > 0 else 0)

                # Cluster bonus
                cluster_bonus = 0.1 if row.get("cluster_id") else 0

                final_score = min(1.0, similarity + cluster_bonus)

                if final_score > 0.3:  # Only include meaningful matches
                    match = GenomeMatch(
                        founder_genome=FounderGenome(
                            id=row["id"],
                            founder_id=row["founder_id"],
                            trait_scores=other_traits,
                            cluster_id=row.get("cluster_id"),
                            analysis_summary=row.get("analysis_summary"),
                        ),
                        similarity_score=final_score,
                        matching_traits=[
                            t for t in all_traits
                            if abs(trait_scores.get(t, 0.5) - other_traits.get(t, 0.5)) < 0.2
                        ],
                        divergent_traits=[
                            t for t in all_traits
                            if abs(trait_scores.get(t, 0.5) - other_traits.get(t, 0.5)) > 0.5
                        ],
                        insights=row.get("analysis_summary", "")[:200],
                    )
                    matches.append(match)

            # Sort by similarity
            matches.sort(key=lambda m: m.similarity_score, reverse=True)
            return matches[:limit]

        except Exception as e:
            logger.error("Similarity search failed: %s", e)
            return []

    async def get_all_genomes_async(
        self,
        limit: Optional[int] = None
    ) -> List[FounderGenome]:
        """Load all genomes (async)."""
        try:
            from src.db.repository import get_general_repository
            repo = get_general_repository()

            query = "SELECT * FROM founder_genomes ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"

            rows = await repo.fetch_all(query)

            genomes = []
            for row in rows:
                genome = FounderGenome.from_dict(dict(row))
                try:
                    # Decrypt for raw data
                    genome.raw_genome = self._decrypt(row["encrypted_data"])
                except Exception as e:
                    logger.warning("Could not decrypt genome %s: %s", row["id"], e)
                genomes.append(genome)

            return genomes

        except Exception as e:
            logger.error("Failed to load genomes: %s", e)
            return []

    async def delete_genome_async(self, founder_id: str) -> bool:
        """Delete a founder genome (async)."""
        try:
            from src.db.repository import get_general_repository
            repo = get_general_repository()

            await repo.execute(
                "DELETE FROM founder_genomes WHERE founder_id = $1",
                (founder_id,)
            )
            return True
        except Exception as e:
            logger.error("Failed to delete genome: %s", e)
            return False

    def rotate_encryption_key(self, new_key: Optional[bytes] = None) -> None:
        """
        Rotate encryption key (re-encrypt all genomes with new key).

        Args:
            new_key: Optional new key (generates if None)
        """
        if new_key is None:
            if self.use_aesgcm:
                new_key = secrets.token_bytes(32)
            else:
                new_key = Fernet.generate_key()

        # Load all genomes (blocking, for admin operation only)
        genomes = asyncio.run(self.get_all_genomes_async())

        for genome in genomes:
            if genome.raw_genome:
                # Re-encrypt with new key
                old_ciphertext = genome.encrypted_data
                genome.encrypted_data = self._encrypt(genome.raw_genome)
                genome.encryption_key_id = hashlib.sha256(new_key).hexdigest()[:16]
                asyncio.run(self._save_to_database_async(genome))

        # Update key file
        self.encryption_key = new_key
        key_file = self.config_dir / (".aesgcm_key" if self.use_aesgcm else ".fernet_key")
        key_file.write_bytes(new_key)
        os.chmod(key_file, 0o600)

        logger.info("Encryption key rotated, %d genomes re-encrypted", len(genomes))


class GenomeAnalyzer:
    """AI-assisted genome analysis using LLM."""

    def __init__(self, llm_client=None):
        """
        Initialize analyzer with LLM client.

        Args:
            llm_client: LLM client instance (get_client() if None)
        """
        self.llm_client = llm_client
        self._prompt_cache: Dict[str, str] = {}

    def analyze_genome(
        self,
        request: GenomeAnalysisRequest,
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Run AI analysis on founder genome data.

        Args:
            request: Analysis request with founder data
            analysis_type: full, quick_traits, cluster, or recommendations

        Returns:
            Analysis results dictionary
        """
        if self.llm_client is None:
            from src.core.llm_client import get_client
            self.llm_client = get_client()

        if not self.llm_client.is_available:
            logger.warning("LLM client not available, returning mock analysis")
            return self._mock_analysis(request, analysis_type)

        # Get appropriate prompt
        prompt_key = analysis_type if analysis_type in FounderGenomeRepository.ANALYSIS_PROMPTS else "full_analysis"
        prompt = FounderGenomeRepository.ANALYSIS_PROMPTS[prompt_key]

        # Build context
        context = request.to_prompt_context()

        full_prompt = f"{prompt}\n\n=== FOUNDER DATA ===\n{context}\n=== END DATA ===\n\nRespond with valid JSON only."

        try:
            response = self.llm_client.generate(full_prompt)
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                logger.info("AI analysis completed for %s", request.founder_id)
                return result
            else:
                logger.error("No JSON found in LLM response")
                return self._mock_analysis(request, analysis_type)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            return self._mock_analysis(request, analysis_type)
        except Exception as e:
            logger.error("LLM analysis failed: %s", e)
            return self._mock_analysis(request, analysis_type)

    def _mock_analysis(self, request: GenomeAnalysisRequest, analysis_type: str) -> Dict[str, Any]:
        """Generate mock analysis when LLM unavailable."""
        import random
        traits = list(FounderGenome.TRAIT_DEFINITIONS.keys())
        mock_scores = {t: round(0.4 + random.random() * 0.6, 2) for t in traits}

        if analysis_type == "quick_traits":
            return {
                "trait_scores": mock_scores,
                "justifications": {t: "Mock score for testing" for t in traits},
                "data_completeness": 0.7
            }
        elif analysis_type == "cluster":
            return {
                "cluster": "Experimenter",
                "cluster_description": "Adaptable founder who iterates based on feedback",
                "match_confidence": 0.65,
                "alternative_clusters": [
                    {"name": "Operator", "confidence": 0.45},
                    {"name": "Visionary", "confidence": 0.30}
                ],
                "key_indicators": ["high adaptability", "moderate risk tolerance"]
            }
        else:
            return {
                "executive_summary": "Mock analysis - LLM unavailable. Founder shows balanced trait profile with notable adaptability.",
                "trait_scores": mock_scores,
                "cluster": "Experimenter",
                "confidence": 0.60,
                "insights": [
                    "Consider partnering with an operator for execution strength",
                    "High adaptability suggests good pivot potential",
                    "Risk tolerance may need calibration for investor expectations"
                ],
                "complementary_founders": ["Operator", "Visionary"],
                "blind_spots": ["may lack deep specialization", "needs stronger team-building focus"]
            }


# Global service instance
_genome_service: Optional[FounderGenomeRepository] = None


def get_genome_service(config_dir: Optional[Path] = None) -> FounderGenomeRepository:
    """Get or create global genome service instance."""
    global _genome_service
    if _genome_service is None:
        _genome_service = FounderGenomeRepository(config_dir=config_dir)
    return _genome_service


def get_genome_analyzer() -> GenomeAnalyzer:
    """Get genome analyzer instance."""
    return GenomeAnalyzer()


# Synchronous wrapper for CLI usage
class SyncGenomeService:
    """Synchronous wrapper for genome service operations."""

    def __init__(self, config_dir: Optional[Path] = None):
        self._async_service = get_genome_service(config_dir)

    def save_genome(
        self,
        founder_id: str,
        raw_genome: Dict[str, Any],
        analysis_summary: Optional[str] = None,
        confidence_score: Optional[float] = None,
        trait_scores: Optional[Dict[str, float]] = None,
        cluster_id: Optional[int] = None,
    ) -> FounderGenome:
        """Sync wrapper for save_genome_async."""
        return asyncio.run(self._async_service.save_genome_async(
            founder_id, raw_genome, analysis_summary,
            confidence_score, trait_scores, cluster_id
        ))

    def load_genome(self, founder_id: str) -> Optional[FounderGenome]:
        """Sync wrapper for load_genome_async."""
        return asyncio.run(self._async_service.load_genome_async(founder_id))

    def find_similar_genomes(
        self,
        trait_scores: Dict[str, float],
        limit: int = 10,
        exclude_founder_id: Optional[str] = None
    ) -> List[GenomeMatch]:
        """Sync wrapper for find_similar_genomes_async."""
        return asyncio.run(self._async_service.find_similar_genomes_async(
            trait_scores, limit, exclude_founder_id
        ))

    def get_all_genomes(self, limit: Optional[int] = None) -> List[FounderGenome]:
        """Sync wrapper for get_all_genomes_async."""
        return asyncio.run(self._async_service.get_all_genomes_async(limit))

    def delete_genome(self, founder_id: str) -> bool:
        """Sync wrapper for delete_genome_async."""
        return asyncio.run(self._async_service.delete_genome_async(founder_id))

    def rotate_encryption_key(self, new_key: Optional[bytes] = None) -> None:
        """Rotate encryption key."""
        self._async_service.rotate_encryption_key(new_key)


def get_sync_genome_service(config_dir: Optional[Path] = None) -> SyncGenomeService:
    """Get synchronous genome service for CLI usage."""
    return SyncGenomeService(config_dir)


__all__ = [
    "FounderGenomeRepository",
    "FounderGenome",
    "GenomeAnalysisRequest",
    "GenomeMatch",
    "GenomeServiceError",
    "EncryptionError",
    "GenomeNotFoundError",
    "GenomeAnalyzer",
    "get_genome_service",
    "get_genome_analyzer",
    "get_sync_genome_service",
    "SyncGenomeService",
]

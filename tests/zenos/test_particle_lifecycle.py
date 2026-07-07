"""
Particle Lifecycle Tests — create, merge, split, dissolve operations.

Tests the complete lifecycle of economic particles including:
- Particle creation with validation
- Particle merging (combining multiple particles)
- Particle splitting (dividing a particle into multiple)
- Particle dissolution (marking as dissolved/inactive)
- Balance recalculation after lifecycle events
- Error handling and edge cases
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

import pytest

from src.models.particle import (
    EconomicParticle,
    ParticleBalance,
    ParticleAggregation,
    PARTICLE_TYPE_USAGE,
    PARTICLE_TYPE_CREDIT,
    PARTICLE_TYPE_ADJUSTMENT,
    PARTICLE_TYPE_PAYMENT,
    PARTICLE_TYPE_FEE,
    SOURCE_API,
    SOURCE_MANUAL,
    CURRENCY_USD,
    CURRENCY_VND,
)


class TestParticleCreation:
    """Test particle creation and validation."""

    def test_create_minimal_credit_particle(self) -> None:
        """Can create a minimal credit particle with auto-generated ID."""
        particle = EconomicParticle(
            key_id="test_key_001",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100.00"),
        )
        assert particle.id is not None
        assert len(particle.id) == 36  # UUID format
        assert particle.key_id == "test_key_001"
        assert particle.particle_type == PARTICLE_TYPE_CREDIT
        assert particle.amount == Decimal("100.00")
        assert particle.currency == CURRENCY_USD
        assert particle.source == SOURCE_API
        assert particle.is_credit() is True
        assert particle.is_debit() is False

    def test_create_usage_particle(self) -> None:
        """Can create a usage (debit) particle."""
        particle = EconomicParticle(
            key_id="key_123",
            particle_type=PARTICLE_TYPE_USAGE,
            amount=Decimal("-25.50"),
            currency=CURRENCY_VND,
        )
        assert particle.is_credit() is False
        assert particle.is_debit() is True
        assert particle.is_usage() is True
        assert particle.currency == CURRENCY_VND

    def test_create_with_metadata(self) -> None:
        """Particle can include rich metadata."""
        metadata = {
            "rate_card": "enterprise_v2",
            "feature": "api_calls",
            "region": "ap_southeast_1",
            "unit_price": "0.001",
        }
        particle = EconomicParticle(
            key_id="key_456",
            particle_type=PARTICLE_TYPE_USAGE,
            amount=Decimal("-150.75"),
            metadata=metadata,
            reference_id="txn_789",
        )
        assert particle.metadata == metadata
        assert particle.reference_id == "txn_789"

    def test_create_with_tenant_id_legacy_compatibility(self) -> None:
        """Particle can include legacy tenant_id for RaaS compatibility."""
        particle = EconomicParticle(
            tenant_id="tenant_abc123",
            key_id="key_xyz789",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("500.00"),
        )
        assert particle.tenant_id == "tenant_abc123"

    def test_invalid_particle_type_raises(self) -> None:
        """Invalid particle type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid particle_type"):
            EconomicParticle(
                key_id="test",
                particle_type="invalid_type",
                amount=Decimal("10"),
            )

    def test_invalid_currency_raises(self) -> None:
        """Invalid currency raises ValueError."""
        with pytest.raises(ValueError, match="Invalid currency"):
            EconomicParticle(
                key_id="test",
                particle_type=PARTICLE_TYPE_USAGE,
                amount=Decimal("-10"),
                currency="XYZ",
            )

    def test_invalid_source_raises(self) -> None:
        """Invalid source raises ValueError."""
        with pytest.raises(ValueError, match="Invalid source"):
            EconomicParticle(
                key_id="test",
                particle_type=PARTICLE_TYPE_USAGE,
                amount=Decimal("-10"),
                source="unknown_source",
            )

    def test_amount_auto_converted_to_decimal(self) -> None:
        """Amount is automatically converted to Decimal."""
        particle = EconomicParticle(
            key_id="test",
            particle_type=PARTICLE_TYPE_USAGE,
            amount=100,  # Pass int
        )
        assert isinstance(particle.amount, Decimal)
        assert particle.amount == Decimal("100")

    def test_balance_after_auto_converted_to_decimal(self) -> None:
        """balance_after is automatically converted to Decimal."""
        particle = EconomicParticle(
            key_id="test",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100"),
            balance_after="250.50",  # Pass string
        )
        assert isinstance(particle.balance_after, Decimal)
        assert particle.balance_after == Decimal("250.50")

    def test_datetime_timezone_awareness(self) -> None:
        """created_at and updated_at are timezone-aware (UTC)."""
        particle = EconomicParticle(
            key_id="test",
            particle_type=PARTICLE_TYPE_USAGE,
            amount=Decimal("-10"),
        )
        assert particle.created_at.tzinfo is not None
        assert particle.updated_at.tzinfo is not None

    def test_custom_timestamps_preserved(self) -> None:
        """Custom timestamps are preserved."""
        custom_time = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        particle = EconomicParticle(
            key_id="test",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100"),
            created_at=custom_time,
        )
        assert particle.created_at == custom_time


class TestParticleSerialization:
    """Test particle serialization and deserialization."""

    def test_from_dict_database_row(self) -> None:
        """Create particle from database row dict."""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "tenant_id": "tenant_001",
            "key_id": "key_abc",
            "particle_type": PARTICLE_TYPE_CREDIT,
            "amount": "250.75",
            "currency": CURRENCY_VND,
            "balance_after": "1000.25",
            "metadata": {"source": "migration"},
            "source": SOURCE_MANUAL,
            "reference_id": "ref_123",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:35:00Z",
            "tenant_reference_id": "tenant_ref_001",
        }
        particle = EconomicParticle.from_dict(data)
        assert particle.id == "550e8400-e29b-41d4-a716-446655440000"
        assert particle.tenant_id == "tenant_001"
        assert particle.key_id == "key_abc"
        assert particle.particle_type == PARTICLE_TYPE_CREDIT
        assert particle.amount == Decimal("250.75")
        assert particle.currency == CURRENCY_VND
        assert particle.balance_after == Decimal("1000.25")
        assert particle.metadata == {"source": "migration"}
        assert particle.source == SOURCE_MANUAL
        assert particle.reference_id == "ref_123"
        assert particle.tenant_reference_id == "tenant_ref_001"

    def test_to_dict_for_database_insert(self) -> None:
        """Convert particle to dict for database insertion."""
        particle = EconomicParticle(
            key_id="key_xyz",
            particle_type=PARTICLE_TYPE_FEE,
            amount=Decimal("-50.00"),
            currency=CURRENCY_USD,
            balance_after=Decimal("500.00"),
            metadata={"fee_type": "api_overage"},
            reference_id="fee_001",
        )
        data = particle.to_dict()
        assert data["key_id"] == "key_xyz"
        assert data["particle_type"] == PARTICLE_TYPE_FEE
        assert data["amount"] == "-50.00"  # String for DB
        assert data["balance_after"] == "500.00"
        assert data["currency"] == CURRENCY_USD
        assert data["metadata"] == {"fee_type": "api_overage"}
        assert data["reference_id"] == "fee_001"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_to_insert_sql_postgres_format(self) -> None:
        """Generate correct PostgreSQL INSERT statement."""
        particle = EconomicParticle(
            id="test-uuid-123",
            key_id="key_001",
            particle_type=PARTICLE_TYPE_ADJUSTMENT,
            amount=Decimal("75.25"),
            currency=CURRENCY_USD,
        )
        query, params = particle.to_insert_sql()
        assert "INSERT INTO economic_particles" in query
        assert "$1" in query  # PostgreSQL positional params
        assert params[0] == "test-uuid-123"
        assert params[2] == "key_001"
        assert params[3] == PARTICLE_TYPE_ADJUSTMENT
        assert params[4] == Decimal("75.25")

    def test_roundtrip_serialization(self) -> None:
        """Particle survives roundtrip: object -> dict -> object."""
        original = EconomicParticle(
            key_id="roundtrip_key",
            particle_type=PARTICLE_TYPE_PAYMENT,
            amount=Decimal("199.99"),
            currency=CURRENCY_VND,
            metadata={"payment_method": "momo"},
        )
        data = original.to_dict()
        restored = EconomicParticle.from_dict(data)
        assert restored.id == original.id
        assert restored.key_id == original.key_id
        assert restored.particle_type == original.particle_type
        assert restored.amount == original.amount
        assert restored.currency == original.currency
        assert restored.metadata == original.metadata


class TestParticleLifecycle:
    """Test particle lifecycle operations: merge, split, dissolve."""

    def test_merge_particles_same_key(self) -> None:
        """Merging particles combines amounts and preserves key_id."""
        p1 = EconomicParticle(
            key_id="merge_key",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100.00"),
        )
        p2 = EconomicParticle(
            key_id="merge_key",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("50.00"),
        )

        merged = self._merge_particles([p1, p2])

        assert merged.key_id == "merge_key"
        assert merged.particle_type == PARTICLE_TYPE_CREDIT
        assert merged.amount == Decimal("150.00")
        assert merged.metadata.get("merged_from") == 2
        assert merged.reference_id is not None
        assert "merge_" in merged.reference_id

    def test_merge_mixed_types_raises(self) -> None:
        """Cannot merge particles of different types."""
        p1 = EconomicParticle(
            key_id="key_1",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100"),
        )
        p2 = EconomicParticle(
            key_id="key_1",
            particle_type=PARTICLE_TYPE_USAGE,
            amount=Decimal("-30"),
        )
        with pytest.raises(ValueError, match="Cannot merge different particle types"):
            self._merge_particles([p1, p2])

    def test_merge_different_keys_raises(self) -> None:
        """Cannot merge particles with different key_id."""
        p1 = EconomicParticle(
            key_id="key_A",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100"),
        )
        p2 = EconomicParticle(
            key_id="key_B",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("50"),
        )
        with pytest.raises(ValueError, match="Cannot merge particles with different key_id"):
            self._merge_particles([p1, p2])

    def test_merge_preserves_metadata_union(self) -> None:
        """Merge combines metadata from all particles."""
        p1 = EconomicParticle(
            key_id="key_meta",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100"),
            metadata={"source": "stripe", "tx_id": "tx1"},
        )
        p2 = EconomicParticle(
            key_id="key_meta",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("50"),
            metadata={"source": "paypal", "invoice": "inv_123"},
        )
        merged = self._merge_particles([p1, p2])
        # Merge collects sources in a list
        assert "merged_from" in merged.metadata
        assert "sources" in merged.metadata
        assert set(merged.metadata["sources"]) == {"stripe", "paypal"}

    def test_split_particle_equal_parts(self) -> None:
        """Split creates equal parts maintaining total amount."""
        original = EconomicParticle(
            key_id="split_key",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100.00"),
            reference_id="original_tx",
        )
        parts = self._split_particle(original, parts=4)

        assert len(parts) == 4
        total = sum(p.amount for p in parts)
        assert total == Decimal("100.00")
        for part in parts:
            assert part.key_id == original.key_id
            assert part.particle_type == original.particle_type
            assert part.amount == Decimal("25.00")
            assert part.reference_id is not None
            assert "split_" in part.reference_id  # Format: split_{original_id[:8]}_{index}

    def test_split_particle_unequal_parts(self) -> None:
        """Split with custom ratios."""
        original = EconomicParticle(
            key_id="split_unequal",
            particle_type=PARTICLE_TYPE_ADJUSTMENT,
            amount=Decimal("100.00"),
        )
        ratios = [0.25, 0.25, 0.50]
        parts = self._split_particle(original, ratios=ratios)

        assert len(parts) == 3
        assert parts[0].amount == Decimal("25.00")
        assert parts[1].amount == Decimal("25.00")
        assert parts[2].amount == Decimal("50.00")
        assert sum(p.amount for p in parts) == Decimal("100.00")

    def test_split_particle_negative_amount(self) -> None:
        """Split works with negative amounts (debits)."""
        original = EconomicParticle(
            key_id="split_debit",
            particle_type=PARTICLE_TYPE_USAGE,
            amount=Decimal("-100.00"),
        )
        parts = self._split_particle(original, parts=2)
        assert all(p.amount < 0 for p in parts)
        assert sum(p.amount for p in parts) == Decimal("-100.00")

    def test_split_particle_minimum_part_amount(self) -> None:
        """Split respects minimum part amount constraint."""
        original = EconomicParticle(
            key_id="split_min",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("10.00"),
        )
        # With min=0.50, parts of 0.50 are at the boundary and kept
        parts = self._split_particle(original, parts=20, min_part_amount=Decimal("0.50"))
        assert len(parts) == 20  # All parts at exactly 0.50 meet the minimum
        assert all(p.amount >= Decimal("0.50") for p in parts)

    def test_split_invalid_parts_raises(self) -> None:
        """Split with zero or negative parts raises error."""
        original = EconomicParticle(
            key_id="key",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100"),
        )
        with pytest.raises(ValueError, match="parts must be positive"):
            self._split_particle(original, parts=0)

    def test_dissolve_particle_marks_inactive(self) -> None:
        """Dissolve marks particle as dissolved (logical delete) without creating adjustment."""
        particle = EconomicParticle(
            key_id="dissolve_key",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100"),
        )
        dissolved = self._dissolve_particle(particle, create_adjustment=False)
        assert dissolved.metadata.get("dissolved") is True
        assert "dissolved_at" in dissolved.metadata
        assert dissolved.particle_type == PARTICLE_TYPE_ADJUSTMENT  # Type changes

    def test_dissolve_creates_adjustment_pair(self) -> None:
        """Dissolve creates offsetting adjustment to zero out balance."""
        original = EconomicParticle(
            key_id="dissolve_pair",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100.00"),
            balance_after=Decimal("100.00"),
        )
        adjustment = self._dissolve_particle(original, create_adjustment=True)
        assert adjustment is not None
        assert adjustment.amount == Decimal("-100.00")
        assert adjustment.key_id == original.key_id
        assert adjustment.particle_type == PARTICLE_TYPE_ADJUSTMENT
        assert adjustment.reference_id == f"dissolve_{original.id}"

    def test_dissolve_without_adjustment(self) -> None:
        """Dissolve can mark original without creating adjustment."""
        original = EconomicParticle(
            key_id="dissolve_only",
            particle_type=PARTICLE_TYPE_USAGE,
            amount=Decimal("-25.00"),
        )
        dissolved = self._dissolve_particle(original, create_adjustment=False)
        assert dissolved.metadata.get("dissolved") is True
        assert dissolved.amount == Decimal("-25.00")  # Amount unchanged

    def test_lifecycle_chain_create_merge_split(self) -> None:
        """Full lifecycle: create → merge → split → dissolve."""
        # Create particles
        p1 = EconomicParticle(key_id="chain_key", particle_type=PARTICLE_TYPE_CREDIT, amount=Decimal("50"))
        p2 = EconomicParticle(key_id="chain_key", particle_type=PARTICLE_TYPE_CREDIT, amount=Decimal("50"))
        EconomicParticle(key_id="chain_key", particle_type=PARTICLE_TYPE_USAGE, amount=Decimal("-30"))

        # Merge the two credits
        merged_credit = self._merge_particles([p1, p2])
        assert merged_credit.amount == Decimal("100")

        # Split the merged credit
        splits = self._split_particle(merged_credit, parts=2)
        assert len(splits) == 2
        assert all(s.amount == Decimal("50") for s in splits)

        # Dissolve one split (creates adjustment particle)
        adjustment = self._dissolve_particle(splits[0], create_adjustment=True)
        assert adjustment is not None
        assert adjustment.amount == -splits[0].amount  # Offsetting amount
        assert adjustment.key_id == splits[0].key_id
        assert adjustment.particle_type == PARTICLE_TYPE_ADJUSTMENT
        assert adjustment.reference_id == f"dissolve_{splits[0].id}"
        assert adjustment.metadata.get("dissolves") == splits[0].id

    def test_get_effective_amount_credit(self) -> None:
        """get_effective_amount returns positive for credits."""
        particle = EconomicParticle(
            key_id="test",
            particle_type=PARTICLE_TYPE_CREDIT,
            amount=Decimal("100"),
        )
        assert particle.get_effective_amount() == Decimal("100")

    def test_get_effective_amount_debit(self) -> None:
        """get_effective_amount returns negative for debits."""
        particle = EconomicParticle(
            key_id="test",
            particle_type=PARTICLE_TYPE_USAGE,
            amount=Decimal("-50"),
        )
        assert particle.get_effective_amount() == Decimal("-50")

    # ------------------------------------------------------------------
    # Helper methods (in production these would be on ParticleRepository)
    # ------------------------------------------------------------------

    def _merge_particles(
        self,
        particles: List[EconomicParticle],
        target_key_id: str | None = None,
    ) -> EconomicParticle:
        """Merge multiple particles into one (test helper)."""
        if not particles:
            raise ValueError("Cannot merge empty list")

        first = particles[0]
        if target_key_id is None:
            target_key_id = first.key_id

        # Validate all match criteria
        for p in particles:
            if p.key_id != target_key_id:
                raise ValueError(f"Cannot merge particles with different key_id: {p.key_id} != {target_key_id}")
            if p.particle_type != first.particle_type:
                raise ValueError(f"Cannot merge different particle types: {p.particle_type} != {first.particle_type}")

        total_amount = sum(p.amount for p in particles)
        merged_metadata = {"merged_from": len(particles)}
        # Collect sources: prefer metadata['source'] if present, else particle.source
        sources = []
        for p in particles:
            if "source" in p.metadata:
                sources.append(p.metadata["source"])
            else:
                sources.append(p.source)
        merged_metadata["sources"] = list(set(sources))

        merged = EconomicParticle(
            key_id=target_key_id,
            particle_type=first.particle_type,
            amount=total_amount,
            currency=first.currency,
            metadata=merged_metadata,
            source=SOURCE_MANUAL if SOURCE_MANUAL in sources else SOURCE_API,
            reference_id=f"merge_{uuid.uuid4().hex[:8]}",
        )
        return merged

    def _split_particle(
        self,
        particle: EconomicParticle,
        parts: int | None = None,
        ratios: List[float] | None = None,
        min_part_amount: Decimal | None = None,
    ) -> List[EconomicParticle]:
        """Split a particle into multiple parts (test helper)."""
        if parts is None and ratios is None:
            raise ValueError("Must specify either parts or ratios")
        if parts is not None and parts <= 0:
            raise ValueError("parts must be positive")

        total = particle.amount
        abs(total)

        if ratios:
            if abs(sum(ratios) - 1.0) > Decimal("0.001"):
                raise ValueError("Ratios must sum to 1.0")
            split_amounts = [Decimal(str(r)) * total for r in ratios]
        else:
            part_amount = total / Decimal(str(parts))
            split_amounts = [part_amount] * parts

        if min_part_amount is not None:
            split_amounts = [a for a in split_amounts if abs(a) >= min_part_amount]

        # Create split particles
        splits = []
        for i, amount in enumerate(split_amounts):
            split = EconomicParticle(
                key_id=particle.key_id,
                particle_type=particle.particle_type,
                amount=amount,
                currency=particle.currency,
                metadata={**particle.metadata, "split_index": i, "split_from": particle.id},
                reference_id=f"split_{particle.id[:8]}_{i}",
            )
            splits.append(split)

        return splits

    def _dissolve_particle(
        self,
        particle: EconomicParticle,
        create_adjustment: bool = True,
    ) -> EconomicParticle | None:
        """Dissolve a particle (test helper)."""
        if create_adjustment:
            # Create offsetting adjustment to zero out
            adjustment = EconomicParticle(
                key_id=particle.key_id,
                particle_type=PARTICLE_TYPE_ADJUSTMENT,
                amount=-particle.amount,
                currency=particle.currency,
                reference_id=f"dissolve_{particle.id}",
                metadata={"dissolves": particle.id},
            )
            return adjustment
        else:
            # Mark original as dissolved
            particle.metadata["dissolved"] = True
            particle.metadata["dissolved_at"] = datetime.now(timezone.utc).isoformat()
            particle.particle_type = PARTICLE_TYPE_ADJUSTMENT
            return particle


class TestParticleBalance:
    """Test balance calculation and tracking."""

    def test_balance_from_dict(self) -> None:
        """Create ParticleBalance from dict."""
        data = {
            "key_id": "balance_key_001",
            "balance": "1500.50",
            "currency": CURRENCY_VND,
            "last_particle_id": "particle_xyz",
            "last_updated": "2025-01-15T10:30:00Z",
            "particle_count": 42,
        }
        balance = ParticleBalance.from_dict(data)
        assert balance.key_id == "balance_key_001"
        assert balance.balance == Decimal("1500.50")
        assert balance.currency == CURRENCY_VND
        assert balance.last_particle_id == "particle_xyz"
        assert balance.particle_count == 42

    def test_balance_to_dict(self) -> None:
        """Convert ParticleBalance to dict."""
        balance = ParticleBalance(
            key_id="key_001",
            balance=Decimal("999.99"),
            currency=CURRENCY_USD,
            last_particle_id="part_123",
            particle_count=10,
        )
        data = balance.to_dict()
        assert data["key_id"] == "key_001"
        assert data["balance"] == "999.99"
        assert data["currency"] == CURRENCY_USD
        assert data["particle_count"] == 10

    def test_balance_default_values(self) -> None:
        """ParticleBalance uses sensible defaults."""
        balance = ParticleBalance(key_id="default_key")
        assert balance.balance == Decimal("0.0")
        assert balance.currency == CURRENCY_USD
        assert balance.last_particle_id is None
        assert balance.particle_count == 0


class TestParticleAggregation:
    """Test particle aggregation for reporting."""

    def test_aggregation_from_dict(self) -> None:
        """Create ParticleAggregation from database result."""
        data = {
            "key_id": "agg_key",
            "particle_type": PARTICLE_TYPE_USAGE,
            "total_amount": "-5000.00",
            "particle_count": 150,
            "currency": CURRENCY_VND,
            "period_start": "2025-01-01T00:00:00Z",
            "period_end": "2025-01-31T23:59:59Z",
        }
        agg = ParticleAggregation.from_dict(data)
        assert agg.key_id == "agg_key"
        assert agg.particle_type == PARTICLE_TYPE_USAGE
        assert agg.total_amount == Decimal("-5000.00")
        assert agg.particle_count == 150
        assert agg.currency == CURRENCY_VND
        assert agg.period_start is not None

    def test_aggregation_empty_result(self) -> None:
        """Handle None values gracefully."""
        data = {
            "key_id": "key_001",
            "particle_type": PARTICLE_TYPE_CREDIT,
        }
        agg = ParticleAggregation.from_dict(data)
        assert agg.total_amount == Decimal("0.0")
        assert agg.particle_count == 0

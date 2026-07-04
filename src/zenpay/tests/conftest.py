"""ZenPay test base class."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.zenpay.models import Base
from src.zenpay.wallet import WalletManager
from src.zenpay.treasury import TreasuryManager
from src.zenpay.kyc import KycService


@pytest.fixture
async def db_session():
    """Create test database session."""
    engine = create_async_engine(
        "postgresql+asyncpg://zenpay:zenpay@localhost:5432/zenpay_test",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def wallet_manager(db_session: AsyncSession):
    """Create wallet manager."""
    return WalletManager(db_session)


@pytest.fixture
def treasury_manager(db_session: AsyncSession):
    """Create treasury manager."""
    return TreasuryManager(db_session)


@pytest.fixture
def kyc_service(db_session: AsyncSession):
    """Create KYC service."""
    return KycService(db_session)


def assert_decimal_equal(a: Decimal, b: Decimal, places: int = 8):
    """Assert two decimals are equal within tolerance."""
    assert round(a - b, places) == 0


class TestBase:
    """Base test class."""

    @pytest.fixture(autouse=True)
    def auto_inject_fixtures(self, db_session, wallet_manager, treasury_manager, kyc_service):
        """Auto-inject fixtures."""
        self.db = db_session
        self.wallet_manager = wallet_manager
        self.treasury_manager = treasury_manager
        self.kyc_service = kyc_service

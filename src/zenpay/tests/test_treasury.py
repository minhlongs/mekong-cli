"""Treasury manager tests."""

import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock

from src.zenpay.models import Wallet, WalletType, WalletStatus
from src.zenpay.exceptions import ExchangeRateError
from .conftest import TestBase, assert_decimal_equal


class TestTreasuryManager(TestBase):
    """Treasury manager tests."""

    @pytest.mark.asyncio
    async def test_get_user_balance(self):
        """Test getting user balance."""
        # Create multiple wallets
        await self.wallet_manager.create_wallet("test_user", "USD", WalletType.CUSTODIAL)
        await self.wallet_manager.create_wallet("test_user", "VND", WalletType.CUSTODIAL)

        usd_wallet = await self.wallet_manager.get_wallet("test_user", "USD", WalletType.CUSTODIAL)
        vnd_wallet = await self.wallet_manager.get_wallet("test_user", "VND", WalletType.CUSTODIAL)

        await self.wallet_manager.credit(usd_wallet.id, Decimal("100"))
        await self.wallet_manager.credit(vnd_wallet.id, Decimal("10000"))

        balances = await self.treasury_manager.get_user_balance("test_user")

        assert "USD" in balances
        assert "VND" in balances
        assert balances["USD"]["total"] == Decimal("100")
        assert balances["VND"]["total"] == Decimal("10000")

    @pytest.mark.asyncio
    async def test_get_exchange_rate_caching(self):
        """Test exchange rate caching."""
        with patch.object(self.treasury_manager.stripe_client, 'get_exchange_rate') as mock_get:
            mock_get.return_value = Decimal("25000.0")

            # First call should hit Stripe
            rate1 = await self.treasury_manager.get_exchange_rate("USD", "VND")
            assert mock_get.call_count == 1

            # Second call should use cache
            rate2 = await self.treasury_manager.get_exchange_rate("USD", "VND")
            assert mock_get.call_count == 1  # Still 1, using cache
            assert rate1 == rate2 == Decimal("25000.0")

    @pytest.mark.asyncio
    async def test_convert_currency(self):
        """Test currency conversion."""
        # Create wallet for source currency
        wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
            wallet_type=WalletType.VIRTUAL,
        )
        await self.wallet_manager.credit(wallet.id, Decimal("100"))

        with patch.object(self.treasury_manager, 'get_exchange_rate') as mock_rate:
            mock_rate.return_value = Decimal("25000.0")

            result = await self.treasury_manager.convert_currency(
                amount=Decimal("100"),
                from_currency="USD",
                to_currency="VND",
                user_id="test_user",
                description="Test conversion",
            )

            assert result == Decimal("2500000.0")  # 100 * 25000

    @pytest.mark.asyncio
    async def test_calculate_payout_fee(self):
        """Test payout fee calculation."""
        fee_vnd, total_vnd = await self.treasury_manager.calculate_payout_fee(
            Decimal("100000"), "VND"
        )
        assert fee_vnd == Decimal("2000")  # 2%
        assert total_vnd == Decimal("102000")

        fee_usd, total_usd = await self.treasury_manager.calculate_payout_fee(
            Decimal("100"), "USD"
        )
        assert fee_usd == Decimal("1.50")  # 1.5%
        assert total_usd == Decimal("101.50")

    @pytest.mark.asyncio
    async def test_can_payout(self):
        """Test payout eligibility check."""
        wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
        )
        await self.wallet_manager.credit(wallet.id, Decimal("100"))

        # Check can payout
        eligible, reason = await self.treasury_manager.can_payout(
            user_id="test_user",
            amount=Decimal("50"),
            currency="USD",
        )
        assert eligible is True
        assert reason is None

        # Too small amount
        eligible, reason = await self.treasury_manager.can_payout(
            user_id="test_user",
            amount=Decimal("5"),
            currency="USD",
        )
        assert eligible is False
        assert "below minimum" in reason

        # Too large amount
        eligible, reason = await self.treasury_manager.can_payout(
            user_id="test_user",
            amount=Decimal("200"),
            currency="USD",
        )
        assert eligible is False
        assert "Insufficient" in reason

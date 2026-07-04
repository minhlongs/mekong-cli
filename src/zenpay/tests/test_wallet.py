"""Wallet manager tests."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from src.zenpay.models import Wallet, Transaction, WalletType, WalletStatus, TransactionType, TransactionStatus
from src.zenpay.exceptions import WalletError, WalletNotFoundError, InsufficientFundsError
from .conftest import TestBase, assert_decimal_equal


class TestWalletManager(TestBase):
    """Wallet manager tests."""

    @pytest.mark.asyncio
    async def test_create_wallet(self):
        """Test creating a wallet."""
        wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
            wallet_type=WalletType.CUSTODIAL,
        )

        assert wallet.user_id == "test_user"
        assert wallet.currency == "USD"
        assert wallet.wallet_type == WalletType.CUSTODIAL
        assert wallet.status == WalletStatus.ACTIVE
        assert wallet.balance == Decimal("0")
        assert wallet.available_balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_wallet(self):
        """Test getting a wallet."""
        created = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="VND",
        )

        retrieved = await self.wallet_manager.get_wallet("test_user", "VND")
        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_credit_wallet(self):
        """Test crediting a wallet."""
        wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
        )

        txn = await self.wallet_manager.credit(
            wallet_id=wallet.id,
            amount=Decimal("100.50"),
            description="Test deposit",
        )

        assert txn.transaction_type == TransactionType.DEPOSIT
        assert txn.status == TransactionStatus.COMPLETED
        assert txn.amount == Decimal("100.50")

        await self.db.refresh(wallet)
        assert wallet.balance == Decimal("100.50")
        assert wallet.available_balance == Decimal("100.50")

    @pytest.mark.asyncio
    async def test_debit_wallet(self):
        """Test debiting a wallet."""
        wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
        )
        await self.wallet_manager.credit(wallet.id, Decimal("100"))

        txn = await self.wallet_manager.debit(
            wallet_id=wallet.id,
            amount=Decimal("30.25"),
            description="Test withdrawal",
        )

        assert txn.transaction_type == TransactionType.WITHDRAWAL
        assert txn.amount == Decimal("30.25")

        await self.db.refresh(wallet)
        assert wallet.balance == Decimal("69.75")
        assert wallet.available_balance == Decimal("69.75")

    @pytest.mark.asyncio
    async def test_debit_insufficient_funds(self):
        """Test debit with insufficient funds."""
        wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
        )

        with pytest.raises(InsufficientFundsError):
            await self.wallet_manager.debit(wallet.id, Decimal("100"))

    @pytest.mark.asyncio
    async def test_hold_and_release(self):
        """Test hold and release operations."""
        wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
        )
        await self.wallet_manager.credit(wallet.id, Decimal("100"))

        # Place hold
        hold_txn = await self.wallet_manager.hold(
            wallet_id=wallet.id,
            amount=Decimal("20"),
            description="Hold test",
        )

        await self.db.refresh(wallet)
        assert wallet.available_balance == Decimal("80")
        assert wallet.hold_balance == Decimal("20")

        # Release hold
        released = await self.wallet_manager.release_hold(hold_txn.id)

        await self.db.refresh(wallet)
        assert wallet.available_balance == Decimal("100")
        assert wallet.hold_balance == Decimal("0")
        assert released.status == TransactionStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_transfer(self):
        """Test wallet transfer."""
        from_wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
        )
        to_wallet = await self.wallet_manager.create_wallet(
            user_id="test_user",
            currency="USD",
        )

        await self.wallet_manager.credit(from_wallet.id, Decimal("100"))

        txn = await self.wallet_manager.transfer(
            from_wallet_id=from_wallet.id,
            to_wallet_id=to_wallet.id,
            amount=Decimal("50"),
            description="Transfer test",
        )

        assert txn.transaction_type == TransactionType.TRANSFER
        assert txn.amount == Decimal("50")

        await self.db.refresh(from_wallet)
        await self.db.refresh(to_wallet)
        assert from_wallet.balance == Decimal("50")
        assert to_wallet.balance == Decimal("50")

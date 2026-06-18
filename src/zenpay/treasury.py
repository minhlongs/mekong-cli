"""Treasury manager for multi-currency operations."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from .exceptions import ExchangeRateError, InsufficientFundsError
from .models import (
    ExchangeRate, Wallet, Transaction, TransactionType, TransactionStatus,
    WalletType, WalletStatus, Balance
)
from .stripe_client import get_stripe_client

logger = logging.getLogger(__name__)


class TreasuryManager:
    """Manages multi-currency treasury operations."""

    def __init__(self, db_session: AsyncSession):
        """Initialize treasury manager."""
        self.db = db_session
        self.stripe_client = get_stripe_client()

    async def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        refresh: bool = False,
    ) -> Decimal:
        """Get exchange rate with caching."""
        # Check cache first (unless refresh is forced)
        if not refresh:
            stmt = select(ExchangeRate).where(
                ExchangeRate.from_currency == from_currency,
                ExchangeRate.to_currency == to_currency,
                ExchangeRate.source == "stripe",
                ExchangeRate.expires_at > datetime.now(timezone.utc)
            )
            result = await self.db.execute(stmt)
            cached_rate = result.scalar_one_or_none()
            if cached_rate:
                return cached_rate.rate

        # Fetch fresh rate from Stripe
        try:
            rate = self.stripe_client.get_exchange_rate(from_currency, to_currency)
            rate_decimal = Decimal(str(rate))

            # Cache the rate (expires in 1 hour)
            expires_at = datetime.now(timezone.utc)
            expires_at = expires_at.replace(hour=expires_at.hour + 1)

            exchange_rate = ExchangeRate(
                id=f"rate_{from_currency}_{to_currency}_{int(datetime.now().timestamp())}",
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate_decimal,
                source="stripe",
                expires_at=expires_at,
            )
            self.db.add(exchange_rate)
            await self.db.commit()

            return rate_decimal
        except Exception as e:
            logger.error(f"Failed to fetch exchange rate: {e}")
            raise ExchangeRateError(f"Could not get rate {from_currency}->{to_currency}: {e}")

    async def convert_currency(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        user_id: str,
        description: str,
    ) -> Decimal:
        """Convert currency with rate lookup."""
        if from_currency == to_currency:
            return amount

        rate = await self.get_exchange_rate(from_currency, to_currency)
        converted_amount = amount * rate

        # Record conversion transaction
        wallet = await self._get_or_create_wallet(
            user_id=user_id,
            currency=from_currency,
            wallet_type=WalletType.VIRTUAL
        )

        transaction = Transaction(
            id=f"conv_{int(datetime.now().timestamp())}_{user_id}",
            wallet_id=wallet.id,
            transaction_type=TransactionType.CONVERSION,
            status=TransactionStatus.COMPLETED,
            amount=amount,
            currency=from_currency,
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=amount,
            to_amount=converted_amount,
            exchange_rate=rate,
            description=description,
        )
        self.db.add(transaction)
        await self.db.commit()

        logger.info(f"Converted {amount} {from_currency} to {converted_amount} {to_currency} for {user_id}")
        return converted_amount

    async def _get_or_create_wallet(
        self,
        user_id: str,
        currency: str,
        wallet_type: WalletType = WalletType.VIRTUAL,
        **kwargs
    ) -> Wallet:
        """Get or create a wallet for a user."""
        stmt = select(Wallet).where(
            Wallet.user_id == user_id,
            Wallet.currency == currency,
            Wallet.wallet_type == wallet_type
        )
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            wallet = Wallet(
                id=f"wallet_{user_id}_{currency}_{int(datetime.now().timestamp())}",
                user_id=user_id,
                currency=currency,
                wallet_type=wallet_type,
                status=WalletStatus.ACTIVE,
                **kwargs
            )
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)

        return wallet

    async def get_user_balance(
        self,
        user_id: str,
        currency: Optional[str] = None,
    ) -> dict[str, Decimal]:
        """Get user balance across all wallets or specific currency."""
        stmt = select(
            Wallet.currency,
            func.sum(Wallet.available_balance).label("available"),
            func.sum(Wallet.balance).label("total"),
        ).where(
            Wallet.user_id == user_id,
            Wallet.status == WalletStatus.ACTIVE
        )

        if currency:
            stmt = stmt.where(Wallet.currency == currency)

        stmt = stmt.group_by(Wallet.currency)
        result = await self.db.execute(stmt)

        balances = {}
        for row in result.all():
            balances[row.currency] = {
                "available": row.available or Decimal("0"),
                "total": row.total or Decimal("0"),
            }

        return balances

    async def calculate_payout_fee(
        self,
        amount: Decimal,
        currency: str,
    ) -> tuple[Decimal, Decimal]:
        """Calculate payout fee (amount + fee)."""
        fee_bps = {
            "VND": settings.payout_fee_bps_vnd,
            "USD": settings.payout_fee_bps_usd,
            "USDT": settings.payout_fee_bps_usdt,
        }.get(currency, 200)  # Default 2%

        fee = amount * Decimal(fee_bps) / Decimal("10000")
        total = amount + fee
        return fee, total

    async def get_minimum_payout(self, currency: str) -> Decimal:
        """Get minimum payout amount for currency."""
        return {
            "VND": Decimal(settings.min_payout_amount_vnd),
            "USD": Decimal(settings.min_payout_amount_usd),
            "USDT": Decimal(settings.min_payout_amount_usdt),
        }.get(currency, Decimal("10"))

    async def can_payout(
        self,
        user_id: str,
        amount: Decimal,
        currency: str,
    ) -> tuple[bool, Optional[str]]:
        """Check if user can receive payout."""
        # Check minimum amount
        min_amount = await self.get_minimum_payout(currency)
        if amount < min_amount:
            return False, f"Amount {amount} {currency} below minimum {min_amount} {currency}"

        # Check balance
        balances = await self.get_user_balance(user_id, currency)
        if currency not in balances:
            return False, f"No {currency} wallet found"
        if balances[currency]["available"] < amount:
            return False, f"Insufficient {currency} balance: {balances[currency]['available']} available"

        return True, None

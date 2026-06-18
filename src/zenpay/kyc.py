"""KYC compliance service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .exceptions import KycError, KycNotVerifiedError
from .models import Account, KycProfile, KycStatus
from .stripe_client import get_stripe_client

logger = logging.getLogger(__name__)


class KycProvider:
    """KYC provider interface."""

    async def verify_identity(
        self,
        account_id: str,
        document_front: bytes,
        document_back: Optional[bytes] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Verify identity document."""
        raise NotImplementedError

    async def check_status(self, verification_id: str) -> Dict[str, Any]:
        """Check verification status."""
        raise NotImplementedError


class StripeKycProvider(KycProvider):
    """Stripe-based KYC via Connect account verification."""

    def __init__(self):
        """Initialize Stripe KYC provider."""
        self.client = get_stripe_client()

    async def create_verification_session(
        self,
        account_id: str,
        return_url: str,
    ) -> Dict[str, Any]:
        """Create a Stripe verification session."""
        try:
            session = self.client.client.AccountLink.create(
                account=account_id,
                return_url=return_url,
                type="account_verification",
            )
            return {
                "url": session.url,
                "expires_at": session.expires_at,
                " verification_type": "stripe_kyb",
            }
        except Exception as e:
            logger.error(f"Stripe KYC session failed: {e}")
            raise KycError(f"Failed to create verification session: {e}")

    async def get_account_requirements(self, account_id: str) -> Dict[str, Any]:
        """Get KYC requirements for account."""
        return self.client.get_account_requirements(account_id)


class KycService:
    """KYC compliance service."""

    def __init__(self, db_session: AsyncSession):
        """Initialize KYC service."""
        self.db = db_session
        self.provider = self._get_provider()

    def _get_provider(self) -> KycProvider:
        """Get configured KYC provider."""
        if settings.kyc_provider.value == "stripe":
            return StripeKycProvider()
        elif settings.kyc_provider.value == "self_hosted":
            return SelfHostedKycProvider()
        else:
            raise KycError(f"Unsupported KYC provider: {settings.kyc_provider}")

    async def start_verification(
        self,
        account_id: str,
        return_url: str,
    ) -> Dict[str, Any]:
        """Start KYC verification process."""
        if settings.kyc_provider == "stripe":
            return await self.provider.create_verification_session(account_id, return_url)
        raise KycError(f"Provider {settings.kyc_provider} not implemented")

    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        signature: str,
    ) -> None:
        """Handle KYC webhook from provider."""
        if settings.kyc_provider == "stripe":
            await self._handle_stripe_webhook(payload)
        else:
            raise KycError(f"Webhook not supported for {settings.kyc_provider}")

    async def _handle_stripe_webhook(self, event: Dict[str, Any]) -> None:
        """Handle Stripe account update webhook."""
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "account.updated":
            account_id = data.get("id")
            requirements = data.get("requirements", {})

            # Find account in database
            stmt = select(Account).where(Account.stripe_account_id == account_id)
            result = await self.db.execute(stmt)
            account = result.scalar_one_or_none()

            if account:
                await self._update_account_kyc_status(account, requirements)

        elif event_type == "identity.verification_session.verified":
            # Process completed verification
            pass

    async def _update_account_kyc_status(
        self,
        account: Account,
        requirements: Dict[str, Any]
    ) -> None:
        """Update account KYC status based on requirements."""
        current_status = account.kyc_status
        disabled_reason = requirements.get("disabled_reason")

        if disabled_reason:
            account.status = AccountStatus.RESTRICTED
            account.kyc_status = KycStatus.REJECTED
        elif not requirements.get("currently_due"):
            account.kyc_status = KycStatus.VERIFIED
            account.kyc_verified_at = datetime.now(timezone.utc)
        else:
            account.kyc_status = KycStatus.PENDING

        account.requirements_currently_due = requirements.get("currently_due", [])
        account.requirements_past_due = requirements.get("past_due", [])

        await self.db.commit()
        logger.info(f"Updated KYC status for account {account.id}: {current_status} -> {account.kyc_status}")

    async def get_kyc_status(self, account_id: str) -> Dict[str, Any]:
        """Get KYC status for account."""
        stmt = select(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            raise KycError(f"Account not found: {account_id}")

        return {
            "status": account.kyc_status.value,
            "verified_at": account.kyc_verified_at.isoformat() if account.kyc_verified_at else None,
            "requirements_currently_due": account.requirements_currently_due or [],
            "requirements_past_due": account.requirements_past_due or [],
            "account_status": account.status.value,
        }

    async def is_verified(self, account_id: str) -> bool:
        """Check if account KYC is verified."""
        stmt = select(Account.kyc_status).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        status = result.scalar_one_or_none()

        return status == KycStatus.VERIFIED

    async def verify_payout_eligibility(
        self,
        account_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """Check if account can receive payouts."""
        if not settings.kyc_required_for_payout:
            return True, None

        stmt = select(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            return False, "Account not found"

        if account.kyc_status != KycStatus.VERIFIED:
            return False, f"KYC not verified: {account.kyc_status.value}"

        if account.status != AccountStatus.ACTIVE:
            return False, f"Account not active: {account.status.value}"

        if account.requirements_past_due:
            return False, f"Pending requirements: {', '.join(account.requirements_past_due)}"

        return True, None


class SelfHostedKycProvider(KycProvider):
    """Self-hosted KYC provider implementation."""

    async def verify_identity(
        self,
        account_id: str,
        document_front: bytes,
        document_back: Optional[bytes] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Basic document verification."""
        # In production, integrate with Jumio/Veriff APIs
        # For MVP, basic file validation
        if not document_front:
            raise KycError("Document front is required")

        return {
            "status": "verified",
            "provider": "self_hosted",
            "reference": f"self_{account_id}_{int(datetime.now(timezone.utc).timestamp())}",
        }

    async def check_status(self, verification_id: str) -> Dict[str, Any]:
        """Check verification status."""
        return {
            "status": "verified",
            "verification_id": verification_id,
        }

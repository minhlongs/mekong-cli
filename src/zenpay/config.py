"""ZenPay configuration management."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Currency(str, Enum):
    """Supported currencies."""
    VND = "VND"
    USD = "USD"
    USDT = "USDT"


class StripeIntegrationChoice(str, Enum):
    """Stripe integration provider choice."""
    STRIPE = "stripe"
    WISE = "wise"


class KycProviderChoice(str, Enum):
    """KYC provider choice."""
    STRIPE = "stripe"
    JUMIO = "jumio"
    VERIFF = "veriff"
    SELF_HOSTED = "self_hosted"


@dataclass
class ZenPayConfig:
    """ZenPay configuration settings."""

    # Environment
    environment: Environment = field(default=Environment.DEVELOPMENT)
    debug: bool = field(default=True)

    # Stripe Configuration
    stripe_secret_key: str = field(default="")
    stripe_publishable_key: str = field(default="")
    stripe_webhook_secret: str = field(default="")
    stripe_account_id: Optional[str] = field(default=None)  # Platform account ID

    # Wise Configuration (optional alternative)
    wise_api_key: str = field(default="")
    wise_profile_id: str = field(default="")

    # Integration choice
    payment_provider: StripeIntegrationChoice = field(default=StripeIntegrationChoice.STRIPE)

    # Supported currencies
    supported_currencies: list[Currency] = field(default_factory=lambda: [
        Currency.VND, Currency.USD, Currency.USDT
    ])

    # Default currency for conversions
    base_currency: Currency = field(default=Currency.USD)

    # Self-custody wallet
    enable_self_custody: bool = field(default=True)
    eth_rpc_url: str = field(default="")  # For USDT on Ethereum
    # For Tron (TRC20 USDT) - faster/cheaper
    tron_rpc_url: str = field(default="")
    # Mnemonic or private key for wallet operations (stored encrypted)
    wallet_mnemonic_encrypted: str = field(default="")

    # KYC Configuration
    kyc_provider: KycProviderChoice = field(default=KycProviderChoice.STRIPE)
    kyc_webhook_secret: str = field(default="")
    kyc_required_for_wallet: bool = field(default=True)
    kyc_required_for_payout: bool = field(default=True)

    # Minimum balances
    min_payout_amount_vnd: int = field(default=10000)  # 10k VND
    min_payout_amount_usd: int = field(default=10)     # $10 USD
    min_payout_amount_usdt: float = field(default=10.0)  # 10 USDT

    # Fee structure (in basis points, 1% = 100 bps)
    payout_fee_bps_vnd: int = field(default=200)  # 2%
    payout_fee_bps_usd: int = field(default=150)  # 1.5%
    payout_fee_bps_usdt: int = field(default=100)  # 1%

    # Webhook endpoints
    webhook_base_url: str = field(default="http://localhost:8000")

    # Database
    database_url: str = field(default="postgresql+asyncpg://user:pass@localhost/zenpay")

    # Redis (for caching, rate limiting)
    redis_url: str = field(default="redis://localhost:6379")

    # Security
    jwt_secret_key: str = field(default="")
    api_key_header: str = field(default="X-API-Key")

    # Rate limiting
    rate_limit_requests_per_minute: int = field(default=60)

    @classmethod
    def from_env(cls) -> ZenPayConfig:
        """Load configuration from environment variables."""
        return cls(
            environment=Environment(os.getenv("ZENPAY_ENV", "development")),
            debug=os.getenv("ZENPAY_DEBUG", "true").lower() == "true",
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            stripe_publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
            stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
            stripe_account_id=os.getenv("STRIPE_ACCOUNT_ID"),
            wise_api_key=os.getenv("WISE_API_KEY", ""),
            wise_profile_id=os.getenv("WISE_PROFILE_ID", ""),
            payment_provider=StripeIntegrationChoice(
                os.getenv("PAYMENT_PROVIDER", "stripe").lower()
            ),
            supported_currencies=[
                Currency(c) for c in os.getenv(
                    "SUPPORTED_CURRENCIES", "VND,USD,USDT"
                ).split(",") if c
            ],
            base_currency=Currency(os.getenv("BASE_CURRENCY", "USD")),
            enable_self_custody=os.getenv("ENABLE_SELF_CUSTODY", "true").lower() == "true",
            eth_rpc_url=os.getenv("ETH_RPC_URL", ""),
            tron_rpc_url=os.getenv("TRON_RPC_URL", ""),
            wallet_mnemonic_encrypted=os.getenv("WALLET_MNEMONIC_ENCRYPTED", ""),
            kyc_provider=KycProviderChoice(
                os.getenv("KYC_PROVIDER", "stripe").lower()
            ),
            kyc_webhook_secret=os.getenv("KYC_WEBHOOK_SECRET", ""),
            kyc_required_for_wallet=os.getenv("KYC_REQUIRED_FOR_WALLET", "true").lower() == "true",
            kyc_required_for_payout=os.getenv("KYC_REQUIRED_FOR_PAYOUT", "true").lower() == "true",
            min_payout_amount_vnd=int(os.getenv("MIN_PAYOUT_VND", "10000")),
            min_payout_amount_usd=int(os.getenv("MIN_PAYOUT_USD", "10")),
            min_payout_amount_usdt=float(os.getenv("MIN_PAYOUT_USDT", "10.0")),
            payout_fee_bps_vnd=int(os.getenv("PAYOUT_FEE_VND", "200")),
            payout_fee_bps_usd=int(os.getenv("PAYOUT_FEE_USD", "150")),
            payout_fee_bps_usdt=int(os.getenv("PAYOUT_FEE_USDT", "100")),
            webhook_base_url=os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000"),
            database_url=os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/zenpay"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            jwt_secret_key=os.getenv("JWT_SECRET=REDACTED_KEY", ""),
            api_key_header=os.getenv("API_KEY_HEADER", "X-API-Key"),
            rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
        )


# Global settings instance
settings = ZenPayConfig.from_env()

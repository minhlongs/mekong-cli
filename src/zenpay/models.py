"""ZenPay database models using SQLAlchemy."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer,
    String, Text, JSON, Numeric, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base model class."""
    pass


class WalletType(str, Enum):
    """Wallet type enumeration."""
    CUSTODIAL = "custodial"      # Managed by ZenPay/Stripe
    SELF_CUSTODY = "self_custody"  # User-controlled (USDT wallet)
    VIRTUAL = "virtual"          # Internal accounting


class WalletStatus(str, Enum):
    """Wallet status enumeration."""
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"
    PENDING = "pending"


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYOUT = "payout"
    REFUND = "refund"
    FEE = "fee"
    CONVERSION = "conversion"
    INTERNAL = "internal"


class TransactionStatus(str, Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


class AccountType(str, Enum):
    """Account type for Stripe Connect."""
    INDIVIDUAL = "individual"
    COMPANY = "company"
    PLATFORM = "platform"


class AccountStatus(str, Enum):
    """Account status for Stripe Connect."""
    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    CLOSED = "closed"


class KycStatus(str, Enum):
    """KYC verification status."""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REQUIRES_ADDITIONAL = "requires_additional"


class Wallet(Base):
    """Wallet model for storing user balances."""
    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    wallet_type: Mapped[WalletType] = mapped_column(SQLEnum(WalletType), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # VND, USD, USDT
    status: Mapped[WalletStatus] = mapped_column(SQLEnum(WalletStatus), default=WalletStatus.ACTIVE)

    # Balances (in smallest unit for fiat, 8 decimals for crypto)
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    available_balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    hold_balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)

    # Stripe Connect references (for custodial wallets)
    stripe_account_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    stripe_card_id: Mapped[Optional[str]] = mapped_column(String(128))

    # Self-custody wallet references
    blockchain_address: Mapped[Optional[str]] = mapped_column(String(42), index=True)  # ETH address
    blockchain_network: Mapped[Optional[str]] = mapped_column(String(20))  # ethereum, tron

    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="wallet", lazy="selectin"
    )
    account: Mapped[Optional[Account]] = relationship(
        "Account", back_populates="wallet", uselist=False
    )

    __table_args__ = (
        Index("idx_wallet_user_currency", "user_id", "currency", unique=True),
    )


class Transaction(Base):
    """Transaction model for audit trail."""
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # UUID
    wallet_id: Mapped[str] = mapped_column(String(64), ForeignKey("wallets.id"), nullable=False, index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)

    # Amounts (in wallet currency)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # For conversions
    from_currency: Mapped[Optional[str]] = mapped_column(String(3))
    to_currency: Mapped[Optional[str]] = mapped_column(String(3))
    from_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    exchange_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))

    # External references (Stripe, blockchain, etc.)
    external_reference: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    external_provider: Mapped[Optional[str]] = mapped_column(String(50))  # stripe, wise, blockchain

    # Counterparty (for transfers)
    from_wallet_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("wallets.id"))
    to_wallet_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("wallets.id"))

    # Descriptive fields
    description: Mapped[Optional[str]] = mapped_column(Text)
    reference_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)  # User-provided reference

    # Metadata (webhook payload, etc.)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    wallet: Mapped[Wallet] = relationship("Wallet", back_populates="transactions", foreign_keys=[wallet_id])
    from_wallet: Mapped[Optional[Wallet]] = relationship("Wallet", foreign_keys=[from_wallet_id])
    to_wallet: Mapped[Optional[Wallet]] = relationship("Wallet", foreign_keys=[to_wallet_id])


class Account(Base):
    """Stripe Connect account model."""
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    wallet_id: Mapped[str] = mapped_column(String(64), ForeignKey("wallets.id"), nullable=False, unique=True)

    account_type: Mapped[AccountType] = mapped_column(SQLEnum(AccountType), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(SQLEnum(AccountStatus), default=AccountStatus.PENDING)

    # Stripe references
    stripe_account_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    # Individual/Company details
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    # For individuals
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    dob: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    id_number: Mapped[Optional[str]] = mapped_column(String(50))
    id_number_type: Mapped[Optional[str]] = mapped_column(String(50))

    # For companies
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    tax_id: Mapped[Optional[str]] = mapped_column(String(100))
    business_type: Mapped[Optional[str]] = mapped_column(String(100))

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(2))  # ISO 3166-1 alpha-2
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))

    # Payout settings
    default_payout_currency: Mapped[str] = mapped_column(String(3), default="USD")
    payout_schedule: Mapped[Optional[str]] = mapped_column(String(50))  # daily, weekly, monthly
    minimum_payout_amount: Mapped[Optional[int]] = mapped_column(Integer)

    # KYC status
    kyc_status: Mapped[KycStatus] = mapped_column(SQLEnum(KycStatus), default=KycStatus.UNVERIFIED)
    kyc_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    kyc_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Requirements
    requirements_currently_due: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)
    requirements_past_due: Mapped[Optional[list[str]]] = mapped_column(JSON, default=list)

    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    wallet: Mapped[Wallet] = relationship("Wallet", back_populates="account")
    kyc_profiles: Mapped[list[KycProfile]] = relationship(
        "KycProfile", back_populates="account", cascade="all, delete-orphan"
    )


class KycProfile(Base):
    """KYC profile model."""
    __tablename__ = "kyc_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.id"), nullable=False, index=True)

    # Provider
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # stripe, jumio, veriff
    provider_reference: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[KycStatus] = mapped_column(SQLEnum(KycStatus), default=KycStatus.PENDING)

    # Verification data
    verification_method: Mapped[Optional[str]] = mapped_column(String(100))
    verification_level: Mapped[Optional[str]] = mapped_column(String(50))

    # Document references
    document_front_url: Mapped[Optional[str]] = mapped_column(String(500))
    document_back_url: Mapped[Optional[str]] = mapped_column(String(500))
    document_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Risk assessment
    risk_level: Mapped[Optional[str]] = mapped_column(String(20))  # low, medium, high
    risk_score: Mapped[Optional[float]] = mapped_column(Float)

    # Rejection reason (if rejected)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Metadata (full provider response)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    account: Mapped[Account] = relationship("Account", back_populates="kyc_profiles")


class ExchangeRate(Base):
    """Exchange rate cache model."""
    __tablename__ = "exchange_rates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    from_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)

    source: Mapped[str] = mapped_column(String(50), nullable=False)  # stripe, wise, coinbase
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_exchange_rate_unique", "from_currency", "to_currency", "source", unique=True),
        Index("idx_exchange_rate_expires", "expires_at"),
    )


class Balance(Base):
    """Aggregated balance model for reporting."""
    __tablename__ = "balances"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    total_balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    available_balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    hold_balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)

    wallet_count: Mapped[int] = mapped_column(Integer, default=0)

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_balance_user_currency", "user_id", "currency", unique=True),
    )

"""ZenPay database migration - initial schema."""

from __future__ import annotations

from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_zenpay_initial"
down_revision = None  # Adjust based on existing migrations
branch_labels = ("zenpay",)
depends_on = None


def upgrade() -> None:
    """Create ZenPay tables."""
    # Wallets
    op.create_table(
        "wallets",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False, index=True),
        sa.Column("wallet_type", sa.Enum("custodial", "self_custody", "virtual", name="wallet_type"), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.Enum("active", "frozen", "closed", "pending", name="wallet_status"), default="active"),
        sa.Column("balance", sa.Numeric(20, 8), default=0),
        sa.Column("available_balance", sa.Numeric(20, 8), default=0),
        sa.Column("hold_balance", sa.Numeric(20, 8), default=0),
        sa.Column("stripe_account_id", sa.String(128), index=True),
        sa.Column("stripe_customer_id", sa.String(128), index=True),
        sa.Column("stripe_card_id", sa.String(128)),
        sa.Column("blockchain_address", sa.String(42), index=True),
        sa.Column("blockchain_network", sa.String(20)),
        sa.Column("metadata", postgresql.JSONB, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    op.create_index("idx_wallet_user_currency", "wallets", ["user_id", "currency"], unique=True)

    # Transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("wallet_id", sa.String(64), sa.ForeignKey("wallets.id"), nullable=False, index=True),
        sa.Column("transaction_type", sa.Enum("deposit", "withdrawal", "transfer", "payout", "refund", "fee", "conversion", "internal", name="transaction_type"), nullable=False),
        sa.Column("status", sa.Enum("pending", "processing", "completed", "failed", "cancelled", "reversed", name="transaction_status"), default="pending"),
        sa.Column("amount", sa.Numeric(20, 8), nullable=False),
        sa.Column("fee_amount", sa.Numeric(20, 8), default=0),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("from_currency", sa.String(3)),
        sa.Column("to_currency", sa.String(3)),
        sa.Column("from_amount", sa.Numeric(20, 8)),
        sa.Column("exchange_rate", sa.Numeric(20, 8)),
        sa.Column("external_reference", sa.String(255), index=True),
        sa.Column("external_provider", sa.String(50)),
        sa.Column("from_wallet_id", sa.String(64), sa.ForeignKey("wallets.id")),
        sa.Column("to_wallet_id", sa.String(64), sa.ForeignKey("wallets.id")),
        sa.Column("description", sa.Text),
        sa.Column("reference_id", sa.String(128), index=True),
        sa.Column("metadata", postgresql.JSONB, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_transaction_wallet", "transactions", ["wallet_id"])
    op.create_index("idx_transaction_external_ref", "transactions", ["external_reference"])
    op.create_index("idx_transaction_created", "transactions", ["created_at"])

    # Accounts (Stripe Connect)
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False, index=True),
        sa.Column("wallet_id", sa.String(64), sa.ForeignKey("wallets.id"), nullable=False, unique=True),
        sa.Column("account_type", sa.Enum("individual", "company", "platform", name="account_type"), nullable=False),
        sa.Column("status", sa.Enum("pending", "active", "restricted", "closed", name="account_status"), default="pending"),
        sa.Column("stripe_account_id", sa.String(128), unique=True, index=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50)),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("dob", sa.DateTime(timezone=True)),
        sa.Column("id_number", sa.String(50)),
        sa.Column("id_number_type", sa.String(50)),
        sa.Column("company_name", sa.String(255)),
        sa.Column("tax_id", sa.String(100)),
        sa.Column("business_type", sa.String(100)),
        sa.Column("address_line1", sa.String(255)),
        sa.Column("address_line2", sa.String(255)),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(100)),
        sa.Column("country", sa.String(2)),
        sa.Column("postal_code", sa.String(20)),
        sa.Column("default_payout_currency", sa.String(3), default="USD"),
        sa.Column("payout_schedule", sa.String(50)),
        sa.Column("minimum_payout_amount", sa.Integer),
        sa.Column("kyc_status", sa.Enum("unverified", "pending", "verified", "rejected", "requires_additional", name="kyc_status"), default="unverified"),
        sa.Column("kyc_submitted_at", sa.DateTime(timezone=True)),
        sa.Column("kyc_verified_at", sa.DateTime(timezone=True)),
        sa.Column("requirements_currently_due", postgresql.JSONB, default=list),
        sa.Column("requirements_past_due", postgresql.JSONB, default=list),
        sa.Column("metadata", postgresql.JSONB, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    op.create_index("idx_account_user", "accounts", ["user_id"])
    op.create_index("idx_account_stripe_id", "accounts", ["stripe_account_id"])

    # KYC Profiles
    op.create_table(
        "kyc_profiles",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("account_id", sa.String(64), sa.ForeignKey("accounts.id"), nullable=False, index=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_reference", sa.String(255), nullable=False),
        sa.Column("status", sa.Enum("unverified", "pending", "verified", "rejected", "requires_additional", name="kyc_status"), default="pending"),
        sa.Column("verification_method", sa.String(100)),
        sa.Column("verification_level", sa.String(50)),
        sa.Column("document_front_url", sa.String(500)),
        sa.Column("document_back_url", sa.String(500)),
        sa.Column("document_type", sa.String(50)),
        sa.Column("risk_level", sa.String(20)),
        sa.Column("risk_score", sa.Float),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("metadata", postgresql.JSONB, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # Exchange Rates
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("from_currency", sa.String(3), nullable=False),
        sa.Column("to_currency", sa.String(3), nullable=False),
        sa.Column("rate", sa.Numeric(20, 8), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    op.create_index("idx_exchange_rate_unique", "exchange_rates", ["from_currency", "to_currency", "source"], unique=True)
    op.create_index("idx_exchange_rate_expires", "exchange_rates", ["expires_at"])

    # Balances (aggregated)
    op.create_table(
        "balances",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False, index=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("total_balance", sa.Numeric(20, 8), default=0),
        sa.Column("available_balance", sa.Numeric(20, 8), default=0),
        sa.Column("hold_balance", sa.Numeric(20, 8), default=0),
        sa.Column("wallet_count", sa.Integer, default=0),
        sa.Column("last_updated", sa.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    op.create_index("idx_balance_user_currency", "balances", ["user_id", "currency"], unique=True)


def downgrade() -> None:
    """Drop ZenPay tables."""
    op.drop_table("balances")
    op.drop_table("exchange_rates")
    op.drop_table("kyc_profiles")
    op.drop_table("accounts")
    op.drop_table("transactions")
    op.drop_table("wallets")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS wallet_type")
    op.execute("DROP TYPE IF EXISTS wallet_status")
    op.execute("DROP TYPE IF EXISTS transaction_type")
    op.execute("DROP TYPE IF EXISTS transaction_status")
    op.execute("DROP TYPE IF EXISTS account_type")
    op.execute("DROP TYPE IF EXISTS account_status")
    op.execute("DROP TYPE IF EXISTS kyc_status")

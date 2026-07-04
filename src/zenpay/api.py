"""ZenPay API router - all /v1/zenpay endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.database import get_database
from ...core.auth_jwt import decode_jwt
from .config import settings
from .exceptions import (
    WalletNotFoundError, InsufficientFundsError, KycNotVerifiedError,
    WalletError, ZenPayError
)
from .models import (
    Wallet, Transaction, TransactionType, TransactionStatus,
    WalletType, WalletStatus, Account, AccountType, KycStatus
)
from .stripe_client import get_stripe_client
from .treasury import TreasuryManager
from .wallet import WalletManager
from .kyc import KycService

router = APIRouter(prefix="/v1/zenpay", tags=["zenpay"])


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class WalletCreate(BaseModel):
    """Request to create a wallet."""
    currency: str = Field(..., description="Currency code: VND, USD, USDT")
    wallet_type: str = Field(default="custodial", description="custodial|self_custody|virtual")


class WalletResponse(BaseModel):
    """Wallet response model."""
    id: str
    user_id: str
    currency: str
    wallet_type: str
    status: str
    balance: float
    available_balance: float
    hold_balance: float
    stripe_account_id: Optional[str] = None
    blockchain_address: Optional[str] = None
    created_at: datetime


class TransactionResponse(BaseModel):
    """Transaction response model."""
    id: str
    wallet_id: str
    transaction_type: str
    status: str
    amount: float
    fee_amount: float
    currency: str
    description: Optional[str] = None
    external_reference: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class PayoutRequest(BaseModel):
    """Request to create a payout."""
    wallet_id: str
    amount: float = Field(..., gt=0)
    currency: str
    destination_type: str = Field(..., description="bank_account|card|crypto")
    destination_id: str = Field(..., description="Bank account ID or crypto address")
    description: Optional[str] = None


class PayoutResponse(BaseModel):
    """Payout response model."""
    id: str
    wallet_id: str
    amount: float
    currency: str
    fee_amount: float
    destination_type: str
    destination_id: str
    status: str
    external_reference: Optional[str] = None
    estimated_arrival: Optional[datetime] = None
    created_at: datetime


class BalanceResponse(BaseModel):
    """Balance response model."""
    currency: str
    available: float
    total: float
    hold: float


class KycStatusResponse(BaseModel):
    """KYC status response."""
    status: str
    verified_at: Optional[datetime] = None
    requirements_currently_due: list[str] = []
    requirements_past_due: list[str] = []
    account_status: str


class ExchangeRateResponse(BaseModel):
    """Exchange rate response."""
    from_currency: str
    to_currency: str
    rate: float
    source: str
    expires_at: datetime


class ConversionRequest(BaseModel):
    """Currency conversion request."""
    from_currency: str
    to_currency: str
    amount: float = Field(..., gt=0)
    wallet_id: str


class ConversionResponse(BaseModel):
    """Conversion response."""
    from_currency: str
    to_currency: str
    from_amount: float
    to_amount: float
    exchange_rate: float
    fee_amount: float
    transaction_id: str


class AccountCreate(BaseModel):
    """Create connected account request."""
    email: str
    account_type: str = Field(..., description="individual|company")
    country: str = Field(default="US")
    default_currency: str = Field(default="USD")


class AccountResponse(BaseModel):
    """Connected account response."""
    id: str
    user_id: str
    stripe_account_id: str
    account_type: str
    status: str
    email: str
    kyc_status: str
    onboarding_url: Optional[str] = None


# ============================================================================
# Dependencies
# ============================================================================

async def get_user_id_from_token(
    authorization: str = Header(..., alias="Authorization")
) -> str:
    """Extract user_id from JWT token."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_jwt(token)
        return payload["user_id"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def get_db_session() -> AsyncSession:
    """Get database session."""
    async for session in get_database():
        return session


def get_wallet_manager(
    db: AsyncSession = Depends(get_db_session)
) -> WalletManager:
    """Get wallet manager instance."""
    return WalletManager(db)


def get_treasury_manager(
    db: AsyncSession = Depends(get_db_session)
) -> TreasuryManager:
    """Get treasury manager instance."""
    return TreasuryManager(db)


def get_kyc_service(
    db: AsyncSession = Depends(get_db_session)
) -> KycService:
    """Get KYC service instance."""
    return KycService(db)


# ============================================================================
# Wallet Endpoints
# ============================================================================

@router.post("/wallets", response_model=WalletResponse, status_code=201)
async def create_wallet(
    wallet_data: WalletCreate,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
    wallet_manager: WalletManager = Depends(get_wallet_manager),
):
    """Create a new wallet for the user."""
    try:
        wallet_type = WalletType(wallet_data.wallet_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid wallet_type. Use: {[t.value for t in WalletType]}")

    if wallet_data.currency.upper() not in settings.supported_currencies:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported currency. Supported: {settings.supported_currencies}"
        )

    try:
        wallet = await wallet_manager.create_wallet(
            user_id=user_id,
            currency=wallet_data.currency.upper(),
            wallet_type=wallet_type,
        )
        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            currency=wallet.currency,
            wallet_type=wallet.wallet_type.value,
            status=wallet.status.value,
            balance=float(wallet.balance),
            available_balance=float(wallet.available_balance),
            hold_balance=float(wallet.hold_balance),
            stripe_account_id=wallet.stripe_account_id,
            blockchain_address=wallet.blockchain_address,
            created_at=wallet.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallets/{currency}", response_model=WalletResponse)
async def get_wallet(
    currency: str,
    user_id: str = Depends(get_user_id_from_token),
    wallet_type: str = "custodial",
    db: AsyncSession = Depends(get_db_session),
    wallet_manager: WalletManager = Depends(get_wallet_manager),
):
    """Get user's wallet by currency."""
    try:
        wtype = WalletType(wallet_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid wallet_type")

    wallet = await wallet_manager.get_wallet(user_id, currency.upper(), wtype)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        currency=wallet.currency,
        wallet_type=wallet.wallet_type.value,
        status=wallet.status.value,
        balance=float(wallet.balance),
        available_balance=float(wallet.available_balance),
        hold_balance=float(wallet.hold_balance),
        stripe_account_id=wallet.stripe_account_id,
        blockchain_address=wallet.blockchain_address,
        created_at=wallet.created_at,
    )


@router.get("/wallets", response_model=list[WalletResponse])
async def list_wallets(
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
):
    """List all wallets for the user."""
    stmt = select(Wallet).where(
        Wallet.user_id == user_id,
        Wallet.status != WalletStatus.CLOSED
    ).order_by(Wallet.created_at.desc())
    result = await db.execute(stmt)
    wallets = result.scalars().all()

    return [
        WalletResponse(
            id=w.id,
            user_id=w.user_id,
            currency=w.currency,
            wallet_type=w.wallet_type.value,
            status=w.status.value,
            balance=float(w.balance),
            available_balance=float(w.available_balance),
            hold_balance=float(w.hold_balance),
            stripe_account_id=w.stripe_account_id,
            blockchain_address=w.blockchain_address,
            created_at=w.created_at,
        )
        for w in wallets
    ]


@router.get("/balance", response_model=dict[str, BalanceResponse])
async def get_balance(
    user_id: str = Depends(get_user_id_from_token),
    currency: Optional[str] = None,
    treasury: TreasuryManager = Depends(get_treasury_manager),
):
    """Get user balance."""
    balances = await treasury.get_user_balance(user_id, currency)

    response = {}
    for curr, bal in balances.items():
        response[curr] = BalanceResponse(
            currency=curr,
            available=float(bal["available"]),
            total=float(bal["total"]),
            hold=float(bal["hold"]),
        )

    if currency and currency.upper() not in response:
        raise HTTPException(status_code=404, detail="No balance found for currency")

    return response


# ============================================================================
# Transaction Endpoints
# ============================================================================

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
    wallet_manager: WalletManager = Depends(get_wallet_manager),
):
    """Get transaction by ID."""
    txn = await wallet_manager.get_transaction(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Verify ownership
    wallet = await wallet_manager.get_wallet_by_id(txn.wallet_id)
    if wallet.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return TransactionResponse(
        id=txn.id,
        wallet_id=txn.wallet_id,
        transaction_type=txn.transaction_type.value,
        status=txn.status.value,
        amount=float(txn.amount),
        fee_amount=float(txn.fee_amount),
        currency=txn.currency,
        description=txn.description,
        external_reference=txn.external_reference,
        completed_at=txn.completed_at,
        created_at=txn.created_at,
    )


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    wallet_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
):
    """List transactions with optional filters."""
    from sqlalchemy import and_

    # Build query
    conditions = []

    if wallet_id:
        conditions.append(Transaction.wallet_id == wallet_id)
    else:
        # Get all user's wallet IDs
        wallet_stmt = select(Wallet.id).where(Wallet.user_id == user_id)
        wallet_result = await db.execute(wallet_stmt)
        wallet_ids = [row[0] for row in wallet_result.all()]
        if not wallet_ids:
            return []
        conditions.append(Transaction.wallet_id.in_(wallet_ids))

    if transaction_type:
        try:
            ttype = TransactionType(transaction_type)
            conditions.append(Transaction.transaction_type == ttype)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid transaction_type")

    if status:
        try:
            tstatus = TransactionStatus(status)
            conditions.append(Transaction.status == tstatus)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status")

    stmt = select(Transaction).where(and_(*conditions)).order_by(
        Transaction.created_at.desc()
    ).limit(limit).offset(offset)

    result = await db.execute(stmt)
    transactions = result.scalars().all()

    return [
        TransactionResponse(
            id=t.id,
            wallet_id=t.wallet_id,
            transaction_type=t.transaction_type.value,
            status=t.status.value,
            amount=float(t.amount),
            fee_amount=float(t.fee_amount),
            currency=t.currency,
            description=t.description,
            external_reference=t.external_reference,
            completed_at=t.completed_at,
            created_at=t.created_at,
        )
        for t in transactions
    ]


# ============================================================================
# Transfer & Conversion Endpoints
# ============================================================================

@router.post("/transfer")
async def transfer_funds(
    from_wallet_id: str,
    to_wallet_id: str,
    amount: float,
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
    wallet_manager: WalletManager = Depends(get_wallet_manager),
):
    """Transfer funds between wallets (same currency)."""
    try:
        txn = await wallet_manager.transfer(
            from_wallet_id=from_wallet_id,
            to_wallet_id=to_wallet_id,
            amount=Decimal(str(amount)),
            description=description,
            reference_id=reference_id,
        )
        return {
            "success": True,
            "transaction_id": txn.id,
            "amount": float(txn.amount),
            "currency": txn.currency,
        }
    except WalletError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert", response_model=ConversionResponse)
async def convert_currency(
    conversion: ConversionRequest,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
    treasury: TreasuryManager = Depends(get_treasury_manager),
    wallet_manager: WalletManager = Depends(get_wallet_manager),
):
    """Convert currency using exchange rates."""
    from_wallet = await wallet_manager.get_wallet(
        user_id, conversion.from_currency.upper()
    )
    to_wallet = await wallet_manager.get_wallet(
        user_id, conversion.to_currency.upper()
    )

    if not from_wallet:
        raise HTTPException(status_code=404, detail=f"Source {conversion.from_currency} wallet not found")
    if not to_wallet:
        raise HTTPException(status_code=404, detail=f"Destination {conversion.to_currency} wallet not found")

    try:
        # Get exchange rate and calculate converted amount
        rate = await treasury.get_exchange_rate(
            conversion.from_currency.upper(),
            conversion.to_currency.upper()
        )
        to_amount = Decimal(str(conversion.amount)) * rate

        # Debit source wallet
        await wallet_manager.debit(
            from_wallet.id,
            Decimal(str(conversion.amount)),
            description=f"Convert to {conversion.to_currency}",
        )

        # Credit destination wallet
        await wallet_manager.credit(
            to_wallet.id,
            to_amount,
            description=f"Convert from {conversion.from_currency}",
        )

        # Record conversion transaction on source wallet
        txn_id = f"conv_{int(datetime.now().timestamp())}_{from_wallet.id}"

        return ConversionResponse(
            from_currency=conversion.from_currency.upper(),
            to_currency=conversion.to_currency.upper(),
            from_amount=conversion.amount,
            to_amount=float(to_amount),
            exchange_rate=float(rate),
            fee_amount=0.0,  # No fee for internal conversion
            transaction_id=txn_id,
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-rate", response_model=ExchangeRateResponse)
async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    refresh: bool = False,
    treasury: TreasuryManager = Depends(get_treasury_manager),
):
    """Get current exchange rate."""
    try:
        rate = await treasury.get_exchange_rate(
            from_currency.upper(),
            to_currency.upper(),
            refresh=refresh
        )
        # Get cache expiry (simplified)
        return ExchangeRateResponse(
            from_currency=from_currency.upper(),
            to_currency=to_currency.upper(),
            rate=float(rate),
            source="stripe",
            expires_at=datetime.now(timezone.utc).replace(hour=datetime.now().hour + 1),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Payout Endpoints
# ============================================================================

@router.post("/payouts", response_model=PayoutResponse, status_code=202)
async def create_payout(
    payout_request: PayoutRequest,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
    wallet_manager: WalletManager = Depends(get_wallet_manager),
    kyc_service: KycService = Depends(get_kyc_service),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Request a payout from wallet to external destination."""
    # Get wallet
    wallet = await wallet_manager.get_wallet(user_id, payout_request.currency)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if wallet.id != payout_request.wallet_id:
        raise HTTPException(status_code=400, detail="Wallet ID mismatch")

    # Check KYC if required
    if settings.kyc_required_for_payout and wallet.account_id:
        eligible, reason = await kyc_service.verify_payout_eligibility(wallet.account_id)
        if not eligible:
            raise HTTPException(status_code=403, detail=f"KYC verification required: {reason}")

    # Validate amount and balance
    amount = Decimal(str(payout_request.amount))
    if wallet.available_balance < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance: {wallet.available_balance} available"
        )

    # Calculate fee
    fee, total = await wallet_manager.calculate_payout_fee(amount, payout_request.currency)

    # Process payout based on destination type
    stripe_client = get_stripe_client()
    external_reference = None

    try:
        if payout_request.destination_type == "bank_account":
            # Use Stripe Connect for bank payouts
            if not wallet.stripe_account_id:
                raise HTTPException(status_code=400, detail="No connected Stripe account")

            payout = stripe_client.create_payout(
                account_id=wallet.stripe_account_id,
                amount=int(amount * 100),  # Convert to cents
                currency=payout_request.currency.lower(),
                method="standard",
            )
            external_reference = payout.id

        elif payout_request.destination_type == "card":
            # Card payout via Stripe
            if not wallet.stripe_account_id:
                raise HTTPException(status_code=400, detail="No connected Stripe account")

            # Create transfer to card
            transfer = stripe_client.create_transfer(
                destination_account_id=wallet.stripe_account_id,
                amount=int(total * 100),
                currency=payout_request.currency.lower(),
                description=payout_request.description or "Payout to card",
            )
            external_reference = transfer.id

        elif payout_request.destination_type == "crypto":
            # USDT to external crypto address
            if payout_request.currency.upper() != "USDT":
                raise HTTPException(status_code=400, detail="Crypto payouts only support USDT")

            # Self-custody transfer (handled async)
            background_tasks.add_task(
                _process_crypto_payout,
                wallet.id,
                payout_request.destination_id,
                amount,
            )
            external_reference = f"crypto_{int(datetime.now().timestamp())}"

        else:
            raise HTTPException(status_code=400, detail=f"Invalid destination_type: {payout_request.destination_type}")

        # Create transaction record
        txn = await wallet_manager.debit(
            wallet_id=wallet.id,
            amount=total,
            description=payout_request.description or f"Payout to {payout_request.destination_type}",
            external_reference=external_reference,
            metadata={
                "payout_fee": float(fee),
                "destination_type": payout_request.destination_type,
                "destination_id": payout_request.destination_id,
            },
        )

        return PayoutResponse(
            id=txn.id,
            wallet_id=wallet.id,
            amount=float(amount),
            currency=payout_request.currency,
            fee_amount=float(fee),
            destination_type=payout_request.destination_type,
            destination_id=payout_request.destination_id,
            status="processing",
            external_reference=external_reference,
            created_at=txn.created_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _process_crypto_payout(
    wallet_id: str,
    to_address: str,
    amount: Decimal,
):
    """Background task for crypto payout."""
    # Import here to avoid circular dependency
    from .wallet import SelfCustodyWallet

    db = await get_database().__anext__()
    wallet_manager = WalletManager(db)
    wallet = await wallet_manager.get_wallet_by_id(wallet_id)

    if not wallet:
        logger.error(f"Wallet not found for crypto payout: {wallet_id}")
        return

    try:
        self_wallet = SelfCustodyWallet.from_settings()
        if not self_wallet:
            raise SelfCustodyError("Self-custody wallet not configured")

        # Choose network (Tron is cheaper)
        tx_hash, status = await self_wallet.send_usdt_tron(to_address, amount)

        # Update transaction with tx hash
        stmt = select(Transaction).where(
            Transaction.external_reference.startswith("crypto_")
        ).order_by(Transaction.created_at.desc()).limit(1)
        result = await db.execute(stmt)
        txn = result.scalar_one_or_none()
        if txn:
            txn.external_reference = tx_hash
            await db.commit()

        logger.info(f"Crypto payout completed: {tx_hash}")
    except Exception as e:
        logger.error(f"Crypto payout failed: {e}")


# ============================================================================
# Connected Account (Stripe Connect) Endpoints
# ============================================================================

@router.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_connected_account(
    account_data: AccountCreate,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a Stripe Connect account for the user."""
    stripe_client = get_stripe_client()

    try:
        stripe_account = stripe_client.create_connected_account(
            user_id=user_id,
            email=account_data.email,
            account_type=account_data.account_type,
            country=account_data.country,
            default_currency=account_data.default_currency,
        )

        # Create or update wallet with Stripe account ID
        wallet = await WalletManager(db).get_wallet(
            user_id, account_data.default_currency
        )
        if not wallet:
            wallet = await WalletManager(db).create_wallet(
                user_id=user_id,
                currency=account_data.default_currency,
                wallet_type=WalletType.CUSTODIAL,
                stripe_account_id=stripe_account.id,
            )
        else:
            wallet.stripe_account_id = stripe_account.id
            await db.commit()

        # Create account record
        account = Account(
            id=f"acc_{user_id}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            wallet_id=wallet.id,
            account_type=AccountType(account_data.account_type),
            status=AccountStatus.PENDING,
            stripe_account_id=stripe_account.id,
            email=account_data.email,
            default_payout_currency=account_data.default_currency,
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)

        return AccountResponse(
            id=account.id,
            user_id=account.user_id,
            stripe_account_id=account.stripe_account_id,
            account_type=account.account_type.value,
            status=account.status.value,
            email=account.email,
            kyc_status=account.kyc_status.value,
            onboarding_url=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts", response_model=list[AccountResponse])
async def list_connected_accounts(
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
):
    """List user's connected accounts."""
    stmt = select(Account).where(Account.user_id == user_id).order_by(Account.created_at.desc())
    result = await db.execute(stmt)
    accounts = result.scalars().all()

    return [
        AccountResponse(
            id=a.id,
            user_id=a.user_id,
            stripe_account_id=a.stripe_account_id,
            account_type=a.account_type.value,
            status=a.status.value,
            email=a.email,
            kyc_status=a.kyc_status.value,
            onboarding_url=None,
        )
        for a in accounts
    ]


@router.post("/accounts/{account_id}/onboarding-link")
async def create_onboarding_link(
    account_id: str,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
):
    """Create onboarding link for Stripe Connect account."""
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    stripe_client = get_stripe_client()
    return_url = f"{settings.webhook_base_url}/v1/zenpay/accounts/{account_id}/onboarding-complete"

    try:
        link = stripe_client.create_account_link(
            account_id=account.stripe_account_id,
            refresh_url=f"{settings.webhook_base_url}/v1/zenpay/accounts/{account_id}/onboarding-refresh",
            return_url=return_url,
        )
        return {"onboarding_url": link["url"], "expires_at": link["expires_at"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/kyc-status", response_model=KycStatusResponse)
async def get_account_kyc_status(
    account_id: str,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db_session),
    kyc_service: KycService = Depends(get_kyc_service),
):
    """Get KYC status for an account."""
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return KycStatusResponse(
        status=account.kyc_status.value,
        verified_at=account.kyc_verified_at,
        requirements_currently_due=account.requirements_currently_due or [],
        requirements_past_due=account.requirements_past_due or [],
        account_status=account.status.value,
    )


# ============================================================================
# Self-Custody Wallet Endpoints
# ============================================================================

@router.get("/self-custody/balance")
async def get_self_custody_balance(
    user_id: str = Depends(get_user_id_from_token),
):
    """Get USDT balance from self-custody wallet."""
    try:
        from .wallet import SelfCustodyWallet
        wallet = SelfCustodyWallet.from_settings()
        if not wallet:
            raise HTTPException(status_code=503, detail="Self-custody wallet not configured")

        balance = await wallet.get_usdt_balance_tron()
        return {
            "currency": "USDT",
            "balance": float(balance),
            "network": "tron",
            "address": wallet.get_tron_address(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/self-custody/send")
async def send_self_custody(
    to_address: str,
    amount: float,
    user_id: str = Depends(get_user_id_from_token),
):
    """Send USDT from self-custody wallet."""
    try:
        from .wallet import SelfCustodyWallet
        wallet = SelfCustodyWallet.from_settings()
        if not wallet:
            raise HTTPException(status_code=503, detail="Self-custody wallet not configured")

        tx_hash, status = await wallet.send_usdt_tron(
            to_address=to_address,
            amount=Decimal(str(amount)),
        )
        return {
            "success": True,
            "tx_hash": tx_hash,
            "status": status,
            "amount": amount,
            "to_address": to_address,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Webhook Endpoint
# ============================================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """Handle Stripe Connect webhooks."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        stripe_client = get_stripe_client()
        event = stripe_client.webhook_signature_verify(payload, signature)
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})

    # Handle different event types
    if event_type == "payout.paid":
        background_tasks.add_task(_handle_payout_paid, db, event_data)
    elif event_type == "payout.failed":
        background_tasks.add_task(_handle_payout_failed, db, event_data)
    elif event_type == "account.updated":
        background_tasks.add_task(_handle_account_updated, db, event_data)
    elif event_type == "charge.refunded":
        background_tasks.add_task(_handle_charge_refunded, db, event_data)

    return {"received": True}


async def _handle_payout_paid(db: AsyncSession, payout_data: dict):
    """Handle payout.paid webhook."""
    payout_id = payout_data.get("id")
    account_id = payout_data.get("destination")  # Stripe account ID

    stmt = select(Transaction).where(
        Transaction.external_reference == payout_id
    )
    result = await db.execute(stmt)
    txn = result.scalar_one_or_none()

    if txn:
        txn.status = TransactionStatus.COMPLETED
        txn.completed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Payout {payout_id} marked as completed")


async def _handle_payout_failed(db: AsyncSession, payout_data: dict):
    """Handle payout.failed webhook."""
    payout_id = payout_data.get("id")
    failure_reason = payout_data.get("failure_reason", "Unknown")

    stmt = select(Transaction).where(
        Transaction.external_reference == payout_id
    )
    result = await db.execute(stmt)
    txn = result.scalar_one_or_none()

    if txn:
        txn.status = TransactionStatus.FAILED
        txn.metadata["failure_reason"] = failure_reason
        await db.commit()
        logger.warning(f"Payout {payout_id} failed: {failure_reason}")


async def _handle_account_updated(db: AsyncSession, account_data: dict):
    """Handle account.updated webhook."""
    stripe_account_id = account_data.get("id")
    requirements = account_data.get("requirements", {})

    stmt = select(Account).where(Account.stripe_account_id == stripe_account_id)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account:
        kyc_service = KycService(db)
        await kyc_service._update_account_kyc_status(account, requirements)


async def _handle_charge_refunded(db: AsyncSession, charge_data: dict):
    """Handle charge.refunded webhook."""
    # Create refund transactions
    pass


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "zenpay",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

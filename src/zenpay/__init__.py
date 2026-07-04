"""ZenPay Money OS - Multi-currency Payment & Treasury Platform.

A comprehensive financial infrastructure supporting:
- Stripe Connect integration for marketplace payouts
- Multi-currency treasury (VND, USD, USDT)
- Self-custody wallet option
- KYC compliance handling
- API endpoints at /v1/zenpay/*
"""

__version__ = "0.1.0"
__author__ = "Mekong CLI Team"

from .config import settings, ZenPayConfig
from .models import (
    Wallet, WalletType, WalletStatus,
    Transaction, TransactionType, TransactionStatus,
    Account, AccountType, AccountStatus,
    KycProfile, KycStatus,
    ExchangeRate, Balance,
)
from .stripe_client import StripeConnectClient
from .treasury import TreasuryManager
from .wallet import WalletManager, SelfCustodyWallet
from .kyc import KycService, KycProvider
from .api import router as zenpay_router

__all__ = [
    "settings",
    "ZenPayConfig",
    "Wallet",
    "WalletType",
    "WalletStatus",
    "Transaction",
    "TransactionType",
    "TransactionStatus",
    "Account",
    "AccountType",
    "AccountStatus",
    "KycProfile",
    "KycStatus",
    "ExchangeRate",
    "Balance",
    "StripeConnectClient",
    "TreasuryManager",
    "WalletManager",
    "SelfCustodyWallet",
    "KycService",
    "KycProvider",
    "zenpay_router",
]

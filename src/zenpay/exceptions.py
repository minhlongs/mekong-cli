"""Custom exceptions for ZenPay."""

from __future__ import annotations


class ZenPayError(Exception):
    """Base exception for ZenPay errors."""
    pass


class StripeError(ZenPayError):
    """Stripe API error."""
    pass


class AccountNotFoundError(ZenPayError):
    """Account not found error."""
    pass


class WalletError(ZenPayError):
    """Wallet operation error."""
    pass


class InsufficientFundsError(ZenPayError):
    """Insufficient funds error."""
    pass


class WalletNotFoundError(ZenPayError):
    """Wallet not found error."""
    pass


class TransactionError(ZenPayError):
    """Transaction error."""
    pass


class KycError(ZenPayError):
    """KYC-related error."""
    pass


class KycNotVerifiedError(ZenPayError):
    """KYC not verified error."""
    pass


class SelfCustodyError(ZenPayError):
    """Self-custody wallet error."""
    pass


class ExchangeRateError(ZenPayError):
    """Exchange rate error."""
    pass


class ValidationError(ZenPayError):
    """Validation error."""
    pass


class RateLimitError(ZenPayError):
    """Rate limit exceeded error."""
    pass


class PermissionError(ZenPayError):
    """Permission denied error."""
    pass

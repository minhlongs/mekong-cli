# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Compatibility shim — src.mekong.zenpay → src.mekong.treasury

The zenpay module was removed in f5c54c11c but CLI commands still reference it.
"""
from src.mekong.treasury.service import TreasuryService  # noqa: F401
from src.mekong.treasury.models import Transaction  # noqa: F401

__all__ = ["TreasuryService", "Transaction"]

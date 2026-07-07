"""Compatibility shim — re-export Transaction from treasury.models"""
from src.mekong.treasury.models import Transaction  # noqa: F401

__all__ = ["Transaction"]

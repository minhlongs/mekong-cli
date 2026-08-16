# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Shim: src.core.rate_limit → src.core.rate_limit_client.

Tests import RateLimiter (legacy name); real class is RateLimitClient.
"""
from src.core.rate_limit_client import RateLimitClient as RateLimiter  # noqa: F401

__all__ = ["RateLimiter"]

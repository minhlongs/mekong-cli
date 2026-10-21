# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Referral data models and database setup."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

# Referral reward: 20% of referred user's first month
REFERRAL_REWARD_PCT = 0.20
# Extended trial for referred users
REFERRAL_TRIAL_DAYS = 7
# Standard trial days
STANDARD_TRIAL_DAYS = 0

# Tier prices for reward calculation
TIER_PRICES: dict[str, float] = {
    "starter": 49.0,
    "pro": 149.0,
    "elite": 499.0,
}


@dataclass
class ReferralCode:
    """A user's referral code."""
    code: str
    user_id: str
    created_at: str
    total_referrals: int = 0
    total_earnings: float = 0.0


@dataclass
class Referral:
    """A referral record."""
    id: str
    referrer_code: str
    referrer_user_id: str
    referred_user_id: str
    referred_email: str
    referred_tier: str
    reward_amount: float
    reward_paid: bool = False
    created_at: str = ""
    trial_extended: bool = True


def init_referral_db(db_path: str) -> None:
    """Create referral tables if they do not exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS referral_codes (
                code TEXT PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                total_referrals INTEGER DEFAULT 0,
                total_earnings REAL DEFAULT 0.0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id TEXT PRIMARY KEY,
                referrer_code TEXT NOT NULL,
                referrer_user_id TEXT NOT NULL,
                referred_user_id TEXT NOT NULL,
                referred_email TEXT,
                referred_tier TEXT DEFAULT 'starter',
                reward_amount REAL DEFAULT 0.0,
                reward_paid INTEGER DEFAULT 0,
                trial_extended INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_code) REFERENCES referral_codes(code)
            )
        """)

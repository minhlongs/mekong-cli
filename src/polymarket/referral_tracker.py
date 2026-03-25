"""Referral tracker — referral codes, attribution, and reward calculation.

Flow:
  1. Each user gets a unique referral code on signup
  2. Referrer gets 20% of referred user's first month
  3. Referred user gets 7-day extended trial
  4. Tracked via Polar.sh subscription metadata
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = "data/algo-trade.db"

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


class ReferralTracker:
    """Tracks referrals, calculates rewards, manages referral codes."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create referral tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
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

    def generate_code(self, user_id: str) -> ReferralCode:
        """Generate a unique referral code for a user."""
        code = f"cc-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Check if user already has a code
            existing = conn.execute(
                "SELECT code FROM referral_codes WHERE user_id = ?",
                (user_id,),
            ).fetchone()

            if existing:
                return self.get_code(existing[0])

            conn.execute(
                "INSERT INTO referral_codes (code, user_id, created_at) VALUES (?, ?, ?)",
                (code, user_id, now),
            )

        return ReferralCode(code=code, user_id=user_id, created_at=now)

    def get_code(self, code: str) -> Optional[ReferralCode]:
        """Look up a referral code."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM referral_codes WHERE code = ?", (code,)
            ).fetchone()

        if row is None:
            return None

        return ReferralCode(
            code=row["code"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            total_referrals=row["total_referrals"],
            total_earnings=row["total_earnings"],
        )

    def get_user_code(self, user_id: str) -> Optional[ReferralCode]:
        """Get referral code for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM referral_codes WHERE user_id = ?", (user_id,)
            ).fetchone()

        if row is None:
            return None

        return ReferralCode(
            code=row["code"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            total_referrals=row["total_referrals"],
            total_earnings=row["total_earnings"],
        )

    def record_referral(
        self,
        referrer_code: str,
        referred_user_id: str,
        referred_email: str,
        referred_tier: str = "starter",
    ) -> Optional[Referral]:
        """Record a new referral when a user signs up with a code."""
        code_info = self.get_code(referrer_code)
        if code_info is None:
            logger.warning("Invalid referral code: %s", referrer_code)
            return None

        # Prevent self-referral
        if code_info.user_id == referred_user_id:
            logger.warning("Self-referral blocked: %s", referred_user_id)
            return None

        # Calculate reward
        tier_price = TIER_PRICES.get(referred_tier, 49.0)
        reward = tier_price * REFERRAL_REWARD_PCT

        referral_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()

        referral = Referral(
            id=referral_id,
            referrer_code=referrer_code,
            referrer_user_id=code_info.user_id,
            referred_user_id=referred_user_id,
            referred_email=referred_email,
            referred_tier=referred_tier,
            reward_amount=reward,
            created_at=now,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO referrals
                   (id, referrer_code, referrer_user_id, referred_user_id,
                    referred_email, referred_tier, reward_amount, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (referral.id, referral.referrer_code, referral.referrer_user_id,
                 referral.referred_user_id, referral.referred_email,
                 referral.referred_tier, referral.reward_amount, referral.created_at),
            )
            # Update referrer stats
            conn.execute(
                """UPDATE referral_codes
                   SET total_referrals = total_referrals + 1,
                       total_earnings = total_earnings + ?
                   WHERE code = ?""",
                (reward, referrer_code),
            )

        logger.info(
            "Referral recorded: %s → %s (reward=$%.2f)",
            referrer_code, referred_email, reward,
        )
        return referral

    def get_referrals_by_code(self, code: str) -> list[Referral]:
        """Get all referrals for a code."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM referrals WHERE referrer_code = ? ORDER BY created_at DESC",
                (code,),
            ).fetchall()

        return [
            Referral(
                id=r["id"],
                referrer_code=r["referrer_code"],
                referrer_user_id=r["referrer_user_id"],
                referred_user_id=r["referred_user_id"],
                referred_email=r["referred_email"],
                referred_tier=r["referred_tier"],
                reward_amount=r["reward_amount"],
                reward_paid=bool(r["reward_paid"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def mark_reward_paid(self, referral_id: str) -> bool:
        """Mark a referral reward as paid."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE referrals SET reward_paid = 1 WHERE id = ?",
                (referral_id,),
            )
            return cursor.rowcount > 0

    def get_trial_extension(self, referral_code: str) -> int:
        """Get trial days for a referred user (standard + extension)."""
        code = self.get_code(referral_code)
        if code is not None:
            return STANDARD_TRIAL_DAYS + REFERRAL_TRIAL_DAYS
        return STANDARD_TRIAL_DAYS

    def get_leaderboard(self, limit: int = 10) -> list[ReferralCode]:
        """Get top referrers by earnings."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM referral_codes
                   WHERE total_referrals > 0
                   ORDER BY total_earnings DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()

        return [
            ReferralCode(
                code=r["code"],
                user_id=r["user_id"],
                created_at=r["created_at"],
                total_referrals=r["total_referrals"],
                total_earnings=r["total_earnings"],
            )
            for r in rows
        ]

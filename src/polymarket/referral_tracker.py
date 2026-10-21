# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Referral tracker — referral codes, attribution, and reward calculation."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from src.polymarket.referral_models import (
    REFERRAL_REWARD_PCT,
    REFERRAL_TRIAL_DAYS,
    STANDARD_TRIAL_DAYS,
    TIER_PRICES,
    Referral,
    ReferralCode,
    init_referral_db,
)

logger = logging.getLogger(__name__)

DB_PATH = "data/algo-trade.db"


class ReferralTracker:
    """Tracks referrals, calculates rewards, manages referral codes."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        init_referral_db(self.db_path)

    def generate_code(self, user_id: str) -> ReferralCode:
        code = f"cc-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute("SELECT code FROM referral_codes WHERE user_id = ?", (user_id,)).fetchone()
            if existing:
                return self.get_code(existing[0])
            conn.execute("INSERT INTO referral_codes (code, user_id, created_at) VALUES (?, ?, ?)", (code, user_id, now))
        return ReferralCode(code=code, user_id=user_id, created_at=now)

    def get_code(self, code: str) -> Optional[ReferralCode]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM referral_codes WHERE code = ?", (code,)).fetchone()
        if row is None:
            return None
        return ReferralCode(
            code=row["code"], user_id=row["user_id"], created_at=row["created_at"],
            total_referrals=row["total_referrals"], total_earnings=row["total_earnings"],
        )

    def get_user_code(self, user_id: str) -> Optional[ReferralCode]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM referral_codes WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            return None
        return ReferralCode(
            code=row["code"], user_id=row["user_id"], created_at=row["created_at"],
            total_referrals=row["total_referrals"], total_earnings=row["total_earnings"],
        )

    def record_referral(
        self, referrer_code: str, referred_user_id: str, referred_email: str, referred_tier: str = "starter",
    ) -> Optional[Referral]:
        code_info = self.get_code(referrer_code)
        if code_info is None or code_info.user_id == referred_user_id:
            return None

        tier_price = TIER_PRICES.get(referred_tier, 49.0)
        reward = tier_price * REFERRAL_REWARD_PCT
        referral_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat()

        referral = Referral(
            id=referral_id, referrer_code=referrer_code, referrer_user_id=code_info.user_id,
            referred_user_id=referred_user_id, referred_email=referred_email,
            referred_tier=referred_tier, reward_amount=reward, created_at=now,
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO referrals
                   (id, referrer_code, referrer_user_id, referred_user_id, referred_email, referred_tier, reward_amount, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (referral.id, referral.referrer_code, referral.referrer_user_id, referral.referred_user_id,
                 referral.referred_email, referral.referred_tier, referral.reward_amount, referral.created_at),
            )
            conn.execute("UPDATE referral_codes SET total_referrals = total_referrals + 1, total_earnings = total_earnings + ? WHERE code = ?", (reward, referrer_code))

        logger.info("Referral recorded: %s → %s (reward=$%.2f)", referrer_code, referred_email, reward)
        return referral

    def get_referrals_by_code(self, code: str) -> list[Referral]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM referrals WHERE referrer_code = ? ORDER BY created_at DESC", (code,)).fetchall()
        return [
            Referral(
                id=r["id"], referrer_code=r["referrer_code"], referrer_user_id=r["referrer_user_id"],
                referred_user_id=r["referred_user_id"], referred_email=r["referred_email"],
                referred_tier=r["referred_tier"], reward_amount=r["reward_amount"],
                reward_paid=bool(r["reward_paid"]), created_at=r["created_at"],
            )
            for r in rows
        ]

    def mark_reward_paid(self, referral_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("UPDATE referrals SET reward_paid = 1 WHERE id = ?", (referral_id,))
            return cursor.rowcount > 0

    def get_trial_extension(self, referral_code: str) -> int:
        code = self.get_code(referral_code)
        return STANDARD_TRIAL_DAYS + REFERRAL_TRIAL_DAYS if code is not None else STANDARD_TRIAL_DAYS

    def get_leaderboard(self, limit: int = 10) -> list[ReferralCode]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM referral_codes WHERE total_referrals > 0 ORDER BY total_earnings DESC LIMIT ?", (limit,)).fetchall()
        return [
            ReferralCode(
                code=r["code"], user_id=r["user_id"], created_at=r["created_at"],
                total_referrals=r["total_referrals"], total_earnings=r["total_earnings"],
            )
            for r in rows
        ]


__all__ = [
    "DB_PATH", "REFERRAL_REWARD_PCT", "REFERRAL_TRIAL_DAYS", "Referral",
    "ReferralCode", "ReferralTracker", "STANDARD_TRIAL_DAYS", "TIER_PRICES",
    "init_referral_db",
]

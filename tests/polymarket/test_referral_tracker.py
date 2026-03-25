"""Tests for referral tracker — codes, attribution, rewards, leaderboard."""

import os
import sqlite3
import tempfile

import pytest

from src.polymarket.referral_tracker import (
    REFERRAL_REWARD_PCT,
    REFERRAL_TRIAL_DAYS,
    ReferralTracker,
    TIER_PRICES,
)


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def tracker(db_path):
    return ReferralTracker(db_path)


class TestGenerateCode:
    """Test referral code generation."""

    def test_generates_unique_code(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("user_001")
        assert code.code.startswith("cc-")
        assert len(code.code) > 4
        assert code.user_id == "user_001"

    def test_same_user_same_code(self, tracker: ReferralTracker) -> None:
        code1 = tracker.generate_code("user_001")
        code2 = tracker.generate_code("user_001")
        assert code1.code == code2.code

    def test_different_users_different_codes(self, tracker: ReferralTracker) -> None:
        code1 = tracker.generate_code("user_001")
        code2 = tracker.generate_code("user_002")
        assert code1.code != code2.code


class TestGetCode:
    """Test code lookup."""

    def test_get_existing_code(self, tracker: ReferralTracker) -> None:
        created = tracker.generate_code("user_001")
        found = tracker.get_code(created.code)
        assert found is not None
        assert found.code == created.code

    def test_get_nonexistent_code(self, tracker: ReferralTracker) -> None:
        assert tracker.get_code("nonexistent") is None

    def test_get_user_code(self, tracker: ReferralTracker) -> None:
        tracker.generate_code("user_001")
        found = tracker.get_user_code("user_001")
        assert found is not None
        assert found.user_id == "user_001"


class TestRecordReferral:
    """Test referral recording."""

    def test_record_valid_referral(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("referrer_001")
        referral = tracker.record_referral(
            referrer_code=code.code,
            referred_user_id="new_user_001",
            referred_email="new@example.com",
            referred_tier="starter",
        )
        assert referral is not None
        assert referral.referrer_code == code.code
        assert referral.referred_email == "new@example.com"

    def test_reward_calculation_starter(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("referrer_001")
        referral = tracker.record_referral(
            referrer_code=code.code,
            referred_user_id="new_001",
            referred_email="n@e.com",
            referred_tier="starter",
        )
        expected_reward = TIER_PRICES["starter"] * REFERRAL_REWARD_PCT
        assert referral.reward_amount == expected_reward  # 20% of $49 = $9.80

    def test_reward_calculation_pro(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("referrer_002")
        referral = tracker.record_referral(
            referrer_code=code.code,
            referred_user_id="new_002",
            referred_email="n2@e.com",
            referred_tier="pro",
        )
        expected_reward = TIER_PRICES["pro"] * REFERRAL_REWARD_PCT
        assert referral.reward_amount == expected_reward  # 20% of $149 = $29.80

    def test_reward_calculation_elite(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("referrer_003")
        referral = tracker.record_referral(
            referrer_code=code.code,
            referred_user_id="new_003",
            referred_email="n3@e.com",
            referred_tier="elite",
        )
        expected_reward = TIER_PRICES["elite"] * REFERRAL_REWARD_PCT
        assert referral.reward_amount == expected_reward  # 20% of $499 = $99.80

    def test_invalid_code_returns_none(self, tracker: ReferralTracker) -> None:
        assert tracker.record_referral("bad-code", "u1", "e@e.com") is None

    def test_self_referral_blocked(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("user_001")
        result = tracker.record_referral(
            referrer_code=code.code,
            referred_user_id="user_001",
            referred_email="self@e.com",
        )
        assert result is None

    def test_referrer_stats_updated(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("referrer_001")
        tracker.record_referral(code.code, "u1", "a@b.com", "starter")
        tracker.record_referral(code.code, "u2", "c@d.com", "pro")

        updated = tracker.get_code(code.code)
        assert updated.total_referrals == 2
        expected_total = TIER_PRICES["starter"] * 0.2 + TIER_PRICES["pro"] * 0.2
        assert abs(updated.total_earnings - expected_total) < 0.01


class TestTrialExtension:
    """Test trial extension for referred users."""

    def test_referred_gets_extension(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("user_001")
        days = tracker.get_trial_extension(code.code)
        assert days == REFERRAL_TRIAL_DAYS  # 7 extra days

    def test_no_code_no_extension(self, tracker: ReferralTracker) -> None:
        days = tracker.get_trial_extension("invalid")
        assert days == 0


class TestMarkPaid:
    """Test marking rewards as paid."""

    def test_mark_paid(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("referrer_001")
        referral = tracker.record_referral(code.code, "u1", "a@b.com")
        result = tracker.mark_reward_paid(referral.id)
        assert result is True

    def test_mark_paid_nonexistent(self, tracker: ReferralTracker) -> None:
        assert tracker.mark_reward_paid("nonexistent") is False


class TestLeaderboard:
    """Test referral leaderboard."""

    def test_leaderboard_ranked(self, tracker: ReferralTracker) -> None:
        c1 = tracker.generate_code("top_referrer")
        c2 = tracker.generate_code("low_referrer")

        tracker.record_referral(c1.code, "u1", "a@b.com", "elite")
        tracker.record_referral(c1.code, "u2", "b@c.com", "pro")
        tracker.record_referral(c2.code, "u3", "c@d.com", "starter")

        board = tracker.get_leaderboard(limit=10)
        assert len(board) == 2
        assert board[0].total_earnings > board[1].total_earnings

    def test_leaderboard_empty(self, tracker: ReferralTracker) -> None:
        assert tracker.get_leaderboard() == []

    def test_get_referrals_by_code(self, tracker: ReferralTracker) -> None:
        code = tracker.generate_code("user_001")
        tracker.record_referral(code.code, "u1", "a@b.com")
        tracker.record_referral(code.code, "u2", "c@d.com")
        referrals = tracker.get_referrals_by_code(code.code)
        assert len(referrals) == 2

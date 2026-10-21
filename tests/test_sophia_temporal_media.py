# Mekong CLI — MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Temporal-media contract: leading channel, dual-lock cap, no face lock.

These tests assert that the design gates in src/design_intelligence/checks.py
validate a REAL VideoRenderRequest, not just a hand-written payload string.
See docs/design-guidelines-temporal-media.md (RULE-P1, RULE-P2, RULE-P4).
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from src.design_intelligence.gates import run_deterministic_gates
from src.services.sophia_temporal_media import (
    MAX_AVATAR_FRAME_SHARE,
    MAX_DUAL_LOCK_RATIO,
    TemporalScene,
    LeadingChannel,
)
from src.services.sophia_video_models import VideoRenderRequest

SCRIPT = "Chào mừng các bạn đã quay trở lại với Mekong CLI, hôm nay chúng ta tìm hiểu thuế tự động."


def _request(**overrides):
    base = {
        "title": "Tax Automation Overview",
        "script": SCRIPT,
        "leading_channel": "voice_leading",
    }
    base.update(overrides)
    return VideoRenderRequest(**base)


def _gate_failed(payload_text: str, gate_id: str) -> bool:
    results = {r.gate_id: r for r in run_deterministic_gates(payload_text)}
    assert gate_id in results, f"gate {gate_id} not registered — a dead gate is a silent no-op"
    return not results[gate_id].passed


class TestLeadingChannelDeclaration:
    """RULE-P1: every temporal render declares exactly one leading channel."""

    def test_request_requires_a_leading_channel(self) -> None:
        with pytest.raises(ValidationError):
            VideoRenderRequest(title="x", script=SCRIPT)  # type: ignore[call-arg]

    def test_only_the_three_known_values_are_accepted(self) -> None:
        for value in ("voice_leading", "image_leading", "dual_lock"):
            assert _request(leading_channel=value).leading_channel is LeadingChannel(value)
        with pytest.raises(ValidationError):
            _request(leading_channel="picture_first")

    def test_gate_58_fires_on_a_request_without_the_declaration(self) -> None:
        assert _gate_failed(json.dumps({"script": SCRIPT, "subtitles_enabled": True}), "58")

    def test_gate_58_passes_on_a_real_request(self) -> None:
        req = _request()
        assert not _gate_failed(req.model_dump_json(), "58")


class TestDualLockCap:
    """RULE-P2: at most 20 percent of scenes may be dual_lock."""

    def test_scenes_accept_a_leading_channel_each(self) -> None:
        scenes = [TemporalScene(scene_id=f"s{i}", leading_channel="voice_leading") for i in range(4)]
        assert len(_request(scenes=scenes).scenes) == 4

    def test_at_the_cap_is_accepted(self) -> None:
        # 2 of 10 = 20 percent, exactly the ceiling, so it must be accepted.
        scenes = [TemporalScene(scene_id=f"d{i}", leading_channel="dual_lock") for i in range(2)]
        scenes += [TemporalScene(scene_id=f"v{i}", leading_channel="voice_leading") for i in range(8)]
        req = _request(scenes=scenes)
        assert sum(1 for s in req.scenes if s.leading_channel is LeadingChannel.DUAL) == 2

    def test_over_the_cap_is_rejected(self) -> None:
        scenes = [TemporalScene(scene_id=f"s{i}", leading_channel="dual_lock") for i in range(3)]
        scenes += [TemporalScene(scene_id=f"v{i}", leading_channel="voice_leading") for i in range(7)]
        with pytest.raises(ValidationError, match="RULE-P2"):
            _request(scenes=scenes)

    def test_gate_59_reads_a_real_scene_list(self) -> None:
        """The gate must count dual_lock scenes in a real serialised request.

        The model itself already refuses an over-cap scene list, so an
        over-cap request cannot be constructed through VideoRenderRequest.
        The gate is tested against the payload shapes it reads: a real
        at-the-cap request must pass, and a raw over-cap scene list must fail.
        """
        at_cap = [TemporalScene(scene_id=f"d{i}", leading_channel="dual_lock") for i in range(2)]
        at_cap += [TemporalScene(scene_id=f"v{i}", leading_channel="voice_leading") for i in range(8)]
        assert not _gate_failed(_request(scenes=at_cap).model_dump_json(), "59")

        over_cap = json.dumps([
            {"scene": i, "leading_channel": "dual_lock"} for i in range(4)
        ] + [{"scene": i, "leading_channel": "voice_leading"} for i in range(4, 10)])
        assert _gate_failed(over_cap, "59")


class TestNoFaceLock:
    """RULE-P4: an avatar must not hold the frame while a figure is the subject."""

    def test_a_figure_subject_forces_the_avatar_to_recede(self) -> None:
        with pytest.raises(ValidationError, match="RULE-P4"):
            _request(
                leading_channel="image_leading",
                scenes=[TemporalScene(scene_id="s0", leading_channel="image_leading",
                                      subject="chart", avatar_scale=1.0)],
            )

    def test_a_receded_avatar_is_accepted(self) -> None:
        req = _request(
            leading_channel="image_leading",
            scenes=[TemporalScene(scene_id="s0", leading_channel="image_leading",
                                  subject="chart", avatar_scale=0.4)],
        )
        assert req.scenes[0].avatar_scale < MAX_AVATAR_FRAME_SHARE

    def test_a_narration_only_scene_is_unaffected(self) -> None:
        req = _request(
            scenes=[TemporalScene(scene_id="s0", leading_channel="voice_leading",
                                  subject="avatar", avatar_scale=1.0)],
        )
        assert req.scenes[0].avatar_scale == 1.0

    def test_gate_60_reads_a_real_request(self) -> None:
        """Valid requests must pass the gate; the face-lock shape must fail it.

        As with the cap, VideoRenderRequest refuses a full-frame avatar over a
        figure subject, so the failing shape is asserted against the payload the
        gate reads rather than smuggled through the model.
        """
        receded = _request(
            leading_channel="image_leading",
            scenes=[TemporalScene(scene_id="s0", leading_channel="image_leading",
                                  subject="invoice", avatar_scale=0.3)],
        )
        assert not _gate_failed(receded.model_dump_json(), "60")

        locked = json.dumps([{
            "scene": 0, "leading_channel": "image_leading",
            "subject": "invoice", "avatar_scale": 1.0, "avatar_frame": "full",
        }])
        assert _gate_failed(locked, "60")

    def test_a_full_frame_avatar_recedes_on_the_request_model(self) -> None:
        """The model, not only the gate, refuses a face filling a figure subject."""
        with pytest.raises(ValidationError, match="RULE-P4"):
            VideoRenderRequest(
                title="Invoice walkthrough", script=SCRIPT, leading_channel="image_leading",
                scenes=[TemporalScene(scene_id="s0", leading_channel="image_leading",
                                      subject="invoice", avatar_scale=1.0)],
            )


class TestDocumentedThresholds:
    """The two quantitative thresholds stay what the design doc approves."""

    def test_dual_lock_ceiling_is_twenty_percent(self) -> None:
        assert MAX_DUAL_LOCK_RATIO == 0.20

    def test_avatar_frame_share_is_fifty_percent(self) -> None:
        assert MAX_AVATAR_FRAME_SHARE == 0.50

# Mekong CLI — MIT License. Copyright (c) 2026 MekongMind.

"""Deterministic (regex/static) checks for the automatic design gates.

Each check receives (html, css) text and returns True when the gate FAILS.
Checks are pure text analysis — OBJECTIVE evidence, no rendering, no LLM.
Adapted from Hallmark's slop test (github.com/nutlope/hallmark, MIT).
"""

from __future__ import annotations

from .checks_guidelines import (
    _g1, _g10, _g11, _g12, _g14, _g19, _g2, _g20, _g22, _g24, _g25, _g26, _g27, _g3, _g6, _g7,
)

import re
from collections.abc import Callable

from src.design_intelligence.checks_extended import (
    _CSS_BLOCKS,
    _EMOJI_ICONS,
    _blocks,
    _g28,
    _g30,
    _g33,
    _g34,
    _g37,
    _g38a,
    _g47,
    _g48,
    _g50,
    _g51,
    _g54,
    _g55,
    _g56,
)

Check = Callable[[str, str], bool]



# --------------------------------------------------------------- temporal media
# Composed temporal media. The render request carries narration but no
# still-frame structure, so the checked text is the request/scene payload
# (passed as `html`); `css` is unused. All three are pure text checks.

_LEADING_CHANNELS = ("voice_leading", "image_leading", "dual_lock")

# Dual-lock is capped, not merely discouraged: at most 20 percent of scenes in
# one render may be redundant. See docs/design-guidelines-temporal-media.md RULE-P2.
_DUAL_LOCK_CEILING = 0.20


def _g58(html: str, css: str) -> bool:
    """A temporal render request declares narration but no leading channel.

    Scoped to the render-request field names, not the bare words, so a plain
    <script> tag on an ordinary page is never mistaken for a narration payload.
    """
    if not re.search(r'"(?:script|subtitles_enabled)"\s*:|(?:^|\s)script\s*[:=]', html):
        return False
    return not any(f'"{ch}"' in html or f"'{ch}'" in html or f"{ch}=" in html for ch in _LEADING_CHANNELS)


def _g59(html: str, css: str) -> bool:
    """Dual-lock scenes exceed the 20 percent ceiling of the declared scene list."""
    total = len(re.findall(r'"scene"\s*:|^\s*- scene:', html, re.M))
    if total == 0:
        return False
    dual = len(re.findall(r'"leading_channel"\s*:\s*"dual_lock"|leading_channel=dual_lock', html))
    return (dual / total) > _DUAL_LOCK_CEILING


def _g60(html: str, css: str) -> bool:
    """A presenter avatar holds the frame while a figure or document is the subject.

    Scene frame share is read from `avatar_scale`; the gate fails only when a
    figure subject coincides with a face at or above the RULE-P4 ceiling.
    """
    if not re.search(
        r'"(?:subject|content_type)"\s*:\s*"(?:figure|document|table|chart|invoice)"', html
    ):
        return False
    # Subject present: the face must recede below half the frame for its duration.
    for m in re.finditer(r'"avatar_scale"\s*:\s*([0-9.]+)', html):
        if float(m.group(1)) > _MAX_AVATAR_FRAME_SHARE:
            return True
    # Frame-placement fallback for payloads that declare no scale.
    return bool(
        re.search(r'"avatar_frame"\s*:\s*"full"', html)
        and not re.search(r'"avatar_scale"\s*:', html)
        and not re.search(r'"avatar_recedes"\s*:\s*(?:true|yes|1)', html)
    )


# RULE-P4 ceiling. See docs/design-guidelines-temporal-media.md.
_MAX_AVATAR_FRAME_SHARE = 0.50


CHECKS: dict[str, Check] = {
    "1": _g1, "2": _g2, "3": _g3, "6": _g6, "7": _g7, "10": _g10, "11": _g11,
    "12": _g12, "14": _g14, "19": _g19, "20": _g20, "22": _g22, "24": _g24,
    "25": _g25, "26": _g26, "27": _g27, "28": _g28, "30": _g30, "33": _g33,
    "34": _g34, "37": _g37, "38a": _g38a, "47": _g47, "48": _g48, "50": _g50,
    "51": _g51, "54": _g54, "55": _g55, "56": _g56, "58": _g58, "59": _g59,
    "60": _g60,
}

__all__ = [
    "CHECKS",
    "Check",
    "_CSS_BLOCKS",
    "_EMOJI_ICONS",
    "_blocks",
    "_g1",
    "_g2",
    "_g3",
    "_g6",
    "_g7",
    "_g10",
    "_g11",
    "_g12",
    "_g14",
    "_g19",
    "_g20",
    "_g22",
    "_g24",
    "_g25",
    "_g26",
    "_g27",
    "_g28",
    "_g30",
    "_g33",
    "_g34",
    "_g37",
    "_g38a",
    "_g47",
    "_g48",
    "_g50",
    "_g51",
    "_g54",
    "_g55",
    "_g56",
    "_g58",
    "_g59",
    "_g60",
]

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Design Intelligence guideline checks — individual CSS/HTML constraint probes.

Split out of the rule registry so each file stays within the size limit.
"""

from __future__ import annotations

import re

_DEFAULT_FONTS = {"inter", "roboto", "open sans", "poppins", "lato", "sans-serif", "system-ui"}
_CLICHE = re.compile(r"\b(jane doe|john smith|acme|nexus|seamless|unleash)\b", re.I)


def _g1(html: str, css: str) -> bool:
    for m in re.finditer(r"font-family:\s*([^;]+)", css):
        first = m.group(1).split(",")[0].strip().strip("'\"").lower()
        if first in _DEFAULT_FONTS:
            return True
    return False


def _g2(html: str, css: str) -> bool:
    if re.search(r"background-clip:\s*text", css):
        return True
    purple_blue = r"linear-gradient\([^)]*#(8b5cf6|a855f7|7c3aed|6366f1)[^)]*#(3b82f6|2563eb|06b6d4|0ea5e9)"
    return bool(re.search(purple_blue, css, re.I))


def _g3(html: str, css: str) -> bool:
    return bool(re.search(r"grid-template-columns:\s*repeat\(\s*3\b", css))


def _g6(html: str, css: str) -> bool:
    return bool(re.search(r"min-height:\s*100vh", css) and re.search(r"text-align:\s*center", css))


def _g7(html: str, css: str) -> bool:
    return bool(re.search(r"#(000|fff|000000|ffffff)\b", css, re.I))


def _g10(html: str, css: str) -> bool:
    return bool(re.search(r"transition(-property)?:\s*[^;}]*\ball\b", css) or "transition-all" in css)


def _g11(html: str, css: str) -> bool:
    return bool(re.search(r"scale-105|scale\(1\.05\)", css))


def _g12(html: str, css: str) -> bool:
    return bool(re.search(r"cubic-bezier\([^)]*1\.\d+", css))


def _g14(html: str, css: str) -> bool:
    return bool(re.search(r"transition[^;:]*:\s*[^;]*\b(width|height|top|left|margin|padding)\b", css))


def _g19(html: str, css: str) -> bool:
    return bool(_CLICHE.search(html))


def _g20(html: str, css: str) -> bool:
    return not re.search(r"/\*[^*]*(Mekong Design|macrostructure:)", css)


def _g22(html: str, css: str) -> bool:
    return bool(re.search(r"oklch\(\s*[\d.]+%?\s+0(?:\.0+)?\s+[\d.]+", css))


def _g24(html: str, css: str) -> bool:
    for m in re.finditer(r"(?:padding|margin|gap)[^;:]*:\s*([^;]+)", css):
        if any(int(px) % 4 for px in re.findall(r"(\d+)px", m.group(1))):
            return True
    return False


def _g25(html: str, css: str) -> bool:
    return any(not 45 <= int(m.group(1)) <= 75 for m in re.finditer(r"max-width:\s*(\d+)ch", css))


def _g26(html: str, css: str) -> bool:
    if not re.search(r"<(button|a|input|select|textarea)\b", html):
        return False
    return not re.search(r":focus-visible", css)


def _g27(html: str, css: str) -> bool:
    has_motion = bool(re.search(r"@keyframes|animation:", css))
    return has_motion and "prefers-reduced-motion" not in css

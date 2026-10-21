# Mekong CLI — MIT License. Copyright (c) 2026 MekongMind.

"""Extended deterministic checks (gates 28-56) for automatic design gates."""

from __future__ import annotations

import re

_EMOJI_ICONS = ("✨", "🚀", "⚡", "🔥", "🎯", "✅")
_CSS_BLOCKS = re.compile(r"([^{}]+)\{([^{}]*?)\}")


def _blocks(css: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _CSS_BLOCKS.finditer(css)]


def _g28(html: str, css: str) -> bool:
    for m in re.finditer(r"<video\b[^>]*>", html):
        tag = m.group(0)
        if "autoplay" in tag and "poster" not in tag:
            return True
    return False


def _g30(html: str, css: str) -> bool:
    return any(icon in html for icon in _EMOJI_ICONS)


def _g33(html: str, css: str) -> bool:
    if "<svg" not in html:
        return False
    return not re.search(r'aria-hidden\s*=\s*"true"|aria-label', html)


def _g34(html: str, css: str) -> bool:
    return not re.search(r"overflow-x:\s*clip", css)


def _g37(html: str, css: str) -> bool:
    families = set()
    for m in re.finditer(r"font-family:\s*([^;]+)", css):
        for token in m.group(1).split(","):
            name = token.strip().strip("'\"").lower()
            if name:
                families.add(name)
    return len(families) > 3


def _g38a(html: str, css: str) -> bool:
    for selector, body in _blocks(css):
        if re.search(r"font-style:\s*italic", body) and re.search(
            r"(^|[,\s])h[1-6]\b|\btitle|wordmark", selector, re.I
        ):
            return True
    return False


def _g47(html: str, css: str) -> bool:
    return bool(
        re.search(
            r"traffic-light|window-dot|browser-bar|phone-frame|fake-terminal|mock-browser",
            html + css,
            re.I,
        )
    )


def _g48(html: str, css: str) -> bool:
    if not re.search(r":root|\[data-theme", css):
        return False
    stripped = re.sub(r"(:root|\[data-theme[^\]]*\])\s*\{[^{}]*\}", "", css)
    return bool(re.search(r"#[0-9a-f]{3,8}\b|oklch\(|rgba?\(|hsla?\(", stripped, re.I))


def _g50(html: str, css: str) -> bool:
    if not re.search(r"<img\b|<picture\b", html):
        return False
    for m in re.finditer(r"grid-template-columns:\s*([^;]+)", css):
        decl = m.group(1)
        stripped = re.sub(r"minmax\(\s*0\s*,\s*1fr\s*\)", "", decl)
        if re.search(r"\b1fr\b", stripped):
            return True
    return False


def _g51(html: str, css: str) -> bool:
    if not re.search(r"<h1\b", html):
        return False
    return not re.search(r"overflow-wrap:\s*anywhere", css)


def _g54(html: str, css: str) -> bool:
    for selector, body in _blocks(css):
        if not re.search(r"__head|__intro|section-head", selector):
            continue
        m = re.search(r"grid-template-columns:\s*([^;]+)", body)
        if not m:
            continue
        decl = m.group(1).strip()
        if decl in ("1fr", "minmax(0, 1fr)", "minmax(0,1fr)"):
            continue
        stripped = re.sub(r"minmax\(\s*0\s*,\s*1fr\s*\)", "X", decl)
        if len(stripped.split()) > 1:
            return True
    return False


def _g55(html: str, css: str) -> bool:
    for _selector, body in _blocks(css):
        if not re.search(r"text-transform:\s*uppercase", body):
            continue
        m = re.search(r"line-height:\s*([\d.]+)", body)
        if m and float(m.group(1)) < 1.0:
            return True
    return False


def _g56(html: str, css: str) -> bool:
    sticky_top_zero = sum(
        1
        for _selector, body in _blocks(css)
        if re.search(r"position:\s*sticky", body) and re.search(r"top:\s*0\b", body)
    )
    return sticky_top_zero >= 2

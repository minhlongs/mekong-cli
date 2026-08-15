"""Mekong CLI 7 — Context compaction (port of opencode compaction agent).

OmniRoute B6 upgrade: stacked lossless pipeline runs BEFORE any LLM summarize:
  1. dedup — bỏ context blocks trùng content hash
  2. lite — strip ANSI codes + trailing whitespace + collapse blank lines
  3. RTK-style — cắt tool output dài (giữ 100 dòng đầu + 20 cuối,
     đánh dấu `... [TRUNCATED n lines]`)
  4. summarize (LLM) CHỈ nếu vẫn > threshold — bail-out: bước lossless giảm
     ≥ 60% → skip summarize.

`should_compact` + `CompactionResult` interface giữ nguyên (orchestrate.py
callers không đổi).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .llm import LLMClient

DEFAULT_THRESHOLD_CHARS = 8000
DEFAULT_MAX_SUMMARY_CHARS = 1500
BAILOUT_RATIO = 0.6          # giảm ≥ 60% → skip summarize (B6)
RTK_HEAD_LINES = 100         # giữ 100 dòng đầu
RTK_TAIL_LINES = 20          # + 20 dòng cuối

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_TRUNC_MARK = "... [TRUNCATED {n} lines]"


@dataclass
class CompactionResult:
    compacted: bool
    summary: str = ""
    original_chars: int = 0
    summary_chars: int = 0
    pipeline_reduced: int = 0    # B6: lossless giảm được bao nhiêu chars
    summarized: bool = True      # B6: False = bail-out (skip summarize)


SYSTEM_PROMPT = (
    "You are a context compactor. Given raw context blocks from a previous "
    "execution step, produce a compact factual summary preserving: what was done, "
    "files touched, key results/values, errors and their resolutions, and "
    "remaining unknowns. Output ONLY the summary text, no prose around it."
)


def _lite(text: str) -> str:
    """B6 step 2: strip ANSI + trailing whitespace + collapse blank lines."""
    text = _ANSI_RE.sub("", text)
    out: list[str] = []
    prev_blank = False
    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        out.append(stripped)
    return "\n".join(out)


def _truncate_rtk(text: str, head: int = RTK_HEAD_LINES, tail: int = RTK_TAIL_LINES) -> str:
    """B6 step 3: cắt output dài — giữ head dòng đầu + tail dòng cuối."""
    lines = text.splitlines()
    if len(lines) <= head + tail:
        return text
    cut = len(lines) - head - tail
    marker = _TRUNC_MARK.format(n=cut)
    return "\n".join([*lines[:head], marker, *lines[-tail:]])


def _dedup(texts: list[str]) -> list[str]:
    """B6 step 1: bỏ blocks trùng content hash (giữ bản đầu tiên)."""
    seen: set[str] = set()
    out: list[str] = []
    for t in texts:
        h = hashlib.sha1(t.encode("utf-8", errors="replace")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        out.append(t)
    return out


class Compactor:
    def __init__(
        self,
        client: LLMClient | None = None,
        threshold_chars: int = DEFAULT_THRESHOLD_CHARS,
        max_summary_chars: int = DEFAULT_MAX_SUMMARY_CHARS,
    ):
        self.client = client or LLMClient()
        self.threshold_chars = threshold_chars
        self.max_summary_chars = max_summary_chars

    def should_compact(self, shared: dict[str, object], exclude_key: str | None = None) -> bool:
        total = 0
        for key, val in shared.items():
            if exclude_key and key == exclude_key:
                continue
            total += len(str(val))
            if total > self.threshold_chars:
                return True
        return False

    # ── B6: lossless pipeline ────────────────────────────────

    def _blocks(self, shared: dict[str, object], exclude_key: str | None) -> tuple[list[str], int]:
        texts = []
        total = 0
        for key, val in shared.items():
            if exclude_key and key == exclude_key:
                continue
            text = str(val)
            total += len(text)
            texts.append(text)
        return texts, total

    def lossless(self, shared: dict[str, object], exclude_key: str | None = None) -> tuple[int, int]:
        """Chạy dedup → lite → RTK truncate. Returns (chars_before, chars_after)."""
        texts, total = self._blocks(shared, exclude_key)
        texts = _dedup(texts)
        texts = [_truncate_rtk(_lite(t)) for t in texts]
        return total, sum(len(t) for t in texts)

    def compact(self, shared: dict[str, object], exclude_key: str | None = None) -> CompactionResult:
        """Pipeline lossless trước; summarize (LLM) chỉ nếu vẫn cần + bail-out."""
        texts, total = self._blocks(shared, exclude_key)

        if total <= self.threshold_chars:
            return CompactionResult(compacted=False)

        texts = _dedup(texts)
        texts = [_truncate_rtk(_lite(t)) for t in texts]
        after = sum(len(t) for t in texts)
        reduced = total - after

        if reduced >= total * BAILOUT_RATIO:
            # bail-out: lossless đã giảm ≥ 60% → không cần tốn LLM
            return CompactionResult(
                compacted=True,
                summary="\n\n".join(texts) or "(empty context)",
                original_chars=total,
                summary_chars=after,
                pipeline_reduced=reduced,
                summarized=False,
            )

        joined = "\n".join(texts)
        try:
            summary = self._summarize(joined)
        except Exception:  # noqa: BLE001 — model unavailable: hard-truncate
            summary = joined[-self.max_summary_chars :]

        return CompactionResult(
            compacted=True,
            summary=summary,
            original_chars=total,
            summary_chars=len(summary),
            pipeline_reduced=reduced,
            summarized=True,
        )

    def _summarize(self, text: str) -> str:
        model = "openrouter/openai/gpt-oss-20b:free"
        try:
            raw = self.client.text(model, text, system=SYSTEM_PROMPT, max_tokens=2048)
        except Exception:
            from .models import resolve_or_fallback

            entry = resolve_or_fallback("haiku")
            raw = self.client.text(entry.id, text, system=SYSTEM_PROMPT, max_tokens=2048)
        summary = raw.strip()
        if len(summary) > self.max_summary_chars:
            summary = summary[: self.max_summary_chars]
        return summary or "(empty summary)"

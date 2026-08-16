"""Token compression pipeline — RTK-style features only.

Applies deterministic, pure-function compression passes to message lists:
1. Session dedup — remove duplicate system messages across turns.
2. Truncate tool results — cap oversized content.
3. Prose collapse — compress verbose whitespace and formatting.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

DEFAULT_TARGET_SAVINGS = 0.5
DEFAULT_MAX_TOKEN_CHARS = 16000  # ~4 tokens per char heuristic


def compress(
    messages: list[dict[str, object]],
    target_savings: float = DEFAULT_TARGET_SAVINGS,
    max_token_chars: int = DEFAULT_MAX_TOKEN_CHARS,
) -> list[dict[str, object]]:
    """Compress a message list to reduce token usage.

    Applies compression passes in order and returns the resulting list.
    The input list is never mutated.
    """
    result = list(messages)
    original_size = _estimate_size(result)

    # Pass 1: session dedup
    result = _dedup_system_messages(result)

    # Pass 2: truncate tool results
    result = _truncate_tool_results(result, max_token_chars)

    # Pass 3: prose collapse (only if we haven't hit target yet)
    compressed_size = _estimate_size(result)
    savings = 1.0 - (compressed_size / original_size) if original_size > 0 else 0.0
    if savings < target_savings:
        result = _collapse_prose(result)
        compressed_size = _estimate_size(result)
        savings = 1.0 - (compressed_size / original_size) if original_size > 0 else 0.0

    logger.debug(
        "[Compression] original=%d compressed=%d savings=%.1f%%",
        original_size,
        compressed_size,
        savings * 100,
    )
    return result


# ------------------------------------------------------------------
# Internal passes
# ------------------------------------------------------------------


def _estimate_size(messages: list[dict[str, object]]) -> int:
    """Rough character-count estimate across all message content."""
    total = 0
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "")
                    if isinstance(text, str):
                        total += len(text)
    return total


def _dedup_system_messages(
    messages: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Remove duplicate system messages across turns, keeping the first."""
    seen_system: set[str] = set()
    result: list[dict[str, object]] = []
    for msg in messages:
        role = msg.get("role")
        if role == "system":
            content = msg.get("content", "")
            if isinstance(content, str) and content in seen_system:
                continue
            if isinstance(content, str):
                seen_system.add(content)
        result.append(msg)
    return result


def _truncate_tool_results(
    messages: list[dict[str, object]],
    max_chars: int,
) -> list[dict[str, object]]:
    """Truncate tool result content exceeding max_chars."""
    result: list[dict[str, object]] = []
    for msg in messages:
        if msg.get("role") != "tool":
            result.append(msg)
            continue
        content = msg.get("content")
        if not isinstance(content, str) or len(content) <= max_chars:
            result.append(msg)
            continue
        original_len = len(content)
        truncated = content[:max_chars]
        truncated += f" [TRUNCATED — original: {original_len} chars]"
        new_msg = dict(msg)
        new_msg["content"] = truncated
        result.append(new_msg)
        logger.debug(
            "[Compression] truncated tool result: %d -> %d chars",
            original_len,
            max_chars,
        )
    return result


def _collapse_prose(
    messages: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Collapse verbose whitespace and excessive formatting in content."""
    result: list[dict[str, object]] = []
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, str):
            result.append(msg)
            continue
        collapsed = _collapse_text(content)
        if collapsed is content:
            result.append(msg)
            continue
        new_msg = dict(msg)
        new_msg["content"] = collapsed
        result.append(new_msg)
    return result


def _collapse_text(text: str) -> str:
    """Collapse repeated whitespace and excessive blank lines."""
    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs to a single space (preserve newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Strip trailing whitespace on each line
    text = re.sub(r" +\n", "\n", text)
    return text

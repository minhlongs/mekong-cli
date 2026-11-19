"""Pure PII tokenization and subject-token redaction for DSAR ledger retention."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Final

_PII_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("PII_EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("PII_BANK_ACC", re.compile(r"(?i)(?:stk|tk|account|số\s*tài\s*khoản)[:\s#-]*(\d{8,16})\b")),
    ("PII_TAX_ID", re.compile(r"(?i)(?:mst|mã\s*số\s*thuế)[:\s#-]*(\d{10}(?:-\d{3})?)\b|\b\d{10}-\d{3}\b")),
    ("PII_CCCD", re.compile(r"(?i)(?:cccd|cmnd)[:\s#-]*(\d{9}|\d{12})\b|\b0\d{11}\b")),
    ("PII_PHONE", re.compile(r"(?:\+?84|0)[\s.-]?(?:2\d|3|5|7|8|9)(?:[\s.-]?\d){8}\b")),
)


@dataclass(frozen=True)
class RedactionResult:
    """Result of local Vietnamese PII tokenization before external LLM routing."""
    redacted_text: str
    token_map: dict[str, str]
    redacted_count: int


def redact_vietnamese_pii(text: str) -> RedactionResult:
    """Deterministically tokenize VN email, bank account, MST, CCCD/CMND, and phone strings."""
    token_map: dict[str, str] = {}
    working = text
    counter = 0
    for prefix, pattern in _PII_PATTERNS:
        def _sub(match: re.Match[str], pfx: str = prefix) -> str:
            nonlocal counter
            counter += 1
            tok = f"<{pfx}_{counter:02d}>"
            grp_val = next((g for g in match.groups() if g is not None), None)
            if grp_val is not None:
                token_map[tok] = grp_val
                return match.group(0).replace(grp_val, tok, 1)
            token_map[tok] = match.group(0)
            return tok

        working = pattern.sub(_sub, working)
    return RedactionResult(redacted_text=working, token_map=token_map, redacted_count=counter)


def _escape_like(val: str) -> str:
    return val.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _fold_vietnamese_ascii(text: str) -> str:
    replaced = text.replace("đ", "d").replace("Đ", "D")
    return "".join(ch for ch in unicodedata.normalize("NFKD", replaced) if not unicodedata.combining(ch))


def _expand_subject_tokens(tokens: set[str]) -> list[str]:
    expanded: set[str] = set()
    for tok in tokens:
        clean = tok.strip()
        if len(clean) >= 3:
            expanded.add(clean)
            folded = _fold_vietnamese_ascii(clean).strip()
            if len(folded) >= 3:
                expanded.add(folded)
    return sorted(expanded, key=len, reverse=True)


def _redact_memo_tokens(memo: str, ordered_tokens: list[str]) -> str:
    sanitized = redact_vietnamese_pii(memo).redacted_text
    for tok in ordered_tokens:
        pat = rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])" if tok.isascii() and tok.replace("_", "").isalnum() else re.escape(tok)
        sanitized = re.sub(pat, "[REDACTED_DSAR]", sanitized, flags=re.IGNORECASE)
    return sanitized



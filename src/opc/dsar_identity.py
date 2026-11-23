"""Structured, exact-identity DSAR subject resolution and normalization (no JSON substring matching)."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Final, Literal
import unicodedata

_EMAIL_RE: Final[re.Pattern[str]] = re.compile(r"^[^@\s%_]+(?:\.[^@\s%]+)*@[^@\s%]+\.[^@\s%]+$")
_EMAIL_SIMPLE_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_PHONE_CHARS_RE: Final[re.Pattern[str]] = re.compile(r"^\+?[\d\s.\-()]{9,20}$")
_CONTROL_RE: Final[re.Pattern[str]] = re.compile(r"[\x00-\x1f\x7f]")

_SENDER_FIELDS: Final[tuple[str, ...]] = ("sender_id", "subject_id", "zalo_sender_id", "client_id", "client_contact", "recipient")
_PHONE_FIELDS: Final[tuple[str, ...]] = ("sender_id", "phone", "client_phone", "sender_phone", "client_contact", "recipient")
_EMAIL_FIELDS: Final[tuple[str, ...]] = ("email", "client_email", "sender_email", "client_contact")


@dataclass(frozen=True)
class SubjectRef:
    """Validated, normalized DSAR subject identifier."""
    kind: Literal["sender_id", "phone", "email"]
    raw: str
    normalized: str


def normalize_unicode_nfc(value: str | None) -> str:
    return unicodedata.normalize("NFC", value or "").strip()


def normalize_phone_vn(raw: str | None) -> str | None:
    clean = normalize_unicode_nfc(raw)
    if not clean or not _PHONE_CHARS_RE.match(clean):
        return None
    digits = re.sub(r"\D", "", clean)
    if clean.startswith("+84") and 10 <= len(digits) <= 12:
        return digits
    if digits.startswith("84") and 10 <= len(digits) <= 12:
        return digits
    if digits.startswith("0") and len(digits) in (10, 11):
        return "84" + digits[1:]
    if 9 <= len(digits) <= 15:
        return digits
    return None


def normalize_email(raw: str | None) -> str | None:
    clean = normalize_unicode_nfc(raw).lower()
    if not clean or "%" in clean or not _EMAIL_SIMPLE_RE.match(clean):
        return None
    return clean


def _extract_channel_prefix(val: str) -> tuple[str, str | None]:
    low = val.casefold()
    for pfx, hint in (("zalo:", "sender_id"), ("phone:", "phone"), ("tel:", "phone"), ("email:", "email"), ("mailto:", "email")):
        if low.startswith(pfx):
            return val[len(pfx):].strip(), hint
    return val, None


def parse_dsar_subject(subject_id: str, *, subject_type: str | None = None) -> SubjectRef:
    """Validate and normalize a DSAR subject identifier; reject short, wildcard, malformed, or name-only inputs."""
    clean, hint = _extract_channel_prefix(normalize_unicode_nfc(subject_id))
    eff_type = subject_type if subject_type is not None else hint
    if not clean or _CONTROL_RE.search(clean):
        raise ValueError("Invalid subject_id for DSAR erasure: empty or contains control characters.")
    if "%" in clean:
        raise ValueError("Invalid subject_id for DSAR erasure: SQL wildcard '%' is forbidden.")
    if len(clean) < 4:
        raise ValueError("Invalid subject_id for DSAR erasure: identifier too short (min 4 chars).")
    if eff_type == "email" or (eff_type is None and "@" in clean and " " not in clean):
        norm_email = normalize_email(clean)
        if norm_email is None:
            raise ValueError("Invalid subject_id for DSAR erasure: malformed email address.")
        return SubjectRef(kind="email", raw=clean, normalized=norm_email)
    if eff_type == "phone":
        norm_phone = normalize_phone_vn(clean)
        if norm_phone is None:
            raise ValueError("Invalid subject_id for DSAR erasure: malformed phone identifier.")
        return SubjectRef(kind="phone", raw=clean, normalized=norm_phone)
    if eff_type is None and _PHONE_CHARS_RE.match(clean):
        norm_phone = normalize_phone_vn(clean)
        if norm_phone is not None:
            return SubjectRef(kind="phone", raw=clean, normalized=norm_phone)
    if eff_type is not None and eff_type != "sender_id":
        raise ValueError("Invalid subject_type for DSAR erasure: expected 'sender_id', 'phone', or 'email'.")
    if any(ch.isspace() for ch in clean):
        raise ValueError(
            "Invalid subject_id: ambiguous name-only DSAR request rejected; "
            "provide exact sender_id, verified phone, or verified email."
        )
    has_digit = any(ch.isdigit() for ch in clean)
    has_machine_sep = any(ch in ("_", ":", "-") for ch in clean)
    if eff_type != "sender_id" and not (has_digit or has_machine_sep):
        raise ValueError(
            "Invalid subject_id: ambiguous bare word/name rejected; "
            "provide exact sender_id, verified phone, or verified email."
        )
    if not any(ch.isalnum() for ch in clean):
        raise ValueError("Invalid subject_id for DSAR erasure: must contain alphanumeric characters.")
    return SubjectRef(kind="sender_id", raw=clean, normalized=clean.casefold())


def _strip_channel_prefix(val: str) -> str:
    return _extract_channel_prefix(val)[0]


def _iter_candidate_dicts(obj: dict[str, Any] | None, *, _max_depth: int = 4) -> list[dict[str, Any]]:
    if not isinstance(obj, dict):
        return []
    out: list[dict[str, Any]] = []
    stack: list[tuple[dict[str, Any], int]] = [(obj, 0)]
    while stack:
        cur, depth = stack.pop()
        out.append(cur)
        if depth < _max_depth:
            for val in cur.values():
                if isinstance(val, dict):
                    stack.append((val, depth + 1))
    return out


def _field_matches_ref(raw_value: Any, ref: SubjectRef) -> bool:
    if not isinstance(raw_value, str):
        return False
    clean = _strip_channel_prefix(normalize_unicode_nfc(raw_value))
    if not clean:
        return False
    if ref.kind == "email":
        return normalize_email(clean) == ref.normalized
    if ref.kind == "phone":
        return normalize_phone_vn(clean) == ref.normalized
    return clean.casefold() == ref.normalized


def payload_matches_subject(payload: dict[str, Any] | None, ref: SubjectRef) -> bool:
    """Return True iff a structured identity field in *payload* matches *ref* exactly."""
    fields = _EMAIL_FIELDS if ref.kind == "email" else (_PHONE_FIELDS if ref.kind == "phone" else _SENDER_FIELDS)
    for container in _iter_candidate_dicts(payload):
        for field_name in fields:
            if field_name in container and _field_matches_ref(container.get(field_name), ref):
                return True
    return False


def json_blob_matches_subject(raw_json: str | None, ref: SubjectRef) -> tuple[bool, dict[str, Any]]:
    """Parse JSON safely and evaluate exact structured subject identity matching."""
    if not isinstance(raw_json, str) or not raw_json.lstrip().startswith("{"):
        return False, {}
    try:
        parsed = json.loads(raw_json)
    except (ValueError, TypeError):
        return False, {}
    if not isinstance(parsed, dict):
        return False, {}
    return payload_matches_subject(parsed, ref), parsed


def extract_subject_redaction_tokens(proposal_input: dict[str, Any], ref: SubjectRef) -> set[str]:
    """Collect PII tokens strictly from an already-matched subject run for financial-memo redaction."""
    tokens: set[str] = {ref.raw, ref.normalized}
    for key in ("client_name", "sender_name", "sender_id", "client_contact", "client_email", "email", "phone"):
        val = proposal_input.get(key)
        if isinstance(val, str):
            norm = normalize_unicode_nfc(val)
            if len(norm) >= 4:
                tokens.add(norm)
    return tokens


def memo_matches_run_id(memo: str | None, run_id: str) -> bool:
    """Exact boundary match for run_id inside a VietQR bank memo (never substring match on subject_id)."""
    clean_memo = normalize_unicode_nfc(memo)
    if not clean_memo or not run_id:
        return False
    pat = rf"(?<![A-Za-z0-9_-]){re.escape(run_id)}(?![A-Za-z0-9_-])"
    return bool(re.search(pat, clean_memo))

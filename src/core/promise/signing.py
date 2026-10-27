# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Evidence signing, digests and sensitive-data redaction.

Honesty rules baked in here:

* A digest is **not** a signature. Records are signed with a keyed MAC that
  carries the *identity* of the signer (``key_id`` + ``signer_principal``) and
  a fingerprint of the key, so verification can tell "produced by a key this
  workspace trusts" apart from "produced by whoever knows the default".
* If no signing key is configured the record is stored as ``UNSIGNED`` and no
  gate may seal on it — the runtime never pretends to have signed.
* Raw secrets, credentials and payment card data are redacted before an
  evidence record is persisted or exported.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import hmac
import json
import os
import re
import typing

SIGNING_KEY_ENV = "MEKONG_EVIDENCE_SIGNING_KEY"
SIGNING_KEY_FILE_ENV = "MEKONG_EVIDENCE_KEY_FILE"
SIGNING_KEY_ID_ENV = "MEKONG_EVIDENCE_KEY_ID"
ALGORITHM = "HMAC-SHA256"
UNSIGNED_MARKER = "UNSIGNED"

SENSITIVE_KEY_RE = re.compile(
    r"(token|secret|password|passwd|api[_-]?key|apikey|credential|private[_-]?key|"
    r"card[_-]?number|cardno|cvv|cvc|otp|signature|authorization|cookie|session[_-]?id)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_RE = re.compile(r"(?i)(sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]+)")


def canonical_json_bytes(payload: typing.Any) -> bytes:
    """RFC 8785-style canonical JSON (sorted keys, no insignificant whitespace)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      default=str).encode("utf-8")


def sha256_of(payload: typing.Any) -> str:
    if isinstance(payload, (bytes, bytearray)):
        return hashlib.sha256(bytes(payload)).hexdigest()
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def redact(payload: typing.Any, *, depth: int = 0) -> typing.Any:
    """Recursively strip credential-like keys and known secret value shapes."""
    if depth > 12:
        return "[TRUNCATED_DEPTH]"
    if isinstance(payload, dict):
        out: dict[str, typing.Any] = {}
        for key, value in payload.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                out[key] = "[REDACTED]"
            else:
                out[key] = redact(value, depth=depth + 1)
        return out
    if isinstance(payload, (list, tuple)):
        return [redact(v, depth=depth + 1) for v in payload]
    if isinstance(payload, str):
        return SENSITIVE_VALUE_RE.sub("[REDACTED_SECRET]", payload)
    return payload


@dataclasses.dataclass(frozen=True)
class SigningIdentity:
    """Who signed, with which key."""

    key_id: str
    signer_principal: str
    workspace_id: str
    key_fingerprint: str
    algorithm: str = ALGORITHM

    def to_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


class EvidenceSigner:
    """Keyed signer for evidence records with explicit unsigned degradation."""

    def __init__(
        self,
        *,
        key: bytes | None = None,
        key_id: str | None = None,
        signer_principal: str = "runtime",
        workspace_id: str = "",
    ) -> None:
        resolved_key = key if key is not None else self._load_key()
        self._key = resolved_key
        self.identity = SigningIdentity(
            key_id=key_id or os.getenv(SIGNING_KEY_ID_ENV) or self._default_key_id(resolved_key),
            signer_principal=signer_principal,
            workspace_id=workspace_id,
            key_fingerprint=self._fingerprint(resolved_key),
        )

    @staticmethod
    def _load_key() -> bytes | None:
        env_key = os.getenv(SIGNING_KEY_ENV)
        if env_key:
            return env_key.encode("utf-8")
        key_file = os.getenv(SIGNING_KEY_FILE_ENV)
        if key_file and os.path.isfile(key_file):
            with open(key_file, "rb") as handle:
                return handle.read().strip()
        return None

    @staticmethod
    def _default_key_id(key: bytes | None) -> str:
        if not key:
            return UNSIGNED_MARKER
        return f"key-{hashlib.sha256(key).hexdigest()[:12]}"

    @staticmethod
    def _fingerprint(key: bytes | None) -> str:
        if not key:
            return "none"
        return hashlib.sha256(key).hexdigest()[:16]

    @property
    def is_configured(self) -> bool:
        return self._key is not None

    #: Keys excluded from the signed body. Everything else — including the
    #: ``signing`` block that names the signer — is covered by the HMAC, so a
    #: verifier that recomputes the digest after stripping only ``signature`` and
    #: ``algorithm`` (the contract the web receipt verifier implements) arrives at
    #: the same bytes.
    UNSIGNED_BODY_KEYS: frozenset[str] = frozenset({"signature", "algorithm"})

    def sign(self, payload: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """Return ``payload`` plus signature metadata (or an honest UNSIGNED mark)."""
        body = {k: v for k, v in payload.items() if k not in self.UNSIGNED_BODY_KEYS}
        if not self.is_configured:
            body["signing"] = {
                **self.identity.to_dict(),
                "key_id": UNSIGNED_MARKER,
                "status": UNSIGNED_MARKER,
                "reason": f"no signing key configured ({SIGNING_KEY_ENV} / {SIGNING_KEY_FILE_ENV})",
            }
            body["signature"] = None
            return body
        # The signing block is part of the signed body: it names the key and the
        # signer, so re-attribution is detectable. It must therefore be attached
        # *before* the digest is taken, otherwise no verifier can reproduce it.
        body["signing"] = {**self.identity.to_dict(), "status": "SIGNED", "signed_at": utc_now_iso()}
        signature = hmac.new(self._key or b"", canonical_json_bytes(body), hashlib.sha256).hexdigest()
        body["signature"] = signature
        return body

    def verify(self, record: dict[str, typing.Any], *, trusted_key_ids: typing.Iterable[str] | None = None) -> dict[str, typing.Any]:
        """Verify signature *and* signer identity."""
        signing = dict(record.get("signing") or {})
        signature = record.get("signature")
        if signing.get("status") == UNSIGNED_MARKER or not signature:
            return {"valid": False, "reason": signing.get("reason", "record is unsigned"),
                    "key_id": signing.get("key_id", UNSIGNED_MARKER)}
        if not self.is_configured:
            return {"valid": False, "reason": "verifier has no signing key configured",
                    "key_id": signing.get("key_id")}
        if signing.get("key_id") != self.identity.key_id:
            return {"valid": False,
                    "reason": f"signed with key '{signing.get('key_id')}', verifier holds '{self.identity.key_id}'",
                    "key_id": signing.get("key_id")}
        if trusted_key_ids is not None and signing.get("key_id") not in set(trusted_key_ids):
            return {"valid": False, "reason": "signer key is not in the trusted keyring",
                    "key_id": signing.get("key_id")}
        body = {k: v for k, v in record.items() if k not in self.UNSIGNED_BODY_KEYS}
        expected = hmac.new(self._key or b"", canonical_json_bytes(body), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, str(signature)):
            return {"valid": False, "reason": "signature mismatch — evidence was modified",
                    "key_id": signing.get("key_id")}
        return {"valid": True, "key_id": signing.get("key_id"),
                "signer_principal": signing.get("signer_principal"),
                "algorithm": signing.get("algorithm", ALGORITHM)}


def code_version() -> str:
    """Best-effort immutable code version (git commit) for evidence binding."""
    cached = os.getenv("MEKONG_CODE_VERSION")
    if cached:
        return cached
    import subprocess

    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            capture_output=True, text=True, timeout=5, check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


__all__ = [
    "ALGORITHM",
    "UNSIGNED_MARKER",
    "EvidenceSigner",
    "SigningIdentity",
    "canonical_json_bytes",
    "code_version",
    "redact",
    "sha256_of",
    "utc_now_iso",
]

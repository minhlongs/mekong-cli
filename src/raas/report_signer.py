# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Report Signer — Digital signing for audit report integrity and authenticity."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.raas.report_signer_keys import ReportSignerKeysMixin
from src.raas.report_signer_models import (
    SignatureResult,
    VerificationResult,
    compute_hash_chain_events,
)


class ReportSigner(ReportSignerKeysMixin):
    """Digital signing for audit reports."""

    def __init__(
        self, private_key_path: Optional[str] = None, public_key_path: Optional[str] = None
    ) -> None:
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._public_key: Optional[rsa.RSAPublicKey] = None
        self._key_id = "default"
        if private_key_path:
            self.load_private_key(private_key_path)
        if public_key_path:
            self.load_public_key(public_key_path)

    def sign_report(self, content: bytes, include_timestamp: bool = True) -> SignatureResult:
        """Sign report content with RSA private key."""
        if self._private_key is None:
            raise ValueError("Private key not loaded. Call load_private_key() first.")

        hash_value = hashlib.sha256(content).hexdigest()
        sig_bytes = self._private_key.sign(content, padding.PKCS1v15(), hashes.SHA256())
        timestamp = datetime.now(timezone.utc).isoformat() if include_timestamp else ""
        return SignatureResult(
            signature=base64.b64encode(sig_bytes).decode("utf-8"),
            hash_value=hash_value,
            timestamp=timestamp,
            key_id=self._key_id,
        )

    def verify_signature(
        self, content: bytes, signature_b64: str, expected_hash: Optional[str] = None
    ) -> VerificationResult:
        """Verify report signature."""
        now_iso = datetime.now(timezone.utc).isoformat()
        if self._public_key is None:
            return VerificationResult(
                valid=False, hash_match=False, timestamp=now_iso, error="Public key not loaded"
            )

        actual_hash = hashlib.sha256(content).hexdigest()
        hash_match = expected_hash is None or actual_hash == expected_hash

        try:
            signature_bytes = base64.b64decode(signature_b64)
        except Exception as e:
            return VerificationResult(
                valid=False, hash_match=hash_match, timestamp=now_iso,
                error=f"Invalid signature encoding: {e}",
            )

        try:
            self._public_key.verify(signature_bytes, content, padding.PKCS1v15(), hashes.SHA256())
            return VerificationResult(valid=True, hash_match=hash_match, timestamp=now_iso)
        except InvalidSignature:
            err = "Signature verification failed"
        except Exception as e:
            err = str(e)

        return VerificationResult(valid=False, hash_match=hash_match, timestamp=now_iso, error=err)

    def create_signature_file(self, report_path: str, signature_output_path: str) -> SignatureResult:
        """Sign report and save signature to file."""
        path = Path(report_path).expanduser()
        result = self.sign_report(path.read_bytes())
        signature_data = {
            "signature": result.signature,
            "hash_value": result.hash_value,
            "timestamp": result.timestamp,
            "key_id": result.key_id,
            "signed_file": str(path),
        }
        sig_path = Path(signature_output_path).expanduser()
        sig_path.parent.mkdir(parents=True, exist_ok=True)
        sig_path.write_text(json.dumps(signature_data, indent=2), encoding="utf-8")
        return result

    def verify_signature_file(self, report_path: str, signature_file_path: str) -> VerificationResult:
        """Verify report against signature file."""
        content = Path(report_path).expanduser().read_bytes()
        signature_data = json.loads(Path(signature_file_path).expanduser().read_text(encoding="utf-8"))
        return self.verify_signature(
            content, signature_data["signature"], signature_data.get("hash_value")
        )

    def compute_hash_chain(
        self, events: List[Dict[str, Any]], previous_hash: str = "0" * 64
    ) -> str:
        """Compute hash chain for event sequence."""
        return compute_hash_chain_events(events, previous_hash=previous_hash)


_signer: Optional[ReportSigner] = None


def get_signer() -> ReportSigner:
    """Get global signer instance."""
    global _signer
    if _signer is None:
        _signer = ReportSigner()
    return _signer


def sign_file(
    report_path: str, signature_path: str, private_key_path: Optional[str] = None
) -> SignatureResult:
    """Sign a report file."""
    signer = get_signer()
    if private_key_path:
        signer.load_private_key(private_key_path)
    return signer.create_signature_file(report_path, signature_path)


def verify_file(
    report_path: str, signature_path: str, public_key_path: Optional[str] = None
) -> VerificationResult:
    """Verify a report file signature."""
    signer = get_signer()
    if public_key_path:
        signer.load_public_key(public_key_path)
    return signer.verify_signature_file(report_path, signature_path)


__all__ = ["ReportSigner", "SignatureResult", "VerificationResult", "get_signer", "sign_file", "verify_file"]

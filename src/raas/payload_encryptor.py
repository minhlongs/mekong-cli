# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Payload Encryptor - AES-GCM Encryption for Usage Data

Provides secure encryption for usage event payloads before transmission
to RaaS Gateway. Uses AES-256-GCM for authenticated encryption.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .payload_encryptor_builder import PayloadBuilder
from .usage_event_schema import EncryptedPayload, SyncRequest, UsageSummary


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""


class PayloadEncryptor:
    """AES-256-GCM Payload Encryptor."""

    KEY_LENGTH = 32  # 256 bits
    NONCE_LENGTH = 12  # 96 bits for GCM
    VERSION = "v1"

    def __init__(
        self, key: Optional[bytes] = None, key_id: Optional[str] = None
    ) -> None:
        if key is not None:
            if len(key) != self.KEY_LENGTH:
                raise EncryptionError(
                    f"Key must be {self.KEY_LENGTH} bytes, got {len(key)}"
                )
            self.key = key
        else:
            self.key = self._load_or_generate_key()

        self.key_id = key_id or "default"
        self.aesgcm = AESGCM(self.key)

    def _load_or_generate_key(self) -> bytes:
        """Load key from environment or generate random."""
        env_key = os.getenv("RAAS_ENCRYPTION_KEY")
        if env_key:
            return hashlib.sha256(env_key.encode("utf-8")).digest()
        return os.urandom(self.KEY_LENGTH)

    def encrypt(self, payload: Dict[str, Any]) -> EncryptedPayload:
        """Encrypt payload dictionary."""
        try:
            plaintext = json.dumps(payload, sort_keys=True).encode("utf-8")
            nonce = os.urandom(self.NONCE_LENGTH)
            ciphertext = self.aesgcm.encrypt(nonce, plaintext, None)
            return EncryptedPayload.from_bytes(nonce, ciphertext)
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}") from e

    def decrypt(self, encrypted: EncryptedPayload) -> Dict[str, Any]:
        """Decrypt EncryptedPayload."""
        try:
            nonce, ciphertext = encrypted.to_bytes()
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(plaintext.decode("utf-8"))
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}") from e

    def encrypt_sync_request(
        self,
        events: list[Dict[str, Any]],
        license_key: str,
        tenant_id: str,
        summary: UsageSummary,
    ) -> SyncRequest:
        """Build encrypted SyncRequest for /v1/usage/sync."""
        payload = {
            "events": events,
            "event_count": len(events),
            "tenant_id": tenant_id,
        }
        payload_json = json.dumps(payload, sort_keys=True)
        checksum = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        encrypted_payload = self.encrypt(payload)

        return SyncRequest(
            license_key=license_key,
            tenant_id=tenant_id,
            encrypted_payload=encrypted_payload,
            summary=summary,
            checksum=checksum,
        )

    def decrypt_sync_request(self, request: SyncRequest) -> Dict[str, Any]:
        """Decrypt SyncRequest payload and verify checksum."""
        payload = self.decrypt(request.encrypted_payload)
        payload_json = json.dumps(payload, sort_keys=True)
        computed_checksum = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        if computed_checksum != request.checksum:
            raise ValueError("Checksum verification failed - payload may be tampered")
        return payload

    def get_key_id(self) -> str:
        """Get current key identifier."""
        return self.key_id

    def rotate_key(self, new_key: bytes) -> None:
        """Rotate to new encryption key."""
        if len(new_key) != self.KEY_LENGTH:
            raise EncryptionError(
                f"Key must be {self.KEY_LENGTH} bytes, got {len(new_key)}"
            )
        self.key = new_key
        self.aesgcm = AESGCM(self.key)
        self.key_id = f"rotated-{os.urandom(4).hex()}"


_encryptor: Optional[PayloadEncryptor] = None


def get_encryptor() -> PayloadEncryptor:
    """Get global encryptor instance."""
    global _encryptor
    if _encryptor is None:
        _encryptor = PayloadEncryptor()
    return _encryptor


def reset_encryptor() -> None:
    """Reset global encryptor (for testing)."""
    global _encryptor
    _encryptor = None


__all__ = [
    "EncryptionError",
    "PayloadBuilder",
    "PayloadEncryptor",
    "get_encryptor",
    "reset_encryptor",
]

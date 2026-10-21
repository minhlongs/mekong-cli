# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RSA key generation and PEM loading mixin for ReportSigner."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import load_pem_x509_certificate


class ReportSignerKeysMixin:
    """Key pair management methods for ReportSigner."""

    _private_key: Optional[rsa.RSAPrivateKey]
    _public_key: Optional[rsa.RSAPublicKey]
    _key_id: str

    def generate_key_pair(
        self,
        key_size: int = 2048,
        private_key_path: str = "~/.mekong/keys/audit_signing.pem",
        public_key_path: str = "~/.mekong/keys/audit_signing_pub.pem",
    ) -> Tuple[str, str]:
        """Generate new RSA key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend(),
        )
        public_key = private_key.public_key()

        priv_path = Path(private_key_path).expanduser()
        pub_path = Path(public_key_path).expanduser()
        priv_path.parent.mkdir(parents=True, exist_ok=True)

        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        with open(priv_path, "wb") as f:
            f.write(priv_pem)
        priv_path.chmod(0o600)

        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        with open(pub_path, "wb") as f:
            f.write(pub_pem)

        self._private_key = private_key
        self._public_key = public_key
        self._key_id = self._compute_key_id(public_key)

        return str(priv_path), str(pub_path)

    def load_private_key(self, key_path: str) -> None:
        """Load RSA private key from PEM file."""
        path = Path(key_path).expanduser()
        with open(path, "rb") as f:
            key_data = f.read()

        self._private_key = serialization.load_pem_private_key(
            key_data,
            password=None,
            backend=default_backend(),
        )
        self._public_key = self._private_key.public_key()
        self._key_id = self._compute_key_id(self._public_key)

    def load_public_key(self, key_path: str) -> None:
        """Load RSA public key from PEM file."""
        path = Path(key_path).expanduser()
        with open(path, "rb") as f:
            key_data = f.read()

        self._public_key = serialization.load_pem_public_key(
            key_data,
            backend=default_backend(),
        )
        self._key_id = self._compute_key_id(self._public_key)

    def load_certificate(self, cert_path: str) -> None:
        """Load certificate and extract public key."""
        path = Path(cert_path).expanduser()
        with open(path, "rb") as f:
            cert_data = f.read()

        cert = load_pem_x509_certificate(cert_data, backend=default_backend())
        self._public_key = cert.public_key()
        self._key_id = self._compute_key_id(self._public_key)

    def _compute_key_id(self, public_key: rsa.RSAPublicKey) -> str:
        """Compute key ID from public key fingerprint."""
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        fingerprint = hashlib.sha256(pub_pem).hexdigest()
        return fingerprint[:16]

    @property
    def key_id(self) -> str:
        """Get current key identifier."""
        return self._key_id

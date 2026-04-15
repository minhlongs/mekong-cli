"""
Auth Certificate Mixin — Device certificate operations for RaaSAuthClient

Handles:
- Getting certificate headers for API requests (X-Cert-ID, X-Cert-Sig)
- Checking certificate status
- Rotating device certificates
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AuthCertificateMixin:
    """Mixin for device certificate operations."""

    def _get_certificate_headers(self) -> Optional[Dict[str, str]]:
        """
        Get certificate headers for API requests.

        Returns:
            Dict with X-Cert-ID and X-Cert-Sig headers, or None if no cert
        """
        if not self.use_certificate_auth or not self._certificate_store:
            return None

        try:
            cert_headers = self._certificate_store.export_for_request()
            if cert_headers:
                return cert_headers
        except Exception as e:
            logger.debug("Certificate export for request failed: %s", e)

        return None

    def get_certificate_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current certificate status.

        Returns:
            Dict with certificate status info, or None if no cert
        """
        if not self._certificate_store:
            return None

        metadata = self._certificate_store.get_metadata()
        if not metadata:
            return {"has_certificate": False, "message": "No certificate found"}

        return {
            "has_certificate": True,
            "certificate_id": metadata.certificate_id,
            "device_id": metadata.device_id[:16] + "...",
            "valid_from": metadata.valid_from.isoformat(),
            "valid_until": metadata.valid_until.isoformat(),
            "days_until_expiry": (
                metadata.valid_until.day - datetime.now(timezone.utc).day
            ),
            "should_rotate": metadata.should_rotate,
            "is_expired": metadata.is_expired,
            "rotated_count": metadata.rotated_count,
        }

    def rotate_certificate(self) -> Optional[Dict[str, Any]]:
        """
        Rotate device certificate.

        Returns:
            Dict with rotation result, or None if rotation not needed
        """
        if not self._certificate_store:
            return {"success": False, "error": "Certificate auth not enabled"}

        try:
            new_cert = self._certificate_store.rotate_certificate()
            if new_cert:
                return {
                    "success": True,
                    "certificate_id": new_cert.certificate_id,
                    "valid_until": new_cert.valid_until.isoformat(),
                    "days_valid": (
                        new_cert.valid_until - datetime.now(timezone.utc)
                    ).days,
                }
            else:
                return {"success": True, "message": "Certificate not yet due for rotation"}
        except Exception as e:
            return {"success": False, "error": f"Rotation failed: {str(e)}"}

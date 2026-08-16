# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Authentication header construction for GatewayClient.

Builds JWT-bound usage attribution headers from stored credentials or
the RAAS_LICENSE_KEY environment variable.
"""

from __future__ import annotations

import os
from typing import Optional

from ..raas_auth import RaaSAuthClient


def get_auth_header(
    auth: RaaSAuthClient,
) -> tuple[dict[str, str], Optional[str]]:
    """
    Build authorisation headers with JWT-bound usage attribution.

    Priority:
    1. Stored credentials (``auth._load_credentials()``)
    2. ``RAAS_LICENSE_KEY`` environment variable

    Token type detection:
    - Contains ``"."`` → JWT token → add ``X-JWT-Attribution`` header
    - No ``"."`` → API key (mk_*) → add ``X-RaaS-Tenant-ID`` header

    Args:
        auth: Initialised RaaSAuthClient used to load/validate credentials.

    Returns:
        (headers dict, tenant_id or None)
    """
    creds = auth._load_credentials()
    token = creds.get("token") or os.getenv("RAAS_LICENSE_KEY")

    tenant_id: Optional[str] = None
    if token:
        result = auth.validate_credentials(token)
        if result.valid and result.tenant:
            tenant_id = result.tenant.tenant_id

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "X-RaaS-Source": "mekong-cli",
        "X-RaaS-Phase": "6",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"
        if "." in token:
            # JWT — embed first 100 chars for distributed tracing
            headers["X-JWT-Attribution"] = token[:100]
        elif tenant_id:
            headers["X-RaaS-Tenant-ID"] = tenant_id

    return headers, tenant_id

# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mock/fallback responses for local test mode (RAAS_LOCAL_TEST=true).

Phase 6.3: Allows offline CLI testing without hitting the real gateway.
"""

from __future__ import annotations

import random
from datetime import datetime

from .models import GatewayResponse


def mock_request(method: str, path: str) -> GatewayResponse:
    """
    Return a realistic mock GatewayResponse without a network call.

    Handles:
    - ``/v1/usage`` → returns paginated usage metrics
    - All other paths → returns a generic ``{"status": "ok", "mock": True}``

    Args:
        method: HTTP method (informational only).
        path: API path being mocked.

    Returns:
        GatewayResponse with status 200 and mock data.
    """
    if "/v1/usage" in path:
        mock_data: dict = {
            "license_key": "mk_mock_key",
            "tenant_id": "local_mock",
            "metrics": [
                {
                    "license_key": "mk_mock_key",
                    "tenant_id": "local_mock",
                    "tier": "pro",
                    "endpoint": "/v1/cook",
                    "method": "POST",
                    "request_count": random.randint(10, 100),
                    "payload_size": random.randint(100, 1000),
                    "timestamp": datetime.now().isoformat(),
                    "hour_bucket": datetime.now().strftime("%Y-%m-%d-%H"),
                    "metric_name": "api_calls",
                    "quantity": random.randint(10, 100),
                    "unit": "calls",
                }
                for _ in range(random.randint(1, 5))
            ],
            "pagination": {
                "limit": 100,
                "offset": 0,
                "total": random.randint(10, 50),
                "has_more": False,
            },
            "summary": {
                "total_requests": random.randint(100, 1000),
                "total_payload_size": random.randint(10000, 100000),
                "total_hours": random.randint(10, 50),
            },
        }
        return GatewayResponse(
            status_code=200,
            data=mock_data,
            headers={"X-RateLimit-Remaining": str(random.randint(100, 500))},
            elapsed_ms=random.uniform(1, 10),
            rate_limit_remaining=random.randint(100, 500),
            gateway_url="local_mock",
        )

    # Generic mock for all other endpoints
    return GatewayResponse(
        status_code=200,
        data={
            "status": "ok",
            "mock": True,
            "local_test_mode": True,
        },
        headers={"X-RateLimit-Remaining": "500"},
        elapsed_ms=random.uniform(1, 5),
        rate_limit_remaining=500,
        gateway_url="local_mock",
    )

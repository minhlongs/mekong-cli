# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Configuration, modes, and request/response evaluation helpers for Constitutional Review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import Request, Response

from src.core.constitution import ConstitutionalReview as ConReview, Constitution


class MiddlewareMode(Enum):
    """Operational modes for constitutional middleware."""

    MONITOR = "monitor"  # Log only, never block
    AUDIT = "audit"  # Log + add headers, allow all
    ENFORCE = "enforce"  # Block non-compliant requests


@dataclass
class MiddlewareConfig:
    """Configuration for ConstitutionalReview middleware."""

    mode: MiddlewareMode = MiddlewareMode.AUDIT
    constitution: Optional[Constitution] = None
    exclude_paths: List[str] = None  # Paths to skip review
    include_paths: List[str] = None  # Only review these paths (if set)
    minimum_score: float = 0.7  # Block threshold in enforce mode
    log_all_reviews: bool = True  # Log even passing reviews

    def __post_init__(self) -> None:
        if self.exclude_paths is None:
            self.exclude_paths = [
                "/health",
                "/metrics",
                "/docs",
                "/openapi.json",
                "/redoc",
                "/favicon.ico",
            ]
        if self.include_paths is None:
            self.include_paths = []


def build_request_context(request: Request) -> Dict[str, Any]:
    """Build context from request."""
    auth_header = request.headers.get("authorization", "")
    return {
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "has_auth": auth_header.startswith("Bearer "),
    }


def extract_request_parameters(request: Request) -> Dict[str, Any]:
    """Extract action parameters from request."""
    parameters: Dict[str, Any] = {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
    }

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        parameters["body_type"] = "json"
    elif "application/x-www-form-urlencoded" in content_type:
        parameters["body_type"] = "form"
    elif "multipart/form-data" in content_type:
        parameters["body_type"] = "multipart"

    return parameters


def extract_request_metadata(request: Request) -> Dict[str, Any]:
    """Extract metadata from request."""
    metadata: Dict[str, Any] = {
        "source": "api",
        "path": request.url.path,
    }
    agent = request.headers.get("x-mekong-agent")
    if agent:
        metadata["agent"] = agent

    intent = request.headers.get("x-mekong-intent")
    if intent:
        metadata["intent"] = intent

    metadata["priority"] = request.headers.get("x-priority", "normal")
    return metadata


def add_review_headers(response: Response, review: ConReview, duration_ms: float) -> None:
    """Add constitutional review headers to response."""
    response.headers["X-Constitutional-Score"] = f"{review.overall_score:.3f}"
    response.headers["X-Constitutional-Passed"] = str(review.passed).lower()
    response.headers["X-Constitutional-Duration-Ms"] = f"{duration_ms:.1f}"

    for result in review.principle_results:
        header_name = f"X-Constitutional-{result.principle.value.capitalize()}"
        response.headers[header_name] = f"{result.score:.2f}"


def generate_review_suggestions(review: ConReview) -> List[str]:
    """Generate actionable suggestions for failed principles."""
    suggestions: List[str] = []
    _msg_map = {
        "safety": "Review command for dangerous operations",
        "privacy": "Ensure PII is encrypted or masked",
        "security": "Use secure protocols and avoid credential exposure",
        "human_oversight": "Add human approval step for high-risk actions",
        "sustainability": "Review resource usage and add limits",
    }
    for result in review.principle_results:
        if result.score < 0.6:
            msg = _msg_map.get(result.principle.value)
            if msg:
                suggestions.append(msg)
            else:
                suggestions.append(f"Address {result.principle.value} concerns: {result.reason}")
    return suggestions


__all__ = [
    "ConReview",
    "Constitution",
    "MiddlewareConfig",
    "MiddlewareMode",
    "add_review_headers",
    "build_request_context",
    "extract_request_metadata",
    "extract_request_parameters",
    "generate_review_suggestions",
]

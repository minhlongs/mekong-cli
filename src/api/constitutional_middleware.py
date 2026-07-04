"""
Constitutional Review Middleware — API-level ethical guard.

Intercepts API requests and evaluates them against Constitutional AI principles.
Can be configured to:
- Log all reviews (audit mode)
- Block non-compliant requests (enforcement mode)
- Issue warnings (monitor mode)

Usage in FastAPI app:
    from src.api.middleware import ConstitutionalReview

    middleware = ConstitutionalReview(
        mode="enforce",  # "monitor", "audit", "enforce"
        constitution=constitution_instance
    )
    app.add_middleware(middleware)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.core.constitution import (
    ConstitutionalReview as ConReview,
    Constitution,
    PrincipleResult,
    get_constitution,
)

logger = logging.getLogger(__name__)


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
                "/health", "/metrics", "/docs", "/openapi.json", "/redoc",
                "/favicon.ico",
            ]
        if self.include_paths is None:
            self.include_paths = []


class ConstitutionalReview:
    """
    FastAPI middleware for constitutional review of API requests.

    Evaluates each request against constitutional principles and:
    - MONITOR: Logs results, allows all
    - AUDIT: Adds X-Constitutional-Score header, allows all
    - ENFORCE: Blocks requests below minimum_score
    """

    def __init__(self, config: Optional[MiddlewareConfig] = None) -> None:
        """
        Initialize Constitutional Review middleware.

        Args:
            config: Middleware configuration
        """
        self.config = config or MiddlewareConfig()
        self.constitution = self.config.constitution or get_constitution()
        self.logger = logging.getLogger(__name__)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Middleware entry point.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response (possibly blocked)
        """
        start_time = time.time()

        # Check path filtering
        if self._should_skip_path(request.url.path):
            return await call_next(request)

        # Build review context
        context = self._build_context(request)
        parameters = self._extract_parameters(request)
        metadata = self._extract_metadata(request)

        # Perform constitutional review
        review_start = time.time()
        review = self.constitution.review(
            action=self._action_for_request(request),
            context=context,
            parameters=parameters,
            metadata=metadata,
        )
        review_duration = (time.time() - review_start) * 1000

        # Log review
        if self.config.log_all_reviews or not review.passed:
            self._log_review(request, review, review_duration)

        # Check enforcement mode
        if self.config.mode == MiddlewareMode.ENFORCE:
            if not review.is_compliant():
                return self._block_response(request, review)

        # Add headers in audit mode
        response: Optional[Response] = None
        if self.config.mode == MiddlewareMode.AUDIT:
            # Call next but capture to add headers
            response = await call_next(request)
            self._add_headers(response, review, review_duration)
        else:
            response = await call_next(request)

        # Record metrics
        self._record_metrics(request, review, review_duration, start_time)

        return response

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _should_skip_path(self, path: str) -> bool:
        """Check if path should be skipped."""
        if self.config.include_paths:
            # Only include specific paths
            return not any(path.startswith(p) for p in self.config.include_paths)

        # Exclude specific paths
        return any(path.startswith(p) for p in self.config.exclude_paths)

    def _build_context(self, request: Request) -> Dict[str, Any]:
        """Build context from request."""
        context: Dict[str, Any] = {
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # Extract user from auth token if present
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            context["has_auth"] = True
            # Token parsing would happen in actual auth middleware
            # We just note auth is present
        else:
            context["has_auth"] = False

        return context

    def _extract_parameters(self, request: Request) -> Dict[str, Any]:
        """Extract action parameters from request."""
        parameters: Dict[str, Any] = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
        }

        # Body parameters (only for relevant content types)
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                # Note: body must be read; in production use request.state
                # This is simplified for illustration
                parameters["body_type"] = "json"
            except Exception:
                pass
        elif "application/x-www-form-urlencoded" in content_type:
            parameters["body_type"] = "form"
        elif "multipart/form-data" in content_type:
            parameters["body_type"] = "multipart"

        return parameters

    def _extract_metadata(self, request: Request) -> Dict[str, Any]:
        """Extract metadata from request."""
        metadata: Dict[str, Any] = {
            "source": "api",
            "path": request.url.path,
        }

        # Agent identification
        agent = request.headers.get("x-mekong-agent")
        if agent:
            metadata["agent"] = agent

        # Intent
        intent = request.headers.get("x-mekong-intent")
        if intent:
            metadata["intent"] = intent

        # Priority/urgency
        priority = request.headers.get("x-priority", "normal")
        metadata["priority"] = priority

        return metadata

    def _action_for_request(self, request: Request) -> str:
        """Determine action name for review."""
        return f"api:{request.method.lower()}:{request.url.path}"

    def _log_review(self, request: Request, review: ConReview, duration_ms: float) -> None:
        """Log constitutional review result."""
        log_data = {
            "path": request.url.path,
            "method": request.method,
            "overall_score": review.overall_score,
            "passed": review.passed,
            "blocked": review.blocked,
            "duration_ms": duration_ms,
            "principles": [
                {
                    "principle": r.principle.value,
                    "score": r.score,
                    "passed": r.passed,
                }
                for r in review.principle_results
            ],
        }

        if review.passed:
            self.logger.info(f"Constitutional review passed: {review.summary}", extra=log_data)
        else:
            self.logger.warning(
                f"Constitutional review failed: {review.summary}",
                extra={**log_data, "blocked": review.blocked},
            )

    def _block_response(self, request: Request, review: ConReview) -> JSONResponse:
        """Generate blocking response for non-compliant request."""
        self.logger.warning(
            f"Blocking request {request.method} {request.url.path}",
            extra={"score": review.overall_score},
        )

        return JSONResponse(
            status_code=403,
            content={
                "error": "constitutional_violation",
                "message": "Request blocked by Constitutional AI review",
                "details": {
                    "overall_score": review.overall_score,
                    "minimum_required": self.config.minimum_score,
                    "failed_principles": [
                        {
                            "principle": r.principle.value,
                            "score": r.score,
                            "reason": r.reason,
                        }
                        for r in review.principle_results
                        if r.score < 0.6
                    ],
                },
                "suggestions": self._generate_suggestions(review),
            },
        )

    def _add_headers(self, response: Response, review: ConReview, duration_ms: float) -> None:
        """Add constitutional review headers to response."""
        response.headers["X-Constitutional-Score"] = f"{review.overall_score:.3f}"
        response.headers["X-Constitutional-Passed"] = str(review.passed).lower()
        response.headers["X-Constitutional-Duration-Ms"] = f"{duration_ms:.1f}"

        # Add per-principle headers
        for result in review.principle_results:
            header_name = f"X-Constitutional-{result.principle.value.capitalize()}"
            response.headers[header_name] = f"{result.score:.2f}"

    def _record_metrics(
        self, request: Request, review: ConReview, review_duration: float, total_start: float
    ) -> None:
        """Record metrics for monitoring."""
        total_duration = (time.time() - total_start) * 1000

        # In a real implementation, send to metrics system (Prometheus, etc.)
        self.logger.debug(
            f"Metrics: review={review_duration:.1f}ms, total={total_duration:.1f}ms, score={review.overall_score:.3f}"
        )

    def _generate_suggestions(self, review: ConReview) -> List[str]:
        """Generate actionable suggestions for failed principles."""
        suggestions: List[str] = []

        for result in review.principle_results:
            if result.score < 0.6:
                if result.principle.value == "safety":
                    suggestions.append("Review command for dangerous operations")
                elif result.principle.value == "privacy":
                    suggestions.append("Ensure PII is encrypted or masked")
                elif result.principle.value == "security":
                    suggestions.append("Use secure protocols and avoid credential exposure")
                elif result.principle.value == "human_oversight":
                    suggestions.append("Add human approval step for high-risk actions")
                elif result.principle.value == "sustainability":
                    suggestions.append("Review resource usage and add limits")
                else:
                    suggestions.append(f"Address {result.principle.value} concerns: {result.reason}")

        return suggestions


# Convenience function for FastAPI setup
def setup_constitutional_middleware(
    app: Any,
    mode: str = "audit",
    constitution: Optional[Constitution] = None,
    minimum_score: float = 0.7,
) -> None:
    """
    Setup constitutional middleware on a FastAPI app.

    Args:
        app: FastAPI application instance
        mode: "monitor", "audit", or "enforce"
        constitution: Optional Constitution instance
        minimum_score: Blocking threshold (enforce mode)
    """
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError("Expected FastAPI application")

    config = MiddlewareConfig(
        mode=MiddlewareMode(mode),
        constitution=constitution or get_constitution(),
        minimum_score=minimum_score,
    )

    app.add_middleware(ConstitutionalReview, config=config)
    logger.info(f"Constitutional middleware added in {mode} mode")

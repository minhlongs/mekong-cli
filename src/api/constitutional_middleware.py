# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Constitutional Review Middleware — API-level ethical guard.

Intercepts API requests and evaluates them against Constitutional AI principles.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.api.constitutional_rules import (  # noqa: F401
    ConReview,
    Constitution,
    MiddlewareConfig,
    MiddlewareMode,
    add_review_headers,
    build_request_context,
    extract_request_metadata,
    extract_request_parameters,
    generate_review_suggestions,
)
from src.core.constitution import get_constitution

logger = logging.getLogger(__name__)


class ConstitutionalReview:
    """FastAPI middleware for constitutional review of API requests."""

    def __init__(self, config: Optional[MiddlewareConfig] = None) -> None:
        self.config = config or MiddlewareConfig()
        self.constitution = self.config.constitution or get_constitution()
        self.logger = logging.getLogger(__name__)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        if self._should_skip_path(request.url.path):
            return await call_next(request)

        context = self._build_context(request)
        parameters = self._extract_parameters(request)
        metadata = self._extract_metadata(request)

        review_start = time.time()
        review = self.constitution.review(
            action=self._action_for_request(request),
            context=context,
            parameters=parameters,
            metadata=metadata,
        )
        review_duration = (time.time() - review_start) * 1000

        if self.config.log_all_reviews or not review.passed:
            self._log_review(request, review, review_duration)

        if self.config.mode == MiddlewareMode.ENFORCE and not review.is_compliant():
            return self._block_response(request, review)

        response = await call_next(request)
        if self.config.mode == MiddlewareMode.AUDIT:
            self._add_headers(response, review, review_duration)

        self._record_metrics(request, review, review_duration, start_time)
        return response

    def _should_skip_path(self, path: str) -> bool:
        if self.config.include_paths:
            return not any(path.startswith(p) for p in self.config.include_paths)
        return any(path.startswith(p) for p in self.config.exclude_paths)

    def _build_context(self, request: Request) -> Dict[str, Any]:
        return build_request_context(request)

    def _extract_parameters(self, request: Request) -> Dict[str, Any]:
        return extract_request_parameters(request)

    def _extract_metadata(self, request: Request) -> Dict[str, Any]:
        return extract_request_metadata(request)

    def _action_for_request(self, request: Request) -> str:
        return f"api:{request.method.lower()}:{request.url.path}"

    def _log_review(self, request: Request, review: ConReview, duration_ms: float) -> None:
        log_data = {
            "path": request.url.path,
            "method": request.method,
            "overall_score": review.overall_score,
            "passed": review.passed,
            "blocked": review.blocked,
            "duration_ms": duration_ms,
            "principles": [
                {"principle": r.principle.value, "score": r.score, "passed": r.passed}
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
                        {"principle": r.principle.value, "score": r.score, "reason": r.reason}
                        for r in review.principle_results
                        if r.score < 0.6
                    ],
                },
                "suggestions": self._generate_suggestions(review),
            },
        )

    def _add_headers(self, response: Response, review: ConReview, duration_ms: float) -> None:
        add_review_headers(response, review, duration_ms)

    def _record_metrics(
        self, request: Request, review: ConReview, review_duration: float, total_start: float
    ) -> None:
        total_duration = (time.time() - total_start) * 1000
        self.logger.debug(
            f"Metrics: review={review_duration:.1f}ms, total={total_duration:.1f}ms, score={review.overall_score:.3f}"
        )

    def _generate_suggestions(self, review: ConReview) -> List[str]:
        return generate_review_suggestions(review)


def setup_constitutional_middleware(
    app: Any,
    mode: str = "audit",
    constitution: Optional[Constitution] = None,
    minimum_score: float = 0.7,
) -> None:
    """Setup constitutional middleware on a FastAPI app."""
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

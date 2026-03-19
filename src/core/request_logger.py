"""Request logging middleware for Mekong CLI API."""

import logging
import time
import uuid
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Log all HTTP requests and responses with timing.

    Adds X-Request-ID header to all responses for traceability.
    Logs:
    - Request: method, path, client IP, request ID
    - Response: status code, duration in ms
    - Errors: exception message, duration
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        # Log incoming request
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            "REQUEST [%s] %s %s from %s",
            request_id,
            request.method,
            request.url.path,
            client_ip,
        )

        try:
            response = await call_next(request)

            # Log response with timing
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "RESPONSE [%s] %d %s %s in %.2fms",
                request_id,
                response.status_code,
                request.method,
                request.url.path,
                duration_ms,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log unhandled exceptions
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "ERROR [%s] %s %s - %s in %.2fms",
                request_id,
                request.method,
                request.url.path,
                str(e),
                duration_ms,
            )
            raise


__all__ = ["RequestLoggerMiddleware"]

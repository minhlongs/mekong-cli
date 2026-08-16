# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""OpenTelemetry tracing initialization."""
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource


def init_telemetry() -> None:
    """Initialize OpenTelemetry if endpoint configured."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    resource = Resource.create({"service.name": "mekong-cli", "service.version": os.getenv("APP_VERSION", "0.0.0")})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from src.gateway import app
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        pass

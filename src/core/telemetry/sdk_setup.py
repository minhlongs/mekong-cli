# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/telemetry/sdk_setup.py — Bootstrap OTel SDK with OTLP gRPC exporter.

Call setup_telemetry() once at process start (e.g. in cli/main.py or FastAPI lifespan).
OTEL_EXPORTER_OTLP_ENDPOINT env var controls collector address (default: localhost:4317).
"""

import os
import logging

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

_SETUP_DONE = False


def setup_telemetry(service_name: str = "mekong-cli") -> None:
    """
    Initialise OTel SDK. Idempotent — safe to call multiple times.
    Reads OTEL_EXPORTER_OTLP_ENDPOINT (default: grpc://localhost:4317).
    Skips initialisation if OTEL_SDK_DISABLED=true.
    """
    global _SETUP_DONE
    if _SETUP_DONE:
        return

    if os.getenv("OTEL_SDK_DISABLED", "").lower() == "true":
        logger.info("OTel SDK disabled via env — skipping setup")
        return

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    resource = Resource(attributes={SERVICE_NAME: service_name})

    # --- Metrics ---
    try:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )

        metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
        reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=15_000)
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(meter_provider)
    except Exception as exc:
        logger.warning("OTel metrics init failed (non-fatal): %s", exc)

    # --- Traces ---
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
        )
        trace.set_tracer_provider(tracer_provider)
    except Exception as exc:
        logger.warning("OTel traces init failed (non-fatal): %s", exc)

    _SETUP_DONE = True
    logger.info("OTel SDK ready — exporting to %s", endpoint)

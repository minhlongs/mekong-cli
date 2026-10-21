# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Anthropic SDK Engine — Structured tool calling for OCOP RaaS."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from src.ai.anthropic_models import ExportReadinessResult, OCOP_EXPORT_TOOL

logger = logging.getLogger(__name__)


class AnthropicEngine:
    """Anthropic SDK client with OCOP tool bindings."""

    MAX_RETRIES = 3
    BASE_DELAY = 1.0

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import anthropic  # noqa: F811
            except ImportError:
                raise ImportError("anthropic SDK not installed. Run: pip install anthropic")
            if not self._api_key:
                raise ValueError("ANTHROPIC_API_KEY not set. Set it in .env or pass api_key to AnthropicEngine().")
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def analyze_export_readiness(
        self, product_name: str, specifications: dict[str, Any] | None = None,
    ) -> ExportReadinessResult:
        specs_text = f"\nSpecifications: {json.dumps(specifications, ensure_ascii=False)}" if specifications else ""
        prompt = (
            f"Analyze this Vietnamese OCOP agricultural product for international export readiness.\n"
            f"Product: {product_name}{specs_text}\n\n"
            f"Use the analyze_ocop_export_readiness tool to provide your analysis."
        )
        return self._call_with_retry(prompt)

    def _call_with_retry(self, prompt: str) -> ExportReadinessResult:
        import anthropic
        client = self._get_client()
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = client.messages.create(
                    model=self._model, max_tokens=1024, tools=[OCOP_EXPORT_TOOL],
                    messages=[{"role": "user", "content": prompt}],
                )
                return self._parse_response(response)
            except (anthropic.RateLimitError, anthropic.APITimeoutError) as e:
                last_error = e
                delay = self.BASE_DELAY * (2 ** attempt)
                logger.warning("API retryable error (attempt %d/%d): %s, retrying in %.1fs", attempt + 1, self.MAX_RETRIES, e, delay)
                time.sleep(delay)
            except anthropic.APIError as e:
                logger.error("Anthropic API error: %s", e)
                return ExportReadinessResult(fda_compliance_status="error", target_market="unknown", suggested_alibaba_title="", error=str(e))

        return ExportReadinessResult(
            fda_compliance_status="error", target_market="unknown", suggested_alibaba_title="",
            error=f"Max retries ({self.MAX_RETRIES}) exhausted: {last_error}",
        )

    def _parse_response(self, response: Any) -> ExportReadinessResult:
        for block in response.content:
            if block.type == "tool_use" and block.name == "analyze_ocop_export_readiness":
                data = block.input
                return ExportReadinessResult(
                    fda_compliance_status=data.get("fda_compliance_status", "unknown"),
                    target_market=data.get("target_market", "unknown"),
                    suggested_alibaba_title=data.get("suggested_alibaba_title", ""),
                    raw_response=data,
                )
        text_content = next((block.text for block in response.content if block.type == "text"), "")
        return ExportReadinessResult(
            fda_compliance_status="pending_review", target_market="unknown",
            suggested_alibaba_title="", raw_response={"text": text_content},
            error="No tool_use block in response",
        )


def analyze_ocop_export_readiness(
    product_name: str, specifications: dict[str, Any] | None = None, api_key: str | None = None,
) -> ExportReadinessResult:
    engine = AnthropicEngine(api_key=api_key)
    return engine.analyze_export_readiness(product_name, specifications)


__all__ = ["OCOP_EXPORT_TOOL", "ExportReadinessResult", "AnthropicEngine", "analyze_ocop_export_readiness"]

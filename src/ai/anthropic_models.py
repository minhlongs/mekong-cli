# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Anthropic Tool Schema and Results for OCOP RaaS."""

from dataclasses import dataclass
from typing import Any

OCOP_EXPORT_TOOL = {
    "name": "analyze_ocop_export_readiness",
    "description": (
        "Analyze a Vietnamese OCOP agricultural product for export readiness. "
        "Returns FDA compliance status, target market recommendation, "
        "and a suggested Alibaba listing title."
    ),
    "input_schema": {
        "type": "object",
        "required": ["product_name"],
        "properties": {
            "product_name": {
                "type": "string",
                "description": "Vietnamese product name (e.g., 'Khoai lang Bình Minh')",
            },
            "specifications": {
                "type": "object",
                "description": "Product specs (weight, grade, certifications, etc.)",
                "properties": {
                    "weight_kg": {"type": "number"},
                    "grade": {"type": "string"},
                    "certifications": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "origin_province": {"type": "string"},
                    "harvest_date": {"type": "string"},
                },
            },
        },
    },
}


@dataclass
class ExportReadinessResult:
    """Structured result from export readiness analysis."""

    fda_compliance_status: str
    target_market: str
    suggested_alibaba_title: str
    raw_response: dict[str, Any] | None = None
    error: str | None = None


__all__ = ["OCOP_EXPORT_TOOL", "ExportReadinessResult"]

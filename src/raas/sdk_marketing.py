# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Marketing endpoint mixins for synchronous and asynchronous Mekong RaaS SDK clients."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.raas.sdk_models import (
    ContentTemplate,
    PerformanceData,
    RenderedContent,
    TemplateMetadata,
)


def _build_template(template: Dict[str, Any]) -> ContentTemplate:
    return ContentTemplate(
        template_id=template["template_id"], name=template["name"],
        description=template["description"], content_type=template["content_type"],
        channel=template["channel"], template=template["template"],
        placeholders=template.get("placeholders", []), metadata=template.get("metadata", {}),
    )


def _build_performance_payload(performance: PerformanceData) -> Dict[str, Any]:
    return {
        "content_id": performance.content_id, "template_id": performance.template_id,
        "channel": performance.channel, "impressions": performance.impressions,
        "clicks": performance.clicks, "conversions": performance.conversions,
        "engagement_rate": performance.engagement_rate,
        "click_through_rate": performance.click_through_rate,
        "conversion_rate": performance.conversion_rate,
        "revenue": performance.revenue, "published_at": performance.published_at,
    }


def _parse_performance(data: Dict[str, Any]) -> PerformanceData:
    return PerformanceData(
        content_id=data["content_id"], template_id=data["template_id"],
        channel=data["channel"], impressions=data["impressions"],
        clicks=data["clicks"], conversions=data["conversions"],
        engagement_rate=data["engagement_rate"], click_through_rate=data["click_through_rate"],
        conversion_rate=data["conversion_rate"], revenue=data["revenue"],
        published_at=data["published_at"],
    )


def _build_rendered(data: Dict[str, Any]) -> RenderedContent:
    return RenderedContent(
        content_id=data["content_id"], template_id=data["template_id"],
        channel=data["channel"], content_type=data["content_type"],
        rendered_content=data["rendered_content"], placeholders_used=data["placeholders_used"],
        metadata=data.get("metadata", {}),
    )


def _build_filter_params(
    category: Optional[str], channel: Optional[str], content_type: Optional[str]
) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if category:
        params["category"] = category
    if channel:
        params["channel"] = channel
    if content_type:
        params["content_type"] = content_type
    return params


class SDKMarketingMixin:
    """Synchronous marketing API methods for MekongClient."""

    def _request(self, method: str, path: str, **kwargs: Any) -> dict: ...

    def list_marketing_templates(
        self,
        category: Optional[str] = None,
        channel: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> List[ContentTemplate]:
        params = _build_filter_params(category, channel, content_type)
        data = self._request("GET", "/v1/marketing/templates", params=params)
        return [_build_template(t) for t in data.get("templates", [])]

    def get_marketing_template(self, template_id: str) -> ContentTemplate:
        return _build_template(self._request("GET", f"/v1/marketing/templates/{template_id}"))

    def get_marketing_template_metadata(self) -> TemplateMetadata:
        data = self._request("GET", "/v1/marketing/templates/metadata")
        return TemplateMetadata(
            total=data["total"], categories=data["categories"],
            channels=data["channels"], content_types=data["content_types"],
        )

    def render_marketing_content(
        self, template_id: str, placeholders: Dict[str, Any]
    ) -> RenderedContent:
        payload = {"template_id": template_id, "placeholders": placeholders}
        return _build_rendered(self._request("POST", "/v1/marketing/render", json=payload))

    def track_marketing_performance(self, performance: PerformanceData) -> Dict[str, Any]:
        return self._request("POST", "/v1/marketing/performance", json=_build_performance_payload(performance))

    def get_marketing_performance(self, content_id: str) -> PerformanceData:
        return _parse_performance(self._request("GET", f"/v1/marketing/performance/{content_id}"))


class SDKAsyncMarketingMixin:
    """Asynchronous marketing API methods for MekongAsyncClient."""

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict: ...

    async def list_marketing_templates(
        self,
        category: Optional[str] = None,
        channel: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> List[ContentTemplate]:
        params = _build_filter_params(category, channel, content_type)
        data = await self._request("GET", "/v1/marketing/templates", params=params)
        return [_build_template(t) for t in data.get("templates", [])]

    async def get_marketing_template(self, template_id: str) -> ContentTemplate:
        return _build_template(await self._request("GET", f"/v1/marketing/templates/{template_id}"))

    async def get_marketing_template_metadata(self) -> TemplateMetadata:
        data = await self._request("GET", "/v1/marketing/templates/metadata")
        return TemplateMetadata(
            total=data["total"], categories=data["categories"],
            channels=data["channels"], content_types=data["content_types"],
        )

    async def render_marketing_content(
        self, template_id: str, placeholders: Dict[str, Any]
    ) -> RenderedContent:
        payload = {"template_id": template_id, "placeholders": placeholders}
        return _build_rendered(await self._request("POST", "/v1/marketing/render", json=payload))

    async def track_marketing_performance(self, performance: PerformanceData) -> Dict[str, Any]:
        return await self._request("POST", "/v1/marketing/performance", json=_build_performance_payload(performance))

    async def get_marketing_performance(self, content_id: str) -> PerformanceData:
        return _parse_performance(await self._request("GET", f"/v1/marketing/performance/{content_id}"))

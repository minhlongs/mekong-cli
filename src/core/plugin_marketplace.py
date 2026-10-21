# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Plugin Marketplace Client."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)
DEFAULT_MARKETPLACE_URL = "https://marketplace.mekong.dev/api/v1"
MARKETPLACE_TIMEOUT = 30.0


class PluginSortBy(str, Enum):
    POPULARITY, DOWNLOADS, RATING, UPDATED, NAME = "popularity", "downloads", "rating", "updated_at", "name"


class SortOrder(str, Enum):
    ASC, DESC = "asc", "desc"


@dataclass
class MarketplacePlugin:
    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    tags: list[str] = field(default_factory=list)
    repository_url: str = ""
    documentation_url: str = ""
    created_at: str = ""
    updated_at: str = ""
    license: str = "MIT"
    min_mekong_version: str = ""
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketplacePlugin:
        return cls(
            name=data.get("name", ""), version=data.get("version", "0.0.0"), description=data.get("description", ""),
            author=data.get("author", ""), plugin_type=data.get("plugin_type", "agent"), downloads=data.get("downloads", 0),
            rating=data.get("rating", 0.0), rating_count=data.get("rating_count", 0), tags=data.get("tags", []),
            repository_url=data.get("repository_url", ""), documentation_url=data.get("documentation_url", ""),
            created_at=data.get("created_at", ""), updated_at=data.get("updated_at", ""), license=data.get("license", "MIT"),
            min_mekong_version=data.get("min_mekong_version", ""), dependencies=data.get("dependencies", []),
        )


@dataclass
class SearchResult:
    total: int
    page: int
    page_size: int
    total_pages: int
    plugins: list[MarketplacePlugin]


class MarketplaceError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class NetworkError(MarketplaceError):
    pass


class NotFoundError(MarketplaceError):
    pass


class MarketplaceClient:
    """Client for Mekong Plugin Marketplace."""

    def __init__(self, base_url: str | None = None, timeout: float = MARKETPLACE_TIMEOUT, api_key: str | None = None) -> None:
        self._base_url = (base_url or DEFAULT_MARKETPLACE_URL).rstrip("/")
        self._timeout = timeout
        self._api_key = api_key
        self._client = httpx.Client(base_url=self._base_url, timeout=self._timeout, headers=self._build_headers())

    def _build_headers(self) -> dict[str, str]:
        return {"User-Agent": "mekong-cli-marketplace/1.0", **({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {})}

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise NetworkError(f"Cannot connect to marketplace: {e}") from e
        except httpx.TimeoutException as e:
            raise NetworkError(f"Request timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {path}") from e
            raise MarketplaceError(f"HTTP {e.response.status_code}: {e.response.text[:200]}", status_code=e.response.status_code) from e

    def search(
        self, query: str | None = None, plugin_type: str | None = None, tags: list[str] | None = None,
        page: int = 1, page_size: int = 20, sort_by: PluginSortBy = PluginSortBy.POPULARITY, sort_order: SortOrder = SortOrder.DESC,
    ) -> SearchResult:
        params: dict[str, Any] = {"page": page, "page_size": min(page_size, 100), "sort_by": sort_by.value, "sort_order": sort_order.value}
        if query:
            params["q"] = query
        if plugin_type:
            params["type"] = plugin_type
        if tags:
            params["tags"] = ",".join(tags)
        data = self._request("GET", "/plugins", params=params)
        return SearchResult(data.get("total", 0), data.get("page", page), data.get("page_size", page_size), data.get("total_pages", 0), [MarketplacePlugin.from_dict(p) for p in data.get("plugins", [])])

    def get_plugin(self, name: str) -> MarketplacePlugin:
        return MarketplacePlugin.from_dict(self._request("GET", f"/plugins/{name}"))

    def get_featured(self, limit: int = 10) -> list[MarketplacePlugin]:
        return [MarketplacePlugin.from_dict(p) for p in self._request("GET", "/plugins/featured", params={"limit": limit}).get("plugins", [])]

    def get_trending(self, limit: int = 10) -> list[MarketplacePlugin]:
        return [MarketplacePlugin.from_dict(p) for p in self._request("GET", "/plugins/trending", params={"limit": limit}).get("plugins", [])]

    def install(self, name: str) -> dict[str, Any]:
        return self._request("GET", f"/plugins/{name}/install")

    def get_categories(self) -> list[dict[str, Any]]:
        return self._request("GET", "/categories")

    def get_tags(self) -> list[str]:
        return self._request("GET", "/tags").get("tags", [])

    def rate_plugin(self, name: str, rating: int, comment: str | None = None) -> dict[str, Any]:
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return self._request("POST", f"/plugins/{name}/rate", json={"rating": rating, "comment": comment})

    def health_check(self) -> bool:
        try:
            return self._request("GET", "/health").get("status") == "healthy"
        except MarketplaceError:
            return False

    @property
    def base_url(self) -> str:
        return self._base_url

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> MarketplaceClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


__all__ = ["DEFAULT_MARKETPLACE_URL", "MarketplaceClient", "MarketplaceError", "MarketplacePlugin", "NetworkError", "NotFoundError", "PluginSortBy", "SearchResult", "SortOrder"]

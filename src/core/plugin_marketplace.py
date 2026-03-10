"""Mekong CLI - Plugin Marketplace Client.

Remote marketplace client for plugin discovery, search, and installation.
Connects to marketplace API for browsing available plugins.

Usage:
    client = MarketplaceClient()
    plugins = client.search("seo")
    details = client.get_plugin("mekong-plugin-seo")
    client.install("mekong-plugin-seo")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_MARKETPLACE_URL = "https://marketplace.mekong.dev/api/v1"
MARKETPLACE_TIMEOUT = 30.0


class PluginSortBy(str, Enum):
    """Sort options for marketplace queries."""

    POPULARITY = "popularity"
    DOWNLOADS = "downloads"
    RATING = "rating"
    UPDATED = "updated_at"
    NAME = "name"


class SortOrder(str, Enum):
    """Sort order for marketplace queries."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class MarketplacePlugin:
    """Plugin metadata from marketplace."""

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
        """Serialize to dict."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "plugin_type": self.plugin_type,
            "downloads": self.downloads,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "tags": self.tags,
            "repository_url": self.repository_url,
            "documentation_url": self.documentation_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "license": self.license,
            "min_mekong_version": self.min_mekong_version,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketplacePlugin:
        """Deserialize from dict."""
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            plugin_type=data.get("plugin_type", "agent"),
            downloads=data.get("downloads", 0),
            rating=data.get("rating", 0.0),
            rating_count=data.get("rating_count", 0),
            tags=data.get("tags", []),
            repository_url=data.get("repository_url", ""),
            documentation_url=data.get("documentation_url", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            license=data.get("license", "MIT"),
            min_mekong_version=data.get("min_mekong_version", ""),
            dependencies=data.get("dependencies", []),
        )


@dataclass
class SearchResult:
    """Search results from marketplace."""

    total: int
    page: int
    page_size: int
    total_pages: int
    plugins: list[MarketplacePlugin]


class MarketplaceError(Exception):
    """Base exception for marketplace errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class NetworkError(MarketplaceError):
    """Network connectivity error."""

    pass


class NotFoundError(MarketplaceError):
    """Plugin not found in marketplace."""

    pass


class MarketplaceClient:
    """Client for Mekong Plugin Marketplace.

    Provides discovery, search, and installation of plugins from remote marketplace.

    Args:
        base_url: Marketplace API base URL (default: https://marketplace.mekong.dev/api/v1)
        timeout: Request timeout in seconds (default: 30)
        api_key: Optional API key for authenticated endpoints

    Example:
        >>> client = MarketplaceClient()
        >>> results = client.search("seo", plugin_type="agent")
        >>> for plugin in results.plugins:
        ...     print(f"{plugin.name}: {plugin.description}")
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = MARKETPLACE_TIMEOUT,
        api_key: str | None = None,
    ) -> None:
        self._base_url = (base_url or DEFAULT_MARKETPLACE_URL).rstrip("/")
        self._timeout = timeout
        self._api_key = api_key
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {"User-Agent": "mekong-cli-marketplace/1.0"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make HTTP request with error handling.

        Raises:
            NetworkError: On connection/timeout errors
            NotFoundError: On 404 responses
            MarketplaceError: On other HTTP errors
        """
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            logger.error("Failed to connect to marketplace: %s", e)
            raise NetworkError(f"Cannot connect to marketplace: {e}") from e
        except httpx.TimeoutException as e:
            logger.error("Request timeout: %s", e)
            raise NetworkError(f"Request timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {path}") from e
            logger.error("HTTP error %s: %s", e.response.status_code, e)
            raise MarketplaceError(
                f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                status_code=e.response.status_code,
            ) from e

    def search(
        self,
        query: str | None = None,
        plugin_type: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: PluginSortBy = PluginSortBy.POPULARITY,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> SearchResult:
        """Search marketplace for plugins.

        Args:
            query: Free text search query
            plugin_type: Filter by plugin type (agent, provider, hook, recipe)
            tags: Filter by tags (AND logic)
            page: Page number (1-indexed)
            page_size: Results per page (max 100)
            sort_by: Sort field
            sort_order: Sort order

        Returns:
            SearchResult with pagination info and plugin list

        Example:
            >>> results = client.search("seo", plugin_type="agent", page_size=10)
            >>> print(f"Found {results.total} plugins")
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": min(page_size, 100),
            "sort_by": sort_by.value,
            "sort_order": sort_order.value,
        }

        if query:
            params["q"] = query
        if plugin_type:
            params["type"] = plugin_type
        if tags:
            params["tags"] = ",".join(tags)

        logger.debug("Searching marketplace: %s", params)
        data = self._request("GET", "/plugins", params=params)

        return SearchResult(
            total=data.get("total", 0),
            page=data.get("page", page),
            page_size=data.get("page_size", page_size),
            total_pages=data.get("total_pages", 0),
            plugins=[
                MarketplacePlugin.from_dict(p) for p in data.get("plugins", [])
            ],
        )

    def get_plugin(self, name: str) -> MarketplacePlugin:
        """Get plugin details by name.

        Args:
            name: Plugin name (e.g., "mekong-plugin-seo")

        Returns:
            MarketplacePlugin with full details

        Raises:
            NotFoundError: If plugin not found

        Example:
            >>> plugin = client.get_plugin("mekong-plugin-seo")
            >>> print(f"{plugin.name} v{plugin.version} - {plugin.rating}★")
        """
        logger.debug("Fetching plugin details: %s", name)
        data = self._request("GET", f"/plugins/{name}")
        return MarketplacePlugin.from_dict(data)

    def get_featured(self, limit: int = 10) -> list[MarketplacePlugin]:
        """Get featured plugins.

        Args:
            limit: Maximum number of plugins to return

        Returns:
            List of featured plugins
        """
        logger.debug("Fetching featured plugins")
        data = self._request("GET", "/plugins/featured", params={"limit": limit})
        return [MarketplacePlugin.from_dict(p) for p in data.get("plugins", [])]

    def get_trending(self, limit: int = 10) -> list[MarketplacePlugin]:
        """Get trending plugins (most downloaded this week).

        Args:
            limit: Maximum number of plugins to return

        Returns:
            List of trending plugins
        """
        logger.debug("Fetching trending plugins")
        data = self._request("GET", "/plugins/trending", params={"limit": limit})
        return [MarketplacePlugin.from_dict(p) for p in data.get("plugins", [])]

    def install(self, name: str) -> dict[str, Any]:
        """Get plugin installation info (download URL, checksum).

        Args:
            name: Plugin name to install

        Returns:
            Dict with download_url, checksum, version

        Raises:
            NotFoundError: If plugin not found

        Example:
            >>> info = client.install("mekong-plugin-seo")
            >>> print(f"Download from: {info['download_url']}")
        """
        logger.debug("Getting install info for: %s", name)
        return self._request("GET", f"/plugins/{name}/install")

    def get_categories(self) -> list[dict[str, Any]]:
        """Get list of plugin categories.

        Returns:
            List of categories with name, slug, count
        """
        logger.debug("Fetching categories")
        return self._request("GET", "/categories")

    def get_tags(self) -> list[str]:
        """Get list of all tags used in marketplace.

        Returns:
            List of tag strings
        """
        logger.debug("Fetching tags")
        data = self._request("GET", "/tags")
        return data.get("tags", [])

    def rate_plugin(self, name: str, rating: int, comment: str | None = None) -> dict[str, Any]:
        """Submit a rating for a plugin.

        Args:
            name: Plugin name
            rating: Rating 1-5
            comment: Optional review comment

        Returns:
            Confirmation dict

        Raises:
            MarketplaceError: If rating submission fails
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        logger.info("Submitting rating %s for plugin: %s", rating, name)
        return self._request(
            "POST",
            f"/plugins/{name}/rate",
            json={"rating": rating, "comment": comment},
        )

    def health_check(self) -> bool:
        """Check if marketplace API is accessible.

        Returns:
            True if marketplace is healthy, False otherwise
        """
        try:
            data = self._request("GET", "/health")
            return data.get("status") == "healthy"
        except MarketplaceError:
            return False

    @property
    def base_url(self) -> str:
        """Get marketplace base URL."""
        return self._base_url

    def close(self) -> None:
        """Close the client session."""
        self._client.close()

    def __enter__(self) -> MarketplaceClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


__all__ = [
    "DEFAULT_MARKETPLACE_URL",
    "MarketplaceClient",
    "MarketplaceError",
    "MarketplacePlugin",
    "NetworkError",
    "NotFoundError",
    "PluginSortBy",
    "SearchResult",
    "SortOrder",
]

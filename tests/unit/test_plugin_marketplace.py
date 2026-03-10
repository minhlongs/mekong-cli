"""Tests for MarketplaceClient - plugin marketplace discovery.

Coverage:
- Client initialization and configuration
- Search with filters, pagination, sorting
- Get plugin details
- Featured/trending endpoints
- Install info retrieval
- Categories and tags
- Rating submission
- Health check
- Error handling (NetworkError, NotFoundError, MarketplaceError)
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.plugin_marketplace import (
    DEFAULT_MARKETPLACE_URL,
    MarketplaceClient,
    MarketplaceError,
    MarketplacePlugin,
    NetworkError,
    NotFoundError,
    PluginSortBy,
    SortOrder,
)


class TestMarketplaceClientInit(unittest.TestCase):
    """Test client initialization."""

    def test_init_default_url(self):
        """Should use default marketplace URL."""
        client = MarketplaceClient()
        self.assertEqual(client.base_url, DEFAULT_MARKETPLACE_URL.rstrip("/"))

    def test_init_custom_url(self):
        """Should use custom URL with trailing slash stripped."""
        client = MarketplaceClient(base_url="https://custom.market.com/api/")
        self.assertEqual(client.base_url, "https://custom.market.com/api")

    def test_init_custom_timeout(self):
        """Should use custom timeout."""
        client = MarketplaceClient(timeout=60.0)
        self.assertEqual(client._timeout, 60.0)

    def test_init_with_api_key(self):
        """Should store API key for auth headers."""
        client = MarketplaceClient(api_key="test-key-123")
        self.assertEqual(client._api_key, "test-key-123")

    def test_build_headers_no_auth(self):
        """Should build headers without auth when no API key."""
        client = MarketplaceClient()
        headers = client._build_headers()
        self.assertEqual(headers["User-Agent"], "mekong-cli-marketplace/1.0")
        self.assertNotIn("Authorization", headers)

    def test_build_headers_with_auth(self):
        """Should include auth header when API key provided."""
        client = MarketplaceClient(api_key="secret-key")
        headers = client._build_headers()
        self.assertEqual(headers["Authorization"], "Bearer secret-key")


class TestMarketplaceSearch(unittest.TestCase):
    """Test search functionality."""

    @patch("httpx.Client.request")
    def test_search_basic(self, mock_request):
        """Should search with query string."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total": 25,
            "page": 1,
            "page_size": 20,
            "total_pages": 2,
            "plugins": [
                {
                    "name": "mekong-plugin-seo",
                    "version": "1.0.0",
                    "description": "SEO plugin",
                    "author": "Test Author",
                    "plugin_type": "agent",
                    "downloads": 1000,
                    "rating": 4.5,
                }
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        results = client.search("seo")

        self.assertEqual(results.total, 25)
        self.assertEqual(len(results.plugins), 1)
        plugin = results.plugins[0]
        self.assertEqual(plugin.name, "mekong-plugin-seo")
        self.assertEqual(plugin.rating, 4.5)

    @patch("httpx.Client.request")
    def test_search_with_filters(self, mock_request):
        """Should apply type and tag filters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total": 5,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
            "plugins": [],
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        client.search(query="analytics", plugin_type="provider", tags=["seo", "marketing"])

        # Verify params passed
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["q"], "analytics")
        self.assertEqual(params["type"], "provider")
        self.assertEqual(params["tags"], "seo,marketing")

    @patch("httpx.Client.request")
    def test_search_pagination(self, mock_request):
        """Should handle pagination params."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total": 150,
            "page": 3,
            "page_size": 50,
            "total_pages": 3,
            "plugins": [],
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        results = client.search(page=3, page_size=50)

        self.assertEqual(results.page, 3)
        self.assertEqual(results.page_size, 50)
        self.assertEqual(results.total_pages, 3)

    @patch("httpx.Client.request")
    def test_search_sorting(self, mock_request):
        """Should apply sort params."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"total": 0, "page": 1, "page_size": 20, "total_pages": 0, "plugins": []}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        client.search(sort_by=PluginSortBy.RATING, sort_order=SortOrder.ASC)

        call_args = mock_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["sort_by"], "rating")
        self.assertEqual(params["sort_order"], "asc")

    @patch("httpx.Client.request")
    def test_search_page_size_limit(self, mock_request):
        """Should cap page_size at 100."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"total": 0, "page": 1, "page_size": 100, "total_pages": 0, "plugins": []}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        client.search(page_size=500)

        call_args = mock_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["page_size"], 100)


class TestGetPlugin(unittest.TestCase):
    """Test get_plugin method."""

    @patch("httpx.Client.request")
    def test_get_plugin_success(self, mock_request):
        """Should fetch plugin details."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "mekong-plugin-seo",
            "version": "2.0.0",
            "description": "Advanced SEO tools",
            "author": "SEO Team",
            "plugin_type": "agent",
            "downloads": 5000,
            "rating": 4.8,
            "rating_count": 120,
            "tags": ["seo", "marketing"],
            "repository_url": "https://github.com/test/seo-plugin",
            "documentation_url": "https://docs.seo-plugin.com",
            "license": "MIT",
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        plugin = client.get_plugin("mekong-plugin-seo")

        self.assertEqual(plugin.name, "mekong-plugin-seo")
        self.assertEqual(plugin.version, "2.0.0")
        self.assertEqual(plugin.downloads, 5000)
        self.assertEqual(plugin.tags, ["seo", "marketing"])

    @patch("httpx.Client.request")
    def test_get_plugin_not_found(self, mock_request):
        """Should raise NotFoundError for missing plugin."""
        import httpx
        mock_request.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )

        client = MarketplaceClient()
        with self.assertRaises(NotFoundError):
            client.get_plugin("nonexistent-plugin")


class TestFeaturedAndTrending(unittest.TestCase):
    """Test featured and trending endpoints."""

    @patch("httpx.Client.request")
    def test_get_featured(self, mock_request):
        """Should fetch featured plugins."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "plugins": [
                {"name": "featured-1", "version": "1.0", "description": "Desc 1", "author": "A1", "plugin_type": "agent"},
                {"name": "featured-2", "version": "1.0", "description": "Desc 2", "author": "A2", "plugin_type": "agent"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        plugins = client.get_featured(limit=2)

        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins[0].name, "featured-1")

    @patch("httpx.Client.request")
    def test_get_trending(self, mock_request):
        """Should fetch trending plugins."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "plugins": [
                {"name": "trending-1", "version": "1.0", "description": "Desc 1", "author": "A1", "plugin_type": "agent"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        plugins = client.get_trending(limit=1)

        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0].name, "trending-1")


class TestInstall(unittest.TestCase):
    """Test install info retrieval."""

    @patch("httpx.Client.request")
    def test_get_install_info(self, mock_request):
        """Should get download URL and checksum."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "download_url": "https://cdn.mekong.dev/plugins/seo-plugin-1.0.0.tar.gz",
            "checksum": "sha256:abc123...",
            "version": "1.0.0",
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        info = client.install("mekong-plugin-seo")

        self.assertEqual(info["download_url"], "https://cdn.mekong.dev/plugins/seo-plugin-1.0.0.tar.gz")
        self.assertEqual(info["checksum"], "sha256:abc123...")


class TestCategoriesAndTags(unittest.TestCase):
    """Test categories and tags endpoints."""

    @patch("httpx.Client.request")
    def test_get_categories(self, mock_request):
        """Should fetch plugin categories."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"name": "SEO", "slug": "seo", "count": 15},
            {"name": "Analytics", "slug": "analytics", "count": 8},
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        categories = client.get_categories()

        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0]["name"], "SEO")

    @patch("httpx.Client.request")
    def test_get_tags(self, mock_request):
        """Should fetch all tags."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tags": ["seo", "marketing", "analytics", "social-media"]
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        tags = client.get_tags()

        self.assertEqual(len(tags), 4)
        self.assertIn("seo", tags)


class TestRatePlugin(unittest.TestCase):
    """Test plugin rating."""

    @patch("httpx.Client.request")
    def test_rate_plugin_success(self, mock_request):
        """Should submit rating."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "message": "Rating submitted"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        result = client.rate_plugin("mekong-plugin-seo", 5, comment="Excellent!")

        self.assertTrue(result["success"])
        mock_request.assert_called_with(
            "POST",
            "/plugins/mekong-plugin-seo/rate",
            json={"rating": 5, "comment": "Excellent!"},
        )

    def test_rate_plugin_invalid_rating(self):
        """Should reject invalid ratings."""
        client = MarketplaceClient()
        with self.assertRaises(ValueError):
            client.rate_plugin("plugin", 0)  # Rating must be 1-5
        with self.assertRaises(ValueError):
            client.rate_plugin("plugin", 6)  # Rating must be 1-5


class TestHealthCheck(unittest.TestCase):
    """Test health check endpoint."""

    @patch("httpx.Client.request")
    def test_health_check_healthy(self, mock_request):
        """Should return True when healthy."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        client = MarketplaceClient()
        result = client.health_check()

        self.assertTrue(result)

    @patch("httpx.Client.request")
    def test_health_check_unhealthy(self, mock_request):
        """Should return False when unhealthy."""
        import httpx
        mock_request.side_effect = httpx.ConnectError("Connection refused")

        client = MarketplaceClient()
        result = client.health_check()

        self.assertFalse(result)


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""

    @patch("httpx.Client.request")
    def test_network_error_connect(self, mock_request):
        """Should raise NetworkError on connection failure."""
        import httpx
        mock_request.side_effect = httpx.ConnectError("Connection refused")

        client = MarketplaceClient()
        with self.assertRaises(NetworkError):
            client.search("test")

    @patch("httpx.Client.request")
    def test_network_error_timeout(self, mock_request):
        """Should raise NetworkError on timeout."""
        import httpx
        mock_request.side_effect = httpx.TimeoutException("Request timed out")

        client = MarketplaceClient()
        with self.assertRaises(NetworkError):
            client.search("test")

    @patch("httpx.Client.request")
    def test_marketplace_error_500(self, mock_request):
        """Should raise MarketplaceError on server error."""
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_request.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        client = MarketplaceClient()
        with self.assertRaises(MarketplaceError) as context:
            client.search("test")

        self.assertEqual(context.exception.status_code, 500)


class TestMarketplacePlugin(unittest.TestCase):
    """Test MarketplacePlugin dataclass."""

    def test_from_dict_minimal(self):
        """Should handle minimal dict with defaults."""
        data = {"name": "test-plugin", "version": "1.0.0"}
        plugin = MarketplacePlugin.from_dict(data)

        self.assertEqual(plugin.name, "test-plugin")
        self.assertEqual(plugin.version, "1.0.0")
        self.assertEqual(plugin.description, "")
        self.assertEqual(plugin.downloads, 0)
        self.assertEqual(plugin.rating, 0.0)
        self.assertEqual(plugin.tags, [])

    def test_from_dict_full(self):
        """Should parse full plugin data."""
        data = {
            "name": "full-plugin",
            "version": "2.0.0",
            "description": "Complete plugin",
            "author": "Dev Team",
            "plugin_type": "agent",
            "downloads": 10000,
            "rating": 4.9,
            "rating_count": 500,
            "tags": ["tag1", "tag2"],
            "repository_url": "https://github.com/test/plugin",
            "documentation_url": "https://docs.plugin.com",
            "license": "Apache-2.0",
            "min_mekong_version": "0.2.0",
            "dependencies": ["requests", "httpx"],
        }
        plugin = MarketplacePlugin.from_dict(data)

        self.assertEqual(plugin.downloads, 10000)
        self.assertEqual(plugin.rating_count, 500)
        self.assertEqual(plugin.dependencies, ["requests", "httpx"])

    def test_to_dict(self):
        """Should serialize to dict."""
        plugin = MarketplacePlugin(
            name="serialize-test",
            version="1.0.0",
            description="Test desc",
            author="Tester",
            plugin_type="provider",
        )
        data = plugin.to_dict()

        self.assertEqual(data["name"], "serialize-test")
        self.assertEqual(data["plugin_type"], "provider")
        self.assertEqual(data["tags"], [])


class TestContextManager(unittest.TestCase):
    """Test context manager support."""

    @patch("httpx.Client")
    def test_context_manager(self, mock_client_cls):
        """Should close client on exit."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        with MarketplaceClient():
            pass

        mock_client.close.assert_called_once()

    @patch("httpx.Client")
    def test_close_method(self, mock_client_cls):
        """Should close client explicitly."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        client = MarketplaceClient()
        client.close()

        mock_client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()

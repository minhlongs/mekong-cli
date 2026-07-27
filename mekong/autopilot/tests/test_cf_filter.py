"""Unit tests for mekong.orchestrator IdeaLoop with cf_filter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mekong.autopilot import IdeaLoop, RunOptions, RunResult
from mekong.autopilot.tools import write_file, edit_file


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create a temporary repo structure for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "package.json").write_text('{"name": "test"}')
    (repo / "wrangler.toml").write_text("[workerd]")
    return repo


def test_run_options_cf_filter_default() -> None:
    """Test cf_filter defaults to False."""
    opts = RunOptions(idea="test")
    assert opts.cf_filter is False


def test_run_options_cf_filter_enabled() -> None:
    """Test cf_filter can be set to True."""
    opts = RunOptions(idea="test", cf_filter=True)
    assert opts.cf_filter is True


def test_ideal_loop_cf_filter_system_prompt(temp_repo: Path) -> None:
    """Test that cf_filter=True uses Cloudflare system prompt."""
    opts = RunOptions(idea="create a Cloudflare worker", cf_filter=True, max_iter=1, dry_run=True)

    with patch.object(IdeaLoop, '_llm') as mock_llm:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "<tool>DONE test</tool>"
        mock_client.chat.return_value = mock_response
        mock_llm.return_value = mock_client

        with patch('mekong.autopilot.idea_loop.REPO_ROOT', temp_repo):
            loop = IdeaLoop(opts)
            loop._bootstrap_context()

            # Check that the first system message contains Cloudflare-specific content
            messages = loop.ctx.messages()
            system_msg = next(m for m in messages if m["role"] == "system")

            assert "Cloudflare" in system_msg["content"] or "cloudflare" in system_msg["content"]
            assert "Workers" in system_msg["content"] or "workers" in system_msg["content"]
            assert "wrangler" in system_msg["content"].lower()


def test_ideal_loop_non_cf_uses_default_prompt(temp_repo: Path) -> None:
    """Test that cf_filter=False uses default system prompt."""
    opts = RunOptions(idea="build a feature", cf_filter=False, max_iter=1, dry_run=True)

    with patch.object(IdeaLoop, '_llm') as mock_llm:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "<tool>DONE test</tool>"
        mock_client.chat.return_value = mock_response
        mock_llm.return_value = mock_client

        with patch('mekong.autopilot.idea_loop.REPO_ROOT', temp_repo):
            loop = IdeaLoop(opts)
            loop._bootstrap_context()

            messages = loop.ctx.messages()
            system_msg = next(m for m in messages if m["role"] == "system")

            # Default prompt should NOT have Cloudflare-specific content
            assert "Cloudflare specialist" not in system_msg["content"]
            assert "autonomous senior engineer" in system_msg["content"]


def test_cf_filter_file_boundary_write(temp_repo: Path) -> None:
    """Test that cf_filter blocks non-Cloudflare file writes (using package.json as test)."""
    opts = RunOptions(idea="test", cf_filter=True, dry_run=False)

    with patch('mekong.autopilot.idea_loop.REPO_ROOT', temp_repo):
        loop = IdeaLoop(opts)

        # Write to package.json (root file, not in public boundary) should be checked by cf_filter
        result = write_file(temp_repo, "package.json", '{"name": "cloudflare-test"}', cf_filter=True)
        # package.json không phải Cloudflare-specific nên bị reject
        assert result.ok is False
        assert "CF-FILTER" in result.output or "Cloudflare-related" in result.output

        # Write to wrangler.toml should be allowed
        result = write_file(temp_repo, "wrangler.toml", "name = 'worker'", cf_filter=True)
        assert result.ok is True

        # Write to workers/ directory should be allowed
        result = write_file(temp_repo, "workers/my-worker/index.ts", "export default {}", cf_filter=True)
        assert result.ok is True

        # Write to cloudflare/ directory should be allowed
        result = write_file(temp_repo, "cloudflare/config.json", "{}", cf_filter=True)
        assert result.ok is True


def test_cf_filter_file_boundary_edit(temp_repo: Path) -> None:
    """Test that cf_filter blocks non-Cloudflare file edits."""
    opts = RunOptions(idea="test", cf_filter=True, dry_run=False)

    with patch('mekong.autopilot.idea_loop.REPO_ROOT', temp_repo):
        loop = IdeaLoop(opts)

        # Edit package.json (non-CF) should be rejected
        (temp_repo / "package.json").write_text('{"old": "value"}')
        result = edit_file(temp_repo, "package.json", "<old>old</old><new>new</new>", cf_filter=True)
        assert result.ok is False
        assert "CF-FILTER" in result.output or "Cloudflare-related" in result.output

        # Edit wrangler.toml should be allowed
        (temp_repo / "wrangler.toml").write_text("name = 'old'")
        result = edit_file(temp_repo, "wrangler.toml", "<old>name = 'old'</old><new>name = 'new'</new>", cf_filter=True)
        assert result.ok is True


def test_no_cf_filter_allows_root_files(temp_repo: Path) -> None:
    """Test that cf_filter=False allows root files."""
    # package.json ở root không bị public boundary block
    result = write_file(temp_repo, "package.json", '{"test": true}', cf_filter=False)
    assert result.ok is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

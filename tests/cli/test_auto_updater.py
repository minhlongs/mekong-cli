"""
Tests for CLI Auto Updater

Tests the auto updater functionality including:
- Version detection
- Download and verify
- Config preservation
- Rollback support
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


from src.cli.auto_updater import (
    AutoUpdater,
    ReleaseInfo,
    UpdateResult,
    GitHubReleaseFetcher,
    ChecksumVerifier,
    ConfigPreserver,
    get_updater,
)


class TestReleaseInfo:
    """Test ReleaseInfo dataclass."""

    def test_release_info_creation(self):
        """Should create ReleaseInfo correctly."""
        release = ReleaseInfo(
            version="0.3.0",
            tag_name="v0.3.0",
            name="Release 0.3.0",
            body="Bug fixes",
            published_at="2026-03-09T12:00:00Z",
            download_url="https://example.com/download.tar.gz",
            checksum_url="https://example.com/checksum.txt",
            signature_url="https://example.com/signature.sig",
            is_security_update=True,
        )
        assert release.version == "0.3.0"
        assert release.is_security_update is True


class TestUpdateResult:
    """Test UpdateResult dataclass."""

    def test_update_result_success(self):
        """Should create success UpdateResult."""
        result = UpdateResult(
            success=True,
            old_version="0.2.0",
            new_version="0.3.0",
            message="Updated successfully",
            config_preserved=True,
            rollback_available=True,
        )
        assert result.success is True
        assert result.config_preserved is True
        assert result.rollback_available is True

    def test_update_result_failure(self):
        """Should create failure UpdateResult."""
        result = UpdateResult(
            success=False,
            old_version="0.2.0",
            new_version="0.2.0",
            message="Update failed",
            config_preserved=True,
            rollback_available=False,
        )
        assert result.success is False


class TestGitHubReleaseFetcher:
    """Test GitHub release fetcher."""

    def test_get_current_version(self):
        """Should return current version."""
        updater = AutoUpdater()
        version = updater.get_current_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_latest_release_mock(self):
        """Should fetch latest release from GitHub."""
        fetcher = GitHubReleaseFetcher()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tag_name": "v0.3.0",
            "name": "Release 0.3.0",
            "body": "Bug fixes and improvements",
            "published_at": "2026-03-09T12:00:00Z",
            "assets": [
                {
                    "name": "mekong-cli-v0.3.0-darwin-arm64.tar.gz",
                    "browser_download_url": "https://example.com/download.tar.gz",
                }
            ],
        }

        with patch.object(fetcher.session, 'get', return_value=mock_response):
            release = fetcher.get_latest_release()
            assert release.version == "0.3.0"
            assert release.name == "Release 0.3.0"


class TestChecksumVerifier:
    """Test checksum verification."""

    def test_compute_sha256(self):
        """Should compute SHA256 hash correctly."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum = ChecksumVerifier.compute_sha256(temp_path)
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA256 is 64 hex chars
        finally:
            os.unlink(temp_path)

    def test_verify_checksum(self):
        """Should verify file against checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum = ChecksumVerifier.compute_sha256(temp_path)
            assert ChecksumVerifier.verify(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)

    def test_verify_invalid_checksum(self):
        """Should return False for invalid checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            wrong_checksum = "a" * 64
            assert ChecksumVerifier.verify(temp_path, wrong_checksum) is False
        finally:
            os.unlink(temp_path)


class TestConfigPreserver:
    """Test configuration preservation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.preserver = ConfigPreserver()
        self.preserver.CONFIG_DIR = Path(self.temp_dir.name)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_backup_creates_copy(self):
        """Should create backup of config files."""
        # Create test config file
        config_file = self.preserver.CONFIG_DIR / "config.ini"
        config_file.write_text("[test]\nkey=value\n")

        self.preserver.backup()

        # Verify backup was created
        assert self.preserver.backup_dir is not None

    def test_backup_empty_dir(self):
        """Should handle empty config directory."""
        backup_dir = self.preserver.backup()
        assert backup_dir.exists()

    def test_restore_from_backup(self):
        """Should restore config from backup."""
        # Create test config file
        config_file = self.preserver.CONFIG_DIR / "config.ini"
        config_file.write_text("[test]\nkey=value\n")

        self.preserver.backup()

        # Remove original
        config_file.unlink()
        assert not config_file.exists()

        # Restore
        result = self.preserver.restore()
        assert result is True
        assert config_file.exists()

    def test_cleanup_removes_backup(self):
        """Should remove backup directory on cleanup."""
        self.preserver.backup()
        backup_dir = self.preserver.backup_dir
        assert backup_dir is not None

        self.preserver.cleanup()
        assert not backup_dir.exists()


class TestAutoUpdater:
    """Test main AutoUpdater class."""

    def test_get_updater_singleton(self):
        """Should return AutoUpdater instance."""
        updater = get_updater()
        assert isinstance(updater, AutoUpdater)

    def test_get_current_version(self):
        """Should return current version string."""
        updater = AutoUpdater()
        version = updater.get_current_version()
        assert isinstance(version, str)

    def test_check_for_updates_no_updates(self):
        """Should return None when no updates available."""
        updater = AutoUpdater()

        with patch.object(updater.fetcher, 'get_latest_release') as mock_get:
            mock_get.return_value = None
            result = updater.check_for_updates()
            assert result is None

    def test_rollback_no_history(self):
        """Should return False when no update history exists."""
        updater = AutoUpdater()

        with patch('pathlib.Path.exists', return_value=False):
            result = updater.rollback()
            assert result is False

    def test_save_update_history(self):
        """Should save update history for rollback."""
        updater = AutoUpdater()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                updater._save_update_history("0.2.0", "0.3.0")

                history_path = Path(temp_dir) / ".mekong" / "update_history.json"
                assert history_path.exists()


class TestAutoUpdaterUpdateFlow:
    """Test update flow with mocks."""

    def test_update_force_reinstall(self):
        """Should reinstall current version with force flag."""
        updater = AutoUpdater()

        with patch.object(updater.fetcher, 'get_latest_release') as mock_get:
            mock_get.return_value = ReleaseInfo(
                version="0.2.0",
                tag_name="v0.2.0",
                name="Release 0.2.0",
                body="",
                published_at="2026-03-09T12:00:00Z",
                download_url="https://example.com/download.tar.gz",
                checksum_url="",
                signature_url="",
            )

            with patch.object(updater.preserver, 'backup'):
                with patch.object(updater, '_save_update_history'):
                    with patch('src.cli.auto_updater.SandboxedUpdater') as MockUpdater:
                        mock_instance = Mock()
                        MockUpdater.return_value = mock_instance

                        result = updater.update(force=True)
                        assert result.success is True

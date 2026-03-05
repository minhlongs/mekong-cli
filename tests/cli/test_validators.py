"""Tests for CLI validators module."""

import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from src.cli.validators import (
    validate_port,
    validate_host,
    validate_api_token,
    validate_file_exists,
    validate_directory_exists,
    validate_recipe_file,
    validate_complexity,
    validate_percentage,
    create_env_validator,
)


class TestValidatePort:
    """Test validate_port function."""

    def test_valid_port(self):
        """Test valid port numbers."""
        assert validate_port(80) == 80
        assert validate_port(443) == 443
        assert validate_port(8080) == 8080
        assert validate_port(1) == 1
        assert validate_port(65535) == 65535

    def test_port_too_low(self):
        """Test port number below valid range."""
        with pytest.raises(ValueError, match="Port must be 1-65535"):
            validate_port(0)
            validate_port(-1)

    def test_port_too_high(self):
        """Test port number above valid range."""
        with pytest.raises(ValueError, match="Port must be 1-65535"):
            validate_port(65536)
            validate_port(99999)


class TestValidateHost:
    """Test validate_host function."""

    def test_valid_ip_addresses(self):
        """Test valid IP addresses."""
        assert validate_host("127.0.0.1") == "127.0.0.1"
        assert validate_host("0.0.0.0") == "0.0.0.0"
        assert validate_host("192.168.1.1") == "192.168.1.1"

    def test_localhost_variations(self):
        """Test localhost variations."""
        assert validate_host("localhost") == "localhost"

    def test_invalid_host(self):
        """Test invalid host addresses."""
        with pytest.raises(ValueError, match="Invalid host address"):
            validate_host("invalid.host")
            validate_host("256.256.256.256")
            validate_host("192.168.1")


class TestValidateApiToken:
    """Test validate_api_token function."""

    def test_valid_token(self):
        """Test valid API token."""
        token = "test-token-123"
        assert validate_api_token(token) == token

    def test_empty_token(self):
        """Test empty API token."""
        with pytest.raises(ValueError, match="API token required"):
            validate_api_token("")
            validate_api_token(None)


class TestValidateFileExists:
    """Test validate_file_exists function."""

    def test_file_exists(self):
        """Test file that exists."""
        with NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        try:
            result = validate_file_exists(temp_path)
            assert isinstance(result, Path)
            assert result.exists()
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            validate_file_exists("/nonexistent/file.txt")


class TestValidateDirectoryExists:
    """Test validate_directory_exists function."""

    def test_directory_exists(self):
        """Test directory that exists."""
        with TemporaryDirectory() as temp_dir:
            result = validate_directory_exists(temp_dir)
            assert isinstance(result, Path)
            assert result.is_dir()

    def test_file_instead_of_directory(self):
        """Test file when directory expected."""
        with NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        try:
            with pytest.raises(NotADirectoryError, match="Directory not found"):
                validate_directory_exists(temp_path)
        finally:
            os.unlink(temp_path)

    def test_directory_not_found(self):
        """Test non-existent directory."""
        with pytest.raises(NotADirectoryError, match="Directory not found"):
            validate_directory_exists("/nonexistent/directory")


class TestValidateRecipeFile:
    """Test validate_recipe_file function."""

    def test_valid_recipe_file(self):
        """Test valid .md recipe file."""
        with NamedTemporaryFile(suffix=".md", delete=False) as f:
            temp_path = f.name
        try:
            result = validate_recipe_file(temp_path)
            assert isinstance(result, Path)
            assert result.suffix == ".md"
        finally:
            os.unlink(temp_path)

    def test_wrong_extension(self):
        """Test file with wrong extension."""
        with NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name
        try:
            with pytest.raises(ValueError, match="must have .md extension"):
                validate_recipe_file(temp_path)
        finally:
            os.unlink(temp_path)


class TestValidateComplexity:
    """Test validate_complexity function."""

    def test_valid_complexity_levels(self):
        """Test valid complexity levels."""
        assert validate_complexity("simple") == "simple"
        assert validate_complexity("moderate") == "moderate"
        assert validate_complexity("complex") == "complex"
        assert validate_complexity("SIMPLE") == "simple"
        assert validate_complexity("MODERATE") == "moderate"

    def test_invalid_complexity(self):
        """Test invalid complexity level."""
        with pytest.raises(ValueError, match="Complexity must be"):
            validate_complexity("invalid")
            validate_complexity("easy")
            validate_complexity("hard")


class TestValidatePercentage:
    """Test validate_percentage function."""

    def test_valid_percentages(self):
        """Test valid percentage values."""
        assert validate_percentage(0) == 0
        assert validate_percentage(50) == 50
        assert validate_percentage(100) == 100
        assert validate_percentage(25.5) == 25.5
        assert validate_percentage(75.25) == 75.25

    def test_percentage_below_zero(self):
        """Test percentage below 0."""
        with pytest.raises(ValueError, match="Percentage must be 0-100"):
            validate_percentage(-1)
            validate_percentage(-50)

    def test_percentage_above_hundred(self):
        """Test percentage above 100."""
        with pytest.raises(ValueError, match="Percentage must be 0-100"):
            validate_percentage(101)
            validate_percentage(200)


class TestCreateEnvValidator:
    """Test create_env_validator function."""

    def test_required_env_set(self, monkeypatch):
        """Test required env variable when set."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        validator = create_env_validator("TEST_VAR", required=True)
        assert validator() == "test_value"

    def test_required_env_not_set(self, monkeypatch):
        """Test required env variable when not set."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        validator = create_env_validator("TEST_VAR", required=True)
        with pytest.raises(ValueError, match="TEST_VAR required"):
            validator()

    def test_optional_env_not_set(self, monkeypatch):
        """Test optional env variable when not set."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        validator = create_env_validator("TEST_VAR", required=False)
        assert validator() is None

    def test_prebuilt_validators_exist(self, monkeypatch):
        """Test pre-built validators are created."""
        monkeypatch.setenv("MEKONG_API_TOKEN", "test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
        monkeypatch.setenv("OPENAI_API_KEY", "test")
        from src.cli.validators import (
            require_api_token,
            require_llm_url,
            require_anthropic_key,
            require_openai_key,
        )
        assert callable(require_api_token)
        assert callable(require_llm_url)
        assert callable(require_anthropic_key)
        assert callable(require_openai_key)

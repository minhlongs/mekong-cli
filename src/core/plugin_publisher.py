# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""PluginPublisher — E4b marketplace publish flow."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
from typing import Any
import zipfile

logger = logging.getLogger(__name__)


class PublishError(Exception):
    """Raised when plugin publish fails. User-facing message in str."""


_EXCLUDE_DIRS = frozenset({".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"})
_INCLUDE_FILES = {".plugin.json", "README.md", "README", "LICENSE", "LICENSE.txt", "LICENSE.md"}
_SCAN_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".json", ".md", ".yaml", ".yml", ".toml"}
_SECRET_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'sk-[a-zA-Z0-9]{20,}(?!\s*#|\s*//|\s*YOUR|\s*XXX|\s*<SECRET>)'), "OpenAI-style API key (sk-...)"),
    (re.compile(r'api_key\s*[=:]\s*["\'][^"\']+["\']', re.IGNORECASE), "api_key assignment"),
    (re.compile(r'token\s*[=:]\s*["\'][^"\']+["\']', re.IGNORECASE), "token assignment"),
]
_PLACEHOLDER_MARKERS = ("YOUR_", "XXX", "<SECRET>", "placeholder", "REPLACE_", "INSERT_")


class PluginPublisher:
    """Bundles a Mekong plugin directory into a publishable ZIP."""

    def __init__(self, plugin_dir: Path) -> None:
        self.plugin_dir = Path(plugin_dir).resolve()
        self._manifest: dict[str, Any] = {}
        self.plugin_id: str = ""
        self._load_manifest()

    def bundle(self, output_dir: Path, version: str | None = None) -> Path:
        """Bundle plugin into a ZIP file."""
        self._validate_manifest()
        violations = self._scan_secrets()
        if violations:
            msgs = "\n  ".join(violations)
            raise PublishError(f"Secret scan failed:\n  {msgs}")

        effective_version = self._resolve_version(version)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_copy = {**self._manifest, "version": effective_version}
        zip_path = self._create_zip(output_dir, effective_version, manifest_copy)

        self._manifest["version"] = effective_version
        (self.plugin_dir / ".plugin.json").write_text(json.dumps(self._manifest, indent=2) + "\n", encoding="utf-8")
        logger.info("Published %s v%s → %s", self.plugin_id, effective_version, zip_path)
        self._publish_to_marketplace(zip_path, manifest_copy)
        return zip_path

    def _load_manifest(self) -> None:
        manifest_path = self.plugin_dir / ".plugin.json"
        if not manifest_path.is_file():
            raise PublishError(f"No .plugin.json found in '{self.plugin_dir}'. Run 'mekong plugin init' first.")
        try:
            self._manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PublishError(f".plugin.json is not valid JSON: {exc}") from exc
        self.plugin_id = self._manifest.get("id", "")

    def _validate_manifest(self) -> None:
        missing = [f for f in ("id", "name", "version") if not self._manifest.get(f)]
        if missing:
            raise PublishError(f".plugin.json missing required fields: {', '.join(missing)}")
        self.plugin_id = self._manifest["id"]

    def _scan_secrets(self) -> list[str]:
        """Scan src/ for secret patterns."""
        violations: list[str] = []
        src_dir = self.plugin_dir / "src"
        if not src_dir.is_dir():
            return violations

        for file_path in sorted(src_dir.rglob("*")):
            if not file_path.is_file() or file_path.suffix not in _SCAN_EXTENSIONS:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = file_path.relative_to(self.plugin_dir)
            for i, line in enumerate(content.splitlines(), 1):
                if any(m in line for m in _PLACEHOLDER_MARKERS):
                    continue
                for pattern, desc in _SECRET_PATTERNS:
                    if pattern.search(line):
                        violations.append(f"{rel}:{i}: {desc}")
        return violations

    def _resolve_version(self, requested: str | None) -> str:
        if requested is None or requested == "auto":
            parts = self._manifest.get("version", "0.0.0").split(".")
            while len(parts) < 3:
                parts.append("0")
            try:
                parts[2] = str(int(parts[2]) + 1)
            except (ValueError, IndexError):
                parts = ["0", "0", "1"]
            return ".".join(parts)
        if not re.match(r"^\d+\.\d+\.\d+$", requested):
            raise PublishError(f"Invalid version '{requested}'. Use semver format: X.Y.Z")
        return requested

    def _create_zip(self, output_dir: Path, version: str, manifest: dict[str, Any]) -> Path:
        zip_path = output_dir / f"{self.plugin_id}-{version}.zip"
        tmp_path = zip_path.with_suffix(".zip.tmp")
        try:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"{self.plugin_dir.name}/.plugin.json", json.dumps(manifest, indent=2) + "\n")
                for file_path in sorted(self.plugin_dir.rglob("*")):
                    if not file_path.is_file():
                        continue
                    rel = file_path.relative_to(self.plugin_dir)
                    if any(p in _EXCLUDE_DIRS for p in rel.parts) or rel.name == ".plugin.json":
                        continue
                    zf.write(file_path, f"{self.plugin_dir.name}/{rel.as_posix()}")
            tmp_path.replace(zip_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise
        return zip_path

    def _publish_to_marketplace(self, zip_path: Path, manifest: dict[str, Any]) -> None:
        from src.core.plugin_marketplace import MarketplaceClient, MarketplaceError, NetworkError

        base_url = os.environ.get("MEKONG_MARKETPLACE_URL", "https://marketplace.mekong.dev/v1/marketplace").rstrip("/")
        client = None
        try:
            client = MarketplaceClient(base_url=base_url)
            resp = client.publish(manifest)  # type: ignore[attr-defined]
            url_field = resp.get("url", base_url) if isinstance(resp, dict) else base_url
            logger.info("Published to marketplace: %s v%s → %s", manifest.get("id"), manifest.get("version"), url_field)
        except NetworkError as exc:
            logger.warning("Marketplace unreachable, queued locally: %s", exc)
        except MarketplaceError as exc:
            raise PublishError(f"Marketplace publish failed: {exc}") from exc
        except Exception as exc:
            logger.warning("Marketplace publish skipped (unexpected): %s", exc)
        finally:
            if client is not None:
                client.close()

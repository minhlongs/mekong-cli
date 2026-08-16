# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""PluginPublisher — E4b marketplace publish flow.

Bundles a Mekong plugin directory into a publishable ZIP with:
- Directory walking (excludes .git, __pycache__, .venv, node_modules)
- Secret scanning (blocks common API key / token patterns)
- Version bumping (override or auto-patch)
- ZIP creation with deterministic file ordering

MVP: saves ZIP locally to ~/.mekong/plugin-publish/
Future: POST to marketplace API when E3b is deployed.
"""
from __future__ import annotations

import json
import logging
import re
import zipfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PublishError(Exception):
    """Raised when plugin publish fails. User-facing message in str."""
    pass


# Directories to exclude from ZIP
_EXCLUDE_DIRS = frozenset({".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"})

# Files to include even without extension check
_INCLUDE_FILES = {".plugin.json", "README.md", "README", "LICENSE", "LICENSE.txt", "LICENSE.md"}

# Extensions to scan for secrets
_SCAN_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".json", ".md", ".yaml", ".yml", ".toml"}

# (regex pattern, description) — order matters: more-specific first
_SECRET_PATTERNS: list[tuple[re.Pattern, str]] = [
    # OpenAI-style keys: sk- followed by 20+ alphanumeric chars (not placeholder)
    (re.compile(r'sk-[a-zA-Z0-9]{20,}(?!\s*#|\s*//|\s*YOUR|\s*XXX|\s*<SECRET>)'),
     "OpenAI-style API key (sk-...)"),
    # api_key assignment with a value
    (re.compile(r'api_key\s*[=:]\s*["\'][^"\']+["\']', re.IGNORECASE),
     "api_key assignment"),
    # token assignment with a value
    (re.compile(r'token\s*[=:]\s*["\'][^"\']+["\']', re.IGNORECASE),
     "token assignment"),
]

# Strings that mark a value as a placeholder (safe to keep)
_PLACEHOLDER_MARKERS = ("YOUR_", "XXX", "<SECRET>", "placeholder", "REPLACE_", "INSERT_")


class PluginPublisher:
    """Bundles a Mekong plugin directory into a publishable ZIP."""

    def __init__(self, plugin_dir: Path) -> None:
        self.plugin_dir = Path(plugin_dir).resolve()
        self._manifest: dict[str, Any] = {}
        self.plugin_id: str = ""
        self._load_manifest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def bundle(self, output_dir: Path, version: str | None = None) -> Path:
        """Bundle plugin into a ZIP file.

        Steps: validate → scan secrets → bump version → create ZIP.
        Raises PublishError on any failure; no partial ZIP created.
        """
        self._validate_manifest()
        violations = self._scan_secrets()
        if violations:
            msgs = "\n  ".join(violations)
            raise PublishError(f"Secret scan failed:\n  {msgs}")

        effective_version = self._resolve_version(version)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build manifest copy with bumped version for ZIP
        manifest_copy = dict(self._manifest)
        manifest_copy["version"] = effective_version

        zip_path = self._create_zip(output_dir, effective_version, manifest_copy)

        # Update on-disk manifest so subsequent calls see the new version
        self._manifest["version"] = effective_version
        manifest_path = self.plugin_dir / ".plugin.json"
        manifest_path.write_text(json.dumps(self._manifest, indent=2) + "\n", encoding="utf-8")

        logger.info("Published %s v%s → %s", self.plugin_id, effective_version, zip_path)
        self._publish_to_marketplace(zip_path, manifest_copy)
        return zip_path

    # ------------------------------------------------------------------
    # Manifest
    # ------------------------------------------------------------------

    def _load_manifest(self) -> None:
        manifest_path = self.plugin_dir / ".plugin.json"
        if not manifest_path.is_file():
            raise PublishError(
                f"No .plugin.json found in '{self.plugin_dir}'. "
                "Run 'mekong plugin init' first."
            )
        try:
            self._manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PublishError(f".plugin.json is not valid JSON: {exc}") from exc
        self.plugin_id = self._manifest.get("id", "")

    def _validate_manifest(self) -> None:
        missing = [f for f in ("id", "name", "version") if not self._manifest.get(f)]
        if missing:
            raise PublishError(
                f".plugin.json missing required fields: {', '.join(missing)}"
            )
        self.plugin_id = self._manifest["id"]

    # ------------------------------------------------------------------
    # Secret scanning
    # ------------------------------------------------------------------

    def _scan_secrets(self) -> list[str]:
        """Scan src/ for secret patterns. Returns list of violation descriptions."""
        violations: list[str] = []
        src_dir = self.plugin_dir / "src"
        if not src_dir.is_dir():
            return violations

        for file_path in sorted(src_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix not in _SCAN_EXTENSIONS:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            rel = file_path.relative_to(self.plugin_dir)
            for i, line in enumerate(content.splitlines(), 1):
                # Fast skip: if line contains a placeholder marker, skip all checks on it
                if any(m in line for m in _PLACEHOLDER_MARKERS):
                    continue
                for pattern, desc in _SECRET_PATTERNS:
                    if pattern.search(line):
                        violations.append(f"{rel}:{i}: {desc}")
        return violations

    # ------------------------------------------------------------------
    # Version bumping
    # ------------------------------------------------------------------

    def _resolve_version(self, requested: str | None) -> str:
        """Return the effective version string based on requested mode."""
        if requested is None or requested == "auto":
            current = self._manifest.get("version", "0.0.0")
            parts = current.split(".")
            while len(parts) < 3:
                parts.append("0")
            try:
                parts[2] = str(int(parts[2]) + 1)
            except (ValueError, IndexError):
                parts = ["0", "0", "1"]
            return ".".join(parts)
        # Exact semver — validate
        if not re.match(r'^\d+\.\d+\.\d+$', requested):
            raise PublishError(
                f"Invalid version '{requested}'. Use semver format: X.Y.Z"
            )
        return requested

    # ------------------------------------------------------------------
    # ZIP creation
    # ------------------------------------------------------------------

    def _create_zip(
        self, output_dir: Path, version: str, manifest: dict[str, Any]
    ) -> Path:
        """Create the ZIP file. Returns path to the created ZIP."""
        zip_name = f"{self.plugin_id}-{version}.zip"
        zip_path = output_dir / zip_name

        # Write to a temp path first, then rename — atomic-ish
        tmp_path = zip_path.with_suffix(".zip.tmp")

        try:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Write updated manifest (bumped version replaces on-disk version)
                manifest_rel = f"{self.plugin_dir.name}/.plugin.json"
                zf.writestr(manifest_rel, json.dumps(manifest, indent=2) + "\n")

                # Walk source tree — skip .plugin.json (already written above)
                for file_path in sorted(self.plugin_dir.rglob("*")):
                    if not file_path.is_file():
                        continue
                    rel = file_path.relative_to(self.plugin_dir)
                    parts = rel.parts

                    # Skip excluded dirs
                    if any(p in _EXCLUDE_DIRS for p in parts):
                        continue

                    # Skip .plugin.json — already written above with bumped version
                    if rel.name == ".plugin.json":
                        continue

                    # Use directory name (not manifest id) as ZIP root folder
                    arcname = f"{self.plugin_dir.name}/{rel.as_posix()}"
                    zf.write(file_path, arcname)

            tmp_path.replace(zip_path)
        except Exception:
            # Clean up temp file on failure
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        return zip_path

    # ------------------------------------------------------------------
    # Marketplace (stub — E3b not deployed yet)
    # ------------------------------------------------------------------

    def _publish_to_marketplace(self, zip_path: Path, manifest: dict[str, Any]) -> None:
        """POST plugin metadata to marketplace API.

        The ZIP bundle is stored locally at *zip_path*. The marketplace
        endpoint receives **manifest JSON only** (the Worker stores metadata;
        ZIP storage on R2 can be added later).

        Configure the marketplace URL via ``MEKONG_MARKETPLACE_URL`` env var
        (must point to the Worker's *base* path, e.g.
        ``https://marketplace.mekong.dev/v1/marketplace``).

        On failure, raises :class:`PublishError` so :meth:`bundle` reports
        it to the user without a partial state.
        """
        import os

        from src.core.plugin_marketplace import MarketplaceClient, MarketplaceError, NetworkError

        base_url = os.environ.get(
            "MEKONG_MARKETPLACE_URL",
            "https://marketplace.mekong.dev/v1/marketplace",
        ).rstrip("/")

        client = None
        try:
            client = MarketplaceClient(base_url=base_url)
            resp = client.publish(manifest)  # type: ignore[attr-defined]
            url_field = resp.get("url", base_url) if isinstance(resp, dict) else base_url
            logger.info(
                "Published to marketplace: %s v%s → %s",
                manifest.get("id"),
                manifest.get("version"),
                url_field,
            )
        except NetworkError as exc:
            logger.warning("Marketplace unreachable, queued locally: %s", exc)
        except MarketplaceError as exc:
            raise PublishError(f"Marketplace publish failed: {exc}") from exc
        except Exception as exc:
            logger.warning("Marketplace publish skipped (unexpected): %s", exc)
        finally:
            if client is not None:
                client.close()

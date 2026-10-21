# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin registry record and loader implementation."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ManifestError, PluginLoadError, PluginNotFoundError
from .types import Manifest, PluginId

logger = logging.getLogger(__name__)

REQUIRED_MANIFEST_KEYS = ("id", "name", "version", "entry_point")


@dataclass
class PluginRecord:
    """A fully loaded flavour of ``Manifest`` carrying the live module + state."""

    manifest: Manifest
    module: Optional[Any] = None
    loaded_at: float = field(default_factory=lambda: __import__("time").time())
    error: Optional[str] = None
    checksum: str = ""

    def is_loaded(self) -> bool:
        return self.module is not None and self.error is None

    def as_dict(self) -> Dict[str, Any]:
        data = asdict(self.manifest)
        data.update({"loaded_at": self.loaded_at, "error": self.error, "checksum": self.checksum})
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> PluginRecord:
        manifest = Manifest.from_dict({k: v for k, v in data.items() if k in Manifest.__dataclass_fields__})
        return PluginRecord(
            manifest=manifest, module=None, loaded_at=float(data.get("loaded_at", 0.0)),
            error=data.get("error"), checksum=data.get("checksum", ""),
        )


class PluginLoaderMixin:
    """Mixin for reading manifests and importing plugin modules."""

    _dirs: list[Path]

    def _read_manifest(self, path: Path) -> Manifest:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ManifestError(f"Failed to read manifest at {path}: {exc}") from exc
        missing = [k for k in REQUIRED_MANIFEST_KEYS if k not in raw]
        if missing:
            raise ManifestError(f"Manifest at {path} missing required keys: {', '.join(missing)}")
        try:
            return Manifest.from_dict(raw)
        except Exception as exc:
            raise ManifestError(f"Invalid manifest at {path}: {exc}") from exc

    def _resolve_manifest(self, pid: PluginId) -> Manifest:
        for directory in self._dirs:
            manifest_path = Path(directory) / pid / ".mekong-plugin.json"
            if manifest_path.exists():
                try:
                    return self._read_manifest(manifest_path)
                except Exception:
                    continue
        raise PluginNotFoundError(f"Cannot locate manifest for plugin '{pid}' in plugin dirs: {self._dirs}")

    def _import_plugin(self, pid: PluginId, manifest: Manifest, entry_point: str) -> Any:
        import importlib
        import sys

        root_dir = None
        for directory in self._dirs:
            candidate = Path(directory) / pid
            if candidate.exists():
                root_dir = candidate
                break
        if root_dir is None:
            raise PluginNotFoundError(f"No plugin directory for '{pid}'")

        target_dir = root_dir / Path(entry_point).parent if entry_point and "/" in entry_point else root_dir
        target_dir_str = str(target_dir)
        already_on_path = target_dir_str in sys.path
        if not already_on_path:
            sys.path.insert(0, target_dir_str)

        module_name = entry_point.split(".")[0] if entry_point else "__init__"
        try:
            mod = importlib.import_module(module_name)
            if "." in entry_point:
                obj = mod
                for attr in entry_point.split(".")[1:]:
                    obj = getattr(obj, attr)
                return obj
            return mod
        except Exception as exc:
            raise PluginLoadError(f"Failed to import plugin '{pid}' entry_point='{entry_point}': {exc}") from exc
        finally:
            if not already_on_path:
                try:
                    sys.path.remove(target_dir_str)
                except ValueError:
                    pass

    def _plugin_checksum(self, manifest: Manifest, module: Any) -> str:
        try:
            source = getattr(module, "__file__", None)
            if not source:
                return ""
            content = Path(source).read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        except Exception:
            return ""

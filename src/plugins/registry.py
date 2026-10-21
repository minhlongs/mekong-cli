# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin registry."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple, Union

from .exceptions import PluginError, PluginNotFoundError
from .registry_loader import PluginLoaderMixin, PluginRecord
from .types import Manifest, PluginId, Result

logger = logging.getLogger(__name__)

DEFAULT_PLUGIN_DIRS: Tuple[Path, ...] = (
    Path(os.environ.get("MEKONG_PLUGIN_DIR", "")) if os.environ.get("MEKONG_PLUGIN_DIR") else (),
    Path.home() / ".mekong" / "plugins",
    Path(__file__).resolve().parent.parent / "plugins",
    Path(".claude") / "plugins",
)

DEFAULT_REGISTRY_PATH = Path.home() / ".mekong" / "plugin-registry.json"
PLUGIN_MANIFEST_FILE = ".mekong-plugin.json"
REQUIRED_MANIFEST_KEYS = ("id", "name", "version", "entry_point")


class PluginRegistry(PluginLoaderMixin):
    """Central plugin book-keeper."""

    def __init__(
        self,
        plugin_dirs: Optional[List[Union[str, Path]]] = None,
        registry_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._dirs = [Path(d) for d in (plugin_dirs or list(DEFAULT_PLUGIN_DIRS)) if d]
        self._path = Path(registry_path or DEFAULT_REGISTRY_PATH)
        self._records: Dict[PluginId, PluginRecord] = {}
        self._loaded_ids: Set[PluginId] = set()
        self.restore()

    def persist(self) -> None:
        """Write the current registry to disk (atomic rename)."""
        try:
            payload = {pid: rec.as_dict() for pid, rec in self._records.items()}
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_fd, tmp_name = tempfile.mkstemp(dir=str(self._path.parent), suffix=".tmp.json")
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2, default=str)
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(tmp_name, str(self._path))
            except Exception:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
                raise
        except Exception as exc:
            logger.debug("Registry persist skipped: %s", exc)

    def restore(self) -> None:
        """Restore registry from disk, if present and well-formed."""
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            for pid, blob in raw.items():
                try:
                    pid_obj = PluginId(pid)
                    self._records[pid_obj] = PluginRecord.from_dict(blob)
                    self._loaded_ids.add(pid_obj)
                except Exception as exc:
                    logger.debug("Skipping corrupted registry entry %s: %s", pid, exc)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Registry file unreadable at %s: %s", self._path, exc)

    def scan(self, extra_dirs: Optional[List[Union[str, Path]]] = None) -> List[Manifest]:
        """Walk plugin dirs and return discovered manifests (no import)."""
        dirs = self._dirs + [Path(d) for d in (extra_dirs or [])]
        manifests: List[Manifest] = []
        seen: Set[str] = set()
        for directory in dirs:
            manifest_path = Path(directory) / PLUGIN_MANIFEST_FILE
            if not manifest_path.exists():
                continue
            try:
                m = self._read_manifest(manifest_path)
                if m.id in seen:
                    continue
                manifests.append(m)
                seen.add(m.id)
            except Exception as exc:
                logger.debug("Skipping manifest at %s: %s", manifest_path, exc)
        return manifests

    def load(self, plugin_id: Union[str, PluginId]) -> PluginRecord:
        """Import the plugin module for *plugin_id* and cache the record."""
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        if pid in self._records and self._records[pid].is_loaded():
            return self._records[pid]

        manifest = self._resolve_manifest(pid)
        entry_point: str = manifest.entry_point or "register"
        module = self._import_plugin(pid, manifest, entry_point)
        checksum = self._plugin_checksum(manifest, module)

        if pid in self._records:
            rec = self._records[pid]
            rec.module, rec.error, rec.checksum, rec.manifest = module, None, checksum, manifest
        else:
            rec = PluginRecord(manifest=manifest, module=module, checksum=checksum)
            self._records[pid] = rec
        self._loaded_ids.add(pid)
        return rec

    def all(self) -> List[PluginRecord]:
        return list(self._records.values())

    def get(self, plugin_id: Union[str, PluginId]) -> Optional[PluginRecord]:
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        return self._records.get(pid)

    def has(self, plugin_id: Union[str, PluginId]) -> bool:
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        return pid in self._records

    def ids(self) -> List[PluginId]:
        return list(self._records.keys())

    def remove(self, plugin_id: Union[str, PluginId]) -> None:
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        if pid not in self._records:
            raise PluginNotFoundError(f"Unknown plugin '{pid}'")
        rec = self._records.pop(pid)
        try:
            import sys
            mod_name = getattr(rec.module, "__name__", None)
            if mod_name and mod_name in sys.modules:
                del sys.modules[mod_name]
        except Exception:
            pass
        self.persist()

    def loaded_ids(self) -> Set[PluginId]:
        return set(self._loaded_ids)

    def validate_manifest(self, manifest: Manifest) -> Result:
        try:
            missing = [k for k in REQUIRED_MANIFEST_KEYS if not getattr(manifest, k, None)]
            if missing:
                return Result.err(f"Manifest missing required keys: {', '.join(missing)}")
            PluginId(manifest.id)
            return Result.ok()
        except (PluginError, ValueError) as exc:
            return Result.err(str(exc))

    def __iter__(self) -> Iterator[PluginRecord]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:
        return f"<PluginRegistry loaded={len(self._loaded_ids)} total={len(self._records)}>"


__all__ = [
    "PluginRecord", "PluginRegistry", "DEFAULT_PLUGIN_DIRS",
    "DEFAULT_REGISTRY_PATH", "PLUGIN_MANIFEST_FILE", "REQUIRED_MANIFEST_KEYS",
]

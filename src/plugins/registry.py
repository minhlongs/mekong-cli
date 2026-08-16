# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin registry.

Responsibilities
- ``scan()``: walk plugin directories and discover plugins.
- ``load()``: import plugin module and emit a live PluginRecord.
- ``get()`` / ``all()`` / ``has()`` / ``remove()``: inspect and mutate state.
- ``persist()`` / ``restore()``: atomic JSON snapshot to ``~/.mekong/plugin-registry.json``.
- ``validate_manifest()``: schema coverage for ``.mekong-plugin.json``.

All public entry points are synchronous; concurrency is an application concern.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union

from .exceptions import (
    ManifestError,
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
)
from .types import Manifest, PluginId, Result

logger = logging.getLogger(__name__)

DEFAULT_PLUGIN_DIRS: Tuple[Path, ...] = (
    Path(os.environ.get("MEKONG_PLUGIN_DIR", ""))
    if os.environ.get("MEKONG_PLUGIN_DIR")
    else (),
    Path.home() / ".mekong" / "plugins",
    Path(__file__).resolve().parent.parent / "plugins",
    Path(".claude") / "plugins",
)

DEFAULT_REGISTRY_PATH = Path.home() / ".mekong" / "plugin-registry.json"

PLUGIN_MANIFEST_FILE = ".mekong-plugin.json"

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
        """Serialise to plain dict — safe for JSON persistence."""
        data = asdict(self.manifest)
        data.update(
            {
                "loaded_at": self.loaded_at,
                "error": self.error,
                "checksum": self.checksum,
            }
        )
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PluginRecord":
        """Rehydrate from plain dict (no live module)."""
        manifest = Manifest.from_dict(
            {k: v for k, v in data.items() if k in Manifest.__dataclass_fields__}
        )
        return PluginRecord(
            manifest=manifest,
            module=None,
            loaded_at=float(data.get("loaded_at", 0.0)),
            error=data.get("error"),
            checksum=data.get("checksum", ""),
        )


class PluginRegistry:
    """Central plugin book-keeper.

    Usage::

    registry = PluginRegistry()
    registry.scan()                       # discover from canonical dirs
    registry.load("com.example.foo")      # import a single plugin
    registry.get("com.example.foo")       # fetch live record
    registry.persist()                    # write atomically to disk
    """

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

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def persist(self) -> None:
        """Write the current registry to disk (atomic rename).

        On any IO failure the registry stays consistent in memory; we
        never raise to the caller because persistence is best-effort.
        """
        try:
            payload = {
                pid: rec.as_dict() for pid, rec in self._records.items()
            }
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_fd, tmp_name = tempfile.mkstemp(
                dir=str(self._path.parent), suffix=".tmp.json"
            )
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
                    rec = PluginRecord.from_dict(blob)
                    self._records[pid_obj] = rec
                    self._loaded_ids.add(pid_obj)
                except Exception as exc:
                    logger.debug("Skipping corrupted registry entry %s: %s", pid, exc)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Registry file unreadable at %s: %s", self._path, exc)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

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
                    logger.debug("Duplicate plugin id %s at %s — skipping", m.id, manifest_path)
                    continue
                manifests.append(m)
                seen.add(m.id)
            except Exception as exc:
                logger.debug("Skipping manifest at %s: %s", manifest_path, exc)
        return manifests

    def _read_manifest(self, path: Path) -> Manifest:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ManifestError(f"Failed to read manifest at {path}: {exc}") from exc
        missing = [k for k in REQUIRED_MANIFEST_KEYS if k not in raw]
        if missing:
            raise ManifestError(
                f"Manifest at {path} missing required keys: {', '.join(missing)}"
            )
        try:
            return Manifest.from_dict(raw)
        except Exception as exc:
            raise ManifestError(f"Invalid manifest at {path}: {exc}") from exc

    # ------------------------------------------------------------------
    # Load / import
    # ------------------------------------------------------------------

    def load(self, plugin_id: Union[str, PluginId]) -> PluginRecord:
        """Import the plugin module for *plugin_id* and cache the record.

        Returns the record (existing if already loaded; raises on failure).
        """
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        if pid in self._records and self._records[pid].is_loaded():
            return self._records[pid]

        manifest = self._resolve_manifest(pid)
        entry_point: str = manifest.entry_point or "register"
        module = self._import_plugin(pid, manifest, entry_point)
        checksum = self._plugin_checksum(manifest, module)

        if pid in self._records:
            rec = self._records[pid]
            rec.module = module
            rec.error = None
            rec.checksum = checksum
            rec.manifest = manifest
        else:
            rec = PluginRecord(manifest=manifest, module=module, checksum=checksum)
            self._records[pid] = rec
        self._loaded_ids.add(pid)
        return rec

    def _resolve_manifest(self, pid: PluginId) -> Manifest:
        """Find a Manifest for *pid* by scanning all plugin dirs."""
        for directory in self._dirs:
            manifest_path = Path(directory) / pid / PLUGIN_MANIFEST_FILE
            if manifest_path.exists():
                try:
                    return self._read_manifest(manifest_path)
                except Exception:
                    continue
        raise PluginNotFoundError(
            f"Cannot locate manifest for plugin '{pid}' in plugin dirs: {self._dirs}"
        )

    def _import_plugin(self, pid: PluginId, manifest: Manifest, entry_point: str) -> Any:
        """Import the plugin's Python module and invoke its entry point.

        Convention: ``entry_point`` is ``module.function`` relative to the
        plugin's root directory on ``sys.path`` (or directly importable).
        """
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

        # Seed sys.path temporarily so relative imports work
        target_dir = root_dir
        if entry_point and "/" in entry_point:
            target_dir = root_dir / Path(entry_point).parent

        target_dir_str = str(target_dir)
        already_on_path = target_dir_str in sys.path
        if not already_on_path:
            sys.path.insert(0, target_dir_str)

        module_name = entry_point.split(".")[0] if entry_point else "__init__"

        try:
            mod = importlib.import_module(module_name)
            # If the entry point dots into deeper attributes, follow them.
            if "." in entry_point:
                obj = mod
                for attr in entry_point.split(".")[1:]:
                    obj = getattr(obj, attr)
                return obj
            return mod
        except Exception as exc:
            raise PluginLoadError(
                f"Failed to import plugin '{pid}' entry_point='{entry_point}': {exc}"
            ) from exc
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

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    def all(self) -> List[PluginRecord]:
        """All known plugin records (loaded + persisted)."""
        return list(self._records.values())

    def get(self, plugin_id: Union[str, PluginId]) -> Optional[PluginRecord]:
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        return self._records.get(pid)

    def has(self, plugin_id: Union[str, PluginId]) -> bool:
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        return pid in self._records

    def ids(self) -> List[PluginId]:
        """All registered plugin ids."""
        return list(self._records.keys())

    def remove(self, plugin_id: Union[str, PluginId]) -> None:
        """Unregister a plugin entirely (does not delete files on disk)."""
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        if pid not in self._records:
            raise PluginNotFoundError(f"Unknown plugin '{pid}'")
        rec = self._records.pop(pid)
        # Best-effort module eviction.
        try:
            import sys

            mod_name = getattr(rec.module, "__name__", None)
            if mod_name and mod_name in sys.modules:
                del sys.modules[mod_name]
        except Exception:
            pass
        self.persist()

    def loaded_ids(self) -> Set[PluginId]:
        """Plugin ids that have been successfully loaded (live module)."""
        return set(self._loaded_ids)

    # ------------------------------------------------------------------
    # Manifest helpers
    # ------------------------------------------------------------------

    def validate_manifest(self, manifest: Manifest) -> Result:
        """Ensure *manifest* has acceptable fields; return Result."""
        try:
            missing = [k for k in REQUIRED_MANIFEST_KEYS if not getattr(manifest, k, None)]
            if missing:
                return Result.err(f"Manifest missing required keys: {', '.join(missing)}")
            PluginId(manifest.id)
            return Result.ok()
        except (PluginError, ValueError) as exc:
            return Result.err(str(exc))

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[PluginRecord]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:
        return f"<PluginRegistry loaded={len(self._loaded_ids)} total={len(self._records)}>"

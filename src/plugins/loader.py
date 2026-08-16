# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin loader — dynamic import system.

Responsibilities:
- Load plugins by id from file-based plugin dirs.
- Compile and load plugins from in-memory source (ObjectMode).
- Surface clear OK/FAIL outcomes via ``PluginRecord.status``.
"""
from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from .registry import DEFAULT_PLUGIN_DIRS, PluginId, PluginRecord, PluginRegistry
from .types import Manifest

logger = logging.getLogger(__name__)


class PluginLoader:
    """High-level loader that wraps ``PluginRegistry``.

    All public API methods return a ``PluginRecord`` with
    ``.status == PluginLoader.OK`` or ``PluginLoader.FAIL`` so callers
    can branch without catching exceptions.
    """

    OK = "OK"
    FAIL = "FAIL"
    PENDING = "PENDING"

    def __init__(self, registry: PluginRegistry) -> None:
        if registry is None:
            raise ValueError("registry is required")
        self.registry = registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_by_id(self, plugin_id: Union[str, PluginId]) -> PluginRecord:
        """Load plugin by id using the registry's file-based path."""
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        try:
            record = self.registry.load(pid)
            record.status = self.OK
            return record
        except Exception as exc:
            return self._fail_record(pid, exc)

    def load_directory(self, directory: Optional[Union[str, Path]] = None) -> Dict[str, PluginRecord]:
        """Scan ``directory`` for ``.mekong-plugin.json``, load each plugin.

        Returns: ``{plugin_id: PluginRecord}``
        """
        base = Path(directory) if directory else self._default_base()
        results: Dict[str, PluginRecord] = {}
        if not base.exists():
            return results
        for manifest_path in self._iter_manifest_paths(base):
            pid_str = manifest_path.parent.name
            try:
                pid = PluginId(pid_str)
            except ValueError:
                logger.debug("Skipping non-reverse-domain plugin dir %s", pid_str)
                continue
            results[pid_str] = self._load_from_disk(pid, manifest_path)
        return results

    def load_modules(self, module_names: Sequence[str]) -> Dict[str, PluginRecord]:
        """Import each Python module by name and build a ``PluginRecord``.

        The module **must** expose ``__plugin_meta__: dict``.
        """
        results: Dict[str, PluginRecord] = {}
        for mod_name in module_names:
            try:
                mod = importlib.import_module(mod_name)
                meta = getattr(mod, "__plugin_meta__", None)
                if not isinstance(meta, dict) or "id" not in meta:
                    raise ValueError(f"Module {mod_name} missing valid __plugin_meta__")
                pid = PluginId(str(meta["id"]))
                manifest_obj = Manifest.from_dict(meta)
                record = PluginRecord.from_meta(manifest_obj, pid)
                record.module = mod
                record.status = self.OK
                results[str(pid)] = record
            except Exception as exc:
                results[str(mod_name)] = self._fail_record(
                    PluginId(str(mod_name)), exc
                )
        return results

    def load_object(
        self,
        plugin_id: Union[str, PluginId],
        manifest: Dict[str, Any],
        source: str,
    ) -> PluginRecord:
        """Object-mode: build a ``PluginRecord`` from in-memory data.

        The *source* string is compiled into a transient module; the
        ``entry_point`` dotted path from *manifest* is resolved against it.
        """
        pid = PluginId(plugin_id) if not isinstance(plugin_id, PluginId) else plugin_id
        manifest_obj = Manifest.from_dict(manifest)
        module = self._compile_module(pid, manifest_obj, source)
        record = PluginRecord.from_meta(manifest_obj, pid)
        record.module = module
        record.status = self.OK
        return record

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _default_base(self) -> "Path":
        return DEFAULT_PLUGIN_DIRS[0] if DEFAULT_PLUGIN_DIRS else (Path.home() / ".mekong" / "plugins")

    def _iter_manifest_paths(self, base: "Path") -> List["Path"]:
        return list(base.glob("*/.mekong-plugin.json"))

    def _load_from_disk(self, pid: PluginId, manifest_path: "Path") -> PluginRecord:
        # Hydrate Manifest
        try:
            manifest_obj = self.registry._read_manifest(manifest_path)
        except Exception as exc:
            return self._fail_record(pid, exc)

        # Import the module under the plugin's src/ or root on sys.path
        plugin_root = manifest_path.parent
        src_dir = plugin_root / "src"
        target_dir = src_dir if src_dir.exists() else plugin_root
        entry_point: str = manifest_obj.entry_point or ""

        target_str = str(target_dir)
        already_on_path = target_str in sys.path
        if not already_on_path:
            sys.path.insert(0, target_str)

        try:
            mod_name = entry_point.split(".")[0] if entry_point else "src"
            mod = importlib.import_module(mod_name)
            if entry_point and "." in entry_point:
                cur = mod
                for attr in entry_point.split(".")[1:]:
                    cur = getattr(cur, attr)
                mod = cur
            record = PluginRecord.from_meta(manifest_obj, pid)
            record.module = mod
            record.status = self.OK
            return record
        except Exception as exc:
            return self._fail_record(pid, exc)
        finally:
            if not already_on_path:
                try:
                    sys.path.remove(target_str)
                except ValueError:
                    pass

    def _compile_module(self, pid: PluginId, manifest_obj: Manifest, source: str) -> types.ModuleType:
        safe_name = str(pid).replace(".", "_").replace("-", "_")
        mod_name = f"_mekong_plugin_{safe_name}"
        try:
            spec = importlib.util.spec_from_loader(
                mod_name,
                loader=None,
                origin="<mekong-object-mode>",
            )
            if spec is None:
                raise ImportError("spec_from_loader returned None")
            mod = types.ModuleType(mod_name)
            mod.__file__ = "<mekong-object-mode>"
            exec(compile(source, mod_name, "exec"), mod.__dict__)  # noqa: S102
            sys.modules[mod_name] = mod
            return mod
        except Exception as exc:
            raise ImportError(f"Object-mode compile failed for {pid}: {exc}") from exc

    def _fail_record(self, pid: PluginId, exc: BaseException) -> PluginRecord:
        pseudo_manifest = Manifest(
            id=str(pid),
            name=str(pid),
            version="0.0.0",
            entry_point="",
        )
        record = PluginRecord.from_meta(pseudo_manifest, pid)
        record.status = self.FAIL
        record.error = repr(exc)
        record.module = None
        return record

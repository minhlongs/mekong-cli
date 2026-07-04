"""Generate an Emacs package from command fabric records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog


@dataclass(frozen=True)
class EmacsPackageArtifact:
    """One generated Emacs package artifact."""

    name: str
    path: str


def emacs_lisp(records: list[CommandRecord]) -> str:
    """Return a dependency-free Emacs command bridge."""
    commands = {
        record.name: {"execution": record.execution, "description": record.description}
        for record in records
    }
    payload = json.dumps(commands, indent=2)
    return f""";;; mekong-command-fabric.el --- Mekong command bridge -*- lexical-binding: t; -*-

(require 'json)
(require 'subr-x)

(defvar mekong-command-fabric-data
  (json-parse-string {json.dumps(payload)} :object-type 'alist))

(defun mekong-command-fabric--names ()
  (mapcar #'symbol-name (mapcar #'car mekong-command-fabric-data)))

(defun mekong-command-fabric-run (name args)
  "Run Mekong command NAME with ARGS in a compilation buffer."
  (interactive
   (list
    (completing-read "Mekong command: " (mekong-command-fabric--names) nil t)
    (read-string "Arguments: ")))
  (let* ((entry (alist-get (intern name) mekong-command-fabric-data))
         (execution (alist-get 'execution entry))
         (invocation (if (string-match-p "\\$ARGUMENTS" execution)
                         (replace-regexp-in-string "\\$ARGUMENTS" args execution t t)
                       (string-trim (concat execution " " args)))))
    (compile invocation)))

(provide 'mekong-command-fabric)
;;; mekong-command-fabric.el ends here
"""


def _write(path: Path, content: str) -> EmacsPackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return EmacsPackageArtifact(path.name, path.as_posix())


def materialize_emacs_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write an Emacs package scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "mekong-command-fabric.el", emacs_lisp(command_records)),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "emacs.json", json.dumps(export_adapter_manifest("emacs", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Emacs\n\nEmacs package generated from Mekong command fabric.\n"),
    ]
    return {
        "schema": "mekong.command_fabric.emacs_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["EmacsPackageArtifact", "emacs_lisp", "materialize_emacs_package"]

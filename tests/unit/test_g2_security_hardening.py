"""Regression tests for Issue #154 G2 security hardening across XML, docs publish, and VietQR env."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.command_fabric.package_build_editor_verifiers import (
    parse_safe_xml_root,
    verify_eclipse_package,
    verify_visual_studio_package,
)
from src.commands.docs import publish_to_custom
from src.services.vietqr_verifier import SepayVerifier, get_verifier


def test_parse_safe_xml_root_allows_clean_xml_and_blocks_xxe(tmp_path: Path) -> None:
    clean = tmp_path / "plugin.xml"
    clean.write_text("<plugin><command id='mekong.cook'/></plugin>", encoding="utf-8")
    root = parse_safe_xml_root(clean)
    assert root.tag == "plugin"
    assert len(root.findall(".//command")) == 1

    xxe = tmp_path / "xxe.xml"
    xxe.write_text(
        '<?xml version="1.0"?><!DOCTYPE p [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><p>&xxe;</p>',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="DTD/entity"):
        parse_safe_xml_root(xxe)


def test_editor_verifiers_use_safe_xml_parser(tmp_path: Path) -> None:
    vs_dir = tmp_path / "vs"
    (vs_dir / "data").mkdir(parents=True)
    (vs_dir / "source.extension.vsixmanifest").write_text("<PackageManifest/>", encoding="utf-8")
    (vs_dir / "Mekong.CommandFabric.VisualStudio.csproj").write_text(
        "<Project>Microsoft.VisualStudio.SDK</Project>", encoding="utf-8"
    )
    (vs_dir / "MekongCommandFabricPackage.cs").write_text(
        "class MekongCommandFabricPackage { void Run(){ Process.Start(); } }", encoding="utf-8"
    )
    (vs_dir / "data" / "visual-studio.json").write_text(
        '{"schema": "mekong.command_fabric.adapter.visual-studio.v1"}', encoding="utf-8"
    )
    assert verify_visual_studio_package(vs_dir)["host"] == "visual-studio-package"

    ec_dir = tmp_path / "eclipse"
    (ec_dir / "src" / "com" / "mekong" / "commandfabric").mkdir(parents=True)
    (ec_dir / "data").mkdir(parents=True)
    (ec_dir / "plugin.xml").write_text("<plugin><command id='c'/></plugin>", encoding="utf-8")
    (ec_dir / "pom.xml").write_text("<packaging>eclipse-plugin</packaging>", encoding="utf-8")
    (ec_dir / "src" / "com" / "mekong" / "commandfabric" / "MekongCommandHandler.java").write_text(
        "class X extends AbstractHandler { ProcessBuilder p; }", encoding="utf-8"
    )
    (ec_dir / "data" / "eclipse.json").write_text(
        '{"schema": "mekong.command_fabric.adapter.eclipse.v1"}', encoding="utf-8"
    )
    assert verify_eclipse_package(ec_dir)["host"] == "eclipse-package"


def test_publish_to_custom_rejects_outside_workspace_script_and_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outside_script = tmp_path / "outside.sh"
    outside_script.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "docs").mkdir()
    local_script = ws / "publish-docs.sh"
    local_script.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")

    monkeypatch.chdir(ws)
    with patch("src.commands.docs.subprocess.run") as mock_run:
        monkeypatch.setenv("CUSTOM_DOCS_PUBLISH_SCRIPT", str(outside_script))
        publish_to_custom("docs", verbose=False)
        mock_run.assert_not_called()

        monkeypatch.setenv("CUSTOM_DOCS_PUBLISH_SCRIPT", "./publish-docs.sh")
        publish_to_custom("../outside_docs", verbose=False)
        mock_run.assert_not_called()


def test_vietqr_get_verifier_accepts_prefixed_and_legacy_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MEKONG_VIETQR_PROVIDER", "sepay")
    monkeypatch.delenv("MEKONG_VIETQR_WEBHOOK_SECRET", raising=False)
    monkeypatch.setenv("VIETQR_WEBHOOK_SECRET", "legacy_hmac_key_value_123456")
    verifier = get_verifier()
    assert isinstance(verifier, SepayVerifier)

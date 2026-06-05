"""Tests for the Binh Phap solo-company operating doctrine."""

from __future__ import annotations

import json
from pathlib import Path

from src.binh_phap.operating_system import (
    BinhPhapOperatingSystem,
    validate_doctrine,
)


def test_default_doctrine_has_all_13_chapters() -> None:
    doctrine = BinhPhapOperatingSystem.load()

    assert doctrine.schema == "mekong.binh_phap_os.v1"
    assert doctrine.chapter_ids() == set(range(1, 14))
    assert {"ceo", "ae", "pm", "eng", "ops"} == doctrine.agent_ids()


def test_default_doctrine_validates_against_registry_and_sops() -> None:
    result = validate_doctrine()

    assert result.valid is True
    assert result.errors == []


def test_validation_reports_missing_chapter(tmp_path: Path) -> None:
    source = BinhPhapOperatingSystem.load()
    data = {
        "schema": source.schema,
        "version": source.version,
        "mission": source.mission,
        "layers": source.layers,
        "chapters": source.chapters[:-1],
    }
    doctrine_path = tmp_path / "bad-doctrine.json"
    doctrine_path.write_text(json.dumps(data), encoding="utf-8")
    doctrine = BinhPhapOperatingSystem.load(doctrine_path)

    result = validate_doctrine(doctrine)

    assert result.valid is False
    assert "Missing chapters" in result.errors[0]

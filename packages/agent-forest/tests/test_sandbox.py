"""Per-user sandbox isolation + traversal guards."""

from __future__ import annotations

import pytest


def test_user_output_dir_creates_isolated_subdir(tmp_path):
    from agent_forest.sandbox import user_output_dir

    d1 = user_output_dir(tmp_path, "u1")
    d2 = user_output_dir(tmp_path, "u2")
    assert d1.parent == tmp_path.resolve()
    assert d1 != d2


def test_user_output_dir_rejects_traversal(tmp_path):
    from agent_forest.sandbox import SandboxViolation, user_output_dir

    for bad in ["../escape", "a/b", "", "..", "a\x00b"]:
        with pytest.raises(SandboxViolation):
            user_output_dir(tmp_path, bad)


def test_resolve_under_rejects_escape(tmp_path):
    from agent_forest.sandbox import SandboxViolation, resolve_under

    with pytest.raises(SandboxViolation):
        resolve_under(tmp_path, "../outside.txt")


def test_resolve_under_accepts_nested(tmp_path):
    from agent_forest.sandbox import resolve_under

    (tmp_path / "sub").mkdir()
    assert resolve_under(tmp_path, "sub/file.txt").parent == (tmp_path / "sub").resolve()

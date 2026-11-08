"""Tests for MEKONG-BENCH 5-Layer Deterministic Runtime Evaluation Suite."""
from __future__ import annotations

from pathlib import Path

from src.opc.mekong_bench import MekongBenchRunner


def test_mekong_bench_all_five_layers_pass_deterministically(tmp_path: Path) -> None:
    """All 5 MEKONG-BENCH layers must pass their programmatic oracles with pass_rate == 1.0."""
    runner = MekongBenchRunner()
    result = runner.run_all(tmp_dir=tmp_path / "bench_run")

    assert result.total_count == 5
    assert result.passed_count == 5
    assert result.pass_rate == 1.0
    assert [layer.layer_id for layer in result.layers] == ["L1", "L2", "L3", "L4", "L5"]
    for layer in result.layers:
        assert layer.passed is True, f"Layer {layer.layer_id} failed: {layer.evidence}"
        assert layer.assertions_checked >= 2
        assert layer.evidence != ""


def test_mekong_bench_markdown_table_rendering(tmp_path: Path) -> None:
    """format_markdown_table renders a deterministic 5-row Markdown table with PASS verdicts."""
    runner = MekongBenchRunner()
    result = runner.run_all(tmp_dir=tmp_path / "bench_md")
    table = runner.format_markdown_table(result)

    assert "| Layer | Benchmark Name | Verdict | Assertions | Programmatic Oracle Evidence |" in table
    for layer_id in ("L1", "L2", "L3", "L4", "L5"):
        assert f"| {layer_id} |" in table
    assert "FAIL" not in table
    assert "5/5 layers passed (`pass_rate=100.00%`)" in table

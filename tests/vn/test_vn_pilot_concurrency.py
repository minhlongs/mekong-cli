"""
Concurrency stress test — verify fcntl.flock prevents JSONL corruption.

Spawns N child processes each appending K records to the same JSONL via
vpr._append_jsonl. Without flock, kernel-level write interleaving can
produce torn lines (e.g., half of record A followed by start of record B
on the same line). With flock, each write is atomic w.r.t. file content.

Assertions:
1. Total line count == N * K (no records lost)
2. Every line parses as valid JSON (no torn writes)
3. Every record has the expected schema keys

POSIX-only — fcntl.flock isn't available on Windows. Test will fail at
import if run on Windows, which is the correct fail-fast signal.
"""
from __future__ import annotations

import json
import multiprocessing as mp
from pathlib import Path

import pytest

from src.api import vn_pilot_routes as vpr


# Stress params — tunable for slower CI. 8×20 = 160 writes runs in <2s on M1.
NUM_WRITERS = 8
WRITES_PER_WORKER = 20
EXPECTED_TOTAL = NUM_WRITERS * WRITES_PER_WORKER


def _writer_worker(worker_id: int, config_dir: str, count: int) -> None:
    """Run in child process. Set CONFIG_DIR + append `count` records.

    Each worker writes to the same `pilots.jsonl` file under the shared
    config_dir. flock serializes the writes; without it, file would be
    corrupted by interleaving.
    """
    vpr.CONFIG_DIR = Path(config_dir)
    for i in range(count):
        vpr._append_jsonl(vpr._pilots_path(), {
            "worker_id": worker_id,
            "seq": i,
            "user_id": f"opc_w{worker_id}_s{i}",
            "name": f"Stress User {worker_id}.{i}",
        })


class TestAppendConcurrency:
    """Multi-process stress test — verifies flock prevents torn writes."""

    def test_no_corruption_under_8_concurrent_writers(
        self, tmp_path: Path
    ) -> None:
        """8 processes × 20 writes → 160 valid JSONL lines, 0 corruption."""
        config_dir = str(tmp_path)

        # Use spawn context for cross-platform consistency (default on macOS 3.8+).
        ctx = mp.get_context("spawn")
        processes = [
            ctx.Process(
                target=_writer_worker,
                args=(wid, config_dir, WRITES_PER_WORKER),
            )
            for wid in range(NUM_WRITERS)
        ]
        for p in processes:
            p.start()
        for p in processes:
            p.join(timeout=10)
            assert p.exitcode == 0, f"Worker {p.pid} crashed (exit={p.exitcode})"

        # Verify: count lines, parse each, check schema
        pilots_file = tmp_path / "pilots.jsonl"
        assert pilots_file.exists(), "JSONL file should have been created"
        lines = pilots_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == EXPECTED_TOTAL, (
            f"Expected {EXPECTED_TOTAL} lines, got {len(lines)}. "
            "Missing records suggest a write was lost (flock not protecting)."
        )

        # Each line must parse as JSON and have the expected schema
        parsed = []
        for i, line in enumerate(lines):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(
                    f"Line {i+1} is corrupted (JSONDecodeError: {e}). "
                    f"Raw: {line[:200]!r}. flock may have failed."
                )
            for key in ("worker_id", "seq", "user_id", "name"):
                assert key in rec, f"Line {i+1} missing key {key!r}: {rec}"
            parsed.append(rec)

        # Verify exact write counts per worker
        from collections import Counter
        counts = Counter(r["worker_id"] for r in parsed)
        for wid in range(NUM_WRITERS):
            assert counts[wid] == WRITES_PER_WORKER, (
                f"Worker {wid} wrote {counts[wid]}, expected {WRITES_PER_WORKER}"
            )

    def test_repeated_runs_stable(self, tmp_path: Path) -> None:
        """Smaller stress (4×5=20 writes) repeated 3 times — catches flaky races.
        Faster than the main stress test; runs the concurrency loop 3x to
        catch race conditions that only surface intermittently.
        """
        config_dir = str(tmp_path)
        ctx = mp.get_context("spawn")
        for run in range(3):
            # Fresh file each iteration
            pilots_file = tmp_path / "pilots.jsonl"
            if pilots_file.exists():
                pilots_file.unlink()
            processes = [
                ctx.Process(target=_writer_worker, args=(wid, config_dir, 5))
                for wid in range(4)
            ]
            for p in processes:
                p.start()
            for p in processes:
                p.join(timeout=5)
                assert p.exitcode == 0, f"Run {run+1}: worker crashed"
            lines = pilots_file.read_text(encoding="utf-8").splitlines()
            assert len(lines) == 20, f"Run {run+1}: expected 20 lines, got {len(lines)}"
            # Quick JSON parse check
            for line in lines:
                json.loads(line)  # raises if corrupted

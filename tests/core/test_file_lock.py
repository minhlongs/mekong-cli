"""Tests for file_lock — atomic append with fcntl advisory locking."""

import fcntl
import json
import threading
import time
from unittest.mock import patch

import pytest

from src.core.file_lock import locked_append, locked_read, locked_read_write


class TestLockedAppend:
    def test_locked_append_creates_file(self, tmp_path):
        file_path = tmp_path / "test.txt"
        with locked_append(file_path) as f:
            f.write("hello")
        assert file_path.read_text() == "hello"

    def test_locked_append_appends_to_existing(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("first")
        with locked_append(file_path) as f:
            f.write("\nsecond")
        assert file_path.read_text() == "first\nsecond"

    def test_locked_append_yields_file_handle(self, tmp_path):
        file_path = tmp_path / "test.txt"
        with locked_append(file_path) as f:
            assert hasattr(f, "write")
            assert hasattr(f, "fileno")

    def test_locked_append_fallback_on_lock_failure(self, tmp_path):
        file_path = tmp_path / "test.txt"
        with patch("fcntl.flock", side_effect=OSError("lock unavailable")):
            with locked_append(file_path) as f:
                f.write("fallback")
        assert file_path.read_text() == "fallback"

    def test_locked_append_closes_file_on_exception(self, tmp_path):
        file_path = tmp_path / "test.txt"
        try:
            with locked_append(file_path) as f:
                f.write("before error")
                raise ValueError("test error")
        except ValueError:
            pass
        # File should still be closed and written
        assert "before error" in file_path.read_text()

    def test_locked_append_unlock_exception_swallowed(self, tmp_path):
        file_path = tmp_path / "test.txt"
        with patch("fcntl.flock", side_effect=[None, OSError("unlock failed")]):
            with locked_append(file_path) as f:
                f.write("content")
        assert file_path.read_text() == "content"


class TestLockedRead:
    def test_locked_read_existing_file(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with locked_read(file_path) as f:
            content = f.read()
        assert content == "content"

    def test_locked_read_yields_file_handle(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with locked_read(file_path) as f:
            assert hasattr(f, "read")
            assert hasattr(f, "fileno")

    def test_locked_read_fallback_on_lock_failure(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with patch("fcntl.flock", side_effect=OSError("lock unavailable")):
            with locked_read(file_path) as f:
                content = f.read()
        assert content == "content"

    def test_locked_read_closes_file_on_exception(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        try:
            with locked_read(file_path) as f:
                f.read()
                raise ValueError("test error")
        except ValueError:
            pass
        # Should not leak file descriptors

    def test_locked_read_unlock_exception_swallowed(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with patch("fcntl.flock", side_effect=[None, OSError("unlock failed")]):
            with locked_read(file_path) as f:
                assert f.read() == "content"


class TestLockedReadWrite:
    def test_locked_read_write_existing_file(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("original")
        with locked_read_write(file_path) as f:
            assert f.read() == "original"
            f.seek(0)
            f.write("modified")
            f.truncate()
        assert file_path.read_text() == "modified"

    def test_locked_read_write_yields_file_handle(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with locked_read_write(file_path) as f:
            assert hasattr(f, "read")
            assert hasattr(f, "write")
            assert hasattr(f, "seek")
            assert hasattr(f, "fileno")

    def test_locked_read_write_fallback_on_lock_failure(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("original")
        with patch("fcntl.flock", side_effect=OSError("lock unavailable")):
            with locked_read_write(file_path) as f:
                f.seek(0)
                f.write("modified")
                f.truncate()
        assert file_path.read_text() == "modified"

    def test_locked_read_write_closes_file_on_exception(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("original")
        try:
            with locked_read_write(file_path) as f:
                f.read()
                raise ValueError("test error")
        except ValueError:
            pass
        # Should not leak file descriptors

    def test_locked_read_write_unlock_exception_swallowed(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("original")
        with patch("fcntl.flock", side_effect=[None, OSError("unlock failed")]):
            with locked_read_write(file_path) as f:
                assert f.read() == "original"


class TestConcurrency:
    def test_file_lock_concurrency(self, tmp_path):
        file_path = tmp_path / "missions.json"
        file_path.write_text(json.dumps({"missions": []}))

        errors = []

        def writer_thread(tid):
            for i in range(20):
                try:
                    with locked_read_write(file_path) as f:
                        content = f.read()
                        data = json.loads(content) if content else {}
                        missions = data.get("missions", [])
                        missions.append({"thread_id": tid, "index": i})

                        f.seek(0)
                        f.write(json.dumps({"missions": missions}, indent=2))
                        f.truncate()
                except Exception as e:
                    errors.append(f"Writer {tid} error: {e}")
                time.sleep(0.005)

        def reader_thread(tid):
            for i in range(20):
                try:
                    with locked_read(file_path) as f:
                        content = f.read()
                        if content:
                            data = json.loads(content)
                            _ = data.get("missions", [])
                except Exception as e:
                    errors.append(f"Reader {tid} error: {e}")
                time.sleep(0.005)

        threads = []
        for t in range(5):
            threads.append(threading.Thread(target=writer_thread, args=(t,)))
            threads.append(threading.Thread(target=reader_thread, args=(t,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert not errors, f"Errors occurred during concurrent read/write: {errors}"

        with open(file_path, "r") as f:
            data = json.loads(f.read())
            assert len(data.get("missions", [])) == 100

    def test_locked_append_concurrent(self, tmp_path):
        file_path = tmp_path / "append.txt"
        file_path.write_text("")

        def appender(tid):
            for i in range(10):
                with locked_append(file_path) as f:
                    f.write(f"thread{tid}-{i}\n")
                time.sleep(0.001)

        threads = [threading.Thread(target=appender, args=(t,)) for t in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        lines = file_path.read_text().strip().split("\n")
        assert len(lines) == 30


class TestLockTypes:
    def test_locked_append_uses_lock_ex(self, tmp_path):
        file_path = tmp_path / "test.txt"
        with patch("fcntl.flock") as mock_flock:
            with locked_append(file_path):
                pass
            # Verify LOCK_EX was called
            calls = mock_flock.call_args_list
            assert len(calls) >= 1
            assert calls[0][0][1] == fcntl.LOCK_EX

    def test_locked_read_uses_lock_sh(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with patch("fcntl.flock") as mock_flock:
            with locked_read(file_path):
                pass
            calls = mock_flock.call_args_list
            assert len(calls) >= 1
            assert calls[0][0][1] == fcntl.LOCK_SH

    def test_locked_read_write_uses_lock_ex(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with patch("fcntl.flock") as mock_flock:
            with locked_read_write(file_path):
                pass
            calls = mock_flock.call_args_list
            assert len(calls) >= 1
            assert calls[0][0][1] == fcntl.LOCK_EX


class TestEdgeCases:
    def test_locked_append_with_string_path(self, tmp_path):
        file_path = str(tmp_path / "test.txt")
        with locked_append(file_path) as f:
            f.write("string path")
        assert (tmp_path / "test.txt").read_text() == "string path"

    def test_locked_read_with_string_path(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with locked_read(str(file_path)) as f:
            assert f.read() == "content"

    def test_locked_read_write_with_string_path(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")
        with locked_read_write(str(file_path)) as f:
            f.seek(0)
            f.write("modified")
            f.truncate()
        assert file_path.read_text() == "modified"

    def test_locked_read_missing_file_raises(self, tmp_path):
        file_path = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            with locked_read(file_path):
                pass

    def test_locked_read_write_missing_file_raises(self, tmp_path):
        file_path = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            with locked_read_write(file_path):
                pass
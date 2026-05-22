"""Atomic append with fcntl advisory locking for JSONL files."""

from __future__ import annotations

import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Union


@contextmanager
def locked_append(path: Union[str, Path]):
    """Open a file in append mode with an exclusive advisory lock.

    Yields the file handle. The lock is released when the context exits.
    Falls back to unlocked append if flock is unavailable (e.g. mock fds).
    """
    locked = False
    f: IO[str] | None = None
    try:
        f = open(path, "a")
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            locked = True
        except (OSError, TypeError, ValueError):
            pass
        yield f
    finally:
        if f is not None:
            if locked:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (OSError, TypeError, ValueError):
                    pass
            f.close()

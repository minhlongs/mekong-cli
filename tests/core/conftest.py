"""tests/core conftest — ensure src/ is on sys.path + per-test fixes."""
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC = os.path.join(_REPO_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# ---------------------------------------------------------------------------
# Git identity: tests create temp repos that need author/committer info.
# macOS keychain can otherwise cause git commit to exit 128.
# ---------------------------------------------------------------------------
os.environ.setdefault("GIT_AUTHOR_NAME", "Test User")
os.environ.setdefault("GIT_AUTHOR_EMAIL", "test@localhost")
os.environ.setdefault("GIT_COMMITTER_NAME", "Test User")
os.environ.setdefault("GIT_COMMITTER_EMAIL", "test@localhost")

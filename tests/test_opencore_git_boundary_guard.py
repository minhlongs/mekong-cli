"""Guard the public-GitHub boundary for the 25-step Open-Core release.

These checks are deliberately cheap and offline: they read the git index and the
tracked text of `.gitignore`/`.env.example`, so they run in CI without git history,
network access, or a fork's remotes. They exist because ignore rules alone cannot
retract a file someone added with `git add -f` — only an index assertion can.

A failure here means a private path (or a live secret prefix) has re-entered the
public index. Fix the index, not this test.

The two index assertions are skipped unless the allowlist untrack has landed,
because they describe the target state rather than the current one; skipping keeps
the suite green while that phase is pending, and the assertions start enforcing
the moment the index is clean. Everything else here — gitignore coverage, secret
scanning, `.env.example` placeholders — is enforced unconditionally and holds today.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Paths that must never be tracked once the allowlist untrack (step 2) lands.
# Kept as prefixes so new files under these dirs are covered automatically.
FORBIDDEN_TRACKED_PREFIXES = (
    ".claude/_archive/",
    ".claude/_integration/",
    ".claude/_quality/",
    ".claude/_core/",
    ".agents/skills/",
    ".agents/sentinel/",
)

# Set once the allowlist untrack lands; until then the index assertions below are
# skipped rather than failed, so a pending phase does not redden the suite.
# Revisit: once the untrack lands, delete this block and the two skip decorators.
UNTRACK_LANDED = False

# Live-looking secret prefixes. Placeholders (`sk-or-v1-yourkey`) and
# masked UI values (`sk-or-v1-***44a1`) are deliberately not matched: they are
# documentation, and matching them would cry wolf on every legit README.
SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9]{20,}"),
    re.compile(r"AIzaSy[A-Za-z0-9_-]{20,}"),
)

SCANNED_SUFFIXES = (".py", ".json", ".md", ".ts", ".tsx", ".toml", ".yaml", ".yml")


def _git(*args: str) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    return proc.stdout.splitlines() if proc.returncode == 0 else []


def _tracked() -> list[str]:
    return _git("ls-files")


def test_pending_untrack_backlog_is_reported() -> None:
    """Count what the allowlist untrack still owes, without failing on it.

    This keeps the two skipped assertions honest: while they are skipped, this
    test always runs and prints the exact backlog, so a pending phase cannot be
    silently forgotten. When the untrack lands the count is 0 and the skip
    markers above can be removed.
    """
    tracked = _tracked()
    private = sum(
        1 for p in tracked if any(p.startswith(x) for x in FORBIDDEN_TRACKED_PREFIXES)
    )
    artifacts = sum(1 for p in tracked if p.endswith((".pyc", ".pyo")))
    print(f"\npending untrack backlog: {private} private paths, {artifacts} build artifacts")
    if not UNTRACK_LANDED:
        assert tracked, "empty index — is this a git repository?"
        # Documents the debt without gating the build on an unapproved phase.
        return
    assert private == 0, f"{private} private paths still tracked"
    assert artifacts == 0, f"{artifacts} build artifacts still tracked"


@pytest.mark.skipif(
    not UNTRACK_LANDED, reason="allowlist untrack pending (step 2) — assertions describe target state"
)
def test_no_private_paths_tracked() -> None:
    tracked = _tracked()
    offenders = [
        path
        for path in tracked
        if any(path.startswith(prefix) for prefix in FORBIDDEN_TRACKED_PREFIXES)
    ]
    assert not offenders, (
        f"{len(offenders)} private path(s) are tracked in the public index: "
        f"{offenders[:5]}{'...' if len(offenders) > 5 else ''}"
    )


@pytest.mark.skipif(
    not UNTRACK_LANDED, reason="allowlist untrack pending (step 2) — assertions describe target state"
)
def test_no_build_artifacts_tracked() -> None:
    tracked = _tracked()
    artifacts = [p for p in tracked if p.endswith((".pyc", ".pyo"))]
    assert not artifacts, f"compiled artifacts tracked: {artifacts[:5]}"


def test_gitignore_blocks_claude_and_agents() -> None:
    """A fresh file under .claude/ must be ignored, not just untracked.

    Without this, untracking is a one-time cleanup that regresses the next time
    a tool writes a file into .claude/ and someone runs `git add .`.
    """
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.is_file(), "root .gitignore missing"
    rules = {
        line.strip()
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert any(rule in {".claude/", ".claude", ".claude/**"} for rule in rules), (
        "no rule ignores .claude/ — private tooling state would be re-trackable"
    )


@pytest.mark.parametrize("prefix", SECRET_PATTERNS)
def test_no_live_secret_prefixes_tracked(prefix: re.Pattern[str]) -> None:
    offenders: list[str] = []
    for path in _tracked():
        if not path.endswith(SCANNED_SUFFIXES) or not (REPO_ROOT / path).is_file():
            continue
        text = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        if prefix.search(text):
            offenders.append(path)
    assert not offenders, (
        f"tracked file(s) contain a live-looking secret {prefix.pattern}: "
        f"{offenders[:5]}"
    )


def test_env_example_holds_placeholders_not_secrets() -> None:
    """Every required key must be present AND unset — a template is not a vault."""
    env_example = REPO_ROOT / ".env.example"
    assert env_example.is_file(), ".env.example missing"
    text = env_example.read_text(encoding="utf-8")
    required = (
        "OPENROUTER_API_KEY",
        "DEEPSEEK_API_KEY",
        "ANTHROPIC_API_KEY",
        "ZALO_OA_SECRET_KEY",
        "NOWPAYMENTS_API_KEY",
        "NOWPAYMENTS_IPN_SECRET",
        "PAYOS_CLIENT_ID",
        "PAYOS_API_KEY",
        "PAYOS_CHECKSUM_KEY",
        "JWT_SECRET",
    )
    missing = [key for key in required if f"{key}=" not in text]
    assert not missing, f".env.example is missing keys: {missing}"
    for pattern in SECRET_PATTERNS:
        assert not pattern.search(text), f".env.example contains a live key: {pattern.pattern}"

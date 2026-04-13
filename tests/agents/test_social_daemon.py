"""Tests for SocialDaemon — covers state helpers, publish_content, poll_and_reply, run_loop."""

import json
import signal
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Patch heavy external imports before importing the module
_mock_get_client = MagicMock()
_mock_poster_cls = MagicMock()
_mock_replier_cls = MagicMock()

import sys

# We patch at the module level so SocialDaemon.__init__ doesn't fail on missing LLM
with (
    patch("src.core.llm_client.get_client", return_value=MagicMock()),
    patch.dict(
        sys.modules,
        {
            "src.core.llm_client": MagicMock(get_client=MagicMock(return_value=MagicMock())),
        },
    ),
):
    pass  # pre-import dance handled per test via patches


def make_daemon(tmp_path: Path):
    """Build a SocialDaemon with all external deps mocked."""
    mock_poster = MagicMock()
    mock_replier = MagicMock()
    mock_client = MagicMock()

    with (
        patch("src.agents.social_daemon.get_client", return_value=mock_client),
        patch("src.agents.social_daemon.SocialPosterAgent", return_value=mock_poster),
        patch("src.agents.social_daemon.SocialReplyAgent", return_value=mock_replier),
        patch("src.agents.social_daemon.STATE_PATH", tmp_path / "daemon-state.json"),
    ):
        from src.agents.social_daemon import SocialDaemon

        daemon = SocialDaemon.__new__(SocialDaemon)
        daemon.poster = mock_poster
        daemon.replier = mock_replier
        daemon._running = True
        # Re-register signal handlers pointing at the real method
        daemon._handle_sigterm = SocialDaemon._handle_sigterm.__get__(daemon)

    return daemon, mock_poster, mock_replier, tmp_path / "daemon-state.json"


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

class TestStateHelpers:
    def test_load_state_returns_default_when_no_file(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, *_ = make_daemon(tmp_path)
        with patch("src.agents.social_daemon.STATE_PATH", tmp_path / "missing.json"):
            from src.agents.social_daemon import STATE_PATH as SP
            # call directly via bound method trick
            result = SocialDaemon._load_state(daemon)
        assert result == {"devto": {}, "github": {}, "last_run": 0}

    def test_load_state_reads_existing_file(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        state_file = tmp_path / "daemon-state.json"
        state_file.write_text(json.dumps({"devto": {"1": {}}, "github": {}, "last_run": 99}))

        daemon, *_ = make_daemon(tmp_path)
        with patch("src.agents.social_daemon.STATE_PATH", state_file):
            result = SocialDaemon._load_state(daemon)
        assert result["last_run"] == 99

    def test_load_state_returns_default_on_corrupt_json(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        state_file = tmp_path / "daemon-state.json"
        state_file.write_text("{corrupt json{{")

        daemon, *_ = make_daemon(tmp_path)
        with patch("src.agents.social_daemon.STATE_PATH", state_file):
            result = SocialDaemon._load_state(daemon)
        assert result == {"devto": {}, "github": {}, "last_run": 0}

    def test_save_state_writes_json(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        state_file = tmp_path / "daemon-state.json"
        daemon, *_ = make_daemon(tmp_path)
        with patch("src.agents.social_daemon.STATE_PATH", state_file):
            SocialDaemon._save_state(daemon, {"devto": {}, "github": {}, "last_run": 42})
        assert json.loads(state_file.read_text())["last_run"] == 42

    def test_save_state_logs_warning_on_oserror(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, *_ = make_daemon(tmp_path)
        with patch("src.agents.social_daemon.STATE_PATH") as mock_sp:
            mock_sp.write_text.side_effect = OSError("no space")
            # Should not raise — just log
            SocialDaemon._save_state(daemon, {})


# ---------------------------------------------------------------------------
# publish_content
# ---------------------------------------------------------------------------

class TestPublishContent:
    def _build(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = make_daemon(tmp_path)
        # Rebind methods from real class
        daemon.publish_content = SocialDaemon.publish_content.__get__(daemon)
        return daemon, poster

    def test_publish_missing_file_returns_empty(self, tmp_path):
        daemon, poster = self._build(tmp_path)
        result = daemon.publish_content("/nonexistent/file.md", ["discord"])
        assert result == {}

    def test_publish_to_discord(self, tmp_path):
        daemon, poster = self._build(tmp_path)
        md = tmp_path / "post.md"
        md.write_text("---\ntitle: Test Post\ntags: ai\n---\nBody content here.")
        poster.post_to_discord.return_value = True
        result = daemon.publish_content(str(md), ["discord"])
        assert result["discord"] == "posted"
        poster.post_to_discord.assert_called_once()

    def test_publish_to_discord_failure(self, tmp_path):
        daemon, poster = self._build(tmp_path)
        md = tmp_path / "post.md"
        md.write_text("Body only, no frontmatter.")
        poster.post_to_discord.return_value = False
        result = daemon.publish_content(str(md), ["discord"])
        assert result["discord"] == ""

    def test_publish_to_devto(self, tmp_path):
        daemon, poster = self._build(tmp_path)
        md = tmp_path / "post.md"
        md.write_text("---\ntitle: My Article\ntags: python, ai\n---\nContent here.")
        poster.post_to_devto.return_value = {"url": "https://dev.to/article/123"}
        result = daemon.publish_content(str(md), ["devto"])
        assert result["devto"] == "https://dev.to/article/123"

    def test_publish_to_github_with_meta(self, tmp_path):
        daemon, poster = self._build(tmp_path)
        md = tmp_path / "post.md"
        md.write_text(
            "---\ntitle: GH Post\ngh_repo: owner/repo\ngh_category_id: DIC_xxx\n---\nBody."
        )
        poster.create_gh_discussion.return_value = {"url": "https://github.com/disc/1"}
        result = daemon.publish_content(str(md), ["github"])
        assert result["github"] == "https://github.com/disc/1"

    def test_publish_to_github_missing_meta_skips(self, tmp_path):
        daemon, poster = self._build(tmp_path)
        md = tmp_path / "post.md"
        md.write_text("---\ntitle: No Meta\n---\nBody.")
        result = daemon.publish_content(str(md), ["github"])
        poster.create_gh_discussion.assert_not_called()
        assert "github" not in result

    def test_publish_multiple_platforms(self, tmp_path):
        daemon, poster = self._build(tmp_path)
        md = tmp_path / "post.md"
        md.write_text("---\ntitle: Multi\ntags: x\n---\nBody.")
        poster.post_to_discord.return_value = True
        poster.post_to_devto.return_value = {"url": "https://dev.to/x"}
        result = daemon.publish_content(str(md), ["discord", "devto"])
        assert "discord" in result
        assert "devto" in result


# ---------------------------------------------------------------------------
# poll_and_reply
# ---------------------------------------------------------------------------

class TestPollAndReply:
    def _build(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = make_daemon(tmp_path)
        daemon.poll_and_reply = SocialDaemon.poll_and_reply.__get__(daemon)
        daemon._poll_devto = SocialDaemon._poll_devto.__get__(daemon)
        daemon._poll_github = SocialDaemon._poll_github.__get__(daemon)
        daemon._load_state = SocialDaemon._load_state.__get__(daemon)
        daemon._save_state = SocialDaemon._save_state.__get__(daemon)
        return daemon, poster, replier, state_file

    def test_poll_updates_last_run(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = self._build(tmp_path)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({"devto": {}, "github": {}, "last_run": 0}))
        before = int(time.time())
        with patch("src.agents.social_daemon.STATE_PATH", state_file):
            daemon.poll_and_reply()
        saved = json.loads(state_file.read_text())
        assert saved["last_run"] >= before

    def test_poll_devto_replies_to_new_comment(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = self._build(tmp_path)
        comment = {"id": 42, "body_html": "Great post!"}
        poster.get_devto_comments.return_value = [comment]
        replier.should_reply.return_value = True
        replier.generate_reply.return_value = "Thanks!"
        poster.reply_devto_comment.return_value = {"id": 99}

        state = {"devto": {"123": {"title": "My Article", "seen_ids": []}}, "github": {}}
        daemon._poll_devto(state)

        poster.reply_devto_comment.assert_called_once_with(123, 42, "Thanks!")
        assert "42" in state["devto"]["123"]["seen_ids"]

    def test_poll_devto_skips_already_seen(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = self._build(tmp_path)
        poster.get_devto_comments.return_value = [{"id": 42}]
        replier.should_reply.return_value = True

        state = {"devto": {"123": {"title": "T", "seen_ids": ["42"]}}, "github": {}}
        daemon._poll_devto(state)

        replier.should_reply.assert_not_called()
        poster.reply_devto_comment.assert_not_called()

    def test_poll_github_replies_to_new_comment(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = self._build(tmp_path)
        comment = {"id": "C_abc", "body": "Nice!"}
        poster.get_gh_discussion_comments.return_value = [comment]
        replier.should_reply.return_value = True
        replier.generate_reply.return_value = "Thank you!"
        poster.reply_gh_discussion.return_value = {"id": "R_xyz"}

        state = {
            "github": {"disc_1": {"repo": "owner/repo", "number": 1, "id": "D_xxx", "title": "T", "seen_ids": []}},
            "devto": {},
        }
        daemon._poll_github(state)

        poster.reply_gh_discussion.assert_called_once()
        assert "C_abc" in state["github"]["disc_1"]["seen_ids"]

    def test_poll_github_skips_missing_repo(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = self._build(tmp_path)
        state = {
            "github": {"disc_1": {"repo": "", "number": 0, "id": "", "title": "", "seen_ids": []}},
            "devto": {},
        }
        daemon._poll_github(state)
        poster.get_gh_discussion_comments.assert_not_called()


# ---------------------------------------------------------------------------
# run_loop
# ---------------------------------------------------------------------------

class TestRunLoop:
    def test_run_loop_stops_on_sigterm(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = make_daemon(tmp_path)
        daemon.run_loop = SocialDaemon.run_loop.__get__(daemon)
        daemon._handle_sigterm = SocialDaemon._handle_sigterm.__get__(daemon)

        call_count = 0

        def fake_poll_and_reply():
            nonlocal call_count
            call_count += 1
            daemon._running = False  # stop after first iteration

        daemon.poll_and_reply = fake_poll_and_reply

        daemon.run_loop(interval_minutes=0)
        assert call_count == 1
        assert daemon._running is False

    def test_run_loop_handles_exception_in_poll(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, poster, replier, state_file = make_daemon(tmp_path)
        daemon.run_loop = SocialDaemon.run_loop.__get__(daemon)

        iterations = {"n": 0}

        def bad_poll():
            iterations["n"] += 1
            daemon._running = False
            raise RuntimeError("poll failed")

        daemon.poll_and_reply = bad_poll

        # Should not propagate exception
        daemon.run_loop(interval_minutes=0)
        assert iterations["n"] == 1

    def test_handle_sigterm_sets_running_false(self, tmp_path):
        from src.agents.social_daemon import SocialDaemon

        daemon, *_ = make_daemon(tmp_path)
        daemon._handle_sigterm = SocialDaemon._handle_sigterm.__get__(daemon)
        daemon._running = True
        daemon._handle_sigterm(signal.SIGTERM, None)
        assert daemon._running is False


# ---------------------------------------------------------------------------
# parse_frontmatter (helper module)
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    def setup_method(self):
        from src.agents.social_daemon_helpers import parse_frontmatter
        self.parse = parse_frontmatter

    def test_no_frontmatter_returns_defaults(self):
        title, tags, body, meta = self.parse("Just body text.")
        assert title == "Mekong CLI Update"
        assert tags == []
        assert body == "Just body text."
        assert meta == {}

    def test_full_frontmatter(self):
        raw = "---\ntitle: Hello World\ntags: python, ai\ngh_repo: owner/repo\ngh_category_id: DIC_xxx\n---\nBody here."
        title, tags, body, meta = self.parse(raw)
        assert title == "Hello World"
        assert "python" in tags
        assert "ai" in tags
        assert body == "Body here."
        assert meta["gh_repo"] == "owner/repo"
        assert meta["gh_category_id"] == "DIC_xxx"

    def test_frontmatter_missing_separator(self):
        raw = "title: not parsed\nBody here."
        title, tags, body, meta = self.parse(raw)
        assert title == "Mekong CLI Update"  # not parsed
        assert body == raw

    def test_partial_frontmatter_no_tags(self):
        raw = "---\ntitle: Partial\n---\nContent."
        title, tags, body, meta = self.parse(raw)
        assert title == "Partial"
        assert tags == []
        assert body == "Content."


# ---------------------------------------------------------------------------
# build_arg_parser (helper module)
# ---------------------------------------------------------------------------

class TestBuildArgParser:
    def setup_method(self):
        from src.agents.social_daemon_helpers import build_arg_parser
        self.parser = build_arg_parser()

    def test_defaults(self):
        args = self.parser.parse_args([])
        assert args.interval == 60
        assert args.publish == ""
        assert args.platforms == ["devto", "github"]

    def test_custom_interval(self):
        args = self.parser.parse_args(["--interval", "30"])
        assert args.interval == 30

    def test_custom_publish(self):
        args = self.parser.parse_args(["--publish", "/tmp/post.md"])
        assert args.publish == "/tmp/post.md"

    def test_custom_platforms(self):
        args = self.parser.parse_args(["--platforms", "discord", "devto"])
        assert args.platforms == ["discord", "devto"]

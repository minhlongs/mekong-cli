"""
Integration test cho /zalo-oa CLI + ZaloOAClient (mocked transport).
Không gọi Zalo API thật — mock requests.Session.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from integrations.zalo import ZaloOAClient, generate_vn_caption
from src.commands.zalo_oa import main as zalo_main


@pytest.fixture
def mock_response():
    """Factory tạo mock requests.Response."""
    def _make(payload: dict, status: int = 200):
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = payload
        resp.raise_for_status.return_value = None
        return resp
    return _make


@pytest.fixture
def client_with_mock_session(mock_response):
    """ZaloOAClient với _get_session() đã bypass — không cần requests module thật."""
    client = ZaloOAClient(access_token="fake_token", app_id="fake_app")
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response({"data": {"total": 0, "followers": []}})
    mock_session.post.return_value = mock_response({"error": 0, "message": "ok"})
    # Bypass _get_session entirely — tránh check `requests is None`.
    client._get_session = lambda: mock_session  # type: ignore[method-assign]
    return client, mock_session


class TestZaloOAClientTransport:
    """Verify request structure khớp Zalo OA API docs."""

    def test_send_message_posts_correct_payload(self, client_with_mock_session):
        client, sess = client_with_mock_session
        result = client.send_message("user_123", "Xin chào")
        assert sess.post.called
        call_args = sess.post.call_args
        assert "/message" in call_args[0][0]
        payload = call_args[1]["json"]
        assert payload == {
            "recipient": {"user_id": "user_123"},
            "message": {"text": "Xin chào"},
        }
        assert result == {"error": 0, "message": "ok"}

    def test_broadcast_posts_to_broadcast_endpoint(self, client_with_mock_session):
        client, sess = client_with_mock_session
        client.broadcast("Khuyến mãi lớn cuối tuần")
        call_args = sess.post.call_args
        assert "/broadcast/message" in call_args[0][0]
        assert call_args[1]["json"]["message"]["text"] == "Khuyến mãi lớn cuối tuần"

    def test_get_followers_uses_get_with_pagination(self, client_with_mock_session):
        client, sess = client_with_mock_session
        client.get_followers(offset=10, count=20)
        call_args = sess.get.call_args
        assert "/getfollowers" in call_args[0][0]
        assert call_args[1]["params"] == {"data": '{"offset":10,"count":20}'}

    def test_post_article_includes_cover(self, client_with_mock_session):
        client, sess = client_with_mock_session
        client.post_article(
            title="Sản phẩm mới",
            content="Nội dung dài " * 20,
            cover_image="https://example.com/cover.jpg",
        )
        payload = sess.post.call_args[1]["json"]
        assert payload["title"] == "Sản phẩm mới"
        assert payload["cover"] == "https://example.com/cover.jpg"
        # description bị truncate 100 ký tự
        assert len(payload["description"]) == 100

    def test_is_configured_requires_both_token_and_app(self):
        assert not ZaloOAClient(access_token="x", app_id="").is_configured()
        assert not ZaloOAClient(access_token="", app_id="x").is_configured()
        assert ZaloOAClient(access_token="x", app_id="y").is_configured()


class TestVnCaptionGenerator:
    """Caption generator offline — không cần API."""

    @pytest.mark.parametrize("tone", ["than_thien", "chuyen_nghiep", "vui_ve"])
    def test_caption_includes_product_name(self, tone: str):
        caption = generate_vn_caption("áo dài", tone=tone)
        assert "áo dài" in caption.lower()

    def test_caption_than_thien_has_emoji(self):
        caption = generate_vn_caption("trà sữa", tone="than_thien")
        assert "🌟" in caption or "📱" in caption

    def test_caption_chuyen_nghiep_no_excessive_emoji(self):
        caption = generate_vn_caption("phần mềm kế toán", tone="chuyen_nghiep")
        # Bullet points "•" mà không phải emoji rầm rộ
        assert "•" in caption


class TestCliEntrypoint:
    """CLI parsing cho `python -m src.commands.zalo_oa <cmd>`."""

    def test_caption_subcommand_runs_without_token(self, capsys):
        """Caption không cần ZALO_OA_ACCESS_TOKEN (offline)."""
        zalo_main(["caption", "bánh mì", "--tone", "vui_ve"])
        captured = capsys.readouterr()
        assert "bánh mì" in captured.out.lower()

    def test_send_requires_token_env(self, monkeypatch, capsys):
        monkeypatch.delenv("ZALO_OA_ACCESS_TOKEN", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            zalo_main(["send", "user_999", "hello"])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ZALO_OA_ACCESS_TOKEN" in captured.err

    def test_send_with_mock_client(self, monkeypatch, capsys, mock_response):
        monkeypatch.setenv("ZALO_OA_ACCESS_TOKEN", "fake")
        monkeypatch.setenv("ZALO_APP_ID", "fake_app")
        mock_client = MagicMock()
        mock_client.send_message.return_value = {"error": 0, "message_id": "m_001"}
        with patch('src.commands.zalo_oa._get_client', return_value=mock_client):
            zalo_main(["send", "user_999", "Xin chào"])
        captured = capsys.readouterr()
        assert "m_001" in captured.out
        mock_client.send_message.assert_called_once_with("user_999", "Xin chào")

    def test_broadcast_with_mock_client(self, monkeypatch, capsys):
        monkeypatch.setenv("ZALO_OA_ACCESS_TOKEN", "fake")
        mock_client = MagicMock()
        mock_client.broadcast.return_value = {"error": 0, "broadcast_id": "bc_42"}
        with patch('src.commands.zalo_oa._get_client', return_value=mock_client):
            zalo_main(["broadcast", "Khuyến mãi Tết 2026"])
        captured = capsys.readouterr()
        assert "bc_42" in captured.out

    def test_followers_prints_total(self, monkeypatch, capsys):
        monkeypatch.setenv("ZALO_OA_ACCESS_TOKEN", "fake")
        mock_client = MagicMock()
        mock_client.get_followers.return_value = {
            "data": {
                "total": 1234,
                "followers": [
                    {"user_id": "u1", "display_name": "Khách 1"},
                    {"user_id": "u2", "display_name": "Khách 2"},
                ],
            }
        }
        with patch('src.commands.zalo_oa._get_client', return_value=mock_client):
            zalo_main(["followers", "--count", "10"])
        captured = capsys.readouterr()
        assert "1,234" in captured.out
        assert "Khách 1" in captured.out


class TestPilotReadiness:
    """Smoke checks cho 10 pilot OPC users."""

    def test_all_5_subcommands_registered(self, monkeypatch):
        """Pilot doc liệt kê 5 subcommand — đảm bảo argparse nhận tất."""
        monkeypatch.setenv("ZALO_OA_ACCESS_TOKEN", "fake")
        # caption không cần network → safe to test parse-only
        try:
            zalo_main(["caption", "test"])
        except SystemExit:
            pass

        # Verify khác bằng cách parse với --help (should exit 0)
        for cmd in ("send", "broadcast", "followers", "caption", "post"):
            with pytest.raises(SystemExit) as exc_info:
                zalo_main([cmd, "--help"])
            assert exc_info.value.code == 0, f"Subcommand `{cmd}` failed --help"

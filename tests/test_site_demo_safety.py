from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site" / "public"


def test_every_static_screen_is_labeled_demo_and_has_no_payable_qr() -> None:
    pages = sorted(SITE.glob("*.html"))
    assert len(pages) == 21

    for page in pages:
        content = page.read_text(encoding="utf-8")
        assert content.count('id="demo-mode-notice"') == 1, page.name
        assert content.count('id="modal-topup"') == 1, page.name
        assert "no payable qr code" in content.lower(), page.name
        assert "9842099999" not in content, page.name
        assert "img.vietqr.io/image/" not in content, page.name
        assert "Global PayOS VietQR Top-Up Simulation Modal" not in content, page.name
        assert "Global VietQR Top-up Modal Frame" not in content, page.name


def test_public_payment_simulator_cannot_claim_verification_or_credit() -> None:
    worker = (SITE / "_worker.js").read_text(encoding="utf-8")
    static_app = (SITE / "js" / "app.js").read_text(encoding="utf-8")
    react_api = (ROOT / "site" / "react-app" / "src" / "services" / "api.ts").read_text(encoding="utf-8")

    for source in (worker, static_app, react_api):
        assert "mekong-hmac-vietqr-key" not in source
        assert "mcu_credited" not in source
        assert "img.vietqr.io/image/" not in source
        assert "verified: true" not in source

    assert "demo_only: true" in worker
    assert "verified: false" in worker
    assert "result?.demo_only !== true" in static_app
    assert "result?.verified !== false" in static_app
    assert "localhost:8000" not in react_api


def test_react_demo_does_not_claim_real_verification_or_consensus() -> None:
    app = (ROOT / "site" / "react-app" / "src" / "App.tsx").read_text(encoding="utf-8")
    api = (ROOT / "site" / "react-app" / "src" / "services" / "api.ts").read_text(encoding="utf-8")

    assert "5/5 UNANIMOUS" not in app
    assert "badge={invoice ? 'VERIFIED'" not in app
    assert "TT78-VERIFIED-" not in api
    assert "quorum_reached: false" in api
    assert "valid: false" in api

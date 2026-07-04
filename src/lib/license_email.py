"""Email license keys via Resend API.

Best-effort: never raises in webhook flow — failures are logged and the
caller continues (license is still persisted, manual resend is possible).

Configuration:
  RESEND_API_KEY        — required to actually send
  LICENSE_EMAIL_FROM    — defaults to no-reply@mekongmind.com
  IDE_LOGIN_URL         — defaults to https://ide.mekongmind.com/login
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
DEFAULT_FROM = "no-reply@mekongmind.com"
DEFAULT_LOGIN_URL = "https://ide.mekongmind.com/login"


def _build_html(license_key: str, tier: str, login_url: str) -> str:
    return f"""<!doctype html>
<html><body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 2rem auto;">
<h2>Welcome to Mekong CLI ({tier.title()} tier)</h2>
<p>Your license key:</p>
<pre style="background:#f4f4f4;padding:1rem;border-radius:4px;font-size:14px;">{license_key}</pre>
<p><a href="{login_url}" style="display:inline-block;padding:10px 18px;background:#111;color:#fff;text-decoration:none;border-radius:4px;">Open IDE</a></p>
<p style="color:#666;font-size:12px;">Paste your license key on the login page. Keep it secret.</p>
</body></html>"""


def send_license_email(
    email: str,
    license_key: str,
    tier: str,
    *,
    api_key: Optional[str] = None,
    from_addr: Optional[str] = None,
    login_url: Optional[str] = None,
    timeout: float = 5.0,
) -> bool:
    """Send license key via Resend. Returns True on 2xx, False otherwise.

    Never raises. Caller should not block on the result.
    """
    api_key = api_key or os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.warning("license_email.skipped", extra={"reason": "no_api_key"})
        return False

    from_addr = from_addr or os.environ.get("LICENSE_EMAIL_FROM", DEFAULT_FROM)
    login_url = login_url or os.environ.get("IDE_LOGIN_URL", DEFAULT_LOGIN_URL)

    payload = {
        "from": from_addr,
        "to": [email],
        "subject": f"Your Mekong CLI {tier.title()} license key",
        "html": _build_html(license_key, tier, login_url),
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
        if 200 <= resp.status_code < 300:
            logger.info("license_email.sent", extra={"to": email, "tier": tier})
            return True
        logger.error(
            "license_email.failed",
            extra={"to": email, "status": resp.status_code, "body": resp.text[:200]},
        )
        return False
    except Exception as exc:  # network / DNS / etc.
        logger.error("license_email.error", extra={"to": email, "error": str(exc)})
        return False

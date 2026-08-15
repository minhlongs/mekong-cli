"""SSRF-safe webhook notifier.

Rules:
- Must be https:// (or http:// only when FOREST_ALLOW_HTTP_WEBHOOKS=1).
- Rejects localhost/loopback, link-local, RFC 1918 private ranges unless explicitly allowed.
- Single POST attempt (Phase 2 scope cut — retry deferred to Phase 3).
- Short configurable timeout.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import socket
from urllib.parse import urlparse

import httpx

log = logging.getLogger("agent_forest.webhook")


class WebhookRejected(Exception):
    pass


def _is_forbidden_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True if the IP is in any non-public range we refuse to hit."""
    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified  # blocks 0.0.0.0 / ::
        or ip.is_reserved
    ):
        return True
    # Block IPv4-mapped IPv6 (::ffff:127.0.0.1 etc.) whose mapped v4 is forbidden.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return _is_forbidden_ip(ip.ipv4_mapped)
    return False


def _host_resolves_public(host: str) -> bool:
    try:
        addrs = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for *_, sockaddr in addrs:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if _is_forbidden_ip(ip):
            return False
    return True


def validate_webhook_url(url: str) -> None:
    parsed = urlparse(url)
    allow_http = os.getenv("FOREST_ALLOW_HTTP_WEBHOOKS") == "1"
    if parsed.scheme not in ("https",) and not (allow_http and parsed.scheme == "http"):
        raise WebhookRejected(f"scheme not allowed: {parsed.scheme!r}")
    if not parsed.hostname:
        raise WebhookRejected("missing host")
    if not _host_resolves_public(parsed.hostname):
        raise WebhookRejected(f"host resolves to private/loopback range: {parsed.hostname}")


def send_webhook(url: str, payload: dict, timeout: float = 5.0) -> int | None:
    """POST payload. Returns status code on success, None on failure."""
    try:
        validate_webhook_url(url)
    except WebhookRejected as exc:
        log.warning("webhook rejected: %s", exc)
        return None
    try:
        resp = httpx.post(url, json=payload, timeout=timeout)
        return resp.status_code
    except httpx.HTTPError as exc:
        log.warning("webhook POST failed: %s", exc)
        return None

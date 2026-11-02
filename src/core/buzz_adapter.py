# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""BuzzAdapter — bridge between Buzz social platform and Mekong autonomous runtime.

Accepts inbound goals from Buzz, dispatches outbound status updates over a
pluggable HTTP transport (default ``urllib.request``, injectable for tests),
enforces server-side webhook authority and SSRF-safe callback validation,
and collects post-execution feedback.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
import math
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import TYPE_CHECKING, Any, Callable

from src.mekongcli.core.goal_engine.models import (
    ExecutionTruthStatus,
    ImmutableMandate,
    OutboxEntry,
    TicketRecord,
    new_id,
)

if TYPE_CHECKING:
    from src.mekongcli.core.goal_engine.store import SQLiteGoalStore

logger = logging.getLogger(__name__)

# Type of the outbound HTTP transport: (url, payload_dict) -> HTTP status code.
BuzzTransport = Callable[[str, dict[str, Any]], int]

_RISK_LEVEL_ORDER: dict[str, int] = {
    "low": 1,
    "standard": 2,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

_RFC2606_TEST_SUFFIXES = (
    ".test",
    ".example",
    ".example.com",
    ".example.org",
    ".example.net",
)
_RFC2606_TEST_HOSTS = frozenset({
    "test",
    "example",
    "example.com",
    "example.org",
    "example.net",
})
_FORBIDDEN_LOCAL_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".arpa",
    ".home.arpa",
    ".corp",
    ".lan",
)
_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")
_METADATA_IPV4 = ipaddress.ip_address("169.254.169.254")


class BuzzConfigError(RuntimeError):
    """Raised when BuzzAdapter is asked to deliver without a configured transport or store."""


class BuzzSecurityError(BuzzConfigError, PermissionError, ValueError):
    """Raised when a webhook payload or callback URL violates server-side security policy."""


@dataclass(frozen=True)
class WebhookAuthorityPolicy:
    """Server-owned authority policy governing inbound webhook ticket mandates."""

    policy_version: str = "2026.11-sc01.2"
    mandate_version: int = 1
    default_authorized_scope: str = "workspace"
    allowed_scopes: tuple[str, ...] = ("workspace", "read_only", "goal_execution")
    default_capabilities: tuple[str, ...] = ("goal_execute",)
    allowed_capabilities: tuple[str, ...] = (
        "goal_execute",
        "read_status",
        "verify_goal",
        "artifact_read",
    )
    default_resource_boundaries: tuple[str, ...] = (".",)
    allowed_resource_roots: tuple[str, ...] = (".",)
    default_risk_classification: str = "standard"
    min_risk_classification: str = "standard"
    allowed_risk_classifications: tuple[str, ...] = (
        "low",
        "standard",
        "medium",
        "high",
        "critical",
    )
    default_cost_budget: float = 10.0
    max_cost_budget: float = 10.0
    default_retry_budget: int = 3
    max_retry_budget: int = 3
    default_verification_requirements: str = "standard"
    allowed_verification_profiles: tuple[str, ...] = ("standard", "smoke")
    allowed_requesters: tuple[str, ...] | None = None
    allowed_callback_hosts: tuple[str, ...] | None = None
    allowed_http_hosts: tuple[str, ...] = ()
    allow_payload_authority_override: bool = False


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """HTTP redirect handler that refuses all 3xx redirects to prevent SSRF redirect bypass."""

    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Any:
        raise BuzzSecurityError(
            f"HTTP {code} redirect to '{newurl}' is forbidden for callback delivery"
        )


def _validate_ip_address(ip_str: str) -> None:
    """Reject loopback, private, link-local, metadata, CGNAT, multicast, reserved, and unspecified IPs."""
    cleaned = ip_str.split("%", 1)[0].strip()
    try:
        ip_obj = ipaddress.ip_address(cleaned)
    except ValueError as exc:
        raise BuzzSecurityError(f"Invalid IP address '{ip_str}': {exc}") from exc

    candidates = [ip_obj]
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped is not None:
        candidates.append(ip_obj.ipv4_mapped)

    for candidate in candidates:
        if candidate == _METADATA_IPV4:
            raise BuzzSecurityError(
                f"Callback destination IP '{ip_str}' targets forbidden cloud metadata service"
            )
        if isinstance(candidate, ipaddress.IPv4Address) and candidate in _CGNAT_NETWORK:
            raise BuzzSecurityError(
                f"Callback destination IP '{ip_str}' is in forbidden CGNAT range 100.64.0.0/10"
            )
        if (
            candidate.is_loopback
            or candidate.is_private
            or candidate.is_link_local
            or candidate.is_multicast
            or candidate.is_reserved
            or candidate.is_unspecified
        ):
            raise BuzzSecurityError(
                f"Callback destination IP '{ip_str}' is forbidden (non-public address)"
            )


def validate_callback_destination(
    url: str,
    *,
    policy: WebhookAuthorityPolicy | None = None,
    strict_dns: bool = False,
    resolver: Callable[..., list[Any]] | None = None,
) -> str:
    """Validate callback URL against SSRF, scheme downgrade, credential leakage, and DNS rebinding."""
    if not isinstance(url, str) or not url.strip():
        raise BuzzSecurityError("Callback URL must be a non-empty string")
    raw_url = url.strip()
    parsed = urllib.parse.urlparse(raw_url)
    scheme = (parsed.scheme or "").lower()
    eff_policy = policy or WebhookAuthorityPolicy()

    if parsed.username is not None or parsed.password is not None:
        raise BuzzSecurityError("Callback URL must not contain embedded credentials")

    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        raise BuzzSecurityError("Callback URL is missing a valid hostname")

    if scheme == "https":
        pass
    elif scheme == "http" and hostname in eff_policy.allowed_http_hosts:
        pass
    else:
        raise BuzzSecurityError(
            f"Callback URL scheme '{scheme or '<empty>'}' is forbidden; HTTPS is required"
        )

    if (
        hostname in ("localhost", "localhost.localdomain")
        or hostname.endswith(_FORBIDDEN_LOCAL_HOST_SUFFIXES)
    ):
        raise BuzzSecurityError(
            f"Callback hostname '{hostname}' is forbidden (local/internal hostname)"
        )

    if eff_policy.allowed_callback_hosts is not None:
        allowed_hosts = tuple(h.lower().rstrip(".") for h in eff_policy.allowed_callback_hosts)
        if not any(
            hostname == allowed or hostname.endswith(f".{allowed}")
            for allowed in allowed_hosts
        ):
            raise BuzzSecurityError(
                f"Callback hostname '{hostname}' is not in allowed_callback_hosts"
            )

    # Check if hostname is an IP literal (standard or integer/hex encoded)
    is_ip_literal = False
    try:
        ip_lit = ipaddress.ip_address(hostname.split("%", 1)[0])
        is_ip_literal = True
        _validate_ip_address(str(ip_lit))
    except BuzzSecurityError:
        raise
    except ValueError:
        parts = [p for p in hostname.split(".") if p]
        if hostname.isdigit() or hostname.startswith("0x") or (
            parts and all(p.isdigit() or p.lower().startswith("0x") for p in parts)
        ):
            try:
                int_val = int(hostname, 0)
                ip_from_int = ipaddress.ip_address(int_val)
                is_ip_literal = True
                _validate_ip_address(str(ip_from_int))
            except BuzzSecurityError:
                raise
            except ValueError as exc:
                raise BuzzSecurityError(
                    f"Callback hostname '{hostname}' uses forbidden numeric IP encoding"
                ) from exc

    if not is_ip_literal:
        addr_fn = resolver or socket.getaddrinfo
        port = parsed.port or (80 if scheme == "http" else 443)
        try:
            infos = addr_fn(hostname, port, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            is_synthetic_test_host = (
                hostname in _RFC2606_TEST_HOSTS
                or hostname.endswith(_RFC2606_TEST_SUFFIXES)
            )
            if not strict_dns and is_synthetic_test_host and resolver is None:
                return raw_url
            raise BuzzSecurityError(
                f"DNS resolution failed for callback hostname '{hostname}': {exc}"
            ) from exc

        if not infos:
            raise BuzzSecurityError(
                f"Callback hostname '{hostname}' resolved to zero addresses"
            )
        for info in infos:
            sockaddr = info[4]
            if not sockaddr:
                continue
            resolved_ip = str(sockaddr[0])
            _validate_ip_address(resolved_ip)

    return raw_url


validate_callback_url = validate_callback_destination


def _urllib_transport(url: str, payload: dict[str, Any]) -> int:
    """Default stdlib HTTP POST transport with SSRF validation and redirect blocking."""
    validate_callback_destination(url, strict_dns=True)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(_NoRedirectHandler())
    with opener.open(req, timeout=5.0) as resp:
        return int(resp.status)


# Sentinel distinguishing "caller omitted transport" (use stdlib default) from
# "caller passed transport=None" (explicitly disable transport → fail loud).
_DEFAULT_TRANSPORT: Any = object()


@dataclass
class BuzzPayload:
    """Inbound goal payload from Buzz."""

    goal_text: str
    context: dict[str, Any] = field(default_factory=dict)
    callback_url: str | None = None
    mission_id: str | None = None


class BuzzAdapter:
    """Adapter connecting Buzz platform events to MekongCoreRuntime."""

    def __init__(
        self,
        runtime: Any = None,
        transport: BuzzTransport | None = _DEFAULT_TRANSPORT,
        outbox_store: SQLiteGoalStore | None = None,
        authority_policy: WebhookAuthorityPolicy | None = None,
    ) -> None:
        self._runtime = runtime
        self._transport: BuzzTransport | None = (
            _urllib_transport if transport is _DEFAULT_TRANSPORT else transport
        )
        self._outbox_store: SQLiteGoalStore | None = outbox_store
        self._authority_policy: WebhookAuthorityPolicy = (
            authority_policy or WebhookAuthorityPolicy()
        )

    @classmethod
    def without_transport(cls, runtime: Any = None) -> "BuzzAdapter":
        """Construct an adapter with no transport wired (fails loud on callback delivery)."""
        return cls(runtime=runtime, transport=None)

    @property
    def runtime(self) -> Any:
        return self._runtime

    @runtime.setter
    def runtime(self, value: Any) -> None:
        self._runtime = value

    @property
    def transport(self) -> BuzzTransport | None:
        return self._transport

    @property
    def outbox_store(self) -> SQLiteGoalStore | None:
        return self._outbox_store

    @outbox_store.setter
    def outbox_store(self, value: SQLiteGoalStore | None) -> None:
        self._outbox_store = value

    @property
    def authority_policy(self) -> WebhookAuthorityPolicy:
        return self._authority_policy

    @authority_policy.setter
    def authority_policy(self, value: WebhookAuthorityPolicy) -> None:
        self._authority_policy = value

    def _build_validated_mandate(
        self,
        payload: dict[str, Any],
        *,
        ticket_id: str,
        source_id: str,
        event_id: str,
    ) -> ImmutableMandate:
        """Validate webhook fields against ``self._authority_policy`` and build a server-pinned ``ImmutableMandate``."""
        policy = self._authority_policy
        raw_ctx = payload.get("context")
        context: dict[str, Any] = raw_ctx if isinstance(raw_ctx, dict) else {}

        def _get_explicit(key: str) -> tuple[bool, Any]:
            if key in payload:
                return True, payload[key]
            if key in context:
                return True, context[key]
            return False, None

        has_hash, _ = _get_explicit("mandate_hash")
        if has_hash and not policy.allow_payload_authority_override:
            raise BuzzSecurityError("Webhook payload cannot supply pre-forged mandate_hash")

        has_mv, raw_mv = _get_explicit("mandate_version")
        if has_mv and not policy.allow_payload_authority_override:
            if int(raw_mv) != policy.mandate_version:
                raise BuzzSecurityError(
                    f"Webhook payload cannot override server mandate_version ({raw_mv} != {policy.mandate_version})"
                )

        has_pv, raw_pv = _get_explicit("policy_version")
        if has_pv and not policy.allow_payload_authority_override:
            if str(raw_pv) != policy.policy_version:
                raise BuzzSecurityError(
                    f"Webhook payload cannot override server policy_version ({raw_pv!r} != {policy.policy_version!r})"
                )

        requester = str(payload.get("requester") or context.get("requester") or "buzz").strip()
        if not requester or any(c in requester for c in ("\x00", "\r", "\n")):
            raise BuzzSecurityError("Invalid webhook requester identity")
        if policy.allowed_requesters is not None and requester not in policy.allowed_requesters:
            raise BuzzSecurityError(f"Unauthorized webhook requester: {requester!r}")

        has_scope, raw_scope = _get_explicit("authorized_scope")
        if has_scope:
            scope = str(raw_scope or "").strip()
            if scope not in policy.allowed_scopes:
                raise BuzzSecurityError(
                    f"Webhook requested unauthorized scope {scope!r}; allowed: {policy.allowed_scopes}"
                )
        else:
            scope = policy.default_authorized_scope

        has_caps, raw_caps = _get_explicit("permitted_capabilities")
        if has_caps:
            if not isinstance(raw_caps, (list, tuple)) or not raw_caps:
                raise BuzzSecurityError(
                    "Webhook permitted_capabilities must be a non-empty list of allowed strings"
                )
            caps = tuple(str(c).strip() for c in raw_caps)
            unauthorized_caps = [c for c in caps if not c or c not in policy.allowed_capabilities]
            if unauthorized_caps:
                raise BuzzSecurityError(
                    f"Webhook requested unauthorized capabilities: {unauthorized_caps}"
                )
        else:
            caps = policy.default_capabilities

        has_bounds, raw_bounds = _get_explicit("resource_boundaries")
        if has_bounds:
            if not isinstance(raw_bounds, (list, tuple)) or not raw_bounds:
                raise BuzzSecurityError(
                    "Webhook resource_boundaries must be a non-empty list of relative paths"
                )
            validated_bounds: list[str] = []
            for item in raw_bounds:
                b_str = str(item or "").strip()
                if (
                    not b_str
                    or b_str.startswith(("/", "~", "\\"))
                    or "*" in b_str
                    or "\x00" in b_str
                    or ".." in PurePath(b_str).parts
                ):
                    raise BuzzSecurityError(
                        f"Webhook requested forbidden resource boundary: {b_str!r}"
                    )
                if "." not in policy.allowed_resource_roots:
                    top = PurePath(b_str).parts[0] if PurePath(b_str).parts else ""
                    if top not in policy.allowed_resource_roots:
                        raise BuzzSecurityError(
                            f"Webhook resource boundary {b_str!r} is outside allowed roots {policy.allowed_resource_roots}"
                        )
                validated_bounds.append(b_str)
            bounds = tuple(validated_bounds)
        else:
            bounds = policy.default_resource_boundaries

        has_risk, raw_risk = _get_explicit("risk_classification")
        if has_risk:
            risk = str(raw_risk or "").strip().lower()
            if risk not in policy.allowed_risk_classifications or risk not in _RISK_LEVEL_ORDER:
                raise BuzzSecurityError(f"Invalid webhook risk_classification: {risk!r}")
            min_rank = _RISK_LEVEL_ORDER.get(policy.min_risk_classification, 2)
            if _RISK_LEVEL_ORDER[risk] < min_rank and not policy.allow_payload_authority_override:
                raise BuzzSecurityError(
                    f"Webhook cannot downgrade risk_classification to {risk!r} below {policy.min_risk_classification!r}"
                )
        else:
            risk = policy.default_risk_classification

        has_cost, raw_cost = _get_explicit("cost_budget")
        if has_cost:
            try:
                cost_budget = float(raw_cost)
            except (TypeError, ValueError) as exc:
                raise BuzzSecurityError(f"Invalid webhook cost_budget: {raw_cost!r}") from exc
            if not math.isfinite(cost_budget) or cost_budget <= 0.0:
                raise BuzzSecurityError(f"Webhook cost_budget must be finite and > 0 (got {cost_budget})")
            if cost_budget > policy.max_cost_budget and not policy.allow_payload_authority_override:
                raise BuzzSecurityError(
                    f"Webhook cost_budget {cost_budget} exceeds server ceiling {policy.max_cost_budget}"
                )
        else:
            cost_budget = policy.default_cost_budget

        has_retry, raw_retry = _get_explicit("retry_budget")
        if has_retry:
            if isinstance(raw_retry, bool):
                raise BuzzSecurityError("Invalid boolean retry_budget")
            try:
                retry_budget = int(raw_retry)
            except (TypeError, ValueError) as exc:
                raise BuzzSecurityError(f"Invalid webhook retry_budget: {raw_retry!r}") from exc
            if retry_budget <= 0:
                raise BuzzSecurityError(f"Webhook retry_budget must be > 0 (got {retry_budget})")
            if retry_budget > policy.max_retry_budget and not policy.allow_payload_authority_override:
                raise BuzzSecurityError(
                    f"Webhook retry_budget {retry_budget} exceeds server ceiling {policy.max_retry_budget}"
                )
        else:
            retry_budget = policy.default_retry_budget

        has_ver, raw_ver = _get_explicit("verification_requirements")
        if has_ver:
            ver_req = str(raw_ver or "").strip().lower()
            if ver_req not in policy.allowed_verification_profiles:
                raise BuzzSecurityError(
                    f"Webhook verification_requirements {ver_req!r} is not permitted; allowed: {policy.allowed_verification_profiles}"
                )
        else:
            ver_req = policy.default_verification_requirements

        workspace_id = str(payload.get("workspace_id") or context.get("workspace_id") or "default").strip()
        if not workspace_id or ".." in workspace_id or "/" in workspace_id or "\\" in workspace_id:
            raise BuzzSecurityError(f"Invalid workspace_id: {workspace_id!r}")

        return ImmutableMandate(
            ticket_id=ticket_id,
            source_id=source_id,
            event_id=event_id,
            requester=requester,
            authorized_scope=scope,
            workspace_id=workspace_id,
            mandate_version=policy.mandate_version,
            policy_version=policy.policy_version,
            accepted_at=str(time.time()),
            permitted_capabilities=caps,
            resource_boundaries=bounds,
            risk_classification=risk,
            cost_budget=cost_budget,
            retry_budget=retry_budget,
            verification_requirements=ver_req,
        )

    def admit_webhook_event(
        self,
        payload: dict[str, Any],
        *,
        source_id: str | None = None,
        allow_mission_id_fallback: bool = False,
    ) -> tuple[TicketRecord, bool]:
        """Admit a Buzz webhook event idempotently on ``(source_id, event_id)``.

        Enforces:
        - Durable ``outbox_store`` presence (fails closed with ``BuzzConfigError`` if absent)
        - Non-empty ``goal``/``text`` and explicit ``event_id`` (fails closed with ``ValueError``)
        - ``WebhookAuthorityPolicy`` on mandate fields (fails closed with ``BuzzSecurityError``)
        - SSRF validation on ``callback_url`` if provided
        """
        if self._outbox_store is None:
            raise BuzzConfigError(
                "BuzzAdapter.admit_webhook_event requires a durable outbox_store (SQLiteGoalStore)"
            )

        if not isinstance(payload, dict):
            raise ValueError("Webhook payload must be a dictionary")

        goal_text = str(payload.get("goal") or payload.get("text") or "").strip()
        if not goal_text:
            raise ValueError("BuzzPayload missing 'goal' field")

        raw_ctx = payload.get("context")
        context: dict[str, Any] = raw_ctx if isinstance(raw_ctx, dict) else {}

        callback_url = payload.get("callback_url")
        if callback_url is not None:
            validate_callback_destination(
                str(callback_url),
                policy=self._authority_policy,
                strict_dns=False,
            )

        eff_source = str(
            source_id
            or payload.get("source_id")
            or context.get("source_id")
            or "buzz_webhook"
        ).strip()
        if not eff_source:
            raise ValueError("Webhook payload missing valid 'source_id'")

        raw_event_id = payload.get("event_id") if "event_id" in payload else context.get("event_id")
        if raw_event_id is None and allow_mission_id_fallback:
            raw_event_id = payload.get("mission_id")
        eff_event = str(raw_event_id or "").strip()
        if not eff_event:
            raise ValueError("Webhook payload missing required 'event_id'")

        goal_id = str(payload.get("goal_id") or payload.get("mission_id") or f"goal_{eff_event}")
        thread_id = str(payload.get("thread_id") or context.get("thread_id") or eff_event)
        det_hash = hashlib.sha256(f"{eff_source}:{eff_event}".encode("utf-8")).hexdigest()[:16]
        ticket_id = str(payload.get("ticket_id") or f"tkt_{det_hash}")

        mandate = self._build_validated_mandate(
            payload,
            ticket_id=ticket_id,
            source_id=eff_source,
            event_id=eff_event,
        )
        admitted = self._outbox_store.admit_ticket(
            goal_id=goal_id,
            mandate=mandate,
            thread_id=thread_id,
        )
        deduplicated = bool(admitted.get("deduplicated", False))
        created = not deduplicated
        truth_raw = str(admitted.get("truth_status", ExecutionTruthStatus.PLANNED.value))
        truth_enum = (
            ExecutionTruthStatus(truth_raw)
            if truth_raw in ExecutionTruthStatus._value2member_map_
            else ExecutionTruthStatus.PLANNED
        )
        record = TicketRecord(
            ticket_id=str(admitted["ticket_id"]),
            goal_id=str(admitted["goal_id"]),
            mandate=mandate,
            truth_status=truth_enum,
            thread_id=admitted.get("thread_id"),
            measured_tokens=admitted.get("measured_tokens"),
            estimated_tokens=admitted.get("estimated_tokens"),
            actual_cost=admitted.get("actual_cost"),
            estimated_cost=admitted.get("estimated_cost"),
            cost_status=str(admitted.get("cost_status", "UNKNOWN")),
        )
        return record, created

    def receive_goal(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Parse an inbound Buzz webhook payload into a normalized goal dict.

        Raises ``ValueError`` if ``goal`` (or ``text`` fallback) is missing or empty,
        and ``BuzzSecurityError`` if ``callback_url`` violates SSRF policy.
        """
        goal_text = payload.get("goal") or payload.get("text") or ""
        if not goal_text or not str(goal_text).strip():
            raise ValueError("BuzzPayload missing 'goal' field")

        callback_url = payload.get("callback_url")
        if callback_url is not None:
            validate_callback_destination(
                str(callback_url),
                policy=self._authority_policy,
                strict_dns=False,
            )

        bp = BuzzPayload(
            goal_text=str(goal_text).strip(),
            context=payload.get("context", {}),
            callback_url=callback_url,
            mission_id=payload.get("mission_id"),
        )
        return {
            "text": bp.goal_text,
            "context": bp.context,
            "callback_url": bp.callback_url,
            "mission_id": bp.mission_id,
        }

    def send_update(
        self,
        status: str,
        data: dict[str, Any],
        *,
        callback_url: str | None = None,
        ticket_id: str | None = None,
        source_id: str = "buzz_webhook",
        thread_id: str = "default",
        idempotency_key: str | None = None,
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        """Format and (when ``callback_url`` is given) POST a status update back to Buzz.

        When ``self._outbox_store`` is configured, persists the outbound report in
        ``report_outbox`` first and updates its delivery state (``SENT``, ``FAILED_RETRYABLE``,
        or ``DEAD_LETTER``) after attempting transport delivery.
        """
        update: dict[str, Any] = {"status": status, "data": data}
        if callback_url is not None:
            validate_callback_destination(
                callback_url,
                policy=self._authority_policy,
                strict_dns=False,
            )

        if self._outbox_store is not None and (callback_url or ticket_id):
            eff_ticket = ticket_id or "tkt_untracked"
            idem_key = idempotency_key or (
                hashlib.sha256(
                    f"{eff_ticket}:{source_id}:{thread_id}:{status}:{json.dumps(data, sort_keys=True, default=str)}".encode(
                        "utf-8"
                    )
                ).hexdigest()
            )
            entry = OutboxEntry(
                outbox_id=new_id("outbox"),
                ticket_id=eff_ticket,
                source_id=source_id,
                thread_id=thread_id,
                idempotency_key=idem_key,
                payload_json=json.dumps(update, default=str),
                max_attempts=max_attempts,
            )
            enqueued = self._outbox_store.enqueue_outbox(entry, callback_url=callback_url)
            outbox_id = str(enqueued["outbox_id"])
            deduplicated = bool(enqueued.get("deduplicated", False))
            if deduplicated:
                update["outbox_id"] = outbox_id
                update["delivery_status"] = enqueued["delivery_status"]
                update["deduplicated"] = True
                update["attempts"] = int(enqueued.get("attempts", 0))
                return update
            if callback_url:
                if self._transport is None:
                    raise BuzzConfigError(
                        "BuzzAdapter has no transport wired; cannot deliver to callback_url="
                        f"{callback_url!r}"
                    )
                delivered = self._outbox_store.process_outbox_delivery(
                    outbox_id,
                    self._transport,
                )
                update["outbox_id"] = outbox_id
                update["delivery_status"] = delivered["delivery_status"]
                update["deduplicated"] = False
                update["attempts"] = int(delivered.get("attempts", 1))
            else:
                update["outbox_id"] = outbox_id
                update["delivery_status"] = enqueued["delivery_status"]
                update["deduplicated"] = False
                update["attempts"] = int(enqueued.get("attempts", 0))
            return update

        if callback_url:
            if self._transport is None:
                raise BuzzConfigError(
                    "BuzzAdapter has no transport wired; cannot deliver to callback_url="
                    f"{callback_url!r}"
                )
            try:
                code = self._transport(callback_url, update)
                if code >= 400:
                    logger.warning(
                        "Buzz callback to %s returned HTTP %s for status=%s",
                        callback_url, code, status,
                    )
            except BuzzSecurityError:
                raise
            except Exception as exc:
                logger.warning(
                    "Buzz transport raised %s delivering status=%s to %s: %s",
                    type(exc).__name__, status, callback_url, exc,
                )
        return update

    def receive_feedback(self, feedback: dict[str, Any]) -> dict[str, Any]:
        """Accept post-execution feedback from Buzz (ratings, comments, corrections)."""
        return dict(feedback)

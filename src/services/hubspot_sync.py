"""HubSpot CRM sync service — REST client, stdlib only.

Uses urllib + Bearer API key or private app token (read from HUBSPOT_API_KEY env var or config/crm.yaml).
Operations:
  - upsert_contact(email, properties) -> dict (contact id or dry-run placeholder)
  - create_deal(email, deal_name, stage, amount, pipeline) -> None

Idempotent on HubSpot side (upsert uses existing contact match).

Configuration:
  - HUBSPOT_API_KEY env var is the primary credential source (preferred).
  - config/crm.yaml is checked as fallback if env var is absent.

Contract:
  - All HubSpot failures are logged, never raised (best-effort).
  - No secrets logged; HubSpot endpoint/logic errors reported at warning level only.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_HUBSPOT_API_BASE = "https://api.hubapi.com"

_CONTACTS_SEARCH_URL = f"{_HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
_CONTACTS_URL = f"{_HUBSPOT_API_BASE}/crm/v3/objects/contacts"
_DEALS_URL = f"{_HUBSPOT_API_BASE}/crm/v3/objects/deals"
_DEALS_SEARCH_URL = f"{_HUBSPOT_API_BASE}/crm/v3/objects/deals/search"

_PIPELINES_URL = f"{_HUBSPOT_API_BASE}/crm/v3/pipelines/deals"
_TIMEOUT_SECONDS = 15


class HubSpotError(Exception):
    """Raised on non-2xx HubSpot response."""

    def __init__(self, message: str, status_code: int = 0) -> None:
        self.status_code = status_code
        super().__init__(message)


def _api_key() -> str:
    """Read HubSpot API key: env var first, then config/crm.yaml as fallback."""
    key = os.getenv("HUBSPOT_API_KEY")
    if key:
        return key
    # Fallback: parse config/crm.yaml (stdlib YAML not available, parse a tiny subset).
    candidates = [
        os.path.join(os.getcwd(), "config", "crm.yaml"),
        os.path.join(os.path.dirname(__file__), "..", "..", "config", "crm.yaml"),
    ]
    import pathlib as _pathlib

    for candidate in candidates:
        try:
            text = _pathlib.Path(candidate).read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("api_key:"):
                    value = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    if value and "${" not in value:
                        return value
        except (OSError, ValueError):
            continue
    raise RuntimeError(
        "HUBSPOT_API_KEY env var is required. Set it or add to config/crm.yaml."
    )


def _auth_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json; charset=utf-8",
    }


def _post(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=body_bytes,
        headers=_auth_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            resp_body = resp.read().decode("utf-8")
            try:
                return json.loads(resp_body)
            except json.JSONDecodeError:
                return {"status": resp.status}
    except urllib.error.HTTPError as exc:
        error_body = ""
        if exc.fp:
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                pass
        message = f"HubSpot API error {exc.code}: {error_body[:400]}"
        logger.warning(message)
        raise HubSpotError(message, status_code=exc.code) from exc
    except (urllib.error.URLError, OSError) as exc:
        message = f"HubSpot network error: {exc}"
        logger.warning(message)
        raise HubSpotError(message) from exc


def _patch(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=body_bytes,
        headers=_auth_headers(),
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            resp_body = resp.read().decode("utf-8")
            try:
                return json.loads(resp_body)
            except json.JSONDecodeError:
                return {"status": resp.status}
    except urllib.error.HTTPError as exc:
        error_body = ""
        if exc.fp:
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                pass
        message = f"HubSpot API error {exc.code}: {error_body[:400]}"
        logger.warning(message)
        raise HubSpotError(message, status_code=exc.code) from exc
    except (urllib.error.URLError, OSError) as exc:
        message = f"HubSpot network error: {exc}"
        logger.warning(message)
        raise HubSpotError(message) from exc


def _find_contact_id(email: str) -> Optional[str]:
    filter_payload: Dict[str, Any] = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email,
                    }
                ]
            }
        ],
        "properties": ["email"],
        "limit": 1,
    }
    try:
        data = _post(_CONTACTS_SEARCH_URL, filter_payload)
        results = data.get("results", [])
        if not results:
            return None
        return str(results[0].get("id", "")) or None
    except HubSpotError as exc:
        logger.warning("_find_contact_id failed for %s: %s", email, exc)
        return None


def _find_deal_id(email: str, pipeline: str) -> Optional[str]:
    pipeline_id = _resolve_pipeline_id(pipeline)
    if not pipeline_id:
        return None
    filter_payload: Dict[str, Any] = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "dealname",
                        "operator": "CONTAINS_TOKEN",
                        "value": email,
                    },
                    {
                        "propertyName": "pipeline",
                        "operator": "EQ",
                        "value": pipeline_id,
                    },
                ]
            }
        ],
        "properties": ["dealname", "pipeline", "dealstage"],
        "limit": 1,
    }
    try:
        data = _post(_DEALS_SEARCH_URL, filter_payload)
        results = data.get("results", [])
        if not results:
            return None
        return str(results[0].get("id", "")) or None
    except HubSpotError as exc:
        logger.warning("_find_deal_id failed for %s: %s", email, exc)
        return None


def _resolve_pipeline_id(name: str) -> Optional[str]:
    try:
        data = _post(_PIPELINES_URL + "?limit=20", {})
        pipelines = data.get("results", [])
        for p in pipelines:
            if p.get("label") == name or p.get("id") == name:
                return str(p.get("id", "")) or None
    except HubSpotError as exc:
        logger.warning("_resolve_pipeline_id failed: %s", exc)
    return None


def upsert_contact(email: str, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Upsert a HubSpot contact by email. Returns the HubSpot response body.

    Args:
        email: contact email (used for lookup + set as idProperty).
        properties: dict of HubSpot contact properties (e.g. firstname, lastname,
                    hs_lead_status, lifecycle_stage, company).

    Returns:
        HubSpot API JSON response with at least an 'id' field on success,
        or a dry-run placeholder ({id: 'dry-run'}) when HUBSPOT_API_KEY is unset.
    """
    properties = properties or {}
    try:
        _api_key()
    except RuntimeError:
        logger.info("HUBSPOT_API_KEY not set; skipping contact upsert for %s", email)
        return {"id": "dry-run"}

    existing_id = _find_contact_id(email)
    if existing_id:
        return _patch(
            f"{_CONTACTS_URL}/{existing_id}",
            {"properties": properties},
        )
    props_with_email = {"email": email, **properties}
    return _post(
        _CONTACTS_URL,
        {
            "properties": props_with_email,
            " Associations": [],
        },
    )


def create_deal(
    email: str,
    deal_name: str,
    stage: str,
    amount: Optional[float] = None,
    pipeline: str = "Mekong Pipeline",
    properties: Optional[Dict[str, Any]] = None,
) -> None:
    """Create a HubSpot deal (idempotent: skips if deal for the same email/pipeline exists).

    Args:
        email: owner email used in deal name and idempotency lookup.
        deal_name: HubSpot dealname field value.
        stage: HubSpot dealstage value (e.g. 'qualifiedtobuy', 'contractsent', 'closedwon').
        amount: monetary value in USD (stringified on send).
        pipeline: pipeline label (defaults to 'Mekong Pipeline').
        properties: extra arbitrary properties overrides.

    Side effects:
        Calls HubSpot CRM create-deal endpoint; skipped if duplicate found.
    """
    try:
        _api_key()
    except RuntimeError:
        logger.info("HUBSPOT_API_KEY not set; skipping deal creation for %s", email)
        return
    existing = _find_deal_id(email, pipeline)
    if existing:
        logger.info("Deal already exists (id=%s) for %s in pipeline '%s', skipping", existing, email, pipeline)
        return
    contact_id = _find_contact_id(email)
    if not contact_id:
        logger.warning("Cannot create deal for %s: contact not found in HubSpot", email)
        return
    pipeline_id = _resolve_pipeline_id(pipeline)
    if not pipeline_id:
        logger.warning("Cannot create deal for %s: pipeline '%s' not found", email, pipeline)
        return
    deal_payload: Dict[str, Any] = {
        "properties": {
            "dealname": deal_name,
            "dealstage": stage,
            "pipeline": pipeline_id,
            **({"amount": str(amount)} if amount is not None else {}),
            **(properties or {}),
        },
        "associations": [
            {
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
                "to": [{"id": contact_id}],
            }
        ],
    }
    _post(_DEALS_URL, deal_payload)
    logger.info("Created HubSpot deal '%s' for %s (stage=%s)", deal_name, email, stage)

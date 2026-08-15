#!/usr/bin/env python3
"""VN Pilot Drip Scanner — find pilots due for Day-3/7/14 emails.

Usage:
    python3 scripts/cron/vn-drip-scan.py [--dry-run] [--base-url http://localhost:8000]

Reads pilot records from MEKONG_PILOT_DIR (default: ~/.mekong/),
computes days since onboarding, and fires POST /v1/pilot/drip-trigger
for each pilot hitting a drip milestone (3, 7, or 14 days).

Idempotent by caller design: this script does NOT track sent days.
Operator should run once per day; the endpoint handles the rest.

Exit codes:
    0 — success (all sent or dry-run)
    1 — partial failure (some endpoints returned non-2xx)
    2 — fatal error (cannot read pilots, cannot reach API)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("vn-drip-scan")

CONFIG_DIR = Path(os.getenv("MEKONG_PILOT_DIR", str(Path.home() / ".mekong")))
PILOTS_FILE = CONFIG_DIR / "pilots.jsonl"
DRIP_DAYS = (3, 7, 14)


def load_pilots() -> list[dict]:
    if not PILOTS_FILE.exists():
        logger.warning("Pilots file not found: %s", PILOTS_FILE)
        return []
    records: list[dict] = []
    with PILOTS_FILE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def days_since(iso_ts: str) -> int:
    try:
        onboarded = datetime.fromisoformat(iso_ts).date()
        return (datetime.now(timezone.utc).date() - onboarded).days
    except (ValueError, TypeError):
        return -1


def log_outreach(base_url: str, user_id: str, dry_run: bool) -> bool:
    """Log founder contact event after Day-14 drip email is sent."""
    url = f"{base_url.rstrip('/')}/v1/pilot/outreach/log"
    payload = json.dumps({
        "user_id": user_id,
        "channel": "email",
        "day_offset": 14,
        "outcome": "sent",
    }).encode("utf-8")
    req = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if dry_run:
        logger.info("[dry-run] POST %s → %s", url, payload.decode())
        return True
    try:
        with urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            logger.info(
                "Outreach logged user_id=%s channel=%s ts=%s",
                user_id, body.get("channel", "?"), body.get("ts", "?"),
            )
            return resp.status == 200
    except URLError as exc:
        logger.error("POST %s failed: %s", url, exc)
        return False


def fire_drip(base_url: str, user_id: str, drip_day: int, dry_run: bool) -> bool:
    url = f"{base_url.rstrip('/')}/v1/pilot/drip-trigger"
    payload = json.dumps({
        "user_id": user_id,
        "drip_day": drip_day,
        "background": True,
    }).encode("utf-8")
    req = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if dry_run:
        logger.info("[dry-run] POST %s → %s", url, payload.decode())
        return True
    try:
        with urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            logger.info(
                "POST %s → %d user_id=%s day=%d sent=%s",
                url,
                resp.status,
                user_id,
                drip_day,
                body.get("sent", "?"),
            )
            success = resp.status == 200 and body.get("sent")
            # After successful Day-14 drip, log founder outreach so
            # subsequent Day-14 emails don't re-show the Zalo CTA.
            if success and drip_day == 14:
                log_outreach(base_url, user_id, dry_run)
            return success
    except URLError as exc:
        logger.error("POST %s failed: %s", url, exc)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="VN Pilot drip email scanner")
    parser.add_argument("--dry-run", action="store_true", help="Log only, do not fire")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Gateway URL")
    args = parser.parse_args()

    pilots = load_pilots()
    if not pilots:
        logger.info("No pilots found — nothing to do")
        return 0

    today = datetime.now(timezone.utc).date()
    fired = 0
    failed = 0

    for pilot in pilots:
        user_id = pilot.get("user_id", "")
        if not user_id.startswith("opc_"):
            continue
        onboarded = pilot.get("onboarded_at", "")
        elapsed = days_since(onboarded)
        if elapsed < 0:
            continue
        if elapsed > 14:
            continue  # beyond drip window

        matching_days = [d for d in DRIP_DAYS if d <= elapsed]
        for day in matching_days:
            email = pilot.get("email")
            if not email:
                logger.warning("Pilot %s has no email — skipping drip day %d", user_id, day)
                continue
            logger.info(
                "Pilot %s (%s) elapsed=%d days → firing day-%d drip",
                user_id,
                pilot.get("name", "?"),
                elapsed,
                day,
            )
            ok = fire_drip(args.base_url, user_id, day, args.dry_run)
            if ok:
                fired += 1
            else:
                failed += 1

    logger.info("Summary: %d sent, %d failed", fired, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

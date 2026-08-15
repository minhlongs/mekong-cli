#!/usr/bin/env python3
"""VN Pilot Outreach CLI — track Zalo outreach to pilot users.

Tracks who was contacted, when, and the outcome so the founder can
systematically work through the pilot list before trial expiry.

Usage:
    python3 scripts/outreach.py list [--due-in 3] [--status active|all]
    python3 scripts/outreach.py contact OPCH123 --channel zalo --day 7
    python3 scripts/outreach.py respond OPCH123 --outcome interested
    python3 scripts/outreach.py convert OPCH123 --tier starter_vnd --vnd 199000

Storage: ~/.mekong/outreach.jsonl (append-only, one record per event)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".mekong"
OUTREACH_FILE = CONFIG_DIR / "outreach.jsonl"
PILOTS_FILE = CONFIG_DIR / "pilots.jsonl"

_DEFAULT_MESSAGES = {
    3: "Chào {name}, bạn đã dùng Mekong Hub được 3 ngày rồi. Mình thấy bạn chưa thử tính năng Zalo auto-reply — mình setup 1:1 free cho bạn trong 15 phút được không? 😊",
    7: "Chào {name}, tuần đầu với Mekong Hub thế nào? Mình muốn hỏi xem bạn gặp khó khăn gì không — mình giúp bạn tối ưu workflow.",
    14: "Chào {name}, bạn đã dùng Mekong Hub 2 tuần. Mình có ưu đãi đặc biệt cho người dùng tích cực — chuyển sang gói trả phí chỉ 199K/tháng, giữ nguyên 50 credits miễn phí thêm 1 tháng. Bạn interested không?",
}


def load_pilots() -> list[dict]:
    if not PILOTS_FILE.exists():
        return []
    records = []
    for line in PILOTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def load_events() -> list[dict]:
    if not OUTREACH_FILE.exists():
        return []
    return [json.loads(l) for l in OUTREACH_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]


def days_until_due(pilot: dict) -> int:
    try:
        end = date.fromisoformat(pilot["pilot_end_at"][:10])
        return (end - date.today()).days
    except (ValueError, KeyError, TypeError):
        return 999


def list_pilots(status: str, due_in: int):
    pilots = load_pilots()
    events = load_events()
    latest_contact = {}
    for e in events:
        uid = e.get("user_id")
        if uid and e.get("type") == "contact":
            ts = e.get("ts", "")
            if uid not in latest_contact or ts > latest_contact[uid].get("ts", ""):
                latest_contact[uid] = e

    rows = []
    for p in pilots:
        uid = p.get("user_id", "")
        if not uid.startswith("opc_"):
            continue
        due = days_until_due(p)
        if due < 0:
            st = "expired"
        elif due <= 7:
            st = "urgent"
        else:
            st = "active"

        if status == "active" and st not in ("active", "urgent"):
            continue
        if due_in and due > due_in:
            continue

        last = latest_contact.get(uid)
        rows.append({
            "user_id": uid,
            "name": p.get("name", "?"),
            "business": p.get("business_type", "?"),
            "city": p.get("city", "?"),
            "pilot_end": p.get("pilot_end_at", "?")[:10],
            "days_left": due,
            "status": st,
            "last_contact": last.get("ts", "")[:10] if last else "-",
            "last_outcome": last.get("outcome", "-") if last else "-",
        })

    rows.sort(key=lambda r: r["days_left"])
    return rows


def record_event(evt: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    evt.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    with OUTREACH_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")
    print(f"Recorded: {evt['type']} {evt.get('user_id', '?')} at {evt['ts']}")


def cmd_list(args):
    rows = list_pilots(args.status, args.due_in)
    if not rows:
        print("No pilots match filter.")
        return
    fmt = "{:<14} {:<20} {:<12} {:<10} {:<10}"
    print(fmt.format("USER_ID", "NAME", "BUSINESS", "ENDS", "LEFT"))
    print("-" * 70)
    for r in rows:
        print(fmt.format(r["user_id"], r["name"][:18], r["business"], r["pilot_end"], f"{r['days_left']}d"))


def cmd_contact(args):
    pilots = load_pilots()
    pilot = next((p for p in pilots if p.get("user_id") == args.user_id), None)
    if not pilot:
        print(f"User {args.user_id} not found.", file=sys.stderr)
        sys.exit(1)

    due = days_until_due(pilot)
    template = args.message or _DEFAULT_MESSAGES.get(args.day, "Chào {name}!")
    message = template.format(name=pilot.get("name", "bạn"))

    print(f"\n--- Outreach to {pilot.get('name')} ---")
    print(f"Channel : {args.channel}")
    print(f"Day     : {args.day}")
    print(f"Due in  : {due} days (ends {pilot.get('pilot_end_at','')[:10]})")
    print(f"\nMessage:\n{message}\n")

    if args.dry_run:
        print("[dry-run] not recording")
        return

    record_event({
        "type": "contact",
        "user_id": args.user_id,
        "channel": args.channel,
        "day": args.day,
        "message": message,
        "outcome": "sent",
    })


def cmd_respond(args):
    record_event({
        "type": "response",
        "user_id": args.user_id,
        "outcome": args.outcome,
        "notes": args.notes or "",
    })


def cmd_convert(args):
    record_event({
        "type": "conversion",
        "user_id": args.user_id,
        "tier": args.tier,
        "monthly_vnd": args.vnd,
        "notes": args.notes or "",
    })
    print(f"Recorded conversion for {args.user_id}: {args.tier} = {args.vnd:,} VND")


def main():
    parser = argparse.ArgumentParser(description="VN Pilot Outreach Tracker")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="List pilots filtered by status")
    p_list.add_argument("--status", default="all", choices=["active", "urgent", "all"])
    p_list.add_argument("--due-in", type=int, default=0, help="Only show pilots due within N days")

    p_contact = sub.add_parser("contact", help="Record outreach to a pilot")
    p_contact.add_argument("user_id")
    p_contact.add_argument("--channel", default="zalo", choices=["zalo", "phone", "email"])
    p_contact.add_argument("--day", type=int, default=7, choices=[3, 7, 14])
    p_contact.add_argument("--message", help="Custom message (overrides template)")
    p_contact.add_argument("--dry-run", action="store_true")

    p_resp = sub.add_parser("respond", help="Record pilot response")
    p_resp.add_argument("user_id")
    p_resp.add_argument("--outcome", required=True, choices=["interested", "not_interested", "no_reply", "callback"])
    p_resp.add_argument("--notes", default="")

    p_conv = sub.add_parser("convert", help="Record conversion")
    p_conv.add_argument("user_id")
    p_conv.add_argument("--tier", default="starter_vnd")
    p_conv.add_argument("--vnd", type=int, default=199000)
    p_conv.add_argument("--notes", default="")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    {"list": cmd_list, "contact": cmd_contact, "respond": cmd_respond, "convert": cmd_convert}[args.cmd](args)


if __name__ == "__main__":
    main()

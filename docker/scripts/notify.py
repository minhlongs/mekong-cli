#!/usr/bin/env python3
"""Mekong CLI — PEV Pipeline Notification Script
Events: stop, error, plan.complete, execute.complete, verify.pass, verify.fail, cook.done
"""

import os
import sys


def main():
    flag_file = "/home/claude/.claude/notify-on"
    if not os.path.isfile(flag_file):
        sys.exit(0)

    urls = []
    for key, value in os.environ.items():
        if not key.startswith("NOTIFY_"):
            continue
        if not value or not value.strip():
            continue
        if key == "NOTIFY_URLS":
            urls.extend(u.strip() for u in value.split(",") if u.strip())
        else:
            urls.append(value.strip())

    if not urls:
        sys.exit(0)

    event = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    events = {
        "stop":             ("Mekong CLI — Task Complete",       "Claude finished the current task.",                "info"),
        "error":            ("Mekong CLI — Error",               "A tool use failure occurred.",                     "warning"),
        "plan.complete":    ("Mekong CLI — Plan Ready",          "PEV plan phase completed. Review the plan.",      "info"),
        "execute.complete": ("Mekong CLI — Execution Done",      "All steps executed. Verifying results...",         "info"),
        "verify.pass":      ("Mekong CLI — Verified",            "All quality gates passed.",                        "success"),
        "verify.fail":      ("Mekong CLI — Verification Failed", "Quality gates failed. Check the output.",         "failure"),
        "cook.done":        ("Mekong CLI — Mission Complete",    "Full PEV pipeline finished successfully.",         "success"),
    }
    title, body, notify_type = events.get(event, ("Mekong CLI", f"Event: {event}", "info"))

    try:
        import apprise
        ap = apprise.Apprise()
        for url in urls:
            ap.add(url)
        ap.notify(title=title, body=body, notify_type=notify_type)
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()

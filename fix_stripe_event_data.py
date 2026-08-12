#!/usr/bin/env python3
"""Fix remaining event.get() on Stripe event object."""
p = "src/api/billing_endpoints.py"
with open(p) as f:
    src = f.read()

# Only remaining event.get() call that's broken
old = 'event.get("data", {}).get("object", {})'
new = '(event["data"]["object"] if "data" in event else {})'

if old not in src:
    print(f"MISSING: {old!r}")
    # Try to find it with different whitespace
    import re
    for m in re.finditer(r'event\.get\(', src):
        start = max(0, m.start()-10)
        end = min(len(src), m.end()+50)
        print(f"  offset {m.start()}: {src[start:end]}")
else:
    src = src.replace(old, new, 1)
    print("patched event.get('data')")
    with open(p, "w") as f:
        f.write(src)

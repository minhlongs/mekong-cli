#!/usr/bin/env python3
"""Fix billing_endpoints.py: event.get() -> event[key] for StripeObject compat."""
p = "src/api/billing_endpoints.py"
with open(p) as f:
    src = f.read()

# Fix both .get() calls on stripe event objects
fixes = [
    ('event.get("type", "unknown")', 'event["type"] if "type" in event else "unknown"'),
    ('event.get("id", "")', 'event["id"] if "id" in event else ""'),
]

for old, new in fixes:
    if old not in src:
        print(f"MISSING: {old!r}")
    else:
        src = src.replace(old, new, 1)
        print(f"patched: {old!r}")

with open(p, "w") as f:
    f.write(src)

# Also check for other .get() usage on the event variable downstream
import re
for m in re.finditer(r'event\.get\(', src):
    start = max(0, m.start()-20)
    end = min(len(src), m.end()+40)
    print(f"REMAINING event.get at offset {m.start()}: ...{src[start:end]}...")

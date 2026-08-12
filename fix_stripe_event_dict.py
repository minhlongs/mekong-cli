#!/usr/bin/env python3
"""Fix: add .to_dict() to construct_event return so the rest of the code
(which uses .get(), .keys(), etc.) works on the resulting plain dict."""
p = "src/api/billing_endpoints.py"
with open(p) as f:
    src = f.read()

old = 'event = stripe_sdk.Webhook.construct_event(body, sig, webhook_secret)'
new = 'event = stripe_sdk.Webhook.construct_event(body, sig, webhook_secret).to_dict()'

if old not in src:
    print("MISSING:", old)
else:
    src = src.replace(old, new, 1)
    print("patched")
    with open(p, "w") as f:
        f.write(src)

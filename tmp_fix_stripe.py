#!/usr/bin/env python3
"""Fix test_stripe_webhooks.py — revert over-broad status changes, keep signature fix."""

path = "tests/e2e/api/test_stripe_webhooks.py"
with open(path) as f:
    src = f.read()

# Restore 200/404 where we had 200/401 (keep _generate_signature fix + valid→200 + invalid→401)
src = src.replace(
    "assert response.status_code in [200, 401]",
    "assert response.status_code in [200, 404]"
)

with open(path, "w") as f:
    f.write(src)

print("Reverted over-broad status code changes in stripe tests")

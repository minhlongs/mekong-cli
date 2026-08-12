from pathlib import Path

path = Path('/Users/macbook/mekong-cli/src/api/billing_endpoints.py')
text = path.read_text()

OLD = """ # Signal evaluator on trial lifecycle events (grace window)
 if is_trialing:
  evaluate_trial(
   tenant_id=tenant_id,
   customer_id=customer_id,
  )
 elif credits:
  CreditStore().add_credits(
   tenant_id=tenant_id,
   amount=credits,
   reason=f"stripe:{event_type}:{event_id}",
   idempotency_key=event_id,
  )
 credits_provisioned = credits
 logger.info(
  "Provisioned %d credits for tenant %s (tier=%s, event=%s)",
  credits, tenant_id, tier_key, event_type,
 )"""

NEW = """  # Signal evaluator on trial lifecycle events (grace window)
  if is_trialing:
   evaluate_trial(
    tenant_id=tenant_id,
    customer_id=customer_id,
   )
  elif credits:
   CreditStore().add_credits(
    tenant_id=tenant_id,
    amount=credits,
    reason=f"stripe:{event_type}:{event_id}",
    idempotency_key=event_id,
   )
  credits_provisioned = credits
  logger.info(
   "Provisioned %d credits for tenant %s (tier=%s, event=%s)",
   credits, tenant_id, tier_key, event_type,
  )"""

if OLD in text:
    new_text = text.replace(OLD, NEW, 1)
    path.write_text(new_text)
    print("OK: patched")
else:
    print("FAIL: pattern not found")
    idx = text.find("# Signal evaluator")
    print(repr(text[idx-4:idx+400]))

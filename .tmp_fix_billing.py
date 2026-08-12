from pathlib import Path
path = Path('/Users/macbook/mekong-cli/src/api/billing_endpoints.py')
text = path.read_text()

old = '''tenant_id = customer_id
# Find tenant_id from the customer's email
customer = await stripe_service._get_customer_by_id(customer_id)
if customer:
    user_repo = UserRepository()
    user = await user_repo.find_by_email(customer.email)
    if user:
        tenant_id = str(user.id)

# Signal evaluator on trial lifecycle events (grace window)
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
)'''

new = '''tenant_id = customer_id
# Find tenant_id from the customer's email
customer = await stripe_service._get_customer_by_id(customer_id)
if customer:
    user_repo = UserRepository()
    user = await user_repo.find_by_email(customer.email)
    if user:
        tenant_id = str(user.id)

    # Signal evaluator on trial lifecycle events (grace window)
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
    )'''

if old not in text:
    print('ERROR: old string not found')
    # find what's near "Find tenant_id"
    idx = text.find('Find tenant_id')
    print(repr(text[idx:idx+120]))
else:
    text = text.replace(old, new, 1)
    path.write_text(text)
    print('OK: indentation fixed')

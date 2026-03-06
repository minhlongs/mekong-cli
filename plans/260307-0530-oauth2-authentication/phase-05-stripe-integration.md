---
title: "Phase 5: Stripe Integration"
priority: P2
status: pending
effort: 2h
---

# Phase 5: Stripe Customer Integration

## Context

- **Link to Plan:** [plan.md](plan.md)
- **Phase 4:** [phase-04-rbac-system.md](phase-04-rbac-system.md)
- **Existing:** Stripe integration in `src/lib/stripe_client.py`

## Overview

Sync Stripe Customer data with User records and auto-provision roles from subscription tier.

## Key Insights

- Stripe Customer ID linked to User via metadata
- Subscription tier determines role
- Webhooks update roles on subscription changes

## Requirements

### Functional
- Link Stripe Customer → User
- Auto-provision roles from subscription tier
- Webhook handler for role updates
- Customer ownership mapping

### Non-functional
- Role sync within 5 minutes of subscription change
- Idempotent webhook handling
- Audit trail for role changes

## Architecture

```
Subscription Tier → Role Mapping:
┌──────────────────────┬─────────────────────────────┐
│ Stripe Price ID      │ Provisioned Role            │
├──────────────────────┼─────────────────────────────┤
│ price_viewer_monthly │ viewer                      │
│ price_member_monthly │ member                      │
│ price_admin_monthly  │ admin                       │
│ price_owner_monthly  │ owner                       │
│ *cancelled*          │ viewer (downgrade)          │
└──────────────────────┴─────────────────────────────┘

Data Flow:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Stripe    │────▶│  Webhook    │────▶│   License   │
│  Subscription│     │  Handler    │     │   Update    │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Implementation Steps

1. **Add Stripe Customer mapping** `src/models/user.py`
   ```python
   class User(Base):
       # ... existing fields
       stripe_customer_id = Column(String, unique=True, index=True)
   ```

2. **Create role mapping config** `src/stripe/role_mapping.py`
   ```python
   from src.auth.rbac_config import Role

   SUBSCRIPTION_TO_ROLE = {
       "price_viewer_monthly": Role.VIEWER,
       "price_member_monthly": Role.MEMBER,
       "price_admin_monthly": Role.ADMIN,
       "price_owner_monthly": Role.OWNER,
   }

   def get_role_for_price(price_id: str) -> Role:
       return SUBSCRIPTION_TO_ROLE.get(price_id, Role.MEMBER)
   ```

3. **Create Stripe sync service** `src/stripe/sync_service.py`
   ```python
   import stripe
   from src.stripe.role_mapping import get_role_for_price

   class StripeSyncService:
       async def sync_customer(self, stripe_customer_id: str, user_id: UUID):
           """Link Stripe Customer to User."""
           customer = await stripe.Customer.retrieve(stripe_customer_id)
           user = await User.get(user_id)
           user.stripe_customer_id = stripe_customer_id
           await user.save()

       async def sync_subscription(self, user_id: UUID):
           """Sync subscription status and update role."""
           user = await User.get(user_id)
           if not user.stripe_customer_id:
               return

           subscriptions = await stripe.Subscription.list(
               customer=user.stripe_customer_id
           )

           if subscriptions.data:
               sub = subscriptions.data[0]
               price_id = sub.items.data[0].price.id
               role = get_role_for_price(price_id)

               license = await License.get_by_user_id(user_id)
               if license:
                   license.role = role.value
                   await license.save()
   ```

4. **Create webhook handler** `src/api/routes/stripe_webhook.py`
   ```python
   from stripe.error import SignatureVerificationError

   @router.post("/webhook/stripe")
   async def stripe_webhook(request: Request):
       payload = await request.body()
       sig_header = request.headers.get("stripe-signature")

       try:
           event = stripe.Webhook.construct_event(
               payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
           )
       except SignatureVerificationError:
           raise HTTPException(status_code=400, detail="Invalid signature")

       sync_service = StripeSyncService()

       if event["type"] == "customer.subscription.updated":
           # Find user by customer ID
           customer_id = event["data"]["object"]["customer"]
           user = await User.get_by_stripe_id(customer_id)
           if user:
               await sync_service.sync_subscription(user.id)

       elif event["type"] == "customer.subscription.deleted":
           # Downgrade to viewer
           customer_id = event["data"]["object"]["customer"]
           user = await User.get_by_stripe_id(customer_id)
           if user:
               license = await License.get_by_user_id(user.id)
               if license:
                   license.role = Role.VIEWER.value
                   await license.save()

       return {"received": True}
   ```

## Todo List

- [ ] Add `stripe_customer_id` to User model
- [ ] Create `src/stripe/role_mapping.py`
- [ ] Create `src/stripe/sync_service.py`
- [ ] Create/update `src/api/routes/stripe_webhook.py`
- [ ] Test webhook handlers with Stripe CLI

## Success Criteria

- [ ] Stripe Customer linked to User
- [ ] Subscription creates correct role
- [ ] Webhook updates role on change
- [ ] Cancelled subscription downgrades role

## Risk Assessment

- **Risk:** Webhook replay attacks
- **Mitigation:** Signature verification, idempotency keys

## Security Considerations

- Webhook signature verification required
- Stripe secret stored securely
- Idempotent webhook handling

## Next Steps

→ Phase 6: Environment configuration

# Phase 2: Money Layer Integration

## Context
The Money Layer manages revenue. Verification focuses on the correct handling of webhooks to provision subscriptions and generate licenses without manual intervention.

## Verification Checklist

### 1. Environment Setup
- [ ] Install dependencies: `pip install -r api/requirements.txt`.
- [ ] Configure `.env`: Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `SUPABASE_URL`.

### 2. Stripe Webhook Flow
- [ ] **Step 1: Start Server**
    - Run `uvicorn api.main:app --reload`.
- [ ] **Step 2: Forward Webhooks**
    - Run `stripe listen --forward-to localhost:8000/webhooks/stripe`.
- [ ] **Step 3: Trigger Checkout Event**
    - Run `stripe trigger checkout.session.completed`.
- [ ] **Step 4: Verify Processing**
    - Check API logs: "📨 STRIPE EVENT: checkout.session.completed".
    - Verify `PaymentService.handle_webhook_event` is called.
    - Verify `ProvisioningService.activate_subscription` is called.

### 3. Database State Verification
- [ ] **Subscriptions Table:** Check for new entry with `stripe_subscription_id`.
- [ ] **Organizations Table:** Check sync status (`plan` updated).
- [ ] **Licenses Table:** Check if a new license key was generated and stored.

### 4. PayPal Integration (Optional/Secondary)
- [ ] Verify `api/routers/paypal_webhooks.py` exists and is registered.
- [ ] Mock a PayPal webhook payload to `/webhooks/paypal` and verify signature logic.

# Fix Task: Gateway, Stripe, VietQR test failures

Work context: /Users/macbook/mekong-cli
Reports: /Users/macbook/mekong-cli/plans/reports/
Plans: /Users/macbook/mekong-cli/plans/

## Remaining Failures

### test_gateway_missions.py (1 test)
- test_mission_status_transitions: expects 'pending' in ['completed','failed','cancelled'] but got unexpected status list

### test_stripe_webhooks.py (8 tests)
- test_webhook_with_invalid_signature: expects 400, gets 404
- test_webhook_with_missing_signature: expects 400/401, gets 404
- test_webhook_with_tampered_payload: expects 400, gets 404
- TestPaymentIntentEvents: AttributeError: 'TestPaymentIntentEvents' object has no attribute '_generate_signature'
- TestSubscriptionEvents (4 tests): same _generate_signature AttributeError
- TestInvoiceEvents (2 tests): same _generate_signature AttributeError
- TestWebhookIdempotency: same _generate_signature AttributeError

Root cause: _generate_signature is a module-level function, not a class method. Tests in other classes can't find it.

### test_vietqr_payments.py (15 tests - all getting 422)
- All tests expect 200/202/401/400/404 but get 422
- Root cause: Pydantic validation rejecting payloads before signature check

## Your Task
1. Read each failing test file to understand expected behavior
2. For Stripe webhook: convert _generate_signature calls to use the module-level function directly
3. For VietQR: fix Pydantic schema mismatch or TestClient configuration
4. For gateway missions: fix status transition test
5. Run pytest to verify fixes
6. Report back with results

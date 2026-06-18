# ZenPay Test Suite

## Running Tests

```bash
# Run all tests
cd /Users/macbook/mekong-cli
python -m pytest src/zenpay/tests/ -v

# Run specific test file
python -m pytest src/zenpay/tests/test_wallet.py -v

# Run with coverage
python -m pytest src/zenpay/tests/ --cov=src/zenpay --cov-report=html
```

## Test Structure

```
src/zenpay/tests/
├── conftest.py           # Shared fixtures (DB session, managers)
├── test_wallet.py        # Wallet operations
├── test_treasury.py      # Treasury operations
├── test_stripe.py        # Stripe client
├── test_kyc.py           # KYC service
├── test_api.py           # API endpoints
└── fixtures/
    └── sample_data.py    # Test data
```

## Test Categories

### Unit Tests
- Wallet CRUD operations
- Balance calculations
- Fee computations
- Exchange rate caching

### Integration Tests
- Database transactions
- Stripe Connect flows
- Webhook handling

### End-to-End Tests
- Full payout flow
- KYC onboarding
- Multi-currency conversion

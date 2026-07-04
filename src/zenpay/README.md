# ZenPay Money OS

A comprehensive multi-currency payment and treasury platform built for the Mekong CLI ecosystem.

## Features

### 1. Stripe Connect Integration
- Full Stripe Connect marketplace support
- Individual and company account types
- Automated KYC via Stripe
- Multi-currency payouts (VND, USD, USDT)
- Express and Custom onboarding flows

### 2. Multi-Currency Treasury
- Support for VND, USD, USDT
- Real-time exchange rates via Stripe
- Automatic currency conversion
- Aggregated balance reporting
- Hold/available balance tracking

### 3. Self-Custody Wallet Option
- USDT on Tron (TRC20) - low fees
- USDT on Ethereum (ERC20)
- Non-custodial option for advanced users
- Mnemonic-based wallet derivation

### 4. Compliance & KYC
- Stripe-powered KYC verification
- Document upload and verification
- Automated status tracking via webhooks
- Payout eligibility enforcement
- Risk assessment integration

### 5. API Endpoints (`/v1/zenpay/*`)

#### Wallets
- `POST /v1/zenpay/wallets` - Create wallet
- `GET /v1/zenpay/wallets/{currency}` - Get wallet
- `GET /v1/zenpay/wallets` - List wallets
- `GET /v1/zenpay/balance` - Get balances

#### Transactions
- `GET /v1/zenpay/transactions/{id}` - Get transaction
- `GET /v1/zenpay/transactions` - List transactions

#### Transfers & Conversions
- `POST /v1/zenpay/transfer` - Transfer between wallets
- `POST /v1/zenpay/convert` - Convert currency
- `GET /v1/zenpay/exchange-rate` - Get exchange rate

#### Payouts
- `POST /v1/zenpay/payouts` - Request payout

#### Connected Accounts
- `POST /v1/zenpay/accounts` - Create Stripe Connect account
- `GET /v1/zenpay/accounts` - List accounts
- `POST /v1/zenpay/accounts/{id}/onboarding-link` - Get onboarding URL
- `GET /v1/zenpay/accounts/{id}/kyc-status` - Check KYC status

#### Self-Custody
- `GET /v1/zenpay/self-custody/balance` - Get USDT balance
- `POST /v1/zenpay/self-custody/send` - Send USDT

#### Webhooks
- `POST /v1/zenpay/webhooks/stripe` - Stripe Connect webhooks

## Integration Choice: Stripe Connect

**Why Stripe over Wise:**
1. Built-in marketplace/payout infrastructure
2. Comprehensive KYC/AML compliance
3. Multi-currency support with automatic conversion
4. Card and bank payout options
5. Webhook-driven event system
6. Trusted by major platforms (Shopify, Uber, etc.)

Wise can be added as an alternative provider in the future for lower-cost international transfers.

## Database Schema

See `src/zenpay/models.py` for full schema:

- `wallets` - User wallet balances (custodial/self-custody)
- `transactions` - Complete audit trail
- `accounts` - Stripe Connect account references
- `kyc_profiles` - KYC verification records
- `exchange_rates` - Cached exchange rates
- `balances` - Aggregated balance for reporting

## Configuration

Environment variables:

```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_ACCOUNT_ID=acct_...

# Self-custody (optional)
ENABLE_SELF_CUSTODY=true
ETH_RPC_URL=https://mainnet.infura.io/v3/...
TRON_RPC_URL=https://api.trongrid.io
WALLET_MNEMONIC_ENCRYPTED="your twelve word mnemonic here"

# Database
DATABASE_URL=postgresql+asyncpg://...

# Webhook
WEBHOOK_BASE_URL=https://your-api.com
KYC_WEBHOOK_SECRET=...

# Feature flags
KYC_REQUIRED_FOR_PAYOUT=true
KYC_PROVIDER=stripe
```

## Installation

1. Add to gateway.py:
```python
from src.zenpay.api import router as zenpay_router
app.include_router(zenpay_router)
```

2. Run migrations:
```bash
alembic upgrade head
```

3. Configure Stripe webhooks to point to `/v1/zenpay/webhooks/stripe`

## Testing

Tests located in `src/zenpay/tests/` covering:
- Wallet CRUD operations
- Transaction processing
- Currency conversion
- Stripe Connect flows
- KYC compliance
- Webhook handling

## Security Considerations

1. **API Authentication**: All endpoints require JWT via `Authorization: Bearer`
2. **Rate Limiting**: Applied at gateway level
3. **KYC Enforcement**: Configurable requirement for payouts
4. **Audit Trail**: Immutable transaction records
5. **Balance Integrity**: Atomic updates with database constraints
6. **Secret Management**: Mnemonic encrypted at rest

## Next Steps

- Implement Wise integration as alternative payout provider
- Add fraud detection rules
- Build admin dashboard for compliance review
- Add support for additional cryptocurrencies
- Implement reconciliation jobs
- Add email/SMS notifications for payouts

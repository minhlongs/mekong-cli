# Authentication

This document describes authentication mechanisms for Mekong CLI APIs.

---

## Overview

All Mekong APIs use **Bearer token authentication**. Tokens are issued to authenticated users and must be included in the `Authorization` header of each request.

```
Authorization: Bearer <your-api-token>
```

---

## Token Types

| Type | Issued By | Use Case | Expiry |
|------|-----------|----------|--------|
| **User token** | `mekong auth login` | User-facing API calls | 30 days (auto-refresh) |
| **Service token** | Dashboard → API Keys | Backend services, CI/CD | Never expires (revocable) |
| **Plugin token** | Plugin registration | Plugin-to-plugin communication | Same as user token |
| **Admin token** | Founder only | Admin operations | 7 days |

---

## Obtaining a Token

### Method 1: CLI Login (Recommended for Users)

```bash
# Interactive login
mekong auth login

# Prompts for:
# - Email
# - Password (or magic link)
# - 2FA code (if enabled)

# Token saved to ~/.mekong/api-token
```

### Method 2: OAuth2 Password Grant (For Scripts)

```bash
curl -X POST https://api.mekong.cli/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "password",
    "username": "user@example.com",
    "password": "yourpassword",
    "scope": "commands billing plugins"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 2592000,
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "scope": "commands billing plugins"
}
```

### Method 3: API Key (For Integrations)

Generate from dashboard:

1. Go to [api.mekong.cli/keys](https://api.mekong.cli/keys)
2. Click "Generate New Key"
3. Select scopes/permissions
4. Copy key (won't be shown again)

Use as bearer token:

```bash
curl -H "Authorization: Bearer pk_live_abc123..." \
  https://api.mekong.cli/api/v1/commands
```

---

## Token Security

### Storage

- **Never** commit tokens to version control
- **Never** hardcode tokens in source
- Use environment variables: `export MEKONG_API_TOKEN="your-token"`
- Or config files with `chmod 600` (read/write for owner only)

### Best Practices

1. **Least privilege:** Request only needed scopes
2. **Rotate regularly:** Every 90 days for service tokens
3. **Revoke immediately:** If token is leaked or employee leaves
4. **Use HTTPS only:** Tokens transmitted over TLS only
5. **Monitor usage:** Check audit logs for suspicious activity

---

## Scopes & Permissions

Tokens can be limited to specific operations via scopes.

| Scope | Access | Typical Use |
|-------|--------|-------------|
| `commands` | Execute commands | General CLI usage |
| `billing` | View balance, add credits | Billing operations |
| `plugins:read` | List installed plugins | Plugin discovery |
| `plugins:write` | Install/uninstall plugins | Plugin management |
| `users:read` | View user profile | Account info |
| `users:write` | Update user settings | Profile management |
| `admin` | All operations + admin endpoints | Founder/CTO only |

**Example:** Token with `commands` and `billing` scopes can execute commands and view balance, but cannot install plugins.

---

## Refresh Tokens

User tokens expire after 30 days of inactivity. To extend session:

```bash
curl -X POST https://api.mekong.cli/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token_here"
  }'
```

Returns new access token. Refresh tokens are one-time use; new one issued each refresh.

---

## Revocation

### User-Initiated

```bash
# Revoke all tokens
mekong auth logout

# Or via API
curl -X POST https://api.mekong.cli/auth/revoke \
  -H "Authorization: Bearer <token>"
```

### Admin-Initiated

From dashboard or API:

```bash
curl -X POST https://api.mekong.cli/admin/tokens/revoke \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"user_id": "opc_001_abc123"}'
```

---

## Error Cases

### 401 Unauthorized

```json
{
  "detail": "Invalid or expired token",
  "code": "TOKEN_INVALID",
  "request_id": "req_abc123"
}
```

**Action:** Re-authenticate or refresh token.

### 403 Forbidden (Insufficient Scope)

```json
{
  "detail": "Insufficient scope. Required: plugins:write, Got: commands",
  "code": "INSUFFICIENT_SCOPE",
  "request_id": "req_abc123"
}
```

**Action:** Request token with proper scopes or contact admin.

### 429 Too Many Requests (Auth Rate Limit)

Auth endpoint has separate rate limit: 10 requests/min.

```json
{
  "detail": "Too many authentication attempts. Try again in 60s.",
  "code": "AUTH_RATE_LIMIT",
  "request_id": "req_abc123"
}
```

---

## Example Usage

### Python

```python
import os
import requests

token = os.environ["MEKONG_API_TOKEN"]
headers = {"Authorization": f"Bearer {token}"}

response = requests.post(
    "https://api.mekong.cli/api/v1/commands/execute",
    headers=headers,
    json={"command": "/test/echo", "arguments": {"message": "hello"}}
)

result = response.json()
print(result)
```

### TypeScript

```typescript
const token = process.env.MEKONG_API_TOKEN;

const response = await fetch('https://api.mekong.cli/api/v1/commands/execute', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    command: '/test/echo',
    arguments: { message: 'hello' }
  })
});

const result = await response.json();
console.log(result);
```

### cURL

```bash
curl -X POST https://api.mekong.cli/api/v1/commands/execute \
  -H "Authorization: Bearer $MEKONG_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "/test/echo", "arguments": {"message": "hello"}}'
```

---

## Multi-Factor Authentication (MFA)

If MFA enabled on account, additional challenge may be required for sensitive operations.

**Flow:**

1. Initial request returns `401` with `mfa_required: true`
2. Client prompts user for MFA code
3. Retry request with `X-MFA-Token` header:

   ```bash
   curl -H "Authorization: Bearer <token>" \
        -H "X-MFA-Token: 123456" \
        https://api.mekong.cli/api/v1/billing/add-credits
   ```

---

## Auditing & Logging

All authentication events are logged:

- Successful logins (IP, user agent, timestamp)
- Failed login attempts
- Token revocations
- Scope changes
- Admin token usage

Logs retained for 365 days. Accessible via:

```bash
mekong audit auth --last 30d
```

Or API:

```bash
curl -H "Authorization: Bearer <admin-token>" \
  https://api.mekong.cli/api/v1/audit/auth?last=30d
```

---

## Troubleshooting

### "Invalid token" error

- Token expired: `mekong auth login` to refresh
- Token revoked: Check dashboard for revocation
- Typo in token: Verify copied correctly (no extra spaces)

### "Insufficient scope" error

- Token doesn't have required permission
- Generate new token with proper scopes from dashboard
- Contact admin if you need elevated access

### 401 on every request

- Check `MEKONG_API_TOKEN` environment variable set
- Verify token not expired: `mekong auth whoami`
- Ensure using correct API base URL (localhost vs production)

---

## Security Considerations

- 🔒 **Always** use HTTPS in production
- 🔒 Tokens are secret — treat like passwords
- 🔒 Rotate tokens periodically (every 90 days)
- 🔒 Use different tokens for development vs production
- 🔒 Revoke tokens immediately when employee leaves
- 🔒 Monitor audit logs for unusual access patterns

---

## See Also

- [API Reference](../reference/API_REFERENCE.md)
- [Error Codes](./ERROR_CODES.md)
- [Rate Limiting](./RATE_LIMITING.md)
- [OAuth2 Specification (RFC 6749)](https://tools.ietf.org/html/rfc6749)

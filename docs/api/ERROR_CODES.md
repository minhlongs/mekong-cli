# Error Codes

Standard error responses for Mekong CLI APIs.

---

## Overview

All APIs return HTTP status codes with a consistent JSON error body.

**Error format:**

```json
{
  "detail": "Human-readable message",
  "code": "MACHINE_READABLE_CODE",
  "request_id": "req_abc123def456"
}
```

---

## HTTP Status Codes

| Code | Description | When to Use | Retryable |
|------|-------------|-------------|-----------|
| 200 OK | Success | GET/PUT returned data | No |
| 201 Created | Resource created | POST created new resource | No |
| 202 Accepted | Async operation accepted | Long-running task queued | No |
| 400 Bad Request | Invalid request | Validation failed, missing fields | No |
| 401 Unauthorized | Authentication required | Missing/invalid/expired token | Yes after re-auth |
| 402 Payment Required | Insufficient credits | MCU balance too low | Yes after top-up |
| 403 Forbidden | Permission denied | Token valid but lacks scope | No |
| 404 Not Found | Resource doesn't exist | Command, user, plugin not found | No |
| 409 Conflict | Resource conflict | Duplicate resource, state conflict | No |
| 422 Unprocessable Entity | Semantic error | Valid JSON but invalid business logic | No |
| 429 Too Many Requests | Rate limit exceeded | Too many requests in time window | Yes after wait |
| 500 Internal Server Error | Server failure | Unhandled exception | Yes (transient) |
| 503 Service Unavailable | Service down | Backend unavailable | Yes (retry later) |

---

## Error Codes by Category

### Authentication (AUTH-xxx)

| Code | HTTP Status | Description | Example Situation |
|------|-------------|-------------|-------------------|
| `AUTH_INVALID_TOKEN` | 401 | Token is malformed or expired | User session timed out |
| `AUTH_MISSING_TOKEN` | 401 | No Authorization header provided | API call without token |
| `AUTH_INSUFFICIENT_SCOPE` | 403 | Token lacks required scope | User token trying to access admin endpoint |
| `AUTH_MFA_REQUIRED` | 401 | Multi-factor authentication required | Sensitive operation without 2FA |
| `AUTH_RATE_LIMIT` | 429 | Too many auth attempts | Brute force protection |
| `AUTH_ACCOUNT_DISABLED` | 403 | User account is suspended | Founder disabled user |

**Example response:**

```json
{
  "detail": "Token expired. Please re-authenticate.",
  "code": "AUTH_INVALID_TOKEN",
  "request_id": "req_abc123"
}
```

---

### Command Execution (CMD-xxx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `CMD_NOT_FOUND` | 404 | Command path doesn't exist |
| `CMD_DISABLED` | 403 | Command is disabled (maintenance) |
| `CMD_INVALID_ARGS` | 400 | Arguments failed validation |
| `CMD_EXECUTION_FAILED` | 500 | Handler raised exception |
| `CMD_TIMEOUT` | 504 | Command exceeded timeout limit |
| `CMD_CANCELLED` | 499 | Client cancelled request |
| `CMD_NOT_ALLOWED` | 403 | User not permitted to run command |

---

### Billing (BILL-xxx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `BILL_INSUFFICIENT_BALANCE` | 402 | Not enough credits (MCU) |
| `BILL_PAYMENT_FAILED` | 402 | Payment processor declined |
| `BILL_INVALID_AMOUNT` | 400 | Amount below minimum or invalid |
| `BILL_RATE_LIMIT_EXCEEDED` | 429 | Too many billing operations |
| `BILL_TIER_UPGRADE_FAILED` | 500 | Tier change failed |

---

### Plugin System (PLUG-xxx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PLUG_NOT_FOUND` | 404 | Plugin not installed or not in marketplace |
| `PLUG_ALREADY_INSTALLED` | 409 | Plugin already installed |
| `PLUG_VALIDATION_FAILED` | 400 | Manifest validation failed |
| `PLUG_SECURITY_SCAN_FAILED` | 403 | Security scan detected risk |
| `PLUG_INCOMPATIBLE_VERSION` | 409 | Mekong version too old |
| `PLUG_DEPENDENCY_MISSING` | 409 | Required dependency not installed |
| `PLUG_LOAD_ERROR` | 500 | Plugin module failed to load |
| `PLUG_DISABLED` | 403 | Plugin is currently disabled |

---

### User Management (USER-xxx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `USER_NOT_FOUND` | 404 | User ID doesn't exist |
| `USER_ALREADY_EXISTS` | 409 | Email already registered |
| `USER_INVALID_EMAIL` | 400 | Email format invalid |
| `USER_INVALID_PASSWORD` | 400 | Password doesn't meet requirements |
| `USER_VERIFICATION_REQUIRED` | 403 | Email not verified |
| `USER_SUSPENDED` | 403 | Account is suspended |
| `USER_DELETION_FAILED` | 500 | Account deletion failed (DB error) |

---

### Rate Limiting (RATE-xxx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RATE_LIMIT_EXCEEDED` | 429 | General rate limit |
| `RATE_LIMIT_COMMANDS` | 429 | Command execution limit exceeded |
| `RATE_LIMIT_BILLING` | 429 | Billing operations too frequent |
| `RATE_LIMIT_AUTH` | 429 | Authentication attempts too many |
| `RATE_LIMIT_PLUGINS` | 429 | Plugin install/uninstall too frequent |

---

### Validation (VAL-xxx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VAL_REQUIRED_FIELD` | 400 | Required field missing |
| `VAL_INVALID_TYPE` | 400 | Wrong data type (string vs int) |
| `VAL_INVALID_FORMAT` | 400 | String format invalid (email, uuid) |
| `VAL_ENUM_INVALID` | 400 | Value not in allowed set |
| `VAL_MIN_EXCEEDED` | 400 | Number below minimum |
| `VAL_MAX_EXCEEDED` | 400 | Number above maximum |
| `VAL_STRING_TOO_LONG` | 400 | String exceeds max length |
| `VAL_ARRAY_TOO_LONG` | 400 | Array exceeds max items |

---

### Database (DB-xxx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `DB_CONNECTION_FAILED` | 503 | Cannot connect to database |
| `DB_QUERY_FAILED` | 500 | SQL error or constraint violation |
| `DB_DEADLOCK` | 409 | Transaction deadlock, retry |
| `DB_TIMEOUT` | 504 | Database query timeout |
| `DB_INTEGRITY_ERROR` | 409 | Unique constraint violation |

---

### External Services (EXT-xxx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `EXT_UPSTREAM_TIMEOUT` | 504 | Upstream service timed out |
| `EXT_UPSTREAM_ERROR` | 502 | Upstream returned 5xx |
| `EXT_RATE_LIMITED` | 429 | External API rate limit hit |
| `EXT_AUTH_FAILED` | 502 | External service auth failed |
| `EXT_SERVICE_UNAVAILABLE` | 503 | External service down |

---

## Example Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid argument: amount must be greater than 0",
  "code": "VAL_MIN_EXCEEDED",
  "request_id": "req_7d3f9a2b"
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication required or token expired",
  "code": "AUTH_INVALID_TOKEN",
  "request_id": "req_a1b2c3d4"
}
```

### 402 Payment Required

```json
{
  "detail": "Insufficient credits. Current balance: 3 MCU, required: 50 MCU",
  "code": "BILL_INSUFFICIENT_BALANCE",
  "request_id": "req_e5f6g7h8"
}
```

### 404 Not Found

```json
{
  "detail": "Command '/unknown/command' not found. Use 'mekong help' to see available commands.",
  "code": "CMD_NOT_FOUND",
  "request_id": "req_i9j0k1l2"
}
```

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded. Limit: 60 requests/minute, retry after: 12s",
  "code": "RATE_LIMIT_EXCEEDED",
  "request_id": "req_m3n4o5p6",
  "retry_after": 12
}
```

### 500 Internal Server Error

```json
{
  "detail": "Unexpected error executing command. Our team has been notified.",
  "code": "CMD_EXECUTION_FAILED",
  "request_id": "req_q7r8s9t0"
}
```

---

## Error Handling Best Practices (Client)

1. **Check status code first**, then `code` field for programmatic handling
2. **Retry on 429** after `retry_after` seconds (if provided) or with exponential backoff
3. **Refresh token on 401** if `code` is `AUTH_INVALID_TOKEN`
4. **Log request_id** for support escalations
5. **Display user-friendly messages** from `detail` field
6. **Don't retry on 4xx** (except 429) — fix request first

**Example Python error handling:**

```python
import requests
import time

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    result = response.json()
elif response.status_code == 401:
    error = response.json()
    if error["code"] == "AUTH_INVALID_TOKEN":
        refresh_token()  # Re-authenticate
    else:
        raise PermissionError(error["detail"])
elif response.status_code == 402:
    error = response.json()
    print(f"Need credits: {error['detail']}")
    # Prompt user to top up
elif response.status_code == 429:
    error = response.json()
    retry_after = error.get("retry_after", 60)
    time.sleep(retry_after)
    # Retry request
elif response.status_code >= 500:
    # Log request_id and retry with backoff
    request_id = response.json().get("request_id")
    logger.error(f"Server error (request_id={request_id})")
    time.sleep(2 ** attempt)  # Exponential backoff
else:
    response.raise_for_status()
```

---

## Error Codes vs HTTP Status

Use **HTTP status** for general category (auth failure, not found, server error).
Use **error code** for specific reason (which kind of auth failure, what kind of not found).

Example:

- `404` + `CMD_NOT_FOUND` → Command doesn't exist
- `404` + `PLUG_NOT_FOUND` → Plugin doesn't exist
- `403` + `AUTH_INSUFFICIENT_SCOPE` → Valid token but wrong permissions
- `403` + `USER_SUSPENDED` → Account suspended

---

## Testing Error Responses

API tests should verify error conditions:

```python
def test_command_not_found():
    response = client.execute_command("/nonexistent/command")
    assert response.status_code == 404
    error = response.json()
    assert error["code"] == "CMD_NOT_FOUND"
    assert "not found" in error["detail"].lower()
    assert "request_id" in error
```

---

## Internationalization (i18n)

Currently, error messages are in English only. Future versions may support localized `detail` fields based on `Accept-Language` header.

---

## See Also

- [API Reference](../reference/API_REFERENCE.md)
- [Authentication](./AUTHENTICATION.md)
- [Rate Limiting](./RATE_LIMITING.md)

---

**Last Updated:** 2026-06-21  
**API Version:** 1.0

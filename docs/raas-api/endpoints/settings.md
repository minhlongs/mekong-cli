# Settings API — LLM Configuration

> **Purpose**: Cấu hình Bring Your Own Key (BYOK) cho các LLM providers (OpenAI, Google, Anthropic, Custom).

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/v1/settings/llm` | ✅ | Get current LLM configuration |
| PUT | `/v1/settings/llm` | ✅ | Update LLM configuration |
| DELETE | `/v1/settings/llm/:provider` | ✅ | Remove provider configuration |

---

## GET /v1/settings/llm — Get LLM Configuration

### Request

```bash
curl -X GET https://agencyos.network/v1/settings/llm \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response

```json
{
  "tenant_id": "tenant_abc123",
  "providers": {
    "openai": {
      "enabled": true,
      "model": "gpt-4o",
      "base_url": "https://api.openai.com/v1",
      "configured_at": "2026-03-19T10:00:00Z"
    },
    "google": {
      "enabled": true,
      "model": "gemini-2.0-flash",
      "base_url": "https://generativelanguage.googleapis.com/v1beta",
      "configured_at": "2026-03-19T10:00:00Z"
    },
    "anthropic": {
      "enabled": false,
      "model": "claude-sonnet-4-6",
      "base_url": "https://api.anthropic.com/v1",
      "configured_at": null
    },
    "custom": {
      "enabled": false,
      "model": "",
      "base_url": "",
      "configured_at": null
    }
  },
  "default_provider": "openai",
  "fallback_chain": ["openai", "google", "anthropic"]
}
```

### Provider Models

| Provider | Default Model | Description |
|----------|---------------|-------------|
| `openai` | `gpt-4o` | GPT-4 Omni (fastest GPT-4) |
| `google` | `gemini-2.0-flash` | Gemini 2.0 Flash (cost-effective) |
| `anthropic` | `claude-sonnet-4-6` | Claude Sonnet 4.6 (balanced) |
| `custom` | — | Custom OpenAI-compatible endpoint |

---

## PUT /v1/settings/llm — Update LLM Configuration

### Request

```bash
curl -X PUT https://agencyos.network/v1/settings/llm \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-proj-abc123xyz789",
    "model": "gpt-4o",
    "base_url": "https://api.openai.com/v1"
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | ✅ | Provider ID: `openai`, `google`, `anthropic`, `custom` |
| `api_key` | string | ✅ | API key (encrypted at rest) |
| `model` | string | ❌ | Model name (default per provider) |
| `base_url` | string | ❌ | Custom endpoint (for `custom` provider) |

### Response (200 OK)

```json
{
  "provider": "openai",
  "status": "configured",
  "model": "gpt-4o",
  "message": "LLM configuration updated successfully"
}
```

### Error Responses

**400 Invalid Provider:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Unknown provider: 'unknown-provider'"
}
```

**400 Invalid API Key:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid API key format for provider 'openai'"
}
```

**503 Provider Unavailable:**
```json
{
  "error": "SERVICE_UNAVAILABLE",
  "message": "Provider 'openai' is currently unavailable"
}
```

---

## DELETE /v1/settings/llm/:provider — Remove Provider

### Request

```bash
curl -X DELETE https://agencyos.network/v1/settings/llm/openai \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response (200 OK)

```json
{
  "provider": "openai",
  "status": "removed",
  "message": "Provider configuration removed successfully"
}
```

### Security

- API key immediately revoked from tenant config
- Encrypted key deleted from KV storage
- Audit log entry created

---

## Supported Providers

### OpenAI

**Configuration:**
```json
{
  "provider": "openai",
  "api_key": "sk-proj-...",
  "model": "gpt-4o",
  "base_url": "https://api.openai.com/v1"
}
```

**Supported Models:**
- `gpt-4o` — GPT-4 Omni (default)
- `gpt-4o-mini` — Fast, cost-effective
- `o1-preview` — Reasoning model
- `o1-mini` — Fast reasoning

**Rate Limits:**
- Requests/minute: 500 (varies by tier)
- Tokens/minute: 30,000 (varies by tier)

---

### Google (Vertex AI / Gemini)

**Configuration:**
```json
{
  "provider": "google",
  "api_key": "AIza...",
  "model": "gemini-2.0-flash",
  "base_url": "https://generativelanguage.googleapis.com/v1beta"
}
```

**Supported Models:**
- `gemini-2.0-flash` — Fast, multimodal (default)
- `gemini-2.0-pro` — Advanced reasoning
- `gemini-1.5-pro` — Long context (2M tokens)

**Rate Limits:**
- Requests/minute: 60 (free tier)
- Requests/day: 1,500 (free tier)

---

### Anthropic

**Configuration:**
```json
{
  "provider": "anthropic",
  "api_key": "sk-ant-...",
  "model": "claude-sonnet-4-6",
  "base_url": "https://api.anthropic.com/v1"
}
```

**Supported Models:**
- `claude-sonnet-4-6` — Balanced performance (default)
- `claude-opus-4-6` — Most capable
- `claude-haiku-4-5` — Fast, lightweight

**Rate Limits:**
- Requests/minute: 50-400 (varies by tier)
- Tokens/minute: 4,000-32,000

---

### Custom (OpenAI-Compatible)

**Configuration:**
```json
{
  "provider": "custom",
  "api_key": "your-api-key",
  "model": "custom-model-name",
  "base_url": "https://your-custom-endpoint.com/v1"
}
```

**Use Cases:**
- Self-hosted LLMs (Ollama, vLLM, TGI)
- Enterprise private endpoints
- Alternative providers (OpenRouter, Together, Anyscale)

**Examples:**

**Ollama (Local):**
```json
{
  "provider": "custom",
  "api_key": "ollama",
  "model": "llama-3.1-70b",
  "base_url": "http://localhost:11434/v1"
}
```

**OpenRouter:**
```json
{
  "provider": "custom",
  "api_key": "sk-or-v1-...",
  "model": "meta-llama/llama-3.1-70b-instruct",
  "base_url": "https://openrouter.ai/api/v1"
}
```

**Together AI:**
```json
{
  "provider": "custom",
  "api_key": "together-...",
  "model": "meta-llama/Llama-3.1-70B-Instruct-Turbo",
  "base_url": "https://api.together.xyz/v1"
}
```

---

## Fallback Chain

When primary provider fails, requests automatically failover:

```
Primary: openai (gpt-4o)
  ↓ (timeout/error)
Fallback 1: google (gemini-2.0-flash)
  ↓ (timeout/error)
Fallback 2: anthropic (claude-sonnet-4-6)
```

### Configure Fallback Chain

```bash
curl -X PUT https://agencyos.network/v1/settings/llm/fallback \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "fallback_chain": ["openai", "google", "anthropic"]
  }'
```

---

## Environment Variables (Server-Side)

For self-hosted deployments, configure via environment:

```bash
# Primary provider
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-proj-abc123xyz789
export LLM_MODEL=gpt-4o
export LLM_BASE_URL=https://api.openai.com/v1

# Fallback providers
export LLM_FALLBACK_1=google
export LLM_FALLBACK_1_KEY=AIza...
export LLM_FALLBACK_2=anthropic
export LLM_FALLBACK_2_KEY=sk-ant-...
```

---

## Security

### API Key Encryption

- Keys encrypted at rest (AES-256-GCM)
- Keys never logged or exposed in responses
- Keys scoped to tenant_id (cross-tenant isolation)

### Audit Trail

All configuration changes logged:

```typescript
{
  "tenant_id": "tenant_abc123",
  "action": "llm_config_update",
  "provider": "openai",
  "timestamp": "2026-03-19T10:30:00Z",
  "ip_address": "1.2.3.4",
  "user_agent": "curl/7.68.0"
}
```

---

## Related Endpoints

- [POST /v1/tasks](./tasks.md) — Create missions with configured LLM
- [POST /v1/agents/:name/run](./agents.md) — Run agents with LLM routing
- [GET /billing/credits](./billing.md) — Check credit balance

---

## Next Steps

- [Tasks API](./tasks.md) — Execute missions with configured LLM
- [Agents API](./agents.md) — Agent execution with LLM routing
- [Onboarding API](./onboarding.md) — Complete tenant setup

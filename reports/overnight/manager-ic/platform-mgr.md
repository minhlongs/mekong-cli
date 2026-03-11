# Platform Manager Report — Mekong CLI
*Role: Platform Manager | Date: 2026-03-11*

---

## Platform Vision

Mekong CLI is not just a CLI tool — it is a platform for AI-operated business execution.
The platform has three distinct surfaces:

1. **CLI** (`mekong` command) — developer-facing, local execution
2. **Dashboard** (`agencyos.network → /v1/missions`) — web UI for mission tracking
3. **SDK / API** (`src/api/`) — programmatic access for integrations

The platform strategy: CLI drives adoption → Dashboard drives retention → SDK drives
enterprise expansion and partner ecosystem.

---

## Multi-LLM Support Matrix

Current support via `src/core/llm_client.py` fallback chain:

| Provider | Endpoint Type | Cost Tier | Best For |
|----------|--------------|-----------|----------|
| OpenRouter | Aggregator (300+ models) | Medium | Flexibility |
| Qwen/DashScope | Direct | Low ($10/mo unlimited) | Cost optimization |
| DeepSeek | Direct | Very Low | Budget users |
| Anthropic (Claude) | Direct | High | Quality tasks |
| OpenAI (GPT-4o) | Direct | High | Ecosystem compat |
| Google (Gemini) | Direct | Medium | Multimodal future |
| Ollama | Local | Free | Privacy, offline |
| OfflineProvider | Fallback | Free | Degraded mode |

**Platform gap:** No model capability routing — all tasks use the same model.
Opportunity: route simple tasks (file ops) to cheap models, complex reasoning to
premium models. Estimated 60% cost reduction per user.

---

## Plugin / Extension Ecosystem

Current extension points:

```
.agencyos/commands/     — 289 command definitions (Markdown)
factory/contracts/      — 176 JSON machine contracts
src/agents/             — 17+ pluggable agent modules
mekong/adapters/        — LLM provider configs (YAML)
mekong/infra/           — Infrastructure templates
```

**Missing:** No public plugin registry. To grow the ecosystem:

1. Define `PLUGIN_SPEC.md` — standard format for third-party commands/agents
2. Create `mekong plugin install <name>` command
3. Launch `plugins.mekong.dev` registry (CF Pages + D1)
4. Seed with 10 community plugins before public launch

Plugin categories to prioritize:
- CRM integrations (HubSpot, Notion, Airtable)
- Cloud provider ops (AWS, GCP adapters)
- Language-specific scaffolding (Go, Rust, Java)
- Vertical-specific commands (e-commerce, SaaS, fintech)

---

## SDK Strategy

Current API: `src/api/` (FastAPI) with auth and MCU balance check.

**SDK roadmap:**

| Quarter | Deliverable |
|---------|------------|
| Q2 2026 | Python SDK (`pip install mekong-sdk`) — wrap REST API |
| Q3 2026 | TypeScript/Node SDK (`npm install @mekong/sdk`) |
| Q4 2026 | Webhook SDK — receive mission completion events |

SDK enables:
- CI/CD integrations (`mekong.run("cook", "Fix failing tests")` in GitHub Actions)
- Dashboard embeds (no-code trigger from web UI)
- Enterprise workflow automation (Zapier/Make competitor use case)

---

## Tôm Hùm Daemon Platform Role

`apps/openclaw-worker/` houses the autonomous dispatch daemon. Platform implications:

- **Brain process manager** runs missions via `claude -p` (non-interactive)
- **stdin must be `'ignore'`** when spawning via Node.js child_process (hanging bug if piped)
- **CF Queues** as the job dispatch layer — mission submitted → queued → Tôm Hùm picks up

Platform reliability requirement: Tôm Hùm must handle:
- LLM timeout (add 60s per-mission timeout)
- Queue backpressure (CF Queues has 100K msg/day free tier limit)
- Failed mission retry (max 3 attempts before dead-letter queue)

---

## Platform Metrics Dashboard (Proposed)

| Category | Metric | Source |
|----------|--------|--------|
| Usage | Missions run/day | CF Worker logs |
| Quality | Mission success rate | Verifier pass/fail |
| Performance | Median mission duration | CF Analytics |
| Revenue | MCU consumed/user/day | D1 query |
| Scale | Queue depth (Tôm Hùm) | CF Queues metrics |
| Reliability | Worker error rate | CF Analytics |

---

## Platform Versioning

Current version: `v0.2.0` (per `src/main.py`)
No public changelog visible in README.

**Recommendation:**
- Adopt semver strictly: MAJOR.MINOR.PATCH
- MAJOR: breaking CLI interface changes
- MINOR: new commands or agent types
- PATCH: bug fixes, prompt improvements
- Publish `CHANGELOG.md` with each release
- Tag GitHub releases for pip install pinning (`pip install mekong-cli==0.2.0`)

---

## Platform Roadmap (6-Month)

| Q2 2026 | Q3 2026 |
|---------|---------|
| Plugin spec + registry MVP | Python SDK v1.0 |
| Model capability routing | TypeScript SDK v1.0 |
| Dashboard mission history | Plugin marketplace launch |
| Webhook events for missions | Enterprise SSO (SAML) |
| `mekong init --wizard` | Multi-user workspace support |

---

## Platform Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| CF vendor lock-in | Medium | High | Adapter pattern in `mekong/adapters/` |
| Plugin quality control | High | Medium | Review gate before registry listing |
| SDK breaking changes | Medium | High | Semantic versioning + deprecation warnings |
| Queue capacity hit | Low | High | Monitor daily, upgrade CF plan at 80% cap |

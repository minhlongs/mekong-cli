# Legal Manager Report — Mekong CLI
*Role: Legal Manager | Date: 2026-03-11*

---

## License Analysis: MIT

Mekong CLI is published under the MIT License. Key implications:

**Permissions granted to anyone:**
- Commercial use (any business can deploy and sell services built on Mekong CLI)
- Modification (fork, extend, rebrand)
- Distribution (redistribute source or binaries)
- Private use (internal enterprise deployment without disclosure)

**Obligations:**
- Include original copyright notice and MIT license text in any distribution
- No warranty or liability transferred to Binh Phap Venture Studio

**Strategic impact:**
- MIT maximizes adoption — no GPL copyleft friction for enterprise users
- Competitors can fork and rebrand (acceptable tradeoff for ecosystem growth)
- The RaaS/MCU billing layer (src/raas/, Polar.sh webhooks) is the moat, not the code

**Recommendation:** Keep MIT on core CLI. Consider a proprietary license for future
cloud dashboard (`apps/openclaw-worker/`) if it becomes a significant revenue driver.

---

## Terms of Service Considerations

Current gap: No published ToS for the RaaS credit system. Required before $10K MRR.

**ToS must cover:**
1. MCU credit definition and consumption rules
2. No-refund policy for consumed credits
3. Fair use clause for Enterprise "unlimited" tier (suggest: 10,000 MCU/mo soft cap)
4. Prohibited use cases: illegal content, spam generation, credential stuffing
5. Account termination rights (HTTP 402 enforcement is technical ToS)
6. Data handling: what user prompts are stored, for how long

---

## Data Handling & Privacy

**Current data flows:**
- User prompts → LLM provider (OpenRouter / DeepSeek / Ollama local)
- Credit balance → Cloudflare D1 database
- Polar.sh → webhook events stored in KV
- No PII collected in current CLI flow (API key = pseudonymous)

**GDPR/CCPA exposure:**
- EU users using cloud LLM endpoints: prompts may contain personal data
- Must add Privacy Policy stating: "We do not store LLM prompt content"
- Cloudflare D1 data residency: US by default — add EU region option for compliance
- Right to deletion: credit balance + usage logs must be deletable on request

**Action:** Draft Privacy Policy before any marketing to EU audience.

---

## LLM Provider API Terms Compliance

Each upstream provider has restrictions that flow down to Mekong CLI users:

| Provider | Key Restriction | Risk to Mekong |
|----------|----------------|----------------|
| OpenAI API | No competing AI product building | Low (we route, not build) |
| Anthropic (Claude) | No harmful use, no automated deception | Low — enforce in ToS |
| DeepSeek | Chinese data law exposure | Medium — add disclaimer |
| Google (Gemini) | No reverse engineering | Low |
| Ollama (local) | No provider restriction | None |

**Recommendation:** Add disclaimer in docs: "Users are responsible for compliance
with their chosen LLM provider's terms of service."

---

## Intellectual Property

**Owned IP:**
- PEV engine architecture (planner.py, executor.py, verifier.py, orchestrator.py)
- 289 command definitions in `.agencyos/commands/`
- 176 JSON machine contracts in `factory/contracts/`
- Tôm Hùm daemon design (`apps/openclaw-worker/`)
- "OpenClaw" brand and "Mekong CLI" name

**Third-party IP used:**
- Typer (MIT), Rich (MIT), FastAPI (MIT) — all permissive, no issue
- Cloudflare Workers SDK — Cloudflare ToS applies to deployed workers
- Polar.sh SDK — check for attribution requirements

**Trademark:** File "Mekong CLI" and "OpenClaw" trademarks in Vietnam + US before
significant marketing spend. Cost: ~$500-1,500 via USPTO.

---

## Open Source Contribution Risk

Public repo means contributors may submit code. Without a CLA (Contributor License
Agreement), contributors retain copyright on their contributions.

**Recommendation:** Add a lightweight CLA bot (cla-assistant.io) before accepting
non-trivial PRs. Or adopt DCO (Developer Certificate of Origin) as GitHub sign-off.

---

## Payment & Financial Regulation

- Polar.sh handles payment processing — they hold Money Transmitter licenses
- Mekong CLI/Binh Phap Venture Studio receives net revenue via Polar.sh payout
- Credits are not "stored value" in a regulatory sense (they're usage quotas)
- No FinTech license required at current scale
- If credits become transferable between users: consult lawyer immediately

---

## Immediate Legal Actions

- [ ] Draft and publish Privacy Policy (target: before first marketing campaign)
- [ ] Draft and publish Terms of Service (target: before $10K MRR)
- [ ] Add "Prohibited Use" section to README
- [ ] File trademark applications for "Mekong CLI" and "OpenClaw"
- [ ] Add CLA bot to GitHub repo
- [ ] Audit DeepSeek usage for data residency disclosure requirements

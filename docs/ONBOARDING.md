# Mekong IDE — Customer Onboarding

## Choose your use-case

Mekong IDE is a single product with 13 customized landing pages for different industries:

- **Trading Desk** — Algorithmic trading & portfolio management
- **Model Router** — LLM provider orchestration
- **Content Studio** — Content creation & distribution
- **Legal Counsel** — Legal document automation
- **Dev Agency** — Software development teams
- **Growth Engine** — Marketing & growth operations
- **Compliance Vault** — Regulatory compliance
- **Business Intelligence** — Data analytics & BI
- **HR Operations** — Human resources management
- **Sales Operations** — Sales automation
- **Design Studio** — Creative design tools
- **Venture Studio** — Venture capital operations
- **Operations Center** — General business operations

Visit `landing.mekongmind.com` to browse all use-cases, then subscribe. Your use-case choice customizes the department dashboard but does not restrict API access — you always have access to all 22 departments.

## 5-minute setup

### 1. Get your API key

```bash
curl -X POST https://api.mekong.ai/v1/onboard \
  -H "Content-Type: application/json" \
  -d '{"name": "Your Company", "email": "you@company.com"}'
```

Response:
```json
{
  "tenant_id": "abc-123",
  "api_key": "mk_your_key_here",
  "credits": 50,
  "message": "Welcome to Mekong IDE"
}
```

### 2. Run your first mission

```bash
curl -X POST https://api.mekong.ai/v1/missions \
  -H "X-API-Key: mk_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Create a quarterly financial report for Q1 2026"}'
```

The system automatically:
- Classifies your goal → CFO department, finance domain
- Matches the best command → `finance-budget-plan`
- Routes to the optimal LLM model
- Returns structured, actionable output
- Deducts 1 credit from your balance

### 3. Check your balance

```bash
curl https://api.mekong.ai/raas/credits/balance \
  -H "X-API-Key: mk_your_key_here"
```

### 4. Explore departments

```bash
# All departments
curl https://api.mekong.ai/v1/departments

# Or filter by use-case (e.g., "trading-desk", "content-studio")
curl "https://api.mekong.ai/v1/departments?tenant=trading-desk"
```

Returns all 22 departments and 290 commands available in your subscription, optionally filtered to your chosen use-case.

### 5. Stream results (Growth+ tier)

```bash
curl https://api.mekong.ai/v1/missions/MISSION_ID/stream \
  -H "X-API-Key: mk_your_key_here"
```

## Local setup (M1 Max / Ollama)

Run Mekong IDE on your own hardware — zero cloud cost.

```bash
# 1. Clone
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli

# 2. Install deps
 pip install -r requirements.txt

# 3. Start Rapid-MLX
brew install raullenchai/rapid-mlx/rapid-mlx
rapid-mlx serve qwen3.6-35b --port 8001 &

# 4. Configure
export OPENAI_BASE_URL=http://localhost:8001/v1
export LLM_API_KEY=mlx
export LLM_MODEL=qwen3.6-35b

# 5. Start gateway
uvicorn src.gateway:app --port 8000

# 6. Test
curl -X POST http://localhost:8000/v1/missions \
  -H "Content-Type: application/json" \
  -d '{"goal": "Write a marketing plan for product launch"}'
```

## Example missions by department

| Department | Example goal | Command matched |
|-----------|-------------|-----------------|
| Finance | "Create invoice for client ABC" | accounting-invoice-batch |
| Marketing | "Write blog post about AI trends" | marketing-content-engine |
| Engineering | "Deploy staging environment" | devops-deploy-pipeline |
| Legal | "Review NDA contract" | legal-contract-review |
| Sales | "Build sales pipeline report" | sales-pipeline-build |
| HR | "Onboard new engineer" | hr-onboard |
| Compliance | "SOC2 prep checklist" | compliance-soc2-prep |

## Pricing

| Tier | Price | Credits | Best for |
|------|-------|---------|----------|
| Starter | $49/mo | 200 | Solo founders, freelancers |
| Growth | $149/mo | 1,000 | Small teams, agencies |
| Pro | $499/mo | 5,000 | Companies, enterprises |

All tiers include all 22 departments and all 290 commands.

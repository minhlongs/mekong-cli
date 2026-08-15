# Mekong CLI — AI-Powered Business Operations for Vietnam

> AI-operated business platform. Open source. MIT license.

## What is Mekong CLI?

Mekong CLI is the AI kernel for [mekongmind.com](https://www.mekongmind.com) — an AI-operated business platform built for Vietnamese one-person companies and small businesses.

**Core mission:** Replace a full back-office team with AI agents — accounting, tax filing, sales outreach, and customer communication — all running on your infrastructure.

## Three Business Funnels

1. **Zalo OA** — Automated customer communication and lead capture via Zalo Official Account
2. **Tax & Accounting (thue_dnvn / ke_toan)** — Full Vietnamese tax compliance: TNCN, TNDN, GTGT, TT78 invoices
3. **AI Video Factory (sophia)** — AI-powered video generation for marketing

## Quick Start

```bash
git clone https://github.com/minhlongs/mekong-cli.git
cd mekong-cli && source scripts/shell-init.sh

# Configure LLM (any OpenAI-compatible provider)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=your-key
export LLM_MODEL=anthropic/claude-sonnet-4

mekong  # Start the CLI
```

Vietnam domestic payments (PayOS) for TNCN/TNDN/GTGT compliance workflows.

## Links

- **Website:** [mekongmind.com](https://www.mekongmind.com)
- **API:** [api.cashclaw.cc](https://api.cashclaw.cc/health)
- **Docs:** [docs/](/Users/macbook/mekong-cli/docs/)

## License

MIT

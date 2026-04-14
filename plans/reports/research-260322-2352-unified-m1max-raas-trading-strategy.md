# Unified Strategy: M1 Max 64GB — RaaS + Trading + AGI Factory

> Tong hop tu 5 researcher agents (2 lan research, 2026-03-22)
> Hardware: M1 Max 64GB | 32-core GPU | 1.8TB SSD

---

## EXECUTIVE SUMMARY

M1 Max 64GB chay DONG THOI 3 workloads:
1. **OpenClaw CTO Brain** — dieu phoi CC CLI, ban RaaS credits
2. **Algo-Trader** — Polymarket binary arb + information edge
3. **Revenue Pipeline** — AI sales automation

**Chia RAM thuc te:**

```
64GB Unified Memory
├── macOS + system:     8GB  (reserved)
├── Qwen 2.5-Coder 32B: 24GB (MLX, Q4_K_M)
├── Algo-Trader process: 4GB  (Node.js + WebSocket feeds)
├── CC CLI sessions:     4GB  (2-3 parallel)
├── Vector DB (ChromaDB): 2GB  (agent memory)
└── Buffer/headroom:    22GB  (cho KV cache + burst)
```

**Ket luan:** DU RAM cho tat ca. Khong can chon 1 trong 2.

---

## I. INFRASTRUCTURE — Mo Het Van (An Toan)

### Thay Ollama bang MLX (Uu tien #1)

| | Ollama | MLX | Winner |
|---|--------|-----|--------|
| Tok/s (32B Q4) | 35 | 50-70 | MLX +100% |
| TTFT | 1.5s | 0.5s | MLX 3x |
| Memory | 30GB | 24GB | MLX -20% |
| Apple Silicon native | No (llama.cpp) | Yes (Metal) | MLX |
| OpenAI-compatible API | Yes | Yes (mlx_lm.server) | Tie |

**Setup MLX tren M1 Max:**
```bash
# Cai MLX
pip install mlx-lm

# Chay server (OpenAI-compatible)
mlx_lm.server \
  --model mlx-community/Qwen2.5-Coder-32B-Instruct-4bit \
  --port 11434 \
  --host 0.0.0.0

# OpenClaw tro vao
export LLM_BASE_URL=http://127.0.0.1:11434/v1
export LLM_MODEL=mlx-community/Qwen2.5-Coder-32B-Instruct-4bit
```

### Ollama Backup Config (neu giu Ollama)
```bash
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_NUM_CTX=32768
export OLLAMA_KV_CACHE_TYPE=q4_0
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KEEP_ALIVE="24h"
export OLLAMA_NUM_THREADS=8
```

### Thermal + Power
```bash
caffeinate -dims &                    # Ngan sleep
sudo pmset -a hibernatemode 0        # Tat hibernate
sudo pmset -a sleep 0                # Tat auto-sleep
```

---

## II. RAAS REVENUE ENGINE

### OpenClaw da co san

| Asset | Count | Status |
|-------|-------|--------|
| Commands | 342+ | Built |
| Skills | 542 | Built |
| MCU billing | Yes | Polar.sh integrated |
| Agent hierarchy | 6 layers | Built |
| CTO daemon | PEV loop | Running |

### Revenue Model

```
RaaS (Robot-as-a-Service):
  Starter: $49/mo (200 MCU)
  Pro:     $149/mo (1,000 MCU)
  Enterprise: $499/mo (unlimited)

Target: 100 Pro customers = $14,900/mo MRR
Timeline: 6 months to $15K MRR
```

### AI Sales Pipeline (chay tren M1 Max)

```
Local Qwen 32B handles:
  1. Lead scraping + qualification    → 1000+ leads/mo
  2. Personalized outreach emails     → 100+ emails/mo
  3. Proposal generation              → 50+ proposals/mo
  4. Follow-up sequences              → automated

Cloud Claude handles:
  5. Complex negotiation responses    → when needed
  6. Contract review                  → when needed

Cost: $28.50 per 100 leads (local) vs $285 (cloud)
ROI: 7,750% per converted deal
```

---

## III. ALGO-TRADER — POLYMARKET

### Architecture (chay song song voi RaaS)

```
M1 Max Process Map:
┌─────────────────────────────────────────────┐
│ Process 1: MLX Server (Qwen 32B)            │
│   Port 11434 — shared by RaaS + Trading     │
│   RAM: 24GB                                 │
├─────────────────────────────────────────────┤
│ Process 2: Algo-Trader (Node.js)            │
│   - Polymarket WebSocket feed               │
│   - Binary arb detector                     │
│   - Risk manager + circuit breakers         │
│   RAM: 4GB                                  │
├─────────────────────────────────────────────┤
│ Process 3: OpenClaw CTO Daemon              │
│   - CC CLI orchestration                    │
│   - RaaS customer missions                  │
│   RAM: 4GB                                  │
├─────────────────────────────────────────────┤
│ Process 4: ChromaDB (vector memory)         │
│   - Agent long-term memory                  │
│   - Trading history + patterns              │
│   RAM: 2GB                                  │
└─────────────────────────────────────────────┘
Total: ~34GB / 64GB = 53% utilization (headroom: 30GB)
```

### Trading Strategy Stack

| Strategy | Win Rate | Monthly ROI | LLM Role |
|----------|----------|-------------|----------|
| Information Edge | 50-80% | 4-6% | News sentiment filter |
| Binary Arbitrage | 60-75% | 3-5% | Probability calibration |
| Settlement Arb | 70-90% | 8-12% | Event resolution prediction |
| Market Making | 78-85% | 1-3% | Spread optimization |

**LLM Integration Pattern:**
```
News arrives → Qwen 32B scores sentiment (0-1)
  ├── Score > 0.7 → Signal to trade
  ├── Score 0.4-0.7 → Hold, monitor
  └── Score < 0.4 → Skip (avoid loss)

Result: -46.5% losing trade size, +3.1% win rate
```

### Polymarket Gaps (5-8 ngay code)

| File | Purpose | Days |
|------|---------|------|
| `polymarket-ws-feed.ts` | WebSocket price feed | 1 |
| `polymarket-signer.ts` | ECDSA order signing | 1 |
| `polymarket-adapter.ts` | CLOB integration | 1 |
| `settlement-listener.ts` | Event resolution | 1 |
| `binary-opportunity-detector.ts` | Arb detection | 1 |
| `binary-arbitrage-executor.ts` | Arb execution | 1 |
| `binary-market-maker.ts` | MM strategy | 1 |
| `probability-calibrator.ts` | LLM probability | 1 |

---

## IV. UNIFIED SCHEDULE

### Week 1 (Mar 24-30): Infrastructure

| Day | Task | Workload |
|-----|------|----------|
| Mon | MLX setup + benchmark on M1 Max | Infra |
| Tue | Qwen 2.5-Coder-32B install + test | Infra |
| Wed | LLM Router (local vs cloud) | Code |
| Thu | ChromaDB + agent memory | Code |
| Fri | Polymarket WebSocket + signer | Trading |
| Sat-Sun | Polymarket adapter + settlement | Trading |

### Week 2 (Mar 31 - Apr 6): Trading MVP

| Day | Task | Workload |
|-----|------|----------|
| Mon | Binary arb detector + executor | Trading |
| Tue | Market maker + probability calibrator | Trading |
| Wed | Backtesting trên 6 thang data | Trading |
| Thu | Paper trading ($50K testnet) | Trading |
| Fri | Risk tuning + circuit breakers | Trading |
| Sat-Sun | Go-live mainnet (nếu backtest > 55% win) | Trading |

### Week 3-4 (Apr 7-20): RaaS Sales

| Week | Task | Workload |
|------|------|----------|
| W3 | AI lead gen + outreach pipeline | RaaS |
| W4 | First 10 RaaS customers | RaaS |

### Month 2-3: Scale

```
Trading: $50K → $200K capital, 4-strategy stack
RaaS: 10 → 50 customers, $7.5K MRR
AGI Factory: Self-improving agent loops
```

---

## V. REVENUE PROJECTION (12 MONTHS)

| Source | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|----------|
| RaaS MRR | $2K | $15K | $50K |
| Trading profit | $3K | $10K | $30K |
| **Total/month** | **$5K** | **$25K** | **$80K** |
| **Annual run rate** | $60K | $300K | **$960K** |

**Chi phi:**
- M1 Max hardware: $0 (da co)
- Cloud API: $400-1,200/mo
- Polymarket capital: $50K (rotating)
- Total opex: ~$1,500/mo

**Net margin: 92-97%**

---

## VI. RISK MATRIX

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Trading loss >20% | Medium | High | Kelly 25%, circuit breaker, daily cap $500 |
| Polymarket regulatory | Low | High | Diversify to Kalshi, Metaculus |
| M1 Max hardware failure | Low | Critical | Cloud fallback (OpenRouter) |
| RaaS slow adoption | Medium | Medium | Free tier, content marketing |
| LLM edge degradation | Medium | Medium | Multi-model ensemble |

---

## VII. IMMEDIATE NEXT STEPS

1. **NGAY BAY GIO:** Khi M1 Max len lai → fix Ollama config an toan
2. **Ngay mai:** Cai MLX + Qwen 2.5-Coder-32B, benchmark
3. **Ngay 3:** Build LLM Router + ChromaDB
4. **Ngay 4-8:** Code 8 files Polymarket integration
5. **Ngay 9-10:** Backtest + paper trade
6. **Ngay 11+:** Go-live trading + RaaS sales pipeline

---

## REPORTS REFERENCE

### AGI Factory Research (lan 1)
- `researcher-260322-2259-agi-solo-factory-research.md`
- `researcher-260322-2300-local-llm-m1-max-optimization.md`
- `researcher-260322-2300-agi-factory-evolution.md`
- `research-260322-2303-agi-solo-factory-master-strategy.md`

### Polymarket Trading Research (lan 2)
- `INDEX-260322-polymarket-research.md`
- `researcher-260322-2341-executive-summary.md`
- `researcher-260322-2341-algo-trader-architecture-analysis.md`
- `researcher-260322-2341-polymarket-integration-plan.md`
- `researcher-260322-2341-polymarket-ai-trading-comprehensive.md`

---

*Generated: 2026-03-22 23:52 ICT*
*Data: 5 researcher agents, 60+ web searches, 90+ sources*

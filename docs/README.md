# Mekong CLI — Documentation Hub

Welcome to the documentation for **Mekong CLI**, the AI-operated business platform for Vietnamese enterprises and solo founders.

---

## Architecture Overview

```
mekong (CLI) / api-gateway (FastAPI)
  ├── src/core/        — Zero-dependency domain engines (Tax, Disputes, Maritime, etc.)
  ├── src/cli/         — Typer CLI application, formatting, and commands
  ├── src/harness/     — PEV engine (Plan-Execute-Verify), agents, observability
  ├── scripts/         — MCP JSON-RPC and FastMCP servers
  └── tests/           — Pytest automated test suites
```

---

## Core Modules & Features

### 1. Dispute Resolution & Maritime Law (Phases 159 - 162)
- **Arbitration (VIAC 2024):** Clause validity, 6-tier fee scale, Sole Arbitrator 30% discount.
- **Enforcement (THADS):** 5-year limitation, 3% fee with 200M cap, Article 47 priority queue.
- **Litigation (BLTTDS):** District vs Provincial jurisdiction, Resolution 326 court fee scale.
- **Maritime (BLHH 2015):** Hague-Visby SDR package/weight limits, York-Antwerp General Average, Salvage rewards, and maritime liens.

### 2. Business Funnels
- **Zalo OA:** Customer communication automation.
- **Tax & Accounting:** TNCN, TNDN, GTGT compliance, and Circular 78 electronic invoices.
- **Sophia AI Video Factory:** Multi-platform video generation via Cloudflare Workers.

---

## CLI Usage Examples

### Commercial Arbitration
```bash
mekong dispute viac-fee 1500000000 --sole
mekong dispute arbitration-clause "Mọi tranh chấp giải quyết tại VIAC"
```

### Civil Judgment Enforcement
```bash
mekong dispute enforcement-fee 500000000
mekong dispute enforcement-priority 100000000 --alimony 20000000 --labor 30000000 --court 10000000 --other 20000000
```

### Court Litigation
```bash
mekong dispute court-fee 500000000
mekong dispute court-jurisdiction --foreign --province "Đà Nẵng"
```

### Maritime Disputes & Shipping
```bash
mekong dispute carrier-liability 10 2000 500000000
mekong dispute general-average --ship-val 1000000000 --cargo-val 500000000 --ship-loss 50000000
```

---

## Testing & Quality

Run the test suite:
```bash
python3 -m pytest tests/test_dispute_maritime_suite.py -v
```

Lint with Ruff:
```bash
python3 -m ruff check src/ tests/
```

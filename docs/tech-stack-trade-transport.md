# Tech Stack — International Trade, Transport & Trade Remedies Suite (Phases 163 - 166)

## 1. Architecture Philosophy
- **100% Python Standard Library**: All mathematical, statutory, and legal algorithms in `src/core/trade_transport_engine.py` rely strictly on standard library packages (`dataclasses`, `datetime`, `enum`, `typing`, `math`). Zero external dependencies.
- **Dual Client Exposure**:
  1. **Typer CLI (`src/cli/commands/trade_command.py`)**: Terminal UI enriched with Rich panels, tables, and machine-readable `--json` output.
  2. **MCP Tool Handlers (`scripts/mcp_server.py`)**: Dual FastMCP & JSON-RPC protocols for AI agent interactions.
- **Strict AST Boundary**: Verified by test fixtures to forbid third-party HTTP or heavy frameworks in core engine layers.

## 2. Core Engines & Data Structures
```
src/core/trade_transport_engine.py
├── MultimodalTransportEngine (Phase 163)
│   ├── calculate_mto_liability()
│   ├── check_mto_claim_limitation()
├── AirCarrierLiabilityEngine (Phase 164)
│   ├── calculate_passenger_injury_liability()
│   ├── calculate_cargo_liability()
│   ├── calculate_baggage_delay_liability()
│   ├── check_aviation_limitation()
├── InternationalSalesIncotermsEngine (Phase 165)
│   ├── evaluate_fundamental_breach()
│   ├── calculate_cisg_price_reduction()
│   ├── lookup_incoterms_rule()
└── TradeRemediesEngine (Phase 166)
    ├── calculate_dumping_margin()
    ├── assess_anti_dumping_application()
    ├── assess_safeguard_surge()
```

## 3. Reference Exchange Rates & Constants
- `DEFAULT_SDR_VND_RATE`: 34,500.0 VND/SDR.
- MTO Unlocalized Loss: 666.67 SDR/pkg & 2.0 SDR/kg (with sea/waterway leg); 8.33 SDR/kg (pure inland).
- Montreal Air Cargo Limit: 22.0 SDR/kg; Baggage: 1,288.0 SDR; Passenger Delay: 5,346.0 SDR; Strict Bodily Injury: 128,821.0 SDR.
- De Minimis Dumping Margin: 2.0%; Negligible Import Volume: 3.0%.

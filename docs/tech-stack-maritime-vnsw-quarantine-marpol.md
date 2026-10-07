# Tech Stack Architecture: Maritime Single Window, Border Control, Quarantine & MARPOL (Phases 191–194)

## 1. Core Technical Stack
- **Pure Standard Library Invariant**: Python 3.9+ standard library only (`dataclasses`, `datetime`, `enum`, `math`, `typing`, `json`, `hashlib`, `re`) in `src/core/maritime_vnsw_quarantine_marpol_engine.py`.
- **Zero External Dependencies**: Pure AST verifiable, zero network I/O, deterministic in-memory calculations and validation logic.
- **CLI Framework**: Typer + Rich tables (`src/cli/commands/maritime_vnsw_quarantine_marpol_command.py`) with `--json` headless automation.
- **Agent/MCP Interface**: FastMCP server endpoints and JSON-RPC dispatchers in `scripts/mcp_server.py`.
- **Test Automation**: pytest test suite in `tests/test_maritime_vnsw_quarantine_marpol_suite.py` with AST import enforcement and 100% test coverage.

## 2. Domain Engines Breakdown
1. **Phase 191 - Maritime Single Window & Port Clearance (`MaritimeSingleWindowEngine`)**:
   - Timelines: 24h arrival notice, 2h arrival confirmation, 2h departure notice.
   - FAL Form 1-7 + Vietnam specific declarations verification.
   - Cryptographic e-Port Clearance signature hash & QR payload assembler.
   - Maritime tonnage dues and safety fees calculation (Circular 261/2016/TT-BTC).

2. **Phase 192 - Seafarer Safe Manning & Border Control (`SeafarerImmigrationEngine`)**:
   - STCW 78/2010 Manila amendments minimum safe manning levels.
   - Crew list passport & Seaman Discharge Book validity.
   - Decree 77/2017/NĐ-CP Shore Pass (Thẻ đi bờ) & Transit Visa evaluator.

3. **Phase 193 - Maritime International Health Quarantine (`MaritimeHealthQuarantineEngine`)**:
   - IHR 2005 Maritime Declaration of Health.
   - 6-month Ship Sanitation Control Exemption Certificate (SSCEC/SSCC) audit.
   - Free Pratique granting vs Yellow Quarantine Flag requirement.

4. **Phase 194 - MARPOL 73/78 & Port Reception Facilities (`MARPOLPortReceptionEngine`)**:
   - Annex I: 15 ppm Bilge Water Separator (OWS) & Oil Discharge Monitoring.
   - Annex VI: 0.50% global sulfur cap vs 0.10% ECA fuel check.
   - Port Reception Facilities (PRF) mandatory waste delivery certificate under Decree 08/2022/NĐ-CP.

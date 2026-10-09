# Kiến trúc Công nghệ: Maritime Phases 339–342

**Tiêu chuẩn Kiến trúc:** Hybrid Modular Facade (<200 LOC/file), Clean Architecture, Zero-Mock Testing.

## 1. Công nghệ & Thư viện
- **Runtime:** Python 3.11+
- **Kiến trúc Lõi (Core Engines):** Standard Library (`dataclasses`, `math`, `typing`, `enum`) — Không phụ thuộc ngoại vi nặng, bảo đảm tính toán thời gian thực determinism.
- **Giao diện Dòng lệnh (CLI):** Typer (v0.9.0+) + Click + Rich formatting.
- **AI Agent Integration:** FastMCP (Model Context Protocol) với async endpoints.
- **Kiểm thử Tự động:** Pytest, pytest-asyncio, Typer CliRunner.

## 2. Tiêu chuẩn Kỹ thuật Quốc tế
| Phân hệ | Cơ quan Ban hành | Văn bản / Công ước Áp dụng |
|---|---|---|
| **Phase 339** | IMO / MSC / MEPC | IMO Polar Code Res. MSC.385(94), MSC.1/Circ.1519 (POLARIS RIO) |
| **Phase 340** | IMO / MEPC | MARPOL Annex V Reg 4 & 6, Res. MEPC.295(71), IMSBC Code |
| **Phase 341** | IMO / EMSA | SOLAS II-2 Reg 20, MSC.1/Circ.1615, EMSA Ro-Ro EV Guidelines |
| **Phase 342** | IMO / Lloyd's / P&I | Salvage Convention 1989 (Art 13/14), LOF 2024, SCOPIC Clause |

## 3. Cấu trúc Mô-đun Code (<200 LOC/file)
1. `src/core/maritime/phase_339_polar_code_polaris_rio.py`: POLARIS RIO, Ice Class matrix, PST calculation.
2. `src/core/maritime/phase_340_hold_washwater_marpol_hme.py`: MARPOL Annex V HME/Non-HME rules, chemical dosage, pH neutralization.
3. `src/core/maritime/phase_341_pctc_ev_fire_safety.py`: EV off-gas detection, deluge flow rate, fire blanket rating.
4. `src/core/maritime/phase_342_salvage_lof_scopic_compensation.py`: LOF Art 13 No Cure-No Pay, SCOPIC tariff, 25% uplift & Art 14 discount.
5. `src/core/maritime_polar_wash_ev_salvage_engine.py`: Central Unified Facade.
6. `src/cli/commands/maritime_polar_wash_ev_salvage_command.py`: 4 Typer apps & direct JSON output.
7. `scripts/mcp_server.py`: 4 FastMCP async tool handlers.
8. `tests/test_maritime_polar_wash_ev_salvage_suite.py`: 18+ zero-mock unit, CLI, and FastMCP tests.

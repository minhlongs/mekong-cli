# Tech Stack Specification: Phases 271-274 Maritime Casualty, e-C/O, Tugboat Tariffs & SOLAS VGM Suite

## Architectural Blueprint
Zero external dependencies across the core engine layer, adhering to pure Python standard library principles (`dataclasses`, `datetime`, `enum`, `math`, `typing`).

```
mekong (CLI) / FastMCP (Agent Tools)
  │
  ├── src/core/maritime_casualty_co_tug_vgm_engine.py
  │     ├── CasualtyInquiryEngine (Phase 271)
  │     ├── ElectronicCOEngine (Phase 272)
  │     ├── SeaportTugTariffEngine (Phase 273)
  │     └── SolasVgmEngine (Phase 274)
  │
  ├── src/cli/commands/maritime_casualty_co_tug_vgm_command.py
  │     ├── casualty_app ("casualty" / "tainan")
  │     ├── co_app ("coform" / "xuatxuhanghoa")
  │     ├── tug_app ("tugtariff" / "laidatcang")
  │     └── vgm_app ("solasvgm" / "xacnhankhoiluong")
  │
  ├── scripts/mcp_server.py
  │     ├── mekong_marine_casualty_inquiry_evaluate
  │     ├── mekong_electronic_co_origin_evaluate
  │     ├── mekong_seaport_tugboat_tariff_calculate
  │     └── mekong_solas_vgm_container_verify
  │
  └── tests/test_maritime_casualty_co_tug_vgm_suite.py
        ├── AST zero-dependency verification
        ├── Core mathematical tests
        ├── Typer CLI command tests
        └── FastMCP handler tests
```

## Key Technical Invariants
1. **Zero External Dependencies**: Validated via Python AST parse tree inspecting all imports.
2. **Dual Currency Tariffs**: Tugboat charges computed in USD for international voyages and VND for domestic voyages, parameterized by port zone (Zones I, II, III).
3. **Double Verification on Origin**: Supports both Direct (Build-Up) and Indirect (Build-Down) RVC calculations, with De Minimis tolerance evaluation (10%).
4. **SOLAS No-VGM-No-Load**: Rejection flags raised when declared VGM is missing, exceeds CSC $R_{\text{max}}$, or violates the $\pm 5\% / \pm 500\text{kg}$ tolerance.

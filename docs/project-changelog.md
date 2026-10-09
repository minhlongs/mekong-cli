# Project Changelog - Mekong CLI v6.0

## [2026-10-09] - Phases 351-354 Shipped
- **Phase 351/Bulk Loading Stability:** Shipped `BulkLoadingEngine` implementing SOLAS XII/11 loading computers, IACS UR S1/S1A longitudinal strength (SWBM & SWSF percentage limits), and IMO 2008 Intact Stability Code criteria ($GM_{\text{fluid}} \ge 0.15\text{ m}$, $GZ_{30^\circ} \ge 0.20\text{ m}$, $GZ_{40^\circ} \ge 0.20\text{ m}$).
- **Phase 352/HNS Chemical Spill Drift:** Shipped `HnsDriftEngine` implementing OPRC-HNS Protocol 2000, CEDRE SEACARAMB 4-quadrant behavior model (Evaporator, Floater, Dissolver, Sinker), vector leeway drift physics ($100\%$ current + $3\%$ wind leeway), and dynamic emergency isolation perimeters.
- **Phase 353/Central Seawater Cooling & MGPS:** Shipped `CentralCoolingEngine` implementing Plate Heat Exchanger (PHE) logarithmic mean temperature difference (LMTD), seawater scoop injection energy conservation ($V \ge 12\text{ kts}$ saving up to $45\text{ kW}$ pumping power), and Marine Growth Prevention System (MGPS) electrolytic Cu/Al ion dosing ($2.0 - 10.0\ \mu\text{g/L}$).
- **Phase 354/Marine E-Certificates:** Shipped `MarineEcertEngine` implementing IMO FAL.5/Circ.39/Rev.2 electronic statutory certificates, Unique Tracking Number (UTN) validation, SHA-256 cryptographic proof verification, lifecycle auditing, and port clearance acceptance checks.
- **Architecture & Interfaces:** Built using Hybrid Modular Facade pattern with all files strictly $< 200\text{ LOC}$, 4 Typer CLI command groups with 8 bilingual Vietnamese aliases (`loadingcomp`/`ondinhtau`, `hnsdrift`/`toicathns`, `centralcool`/`lammatbien`, `ecert`/`chungchiso`), 4 FastMCP tools in `scripts/mcp_server.py`, and 16/16 zero-mock tests passing 100%.

## [2026-10-08] - Phases 291-294 Shipped
- **Phase 291/MARPOL Sewage:** Added `SewageDischargeEngine` validting continuous effluent parameter criteria under MEPC.227(64) and minimum distance & speed variables.
- **Phase 292/STCW Medical:** Introduced `SeafarerMedicalEngine` implementing comprehensive physical, vision, hearing parameters and medical disqualifications for Deck & Engine watchkeeping duties.
- **Phase 293/Port Stevedoring:** Released `StevedoringTariffEngine` based on TT 39/2023 for precise handling cost analysis factoring port region, load status, and dangerous goods modifiers.
- **Phase 294/Customs Bonded Warehouse:** Shipped `BondedWarehouseEngine` enforcing Law on Customs Article 61/63 strict chronologies for bonded inventory holding, extensions, and mandatory forfeiture protocol.
- Integrations: Fully linked to standard FastMCP endpoints and built modular test suites leveraging zero-mock architectural principles.

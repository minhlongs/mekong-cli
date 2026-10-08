# Project Changelog - Mekong CLI v6.0

## [2026-10-08] - Phases 291-294 Shipped
- **Phase 291/MARPOL Sewage:** Added `SewageDischargeEngine` validting continuous effluent parameter criteria under MEPC.227(64) and minimum distance & speed variables.
- **Phase 292/STCW Medical:** Introduced `SeafarerMedicalEngine` implementing comprehensive physical, vision, hearing parameters and medical disqualifications for Deck & Engine watchkeeping duties.
- **Phase 293/Port Stevedoring:** Released `StevedoringTariffEngine` based on TT 39/2023 for precise handling cost analysis factoring port region, load status, and dangerous goods modifiers.
- **Phase 294/Customs Bonded Warehouse:** Shipped `BondedWarehouseEngine` enforcing Law on Customs Article 61/63 strict chronologies for bonded inventory holding, extensions, and mandatory forfeiture protocol.
- Integrations: Fully linked to standard FastMCP endpoints and built modular test suites leveraging zero-mock architectural principles.

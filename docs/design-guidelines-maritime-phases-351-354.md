# Design Guidelines: Maritime Phases 351–354

## 1. Architectural Philosophy
- **Hybrid Modular Facade Pattern**: 4 dedicated micro-engines inside `src/core/maritime/`, bound together by a unified, lightweight central facade `src/core/maritime_loading_hns_cool_ecert_engine.py`.
- **Strict Size Bounds**: All source code, CLI commands, facades, and tests must remain strictly under 200 lines of code.
- **Zero-Mock Verification**: Real physical equations for stability, heat exchange, drift trajectory, and ECDSA/SHA-256 digital signature chains.

## 2. Technical Sub-systems
- **Phase 351**: `loadingcomp` / `ondinhtau` — Bulk Carrier Loading Computer, SOLAS XII/11, IACS UR S1/S1A BM/SF limits, and 2008 IS Code initial GM & GZ curve righting lever.
- **Phase 352**: `hnsdrift` / `toicathns` — Hazardous & Noxious Substances (HNS) chemical spill drift trajectory & CEDRE hazard classification (OPRC-HNS 2000).
- **Phase 353**: `centralcool` / `lammatbien` — Central Seawater Cooling, Plate Heat Exchanger LMTD, Seawater Scoop energy savings & MGPS bio-fouling Cu/Al electrolytic dosing.
- **Phase 354**: `ecert` / `chungchiso` — IMO FAL.5/Circ.39/Rev.2 Electronic Certificates, W3C Verifiable Credentials verification, tamper-evident hash lineage.

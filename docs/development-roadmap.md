# Development Roadmap

## Phases

| Phase | Name            | Status        | Completion % |
|-------|-----------------|---------------|-------------|
| 1     | Spec-kit SDD    | Complete      | 100%        |
| 2     | Command System  | Complete      | 100%        |
| 3     | Billing + Auth  | Complete      | 100%        |
| 4     | Vietnam Hub     | Complete      | 100%        |
| 5     | AI Video (Sophia) | Complete      | 100%        |
| 6     | Cloud Deploy    | Complete      | 100%        |
| 7     | Design Intelligence | Complete | 100%        |
| 8     | Quality Hardening  | Complete | 100%        |
| 159-162 | Dispute Resolution & Maritime Law Suite | Complete | 100% |
| 163-166 | International Trade, Transport & Trade Remedies Suite | Complete | 100% |
| 167-170 | Vietnam Customs, FX, Tech Transfer & Bonded Logistics Suite | Complete | 100% |
| 171-174 | Vietnam FTA Concessions, EPE, AEO & Duty Exemption Suite | Complete | 100% |
| 175-178 | Vietnam E-Com, Specialized Inspection, Chemicals & CBAM Suite | Complete | 100% |
| 179-182 | Vietnam Port Terminal, ICD Cold Chain & SCF Suite | Complete | 100% |
| 183-186 | Vietnam Maritime Operations, Husbandry, P&I & Tokyo MOU PSC Suite | Complete | 100% |
| 187-190 | Vietnam Inland Waterway Navigation, Container Feeder Barging, Maritime SAR & ISPS Security Suite | Complete | 100% |

## Architecture Gaps

| # | Gap                                    | Status   |
|---|----------------------------------------|----------|
| 1 | Duplicated AgentBase / AgentRegistry   | **CLOSED** (2026-09-10) |
| 2 | Billing / Payment Provider Routing     | **CLOSED** (2026-09-10) |
| 3 | Memory store three-way split           | **CLOSED** (2026-09-10) |
| 4 | Harness verifier merge + DAG scheduler swap | **CLOSED** (SC8, 2026-09-08) |
| 5 | External MCP client-side consumption of third-party servers | **CLOSED** (2026-09-09) |
| 6 | CLI command surfaces unification       | **CLOSED** (2026-09-10) |
| 7 | RecipeVerifier autonomous loop merge   | **CLOSED** (2026-09-10) |
| 8 | Orphan command modules clean & shim    | **CLOSED** (2026-09-10) |
| 9 | Tier configuration & rate limiting     | **CLOSED** (2026-09-10) |
| 10 | Funnel restoration (Zalo OA + Tax + Accounting → CLI) | **CLOSED** (2026-09-09) |

## Focus Areas
- PriorityStack + spec-kit SDD pipeline wired
- 39 groups / 128 commands mapped in COMMAND_REGISTRY.md
- MCU billing + license gate active
- MIT license + Python-only contributor flow live
- Core runtime shares `RecipeVerifier`; multi-step plans execute in topological order
- Full convergence of DUPLICATION_MAP items 1-9 across core, harness, and seed layers
- Programmatic JWT session rotation via `POST /auth/refresh` with dynamic tier upgrade resolution and rate limiting
- Vietnam Hub complete (100%): 3 business funnels (Zalo OA, Tax, Accounting) wired into CLI/API, VietQR webhook HMAC verification, multi-tenant org isolation, bilingual soft paywall gate
- Cloud Deploy complete (100%): Unified `deploy` CLI sub-app (`new`, `run`, `status`, `rollback`) supporting Cloudflare, Docker, and custom platform deployments with fail-closed error handling and dry-run simulation
- AI Video Factory (Sophia) complete (100%): RaaS video production engine for Vietnam wired into CLI via `mekong tools video` (`render`, `create`, `status`, `list`, `avatars`, `voices`, `templates`, `cost`), ElevenLabs/D-ID/HeyGen catalogs, Design DNA brand styling integration, MCU credit billing, and deterministic dry-run verification
- Quality Hardening complete (100%): pytest-timeout wired into CI (`--timeout=60`), `file_stats` scoped to `src/` subtree with path traversal guard, pytest config consolidated into canonical `pytest.ini`, stale `cli/` imports repaired, `.orchestrate/` gitignored
- International Trade, Transport & Trade Remedies Suite complete (Phases 163-166, 100%): Multimodal Transport Operator (NĐ 87/2009 & NĐ 144/2018), Civil Aviation Carrier Liability & Montreal 1999 (Luật HKDD 2006/2014), CISG 1980 International Sales & Incoterms 2020, and Vietnamese Trade Remedies & Anti-Dumping (Luật QLNT 2017 & NĐ 10/2018) wired into pure standard library core, rich CLI (`trade`/`thuongmai`), and MCP JSON-RPC/FastMCP servers with 100% green tests.
- Vietnam Customs, FX, Tech Transfer & Bonded Logistics Suite complete (Phases 167-170, 100%): Customs Valuation Method 1 (TT 39/2015/TT-BTC & TT 60/2019/TT-BTC) & Rules of Origin RVC (NĐ 31/2018/NĐ-CP), FX Control & SBV Offshore Loans (TT 12/2022/TT-NHNN & TT 06/2019/TT-NHNN) & Profit Remittance (TT 186/2010/TT-BTC), Technology Transfer & IP Royalty (Luật CGCN 2017 & NĐ 76/2018/NĐ-CP), and Bonded Warehouse & CFS Logistics (Luật HQ 2014 & NĐ 08/2015/NĐ-CP) wired into zero-dependency core, rich CLI (`customs`/`haiquan`), and MCP tools with 44/44 tests 100% green.
- Vietnam FTA Concessions, EPE, AEO & Duty Exemption Suite complete (Phases 171-174, 100%): EVFTA/CPTPP/RCEP/ATIGA preferential tariff savings & rules of origin (WO/CC/CTH/CTSH/RVC/De Minimis), EPE customs supervision 4-criterion verification (NĐ 35/2022) & on-spot 15-day counterpart tracking (TT 38/2015), AEO priority enterprise evaluation & risk channeling (Luật HQ 2014, TT 72/2015, QĐ 1399/QĐ-TCHQ), and SXXK duty refund & Form 15 BCQT material reconciliation (NĐ 134/2016, TT 39/2018) wired into pure standard library core, rich CLI (`fta`/`dncx`), and FastMCP/JSON-RPC servers with 48/48 tests 100% green.
- Vietnam E-Com, Specialized Inspection, Chemicals & CBAM Suite complete (Phases 175-178, 100%): Cross-Border E-Commerce customs & platform withholding under Decision 78 repeal and Decree 134/2016; Hazardous Chemicals National Single Window import declaration & IMDG Code 41-22 dangerous goods segregation under Decree 113/2017 & Decree 82/2022; Specialized Food Safety 3-tier inspection state machine & quarantine certificate validity under Decree 15/2018; EU CBAM specific embedded emissions liability & EUDR closed polygon geolocation verification under EU Regulations 2023/956 & 2023/1115 wired into zero-dependency core (`ecom_inspect_engine.py`), rich CLI (`ecom-customs`/`tmdt` and `inspect`/`kiemtra`), and FastMCP/JSON-RPC tools with 38/38 tests 100% green.
- Vietnam Port Terminal, ICD Cold Chain & SCF Suite complete (Phases 179-182, 100%): Seaport Terminal Tariffs (Circular 39/2023/TT-BGTVT), Demurrage/Detention with Carrier Maritime Liens (Vietnam Maritime Code 2015 Art. 168), SOLAS VGM gate-in validation (MSC.1/Circ.1475), L/C document examination & usance discounting (ICC UCP 600 / ISBP 745), Pharma cold chain Arrhenius MKT integration (Circular 02/2018/TT-BYT), and ISO 14083 / GLEC v3.0 multimodal freight carbon accounting wired into zero-dependency core (`port_supply_chain_engine.py`), rich CLI (`port`/`cangbien`, `tradefinance`/`scf`), and FastMCP/JSON-RPC tools with 35/35 tests 100% green.
- Vietnam Maritime Operations, Pilotage, Ship Husbandry, Marine Insurance & Tokyo MOU PSC Suite complete (Phases 183-186, 100%): Maritime Pilotage & Tugboat Tariffs (Circular 39/2023/TT-BGTVT), Ship Agency Disbursement & MLC 2006 Seafarer Rest Audit (Decree 160/2016/NĐ-CP & MLC 2006 Reg. 2.1/2.3), Marine Hull Insurance ITC Hulls 83 Constructive Total Loss & P&I Bunker Oil Pollution SDR statutory liability limits (Bunkers Convention 2001 & VN Maritime Code 2015 Art. 326), and Tokyo MOU Port State Control (PSC) NIR Ship Risk Profile (LRS/SRS/HRS) & Code 30 Detention Risk matrix wired into pure standard library core (`maritime_operations_engine.py`), rich CLI (`pilotage`/`hoatieu`, `shipagency`/`daily`, `marineins`/`baohiemhanghai`, `psc`/`kiemtratau`), and FastMCP/JSON-RPC tools with 14/14 tests 100% green.
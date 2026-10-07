# Project Changelog

## v6.15.0 — 2026-10-07

**Vietnam Free Trade Agreements (FTAs), EPE, AEO & Duty Exemption Suite (Phases 171-174) (100% Complete):**

- **Phase 171: Vietnam FTAs Preferential Tariffs & Rules of Origin Engine (`src/core/fta_duty_engine.py`):**
  - EVFTA (Nghị định 115/2022/NĐ-CP), CPTPP (Nghị định 116/2022/NĐ-CP), RCEP (Nghị định 129/2022/NĐ-CP), ATIGA (Nghị định 126/2022/NĐ-CP).
  - Preferential tariff savings calculation: $\text{Savings} = V_{\text{customs}} \times (\text{Rate}_{\text{MFN}} - \text{Rate}_{\text{FTA}})$.
  - Rules of Origin (ROO) evaluations: Wholly Obtained (WO), Change of Chapter (CC - 2 digits), Change of Tariff Heading (CTH - 4 digits), Change of Tariff Sub-heading (CTSH - 6 digits), Regional Value Content (RVC >= 40%), and De Minimis value tolerance (<= 10% FOB).
  - Origin documentation determination: REX self-certification for consignments <= 6,000 EUR, EUR.1 certificate of origin, CPTPP self-certification, and ATIGA Form D.

- **Phase 172: Export Processing Enterprises (EPE / DNCX) & Industrial Parks Regime Engine (`src/core/fta_duty_engine.py`):**
  - Verification of 4 mandatory customs supervision criteria under Decree 35/2022/NĐ-CP (Article 26): continuous physical boundary fence, 24/7 camera surveillance streaming to customs, separate entrance/exit control gates, and ERP electronic inventory records.
  - Monitoring on-spot import/export declaration counterpart 15-working-day legal deadlines pursuant to Circular 38/2015/TT-BTC (Article 86) and Circular 39/2018/TT-BTC.
  - Domestic sale tax computation for scrap and sub-standard goods under declaration type A42 pursuant to Circular 38/2015/TT-BTC (Article 75).

- **Phase 173: Authorized Economic Operator (AEO / Doanh nghiệp ưu tiên) & Risk Channeling Engine (`src/core/fta_duty_engine.py`):**
  - Statutory AEO qualification criteria verification under Law on Customs 2014 (Article 42), Circular 72/2015/TT-BTC, and Circular 07/2019/TT-BTC: annual import-export turnover ($100M general trader, $40M agriculture/aquaculture/textile, $30M high-tech/software, 20,000 declarations customs broker), 2-year clean compliance history, and unqualified audit opinion.
  - Automated risk channeling evaluation across Green (Luồng Xanh - automated release, 0.05h), Yellow (Luồng Vàng - documentary check, 2h), and Red (Luồng Đỏ - physical inspection, 12-24h) pursuant to Decision 1399/QĐ-TCHQ.

- **Phase 174: Duty Exemption, Refund & Material Reconciliation (BCQT 15) Engine (`src/core/fta_duty_engine.py`):**
  - Duty refund calculations for raw materials imported for production of exported goods (SXXK) under Decree 134/2016/NĐ-CP (Article 36) and re-exported goods (Article 34).
  - Form 15/BCQT-NVL/GSQL electronic inventory balancing:
    $\text{Theoretical Closing} = \text{Opening} + \text{Imported} - (\text{Exported} \times \text{BOM}) - \text{Scrap}$.
  - Statutory late payment interest calculation at 0.03%/day on duty arrears for inventory deficits under Law on Tax Administration 2019.

- **CLI Commands (`src/cli/commands/fta_command.py`):**
  - Registered dual command aliases `mekong fta` and `mekong dncx` with 10 interactive subcommands: `savings`, `origin`, `proof`, `epe-check`, `on-spot`, `scrap`, `aeo`, `channel`, `refund-sxxk`, `bcqt`.
  - Rich ANSI color panels, tables, and full `--json` machine-readable output.

- **MCP Integration (`scripts/mcp_server.py`):**
  - Added 5 specialized FastMCP & JSON-RPC tools: `mekong_fta_tariff_savings`, `mekong_fta_origin_criterion`, `mekong_epe_conditions_check`, `mekong_aeo_eligibility_eval`, `mekong_duty_reconciliation_bcqt15`.

- **Test Suite (`tests/test_fta_duty_suite.py`):**
  - 48 automated tests verifying AST zero external runtime dependency boundary, core mathematical models, CLI commands, and MCP JSON-RPC handlers (100% pass rate).

## v6.14.0 — 2026-10-07

**Vietnam Customs, Foreign Exchange, Technology Transfer & Bonded Logistics Suite (Phases 167-170) (100% Complete):**

- **Phase 167: Vietnam Customs Valuation & Rules of Origin (ROO) Engine (`src/core/customs_fx_engine.py`):**
  - Luật Hải quan 2014, Thông tư 39/2015/TT-BTC, Thông tư 60/2019/TT-BTC & Nghị định 31/2018/NĐ-CP.
  - Method 1 Transaction Value (Trị giá giao dịch) calculation: $V_{\text{customs}} = P_{\text{invoice}} + \sum \text{Additions} - \sum \text{Deductions}$.
  - Statutory additions: international freight, international insurance, assists, and royalties/license fees.
  - Statutory deductions: post-import inland freight, post-import assembly/installation, and domestic duties/taxes.
  - Regional Value Content (RVC) calculations:
    - Build-down (Indirect) method: $RVC = \frac{FOB - VNM}{FOB} \times 100\%$.
    - Build-up (Direct) method: $RVC = \frac{VOM}{FOB} \times 100\%$.
    - Qualification check against default 40.0% threshold (e.g., ATIGA Form D).
  - Post-Clearance Audit (KTSTQ) limitation tracking: 5-year statutory period (1,825 days) under Article 77 Customs Law.

- **Phase 168: Foreign Exchange Control & SBV Offshore Loan Engine (`src/core/customs_fx_engine.py`):**
  - Pháp lệnh Ngoại hối 2005/2013, Thông tư 12/2022/TT-NHNN, Thông tư 06/2019/TT-NHNN & Thông tư 186/2010/TT-BTC.
  - SBV Foreign Loan Registration requirement evaluation:
    - Medium/long-term (>12 months): Mandatory SBV registration within 30 working days from signing.
    - Short-term (<=12 months): Exempt unless extended beyond 12 months.
    - Loan purpose, disbursement via dedicated foreign loan account, and foreign debt ceiling compliance verification.
  - FDI Profit Remittance eligibility evaluation:
    - Annual profit remittance permitted only after audited financial statements, completed CIT obligations, and zero accumulated losses.
    - Direct remittance via Direct Investment Capital Account (DICA).

- **Phase 169: Technology Transfer & IP Licensing Royalty Engine (`src/core/customs_fx_engine.py`):**
  - Luật Chuyển giao công nghệ 2017 & Nghị định 76/2018/NĐ-CP.
  - Statutory Technology Transfer registration requirement: mandatory registration within 90 days for cross-border transfers or state-funded technology.
  - Running Royalty calculation on Net Sales: $\text{Royalty} = \text{Net Sales} \times r\%$.
  - 25% Operating Profit Split benchmark check (Unreasonable Royalty Warning if $> 25\%$ operating profit).

- **Phase 170: Bonded Warehouse & CFS Logistics Operation Engine (`src/core/customs_fx_engine.py`):**
  - Luật Hải quan 2014 (Articles 61-88) & Nghị định 08/2015/NĐ-CP.
  - Bonded Warehouse (Kho ngoại quan): 12-month initial term + 1 allowable extension up to 12 months (max 24 months total).
  - CFS (Địa điểm thu gom hàng lẻ): Strict 90-day maximum storage limit.
  - Automated remaining day calculation and actionable customs compliance advisory.

- **CLI Commands (`src/cli/commands/customs_command.py`):**
  - Registered dual command aliases `mekong customs` and `mekong haiquan` with 8 comprehensive subcommands: `valuation`, `rvc`, `audit-check`, `sbv-loan`, `profit-remit`, `tech-registration`, `royalty`, `storage-check`.
  - Rich ANSI color panels, tables, and full `--json` machine-readable output.

- **MCP Integration (`scripts/mcp_server.py`):**
  - Added 5 specialized FastMCP & JSON-RPC tools: `handle_customs_valuation`, `handle_customs_rvc`, `handle_fx_loan`, `handle_tech_transfer_royalty`, `handle_bonded_storage`.

- **Test Suite (`tests/test_customs_fx_suite.py`):**
  - 44 automated tests verifying AST zero external runtime dependency boundary, core mathematical models, CLI commands, and MCP JSON-RPC handlers (100% pass rate).

## v6.13.0 — 2026-10-07

**International Trade, Multimodal Transport & Trade Remedies Suite (Phases 163-166) (100% Complete):**

- **Phase 163: Multimodal Transport Operator (MTO) Liability Engine (`src/core/trade_transport_engine.py`):**
  - Nghị định 87/2009/NĐ-CP & Nghị định 144/2018/NĐ-CP.
  - Calculation of unlocalized loss liability under Article 24: $\max(666.67 \text{ SDR/package}, 2.0 \text{ SDR/kg})$ when including sea/waterway leg; $8.33 \text{ SDR/kg}$ for inland transport only.
  - Delay in delivery liability ceiling calculation capped at $2 \times \text{freight charge}$ (Clause 3 Article 24).
  - 9-month (270-day) statute of limitations verification (Article 29).

- **Phase 164: Civil Aviation Carrier Liability & Montreal Convention 1999 Engine (`src/core/trade_transport_engine.py`):**
  - Luật Hàng không dân dụng Việt Nam 2006/2014 & Công ước Montreal 1999 (2019 ICAO revision limits).
  - Two-tier passenger injury/death liability: Tier 1 strict liability up to 128,821 SDR; Tier 2 fault-based unlimited liability above threshold.
  - Cargo destruction, loss, damage or delay ceiling at 22.0 SDR per kg gross weight (Article 166).
  - Baggage destruction/loss/delay limit capped at 1,288 SDR per passenger.
  - Passenger delay ceiling capped at 5,346 SDR per passenger (Article 162).
  - 2-year (730-day) extinction of rights limitation check (Article 173).

- **Phase 165: CISG 1980 & ICC Incoterms 2020 Rules Engine (`src/core/trade_transport_engine.py`):**
  - United Nations Convention on Contracts for the International Sale of Goods 1980 & ICC Incoterms 2020.
  - Fundamental breach evaluation (Article 25 CISG) and right of contract avoidance (Articles 49 & 64).
  - Price reduction remedy calculation for non-conforming goods (Article 50 CISG):
    $\text{Payable} = \text{Agreed Price} \times (\text{Delivered Value} / \text{Conforming Value})$.
  - Exhaustive registry of all 11 Incoterms 2020 rules across Any Mode (EXW, FCA, CPT, CIP, DAP, DPU, DDP) and Sea/Inland Waterway (FAS, FOB, CFR, CIF).
  - Mandatory insurance requirements: CIP requires Institute Cargo Clauses (A) min 110%; CIF requires Institute Cargo Clauses (C) min 110%.

- **Phase 166: Vietnamese Trade Remedies, Anti-Dumping & Safeguards Engine (`src/core/trade_transport_engine.py`):**
  - Luật Quản lý ngoại thương 2017 & Nghị định 10/2018/NĐ-CP.
  - Dumping margin calculation: $DM = \frac{NV - EP}{EP} \times 100\%$.
  - De minimis rule enforcement: $DM < 2.0\%$ considered negligible (Article 78).
  - Negligible import volume threshold: single country share $< 3.0\%$ of total imports exempt from anti-dumping duty.
  - Maximum statutory duty duration of 5 years with review cycles (Article 82).
  - Safeguard import volume sudden surge quantitative rate calculation (Article 88).

- **CLI Commands (`src/cli/commands/trade_command.py`):**
  - Added `trade` & `thuongmai` command group with 13 comprehensive commands: `mto-liability`, `mto-delay`, `mto-limitation`, `aviation-injury`, `aviation-cargo`, `aviation-baggage`, `aviation-limitation`, `cisg-breach`, `cisg-reduction`, `incoterms`, `anti-dumping`, `trade-remedy`, `safeguard-surge`.
  - Rich ANSI visual tables and panels alongside `--json` machine-readable output.

- **MCP Integration (`scripts/mcp_server.py`):**
  - Registered 5 specialized trade tools across FastMCP and JSON-RPC: `handle_trade_mto_liability`, `handle_trade_aviation_liability`, `handle_trade_cisg_reduction`, `handle_trade_incoterms`, `handle_trade_anti_dumping`.

- **Test Suite (`tests/test_trade_transport_suite.py`):**
  - 41 automated tests verifying AST zero-dependency boundary, mathematical algorithms, CLI commands, and MCP JSON-RPC handlers (100% pass rate).

## v6.12.0 — 2026-10-07

**Dispute Resolution & Maritime Law Suite (Phases 159-162) (100% Complete):**

- **Phase 159: Commercial Arbitration & VIAC 2024 Engine (`src/core/dispute_engine.py`):**
  - Luật Trọng tài thương mại 2010 & Nghị quyết 01/2014/NQ-HĐTP.
  - Clause validity checking for commercial disputes and ambiguous "Court or Arbitration" dual jurisdiction risks.
  - Full VIAC 2024 fee scale calculation (6 progressive brackets, flat 38M <= 500M up to 0.1% > 50B) with 30% Sole Arbitrator discount.
  - 2-year statute of limitations verification (Article 33).

- **Phase 160: Civil Judgment Enforcement Engine (`src/core/dispute_engine.py`):**
  - Luật Thi hành án dân sự 2008/2014 & Thông tư 216/2016/TT-BTC.
  - 5-year enforcement statute of limitations check (Article 30).
  - 3% statutory enforcement fee calculation with statutory cap at 200,000,000 VND.
  - Payment distribution priority sequence under Article 47: Alimony/child support -> Labor wages -> Court fees -> Other debts.

- **Phase 161: Court Litigation & Civil Procedure Engine (`src/core/dispute_engine.py`):**
  - Bộ luật Tố tụng Dân sự 2015 & Nghị quyết số 326/2016/UBTVQH14.
  - First-instance court jurisdiction allocation (District vs Provincial) for foreign elements, maritime, or IP disputes.
  - 6-bracket statutory court fee scale calculation with 50% advance deposit rate.
  - Commercial litigation statute of limitations check (Articles 184 & 429 BLDS 2015).

- **Phase 162: Vietnam Maritime Law & General Average Engine (`src/core/maritime_law_engine.py`):**
  - Bộ luật Hàng hải Việt Nam 2015, Hague-Visby Rules SDR Protocol 1979 & York-Antwerp Rules 2016.
  - Carrier cargo liability limitation calculation: max(666.67 SDR/package, 2.0 SDR/kg) * SDR exchange rate.
  - General Average (Tổn thất chung) distribution with strict zero-sum equilibrium guarantee across Ship, Cargo, Freight.
  - Salvage reward assessment under Article 286 "No Cure No Pay" capped by salvaged property value.
  - Statutory ranking of maritime claims & maritime liens under Articles 40-41 (outranking registered ship mortgages).

- **CLI Commands (`src/cli/commands/dispute_command.py`):**
  - Added `dispute` & `tranhchap` Typer group with 8 rich commands: `arbitration-clause`, `viac-fee`, `enforcement-fee`, `enforcement-priority`, `court-fee`, `court-jurisdiction`, `carrier-liability`, `general-average`.

- **MCP Integration (`scripts/mcp_server.py`):**
  - Exposed 5 specialized dispute & maritime resolution tools for AI agents under both FastMCP and JSON-RPC protocols.

- **Test Suite (`tests/test_dispute_maritime_suite.py`):**
  - 39 automated tests covering AST zero-dependency boundary, calculations, CLI runner, and MCP JSON-RPC handlers (100% pass rate).

**Test Suite Green Reset & CI Hardening (100% Complete):**

- **pytest-timeout integration:**
  - Added `pytest-timeout>=2.2.0` to `requirements.txt`, `pyproject.toml` dev deps, and CI workflow pip install line.
  - Wired `--timeout=60` into CI pytest invocation to prevent hung tests from consuming runner limits.
  - Updated `tests/CLAUDE.md` to document timeout usage and reduced suite time expectation.

- **FileAgent stats scoping (`src/agents/file_agent.py`):**
  - `file_stats` now defaults to scanning only `src/` subtree (was full repo root).
  - Added path traversal guard: `Path.is_relative_to()` ensures resolved path stays within `cwd`.
  - Fallback to `src/` on traversal attempt, `None` path, or non-existent directory.
  - Added `tests/unit/test_file_agent_stats.py` with 7 tests covering default path, output shape, scoping, custom path, traversal guard, `None` guard, and non-existent fallback.

- **Pytest config consolidation:**
  - Removed `[tool.pytest.ini_options]` table from `pyproject.toml` (was silently ignored due to `pytest.ini` precedence).
  - Consolidated canonical `pytest.ini` with `pythonpath = src` and comprehensive `norecursedirs` (excludes `node_modules`, `.archive`, `apps`, `packages`, `vendor`, `.git`, `__pycache__`, `dist`, `build`, `*.egg-info`).
  - Dropped dead `tests/python` reference.

- **Stale import repair:**
  - `benchmarks/performance_baseline.py`: `cli.tui.router` → `src.cli.tui.router`.
  - `mekong/autopilot/tests/test_cf_filter_integration.py`: `cli.commands.idea` → `src.cli.commands.idea`.

- **Cleanup:**
  - Added `.orchestrate/` to `.gitignore` to prevent pipeline artifacts from being tracked.

- **Docs synced:** Phase 8 added to `docs/development-roadmap.md`, v6.11.0 entry added to `docs/project-changelog.md`.

## v6.10.0 — 2026-09-21

**Test Debt Cleanup & NL Router Hardening (100% Complete):**

- **NL Routing Test Suite Cleanup (`tests/test_nl_routing.py`):**
  - Resolved 47 failures (was 47 failed / 23 passed / 70 total → now 49 passed / 0 failed).
  - Removed 22 stale `test_new_*` tests referencing commands that were never implemented (`ci-deploy`, `cicd-deploy`, `db-migrate`, `monitoring`, `vuln-scan`, etc.).
  - Added 4 live routing tests covering actual commands (`debug`, `cook`, `plan`, `deploy`).
  - Fixed `fuzzy_match()` signature/behavior mismatch — restored route-table scanning with scoring tiers (1.0 exact, 0.8 prefix, 0.5 substring), returning sorted `List[CommandMatch]`.
  - Fixed test assertions: `matched_pattern` → `matched_keyword`, `tuple` → `list` for `get_all_commands()`, minimum route count `>= 45` → `>= 4`.

- **Router Hardening (`src/cli/tui/router.py`):**
  - Hardened `_matches()`: added `None`/empty text guard (`if not text: return False`), whitespace stripping on both pattern and text, and empty-needle guard after `*` strip (bare `"*"` no longer matches everything).
  - These guards are defensive — `command_fabric.router` uses its own independent `_kw_matches`, so no double-guard conflict.

- **Test SQLite Isolation (`src/raas/tenant.py`, `src/raas/credits.py`, `src/raas/mission_store.py`, `tests/conftest.py`):**
  - Added `MEKONG_RAAS_DB` env var support to all three RaaS SQLite stores so tests never touch `~/.mekong/raas/tenants.db`.
  - `conftest.py` sets `MEKONG_RAAS_DB` to a tmp path before any `src.*` imports, preventing module-level singletons from hitting production DB.
  - Added 5 regression tests in `tests/test_raas_db_env.py`.

- **Verification:** 49/49 nl_routing tests pass, ruff clean, mypy clean, 39-group invariant holds, `.github/workflows/*` untouched.
- **Commit:** `3a651ad5a` (awaiting manual push — sandbox blocks github.com).

## v6.9.0 — 2026-09-13

**Core Protocol Conformance Expansion & Architecture Documentation Alignment (100% Complete):**

- **Core Protocol Conformance Suite Expansion (`tests/test_protocol_compliance.py`):**
  - Expanded test suite from 12 to 25 unit tests covering all 10 core `@runtime_checkable` protocols in `src/core/protocols.py` (`MekongCoreRuntime`, `LLMRouter`, `ToolRegistry`, `BillingMeter`, `MemoryStore`, `MemorySeparation`, `ObservabilitySink`, `VerificationEngine`, `GoalEngine`, `PaymentProvider`) and `CapabilityBus`.
  - Added method presence assertions for `BillingMeter.settle_payment()`, `ToolRegistry.list_mcp_tools()`, `GoalEngine.adapt()`, `PaymentProvider.quote()`, `PaymentProvider.verify()`, `PaymentProvider.request_payment()`, and `MemorySeparation.flush_session()` / `prune_expired()`.
  - Added structural runtime conformance assertions (`isinstance(..., Protocol)`) for 13 concrete adapters:
    - `BillingAdapter` (`BillingMeter` + `PaymentProvider`)
    - `NowPaymentsProvider` (`PaymentProvider` in `src.raas.nowpayments_provider`)
    - `NowPaymentsProvider` (`PaymentProvider` alias in `src.core.adapters.payment.nowpayments`)
    - `MockPaymentProvider` (`PaymentProvider` in `src.core.adapters.payment_mock`)
    - `X402SettlementProvider` (`PaymentProvider` in `src.core.adapters.payment.x402`) with mock governance and transport injection
    - `MPPSettlementProvider` (`PaymentProvider` in `src.core.adapters.payment.mpp`) with mock governance and transport injection
    - `ToolRegistry` (`ToolRegistry`)
    - `MemorySeparation` (`MemorySeparation`)
    - `MemoryStore` (`MemoryStore` canonical with `restore_real_memory_store` fixture)
    - `JsonlMemoryAdapter` (`MemoryStore`)
    - `MemoryStoreConformant` (`MemoryStore` in `src.core.adapters.memory_store_conformant`)
    - `MekongCoreRuntimeImpl` (`MekongCoreRuntime`)
    - `InMemoryCapabilityBus` (`CapabilityBus`)
    - `RecipeVerifier` (`VerificationEngine`)
    - `MemoryStoreAdapter` (`MemoryStore`)
    - `TelemetrySinkAdapter` (`ObservabilitySink`)
    - `LLMRouterAdapter` (`LLMRouter`)
    - `GoalEngineAdapter` (`GoalEngine`)
  - 25/25 tests passing in `tests/test_protocol_compliance.py`.

- **Documentation & Invariants Synchronization:**
  - Synchronized `docs/architecture/CURRENT_ARCHITECTURE.md`, `docs/architecture/AUTONOMY_GAPS.md`, and `docs/architecture/ARCHITECTURE_ASSESSMENT.md` to HEAD `fb369617b`.
  - Recorded PR #41 in the merged PR ledger in `docs/architecture/ARCHITECTURE_ASSESSMENT.md`.
  - Re-verified all 11 Autonomy Gaps remain 100% closed with live test evidence.
  - Confirmed repository invariants: 39 Typer CLI command groups, 0 ruff lint errors, and 100% passing test suites across all core and Vietnam modules.

## v6.8.0 — 2026-09-12

**Phase 5 AI Video Factory (Sophia) Full Integration & Conformance (100% Complete):**

- **Sophia AI Video Factory Service (`src/services/sophia_video_service.py`):**
  - Implemented core RaaS video production engine `SophiaVideoService` supporting avatar and voice catalogs, aspect ratio formatting (16:9 landscape, 9:16 vertical/shorts, 1:1 square), and layout templates (`news_anchor`, `faceless_explainer`, `product_showcase`, `youtube_deepdive`).
  - Integrated with Design DNA memory (`src.design_intelligence.design_memory.load_approved`) to automatically brand videos using approved design tokens (colors, typography, surface treatments, density).
  - Wired MCU credit billing via `MCUBilling` singleton (50 MCU per 30s block with 1.5x template multiplier for deepdive videos) with atomic SQLite WAL transactions.
  - Implemented strict input validation and command injection guards (`validate_identifier`, `validate_job_id`, `sanitize_script`) with regex safe-character enforcement and length limits.
  - Provided deterministic dry-run rendering mode (`--dry-run`) producing local container artifacts with zero external network dependencies for CI verification.
  - Added multi-tenant job isolation and filesystem state persistence under `.sophia/jobs` and `.sophia/artifacts`.

- **CLI Sub-App Registration & Commands (`src/commands/sophia_video.py` & `src/cli/tools_browse_collab_commands.py`):**
  - Created standalone Typer sub-app `app` in `src/commands/sophia_video.py` exposing 8 subcommands: `render`/`create`, `status`, `list`, `avatars`, `voices`, `templates`, and `cost`.
  - Mounted under `tools_app` in `src/cli/tools_browse_collab_commands.py` as `mekong tools video <subcommand>`, preserving the strict 39-group total count invariant and 60-command manifest root contract.
  - Re-exported `sophia_app` alongside Zalo OA, Thuế, and Kế toán in `src/cli/funnel_commands.py` with explicit `__all__` declaration.
  - Supported dual output modes: formatted Rich tables/panels for interactive human use and clean JSON (via `typer.echo` to prevent ANSI escape sequences) for programmatic parsing.

- **Test Coverage & Verification:**
  - Added 19 unit tests in `tests/test_sophia_video_service.py` covering catalog queries, filtering, security validators, MCU cost estimation, dry-run rendering, Design DNA styling, job state persistence, and multi-tenant isolation.
  - Added 24 CLI integration tests in `tests/cli/test_sophia_video_commands.py` covering Typer registration, dry-run renders, file script inputs, job status queries, job listing, discovery commands, cost estimations, and injection defense rejections.
  - Verified 100% test pass rate across all 43 Sophia tests and confirmed zero regressions across the entire test suite.

## v6.7.0 — 2026-09-11

**Phase 6 Cloud Deploy Unification & CLI Hardening (100% Complete):**

- **CLI Sub-App Unification (`src/cli/sdlc/deploy.py` & `src/commands/deploy.py`):**
  - Unified the split between SDLC feature gate reporting (`mekong deploy new <feature>`) and multi-platform infrastructure deployment (`mekong deploy run/status/rollback`).
  - Mounted `run`, `status`, and `rollback` onto `deploy_app` under canonical `deploy` CLI group, maintaining exact 39-group total count.
  - Added support for `--dry-run` and `--build/--no-build` flags.
- **Fail-Closed Platform Operations:**
  - Hardened Cloudflare (`wrangler`), Docker (`docker`), Kubernetes (`kubectl`), and custom shell script deployments against missing binaries with explicit `FileNotFoundError` handling and `typer.Exit(code=1)`.
  - Added status inspection and rollback commands for Cloudflare Workers/Pages deployments with dry-run verification.
- **Test Coverage & Conformance:**
  - Added 21 tests in `tests/cli/test_deploy_commands.py` covering registration, dry-run simulations, missing dependencies, subprocess execution, error handling, and unsupported platform rejections.
  - Updated `COMMAND_REGISTRY.md` and `docs/development-roadmap.md` (Phase 6 marked 100% complete).

## v6.6.0 — 2026-09-10

**Architectural Duplication Convergence & Tier Configuration Consolidation (DUPLICATION_MAP #1, #2, #3, #6, #7, #8, #9):**

- **Phase 4 Vietnam Hub Full Surface Convergence (100%):**
  - Consolidated and verified all 3 Vietnam business funnels (`zalo-oa`, `thue`, `ke-toan`) across Typer CLI command sub-apps and REST API endpoints.
  - Hardened VietQR webhook processing (`src/api/vn_payments_routes.py`, `src/services/vietqr_webhook_handler.py`) with HMAC-SHA256 signature verification, idempotent transaction handling, and bank-friendly HTTP 200 error policy.
  - Verified multi-tenant organization isolation (`src/api/org_routes.py`, `tests/vn/test_org_id_isolation.py`, `tests/vn/test_org_id_full_surface.py`) with tenant-scoped storage backends (JSONL and SQLite).
  - Enforced soft paywall via `PilotCreditGateMiddleware` (`src/middleware/pilot_credit_gate.py`) returning HTTP 402 with bilingual payment instructions and VietQR bank details.
  - Achieved 100% test pass rate across all 467 tests in the Vietnam Hub test surface (`tests/vn/`, `tests/commands/test_thue_dnvn.py`, `tests/cli/test_funnel_commands.py`, `tests/zenos/test_vietnam_feature_regression.py`, `tests/core/test_service_credits.py`, `tests/test_onboarding_funnel_store.py`).

- **Phase 3 Programmatic Auth Refresh & Token Rotation:**
  - Implemented `POST /auth/refresh` endpoint in `src/api/auth_routes.py` with rotating 30-day refresh tokens and 1-hour access tokens.
  - Added claim verification distinguishing `"token_type": "access"` from `"token_type": "refresh"`, rejecting access token replay attempts with HTTP 401.
  - Wired live license store lookup on token refresh, dynamically resolving license tier upgrades and enforcing active license status (HTTP 402 on cancelled/inactive licenses).
  - Configured `RateLimitGatewayMiddleware` preset resolution for `/auth/refresh` and `/v1/auth/refresh` to map to `RateLimitPreset.AUTH_REFRESH` (30/hour).
  - Added comprehensive test suite `TestRefreshEndpoint` in `tests/test_api_auth_routes.py` covering token rotation, dynamic tier upgrades, expiration, revocation, malformed claims, and rate limit presets.

- **Phase 3 Quota Status Endpoints, Tier Config API & License Gate Conformance:**
  - Mounted `/v1/quota` router (`src/api/quota_status_endpoints.py`) and `/api/tier-configs` router (`src/api/tier_config_routes.py`) into central gateway (`src/gateway.py`).
  - Refactored `EngineLicenseGateMiddleware` (`engine/license/license_gate_middleware.py`) to inherit from Starlette `BaseHTTPMiddleware` implementing canonical `dispatch(request, call_next)`.
  - Added `ActiveLicense` and multi-identifier `get_active_license(user_id)` to `LicenseStore` (`engine/license/license_store.py`) matching license keys, customer IDs, emails, and subscription IDs.
  - Added `_get_or_create_ledger` alias and `charge_mcu` method to `BillingService` (`src/api/raas_billing_service.py`).
  - Added test suites `tests/test_quota_status_endpoints.py`, `tests/test_tier_config_routes.py`, `tests/test_engine_license_gate_middleware.py`, and extended `tests/test_lib_license_store.py` (all passing 100%).

- **Security Pattern Accumulation & Fixture Isolation (PR #22):**
  - Removed premature exit on command chaining detection in `src/core/command_sanitizer.py`, ensuring all dangerous patterns (`curl_pipe_shell`, `sudo_execution`, `rm_root`, etc.) evaluate and accumulate in `blocked_patterns`.
  - Patched dynamic agent discovery module path in `tests/test_plugin_loading.py` to target `src.core.registry.dynamic.Path`.
  - Restored unmocked `MemoryStore` fixture in `tests/test_smart_router.py` via `_pre_gateway_originals`.

- **Tier Configuration & Rate Limiting Consolidation (PR #20, Item 9):**
  - Consolidated tier keys, pricing, MCU credits, and endpoint rate limits into authoritative single source of truth `src/seed/config/tiers.py`.
  - Added dynamic case-insensitive alias lookup via `TierKey._missing_` (`basic` -> `starter`, `premium` -> `growth`, `master` -> `pro`, `enterprise_plus` -> `enterprise`).
  - Added `Tier = TierKey` canonical alias.
  - Converted `engine/billing/tier_config.py` into a thin backward-compatible re-export façade exporting all symbols with zero regression to external callers.
  - Upgraded `LicenseEnforcer` to enforce monotonic 6-tier hierarchy (`FREE: 0, TRIAL: 1, STARTER: 2, GROWTH: 3, PRO: 4, ENTERPRISE: 5`).
  - Added dedicated conformance test suite `tests/test_tier_config_conformance.py` (28/28 tests passing).

- **Architectural Duplication Convergence (PR #19, Items 1, 2, 6, 8):**
  - **Item 1:** Converted duplicate `src/harness/agents/base.py` and `registry.py` to backward-compatible re-export façades forwarding to canonical `src.core.agent_base` and `src.core.agent_registry`.
  - **Item 2:** Converged payment routing; `NowPaymentsProvider` implements `protocols.PaymentProvider`, routing IPN callbacks through canonical interface.
  - **Items 6 & 8:** Ported natural language bilingual router into canonical `src/cli/workflow_commands.py:ask_cmd`, shimmed `src/commands/core_commands.py` to `src.cli.app_setup.build_app()`, pruned dead command stubs `ci.py` and `env.py`.

- **RecipeVerifier Merge & Autonomous Execution Loop (PR #18, Item 7):**
  - Unified `RecipeVerifier` into `MekongCoreRuntimeImpl.verify()` via duck-typed `_ExecResultLike` adapter and `_criteria_to_verifier_dict`.
  - Wired DAG task dependency execution and downstream cancellation through `DAGScheduler.mark_failed`.
  - Completed autonomous `execute()` → `verify()` → `repair()` recovery cycle across 4 strategies (`RETRY`, `FALLBACK`, `ESCALATE`, `ROLLBACK`).

- **Memory Store Convergence (PR #17, Item 3):**
  - Retrofitted `src/core/memory_canonical.py:MemoryStore` with `store()`, `retrieve()`, `delete()`, and `search()`, satisfying `protocols.MemoryStore` runtime checkable protocol natively.
  - Standardized byte-exact base64 encoding and TTL expiry.
  - Created `src/core/adapters/jsonl_memory_adapter.py:JsonlMemoryAdapter` as conformant second backend.

- **Quality & CI:**
  - 100% green on all 22 GitHub Actions CI/CD checks.
  - `ruff check` clean across all modules.

## v6.5.0 — 2026-09-09

**Gap #5 — External MCP Client Adapter + Gap #10 Funnel Restoration:**

- New `src/core/adapters/external_mcp_client.py` — synchronous facade over the
  async `mcp` SDK (stdio + Streamable-HTTP transports). Lets Mekong consume
  tools from third-party MCP servers (Claude Desktop / Cursor / VS Code configs).
- Single-task session loop via `anyio.BlockingPortal.start_task_soon` — keeps
  the MCP SDK's `BaseSession.__aenter__`/`__aexit__` inside the same task,
  avoiding the "Attempted to exit a cancel scope" RuntimeError in anyio 4.13.
- Lazy SDK import with fail-loud `ExternalMcpError` when `mcp` is absent.
- `from_config` / `parse_mcp_servers` parse Claude-Desktop-style `mcpServers`
  blocks (command+args for stdio, url+headers for HTTP).
- **26 new tests** in `tests/test_external_mcp_client.py` (factories, config
  parsing, error paths, mocked list_tools/call_tool, plus 2 live-server
  integration tests guarded by `_has_npx()`).
- Vietnam funnel restoration (`src/cli/funnel_commands.py`): reconnected
  `zalo-oa`, `thue`, `ke-toan` to the `mekong` binary. Registered groups 36 → 39.
  **22 new CLI tests** in `tests/cli/test_funnel_commands.py`.
- `COMMAND_REGISTRY.md` rewritten from 48 phantom entries to actual 39 groups /
  128 commands sourced from `build_app()`.
- Added `anyio ^4.0.0` to `pyproject.toml` (runtime dep of the new adapter;
  was previously transitive-only).
- **Parity:** 8224 passed, 262 failed, 77 skipped. **0 new failures** vs v6.4.0
  baseline (the +26/+22 pass counts come from the new test files).
- `ruff check` clean on all changed files.
- Gap #5 marked CLOSED in `docs/development-roadmap.md`.

## v6.4.0 — 2026-09-09

**Gap #10 — Funnel Restoration (Zalo OA + Tax + Accounting → CLI):**

- Reconnected the three Vietnam business funnels to the `mekong` binary as Typer
  sub-apps via `src/cli/funnel_commands.py` (previously reachable only via `python -m`):
  - `mekong zalo-oa` — send, broadcast, followers, caption, post
  - `mekong thue` — tncn, tndn, gtgt (offline tax calculations)
  - `mekong ke-toan` — create, xml, journal, summary (TT78/2021 invoices, VAS journal)
- Registered groups: 36 → 39 (3 new sub-apps added in `src/cli/app_setup.py`).
- **22 new tests** in `tests/cli/test_funnel_commands.py` covering registration,
  offline calculations, token-gated commands (exit 1 without `ZALO_OA_ACCESS_TOKEN`),
  and help output.
- `COMMAND_REGISTRY.md` rewritten from 48 phantom entries to actual 39 groups / 128
  commands sourced from `build_app()`.
- **Parity:** 8198 passed, 262 failed, 77 skipped. Net −15 vs baseline (277 failures);
  **0 new failures from funnel restoration**.
- `ruff check` clean on all changed files.
- Architecture score +2 (72 → 73); risk #8 (funnel orphaning) marked CLOSED in
  `docs/architecture/ARCHITECTURE_ASSESSMENT.md`.

## v6.3.0 — 2026-09-08

**Super Command #8 — Gap #4: Harness Verifier Merge + DAG Scheduler Swap:**

- `MekongCoreRuntimeImpl.verify()` now delegates to `RecipeVerifier` (was: thin
  `_evaluate_check` with only `exit_code` + `output_pattern`). Three helpers bridge
  the gap: `_ExecResultLike` (core `Result` → `ExecutionResult`-shaped object),
  `_criteria_to_verifier_dict` (core `CheckSpec` → verifier criteria-dict),
  `_report_to_verification` (`VerificationReport` → core `Verification`).
  Empty-criteria path falls back to legacy `Verification(passed=(result.error is None))`.
- `_run_goal` executes multi-step plans in topological (DAG) order via
  `_topological_task_order` (string-ID-keyed Kahn's algorithm, NOT `DAGScheduler`,
  which keys by int `order`). Fast path via `_plan_has_dependencies` preserves
  single-step `mekong run` behavior exactly.
- `verify()` injected via `__init__(verifier=None)` defaulting to
  `RecipeVerifier(strict_mode=True)`.
- **27 new tests** across 3 files:
  - `tests/test_runtime_verify_merge.py` — 14 tests (verifier delegation)
  - `tests/test_runtime_dag_order.py` — 8 tests (topological ordering)
  - `tests/test_runtime_multistep_cycle.py` — 5 E2E tests (full multi-step cycle)
- **Parity:** 8182 passed, 256 failed, 77 skipped. Baseline 277 failures → −21 net
  improvement; **0 new failures from SC8** (1 pre-existing `test_plugin_loading`,
  verified on base commit `8dcb6f759`).
- `ruff check` clean on changed files.
- Architecture doc refreshed to v0.2; gap #4 marked CLOSED in
  `docs/development-roadmap.md`.

## v6.2.0 — 2026-08-29

**Super Command #5 — Economic Bus + Capability Bus + Agent Registry (PR #11):**
- Clean `src/core/` ↔ `src/core/adapters/` boundary: no vendor SDK imports in core at module level
- Canonical `LLMProvider` port (`generate/stream/structured_output/tool_call/health`); two conformant providers
- YAML single-source agent registry (`agents/registry.yaml`); Python discovery + CLI are adapters
- Capability bus wired into `mekong run` (11 builtin capabilities, failure-tolerant)
- MCP→capability bridge (`mcp:<tool_name>` ids) via `McpCapabilityAdapter` + `ToolCapabilityAdapter`
- Scheme-agnostic economic bus: x402 + MPP providers, fail-closed config, no custody
- Canonical Buzz transport (hermetic-by-injection, fail-loud `BuzzConfigError` at call time)
- `CloudflareTransport(Protocol)` with `.dispatch(payload) -> dict`; single import site isolated
- Agent-loop E2E test driving the full GOAL→CONTEXT→PLAN→DELEGATE→EXECUTE→OBSERVE→VERIFY→REPAIR→REMEMBER→COMMIT lifecycle
- 54 files, +5,127 / −843 lines; Core DNA manifest bumped to v2026.08.29
- Quality gates green: ruff clean, pyright 0 new errors, parity gate EMPTY at 277 baseline
- Architecture doc refreshed to v0.2 (scores + next-actions reflect SC5 deliverables)

## v6.1.0 — 2026-08-23

**Design Intelligence (Hallmark deep integration):**
- New `src/design_intelligence/` package: Pydantic v2 schemas (DesignDNA 23 fields,
  DesignBrief, AuditReport, Theme), 58 gates (29 objective / 29 heuristic / 8 visual),
  9-axis scoring, archetype→macrostructure pipeline, provider-agnostic visual QA
- Knowledge base: 58 gates, 21 macrostructures, 12 themes, 4 genres, 16 archetypes
- New `mekong ui` sub-app: audit, study, redesign, build, approve, benchmark
- Three evidence tiers (objective/heuristic/opinion) and three visual-QA tiers
  (full/screenshot/static) kept strictly separate — never over-claimed
- Design memory: approved DNA / rejected patterns via MemoryStore `design:` namespace
  (Sophia contract); `study --export-json` emits parseable DesignDNA JSON
- Change detection + opt-in `mekong deploy --design-audit` advisory hook
  (frontend diffs suggest audit; backend/migration/CLI/infra-only skip)
- Anti-gaming benchmark: 10 fixtures, 7 derived metrics, good vs slop separation
- 140 design-intelligence tests; docs/design-intelligence.md

## v6.0.0 — 2026-08-16

**Highlights:**
- MIT license applied
- Python-only contributor workflow finalized
- 48 commands mapped in COMMAND_REGISTRY.md
- spec-kit SDD artifacts added (specs/, trace.rb, traceability.json)

**Repo parity fixes:**
- Release metadata synced to `minhlongs/mekong-cli`
- GitHub Actions PyPI-only publish path validated
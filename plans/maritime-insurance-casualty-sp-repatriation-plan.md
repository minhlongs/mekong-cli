# Implementation Plan: Maritime Insurance Subrogation, Marine Casualties Investigation, Ship Sale & Purchase (Saleform), and Seafarer Repatriation Contingency Suite (Phases 211-214)

## 1. Overview
Implement Phases 211–214 for Mekong CLI:
- **Phase 211**: Marine Insurance Subrogation, Abandonment & Indemnity (Luật Kinh doanh bảo hiểm 2022, VMC 2015 Arts. 310–336, ITC Hulls 1/10/83, MIA 1906). Notice of abandonment for Constructive Total Loss (CTL >= 80% or repair cost > repaired value), subrogation rights assignment, insurer salvage rights, and third-party recovery ceiling ($V_{subrogation} \le V_{indemnified}$).
- **Phase 212**: Marine Casualties & Investigation Protocols (IMO Casualty Investigation Code - Res. MSC.255(84), Circular 01/2020/TT-BGTVT, VMC Arts. 115–124). Severity categorization (Very Serious Marine Casualty - VSMC, Serious Marine Casualty - SMC, Marine Incident), statutory notification deadlines (24h initial report, 30 days preliminary investigation, 60 days formal safety report), VDR preservation requirement.
- **Phase 213**: Ship Sale & Purchase (S&P), Escrow & Closing Protocol (BIMCO SALEFORM 2012 / SHIPSALE 22, VMC Arts. 29–36). 10% deposit escrow, Notice of Readiness for delivery (NOR), underwater diver inspection & drydock repairs deduction, Cancelling Date breach remedies, and documentary closing fund release.
- **Phase 214**: Seafarer Repatriation & MLC 2006 Contingency Security (MLC 2006 Standard A2.5 & Reg 2.5, Circular 22/2017/TT-BGTVT, VMC Arts. 64–66). Compulsory financial security certificate for repatriation, abandonment assistance fund (4 months outstanding wages + flight + sustenance), and shipowner liability recourse.

## 2. Architecture & File Plan
1. `src/core/maritime_insurance_casualty_sp_repatriation_engine.py`:
   - Pure Python stdlib with AST zero-external-dependency guarantee.
   - Enums:
     - `MarineLossType`: ACTUAL_TOTAL_LOSS, CONSTRUCTIVE_TOTAL_LOSS, PARTIAL_AVERAGE, GENERAL_AVERAGE_CONTRIBUTION.
     - `AbandonmentStatus`: VALID_ACCEPTED, VALID_DECLINED_PAYOUT_MAINTAINED, INVALID_REPAIR_BELOW_THRESHOLD, UNTIMELY_TENDERED.
     - `CasualtySeverity`: VERY_SERIOUS_MARINE_CASUALTY, SERIOUS_MARINE_CASUALTY, LESS_SERIOUS_CASUALTY, MARINE_INCIDENT.
     - `SaleformStage`: MOA_EXECUTION, DEPOSIT_ESCROW_LODGED, CLASS_INSPECTION_CONFIRMED, DIVER_INSPECTION_APPROVED, NOR_DELIVERY_TENDERED, CLOSING_TITLE_TRANSFERRED, CANCELLED_DEFAULT.
     - `RepatriationReason`: CONTRACT_EXPIRY, SHIPOWNER_INSOLVENCY_ABANDONMENT, UNSEAWORTHINESS_TERMINATION, SICKNESS_INJURY_EVACUATION, WAR_PIRACY_ZONE_REFUSAL.
   - Classes:
     - `MaritimeInsuranceSubrogationEngine`: Evaluates actual/constructive total loss, abandonment validity, insurer indemnity payout, and subrogation recovery cap.
     - `MarineCasualtyInvestigationEngine`: Categorizes casualty severity, computes investigation statutory timebars, and evaluates safety recommendation triggers.
     - `ShipSalePurchaseEscrowEngine`: Models BIMCO SALEFORM 2012 / SHIPSALE 22 financial escrow, defect holdbacks, cancellation liquidated damages, and title transfer balances.
     - `SeafarerRepatriationContingencyEngine`: Calculates MLC Standard A2.5 repatriation obligations, back wage caps, financial security validation, and maritime authority recovery orders.
2. `src/cli/commands/maritime_insurance_casualty_sp_repatriation_command.py`:
   - Typer sub-apps: `maritimeins`, `casualty`, `shipsale`, `repatriate`.
   - Aliases: `baohiemhanghai`, `tainanhanghai`, `muabantau`, `hoihuong`.
3. `src/cli/app_setup.py`:
   - Register the 4 command groups with aliases.
4. `scripts/mcp_server.py`:
   - FastMCP tool definitions and JSON-RPC dispatchers.
5. `tests/test_maritime_insurance_casualty_sp_repatriation_suite.py`:
   - Unit tests, AST invariant test, CLI runner tests, FastMCP tests.

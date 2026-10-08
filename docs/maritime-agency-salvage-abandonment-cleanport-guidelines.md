# Tech Stack & Design Guidelines: Phases 255-258 Statutory Maritime Engine

## Architecture Overview

```
                      +---------------------------------------+
                      | Mekong CLI v6.0 / FastMCP Server     |
                      +---------------------------------------+
                                         |
     +-------------------+---------------+-------------------+-------------------+
     |                   |                                   |                   |
[shipagency]       [salvage]                           [abandonment]       [greentug]
Phase 255           Phase 256                           Phase 257           Phase 258
Agency PDA/FDA      LOF 2024 / SCOPIC                   MLC 2006 Repat      Green Tug / Craft
Reconciliation      Salvage Arbitration                 Security Claim      Incentives & Payback
     |                   |                                   |                   |
     +-------------------+---------------+-------------------+-------------------+
                                         |
                      +---------------------------------------+
                      | Pure Python Standard Library Engine   |
                      | (Zero external dependencies)          |
                      +---------------------------------------+
```

## 1. Phase 255: Maritime Ship Agency PDA/FDA Engine
- **Classes**:
  - `DisbursementCategory`: `PORT_DUES`, `PILOTAGE`, `TUGBOAT`, `MOORING`, `WASTE_PRF`, `CUSTOMS_IMMIGRATION`, `HUSBANDRY_CREW`, `BUNKER_SURVEY`.
  - `DisbursementItem`: `category`, `item_name`, `estimated_usd`, `actual_usd`, `voucher_ref`.
  - `DisbursementAccountReport`: `vessel_name`, `call_id`, `items`, `advance_deposit_usd`, `total_estimated_usd`, `total_actual_usd`, `balance_due_usd`, `agency_fee_usd`, `freight_commission_usd`.
  - Method: `ShipAgencyDisbursementEngine.reconcile_pda_fda(...)`.

## 2. Phase 256: Maritime Salvage & SCOPIC Settlement Engine
- **Classes**:
  - `SalvageContractType`: `LOF_NO_CURE_NO_PAY`, `TOWCON_COMMERCIAL`, `SCOPIC_INVOKED`.
  - `SalvedPropertyValues`: `ship_sound_value_usd`, `repair_costs_usd`, `cargo_cif_usd`, `freight_at_risk_usd`.
  - `SCOPICExpenseSummary`: `tug_daily_rate_usd`, `equipment_rate_usd`, `personnel_per_diem_usd`, `duration_days`, `bonus_markup_pct` (default 25.0%).
  - `SalvageSettlementResult`: `contract_type`, `net_salved_fund_usd`, `art13_salvage_award_usd`, `scopic_remuneration_usd`, `final_payable_award_usd`, `penalized_discount_usd`, `remarks`.
  - Method: `MaritimeSalvageEngine.calculate_salvage_settlement(...)`.

## 3. Phase 257: Seafarer Abandonment Financial Guarantee Engine
- **Classes**:
  - `AbandonmentTriggerReason`: `UNPAID_WAGES_2_MONTHS`, `SEVERED_TIES`, `FAILURE_TO_REPATRIATE`, `LACK_OF_PROVISIONS`.
  - `SeafarerClaimItem`: `seafarer_name`, `rank_or_role`, `monthly_wage_usd`, `unpaid_months`, `outstanding_contractual_dues_usd`, `home_destination_country`.
  - `AbandonmentSettlementReport`: `vessel_name`, `imo_number`, `guarantor_pni_club`, `claims`, `capped_wages_usd`, `repatriation_travel_usd`, `subsistence_costs_usd`, `total_guarantee_payout_usd`, `shipowner_indemnity_recourse_usd`.
  - Method: `SeafarerAbandonmentEngine.assess_abandonment_guarantee(...)`.

## 4. Phase 258: Seaport Green Tug & Clean Energy Harbor Craft Transition Engine
- **Classes**:
  - `HarborCraftType`: `ASD_TUGBOAT`, `PILOT_BOAT`, `MOORING_LAUNCH`, `BUNKER_BARGE`.
  - `PropulsionTechnology`: `CONVENTIONAL_MGO`, `HYBRID_DIESEL_ELECTRIC`, `FULL_BATTERY_ELECTRIC`, `GREEN_HYDROGEN_FC`, `GREEN_METHANOL`.
  - `GreenTugTransitionMetrics`: `craft_name`, `annual_operating_hours`, `baseline_mgo_co2_tons`, `abated_co2_tons`, `annual_fuel_savings_usd`, `annual_port_tariff_rebate_usd`, `annual_total_benefit_usd`, `capex_premium_usd`, `simple_payback_years`, `statutory_compliance_status`.
  - Method: `GreenHarborCraftEngine.evaluate_transition_incentives(...)`.

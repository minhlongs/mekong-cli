# Tech Stack & Schema Design: Phases 263-266

## Core Architecture
- File: `src/core/maritime_loi_ga_bunker_demurrage_engine.py`
- Zero external dependencies: imports strictly restricted to Python standard library.
- Strict dataclasses with validation and `to_dict()` methods.

## Data Models & Enums

### Phase 263: Letter of Indemnity (LOI) & Switch B/L
- `LOIType`: `DELIVERY_WITHOUT_ORIGINAL_BL`, `CHANGE_OF_DISCHARGE_PORT`, `SPLIT_BL`, `CLEAN_BL_AGAINST_DEFECTS`
- `BankGuaranteeStatus`: `FIRST_CLASS_INTERNATIONAL_BANK`, `LOCAL_COMMERCIAL_BANK`, `UNSECURED_CORPORATE_ONLY`, `NO_BANK_JOIN`
- `LOIEvaluationInput` & `LOIRiskAssessment`

### Phase 264: General Average (GA) Adjustment
- `GASacrificeExpenditure`: vessel repairs, cargo jettison, salvage awards, port of refuge expenses, fuel/stores consumed
- `ContributoryInterests`: ship sound value + repairs deduction, cargo CIF value + damage deduction, freight at risk
- `GeneralAverageAdjustmentResult`: GA contribution percentages, net settlements, Cash Deposit / Average Bond values

### Phase 265: Bunker Delivery Note (BDN) & Sulfur Cap
- `FuelGrade`: `VLSFO` (<=0.50%), `ULSFO` (<=0.10%), `HSFO` (>0.50% requires scrubber), `MGO` (<=0.10%), `BIOFUEL`
- `EmissionControlZone`: `OPEN_OCEAN_GLOBAL`, `IMO_ECA_ZONE`, `VIETNAMESE_SEAPORT_WATERS`
- `BunkerComplianceAssessment`: sulfur check, scrubber ratio check, de-bunkering estimation, FONAR status

### Phase 266: Demurrage & Detention (D&D)
- `ContainerType`: `DRY_20FT`, `DRY_40FT`, `REEFER_20FT`, `REEFER_40FT`, `SPECIAL_EQUIPMENT`
- `FreeTimeAgreement`: terminal free days, equipment free days, progressive tariff brackets
- `DemurrageDetentionResult`: terminal demurrage, shipping line detention, maritime lien alert under VMC Art. 168

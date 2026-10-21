# Phase 06: Zero-Mock Unit & Integration Testing

## Test Suites
1. `tests/test_maritime_pto_berth_unit_suite.py` (< 200 LOC):
   - PTO/PTI engine: normal PTO savings, low RPM inhibit, overload warning, PTH booster mode.
   - Berth/Crane engine: standard berth allocation, tide gating required, crane distance violation.
2. `tests/test_maritime_biofoul_waste_unit_suite.py` (< 200 LOC):
   - Biofouling: LoF 1 grooming, LoF 2 filtered capture, LoF 4 drydock mandatory.
   - Waste Oil: normal RFO clinker offset, flash point < 60°C rejection, effluent > 15 ppm alarm.
3. `tests/test_maritime_371_to_374_cli_mcp_suite.py` (< 200 LOC):
   - Facade integration test.
   - CLI execution (English & Vietnamese).
   - FastMCP tool async execution.

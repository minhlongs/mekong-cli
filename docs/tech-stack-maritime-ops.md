# Tech Stack & Architectural Specification — Maritime Operations & Vessel Husbandry Suite

**Phases:** 183 - 186  
**Modules:**
- `src/core/maritime_operations_engine.py` (Domain Engine)
- `src/cli/commands/maritime_operations_command.py` (CLI Interface)
- `scripts/mcp_server.py` (FastMCP / JSON-RPC Tools)
- `tests/test_maritime_operations_suite.py` (Pytest Verification)

---

## 1. Design Constraints
- **Standard Library Only in Core**: `math`, `datetime`, `dataclasses`, `enum`, `typing`, `json`.
- **Zero Third-Party Dependency in `src/core/`**: Checked via AST visitor in unit test.
- **Microsecond Latency**: Pure numerical calculations for pilotage GT-NM, tugboat assistance, MLC rest hour validation, H&M/P&I deductibles, and Tokyo MOU PSC target risk points.
- **Dual Invocation Model**:
  1. CLI via Typer sub-apps (`mekong pilotage` / `hoatie`, `mekong shipagency` / `daily`, `mekong marineins` / `baohiemhanghai`, `mekong psc` / `kiemtratau`).
  2. MCP Server via FastMCP JSON-RPC tools (`mekong_pilotage_*`, `mekong_shipagency_*`, `mekong_marineins_*`, `mekong_psc_*`).

---

## 2. Domain Data Structures & Contracts

```python
# Pilotage & Towage
class PilotageArea(str, Enum):
    AREA_I = "AREA_I"      # Quang Ninh, Hai Phong (Lach Huyen)
    AREA_II = "AREA_II"    # Da Nang, Quy Nhon
    AREA_III = "AREA_III"  # Cai Mep - Thi Vai, HCM, Dong Nai
    OFFSHORE = "OFFSHORE"  # Offshore Oil & Gas Terminals

class TugboatClass(str, Enum):
    CLASS_A = "CLASS_A"  # < 1,000 HP
    CLASS_B = "CLASS_B"  # 1,000 - 2,000 HP
    CLASS_C = "CLASS_C"  # 2,001 - 3,000 HP
    CLASS_D = "CLASS_D"  # 3,001 - 4,000 HP
    CLASS_E = "CLASS_E"  # > 4,000 HP

# Ship Agency & MLC 2006
class SeafarerRank(str, Enum):
    MASTER = "MASTER"
    CHIEF_ENGINEER = "CHIEF_ENGINEER"
    OFFICER = "OFFICER"
    RATING = "RATING"
    CADET = "CADET"

class MLCComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    REST_HOURS_BREACH = "REST_HOURS_BREACH"
    CONTRACT_OVERDUE = "CONTRACT_OVERDUE"
    MANDATORY_REPATRIATION = "MANDATORY_REPATRIATION"

# Marine Insurance & Claims
class MarineClaimType(str, Enum):
    PARTICULAR_AVERAGE = "PARTICULAR_AVERAGE"
    CONSTRUCTIVE_TOTAL_LOSS = "CONSTRUCTIVE_TOTAL_LOSS"
    ACTUAL_TOTAL_LOSS = "ACTUAL_TOTAL_LOSS"
    PI_POLLUTION = "PI_POLLUTION"
    PI_CREW_LIABILITY = "PI_CREW_LIABILITY"

# Tokyo MOU PSC
class PSCShipRiskProfile(str, Enum):
    LRS = "LOW_RISK_SHIP"
    SRS = "STANDARD_RISK_SHIP"
    HRS = "HIGH_RISK_SHIP"

class PSCDetentionAction(str, Enum):
    CODE_17_RECTIFY_BEFORE_DEPARTURE = "CODE_17"
    CODE_30_DETENTION = "CODE_30"
    NO_DEFICIENCIES = "NO_DEFICIENCIES"
```

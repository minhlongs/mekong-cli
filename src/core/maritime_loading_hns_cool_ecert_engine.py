"""Central Facade for Maritime Phases 351-354.

Unifies:
- Phase 351: BulkLoadingEngine (SOLAS XII/11 BM/SF, 2008 IS Code GM/GZ)
- Phase 352: HnsDriftEngine (OPRC-HNS 2000, CEDRE SEACARAMB drift vector & hazard zone)
- Phase 353: CentralCoolingEngine (Plate heat exchanger LMTD, seawater scoop, MGPS Cu/Al dosing)
- Phase 354: MarineEcertEngine (IMO FAL.5/Circ.39/Rev.2 electronic certificates, UTN, SHA-256 verification)
Strictly kept under 200 lines.
"""

from src.core.maritime.phase_351_bulk_loading_stability import (
    BulkLoadingEngine,
    BulkLoadingInput,
    BulkLoadingResult,
)
from src.core.maritime.phase_352_hns_chemical_spill_drift import (
    HnsDriftEngine,
    HnsDriftInput,
    HnsDriftResult,
)
from src.core.maritime.phase_353_central_cooling_mgps import (
    CentralCoolingEngine,
    CentralCoolingInput,
    CentralCoolingResult,
)
from src.core.maritime.phase_354_marine_ecert_verification import (
    MarineEcertEngine,
    MarineEcertInput,
    MarineEcertResult,
)

__all__ = [
    "BulkLoadingEngine",
    "BulkLoadingInput",
    "BulkLoadingResult",
    "HnsDriftEngine",
    "HnsDriftInput",
    "HnsDriftResult",
    "CentralCoolingEngine",
    "CentralCoolingInput",
    "CentralCoolingResult",
    "MarineEcertEngine",
    "MarineEcertInput",
    "MarineEcertResult",
]

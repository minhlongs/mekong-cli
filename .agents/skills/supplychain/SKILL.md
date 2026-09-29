---
name: supplychain
description: Vietnamese agricultural & timber supply chain traceability, EUDR anti-deforestation compliance & EPCIS custody tracking.
---

# Supply Chain & EUDR Traceability Engine (`mekong supplychain`)

Autonomous supply chain traceability, EU Deforestation Regulation (EUDR - Regulation (EU) 2023/1115), VNTLAS timber legality (Law on Forestry 2017), and GS1 EPCIS 2.0 digital custody transfer engine for Vietnamese agricultural and forestry exports.

## Core Capabilities

1. **EUDR Production Plot Geolocation (Regulation EU 2023/1115)**:
   - Registers production plots across key Vietnamese commodities: `COFFEE` (Tây Nguyên), `RUBBER`, `TIMBER_WOOD`, `COCOA`, `PALM_OIL`, `SOYA`, `CATTLE`.
   - Validates coordinates: single point coordinates for plots $\le 4.0$ ha, mandatory polygon boundaries for plots $> 4.0$ ha.
   - Enforces the statutory cut-off date: **31/12/2020** (zero deforestation or forest degradation post-2020).
2. **Traceability Batch Aggregation & SHA-256 Fingerprinting**:
   - Aggregates harvest origins into export batches with volume metering, processor identity, and quality certifications (`VIETGAP`, `4C`, `FSC`, `VFCS`, `PEFC`).
   - Generates genesis SHA-256 fingerprint anchoring provenance integrity.
3. **GS1 EPCIS 2.0 Custody Transfer & Tamper-Evident Chaining**:
   - Logs supply chain milestone events: `HARVEST`, `COLLECT`, `PROCESS`, `AGGREGATE`, `QUALITY_INSPECT`, `PACK`, `CUSTOMS_CLEAR`, `SHIP`.
   - Links consecutive events using cryptographic hash chaining (`prev_hash` $\to$ `event_hash`).
4. **EUDR Due Diligence Statement (DDS) Dossier Synthesis**:
   - Synthesizes official EU customs Due Diligence Statements with unique reference codes (`EUDR-VN-2026-XXXX`).
   - Computes automated risk evaluation grades: `NEGLIGIBLE_RISK` (cleared for EU import), `STANDARD_RISK`, `HIGH_RISK`.
5. **Full Provenance Audit & Timeline Inspection**:
   - Inspects full end-to-end custody history and plot origins for any export batch.
   - Persistent SQLite WAL storage at `.mekong/supplychain.db`.

## CLI Usage

```bash
# System overview and traceability telemetry
mekong supplychain
mekong supplychain status --json

# Register agricultural or forestry production plot
mekong supplychain plot "Nguyễn Văn An" "Đắk Lắk" "COFFEE" 12.6667 108.0333 3.5 --district "Cư M'gar" --deforestation-free --json

# Create traceability export batch
mekong supplychain batch "LOT-CF-2026-001" "COFFEE" 18500 "Công ty CP Cà phê Simexco Đắk Lắk" --plots "PLOT-VN-01,PLOT-VN-02" --cert "4C,RA" --json

# Record custody transfer event (GS1 EPCIS)
mekong supplychain event "LOT-CF-2026-001" "PROCESS" "Nhà máy Chế biến Buôn Ma Thuột" "KCS Simexco" --notes "Sơ chế ướt, độ ẩm 12.5%" --json
mekong supplychain event "LOT-CF-2026-001" "SHIP" "Cảng Cát Lái, TP.HCM" "Hãng tàu Maersk" --notes "Bốc hàng lên tàu xuất khẩu sang Hamburg" --json

# Synthesize official EUDR Due Diligence Statement (DDS)
mekong supplychain eudr "LOT-CF-2026-001" "Simexco DakLak Corp" "Neumann Kaffee Gruppe (NKG)" --dest "Germany" --json

# Query end-to-end provenance timeline
mekong supplychain trace "LOT-CF-2026-001" --json

# List plots or batches
mekong supplychain list --type plots --commodity COFFEE --json
mekong supplychain list --type batches --json
```

## Native MCP Tools

- `mekong_supplychain_plot`: Register agricultural or forestry production plot with EUDR coordinates.
- `mekong_supplychain_batch`: Initialize traceability batch with plot linkage and SHA-256 fingerprint.
- `mekong_supplychain_event`: Record EPCIS custody transfer event with cryptographic hash chaining.
- `mekong_supplychain_eudr`: Synthesize official EUDR Due Diligence Statement (DDS) for EU customs.
- `mekong_supplychain_trace`: Retrieve full provenance timeline and chain of custody for a batch.
- `mekong_supplychain_status`: Retrieve supply chain engine telemetry, monitored area, and volume metrics.

# Technical Report: Phase 375/376 - Weather Routing, CII & VOC Recovery

## 1. Phase 375: Weather Routing & CII Compliance
**Objective:** Optimize voyage via ISO 15016 / speed-power cubic law and maintain CII rating.

### Mathematical Models
- **Speed-Power Law:** $P \propto V^3$. A reduction in speed $V$ by 10% reduces fuel consumption by $\approx 27.1\%$.
- **ISO 15016 Resistance:** Total resistance $R_T = R_C + R_W + R_{AA}$, where $R_W$ (wave resistance) is calculated via spectral wave height $H_s$ and period $T_p$.
- **CII Calculation:** $CII_{att} = \frac{\sum{F_{i} \times C_F}}{\sum{D_i \times Capacity_i}}$. Required $CII = (1 - Z/100) \times CII_{ref}$.

### Implementation Strategy
- Use GRIB2 weather weather feed for current/wave drag integration.
- Implement SEEMP III contingency logic: If $CII > Threshold$, trigger automatic speed mandate $V_{opt} = V_{ref} \times (CII_{act} / CII_{req})^{1/3}$.

## 2. Phase 376: VOC Recovery (MARPOL Annex VI Reg 15)
**Objective:** Vapor emission control during loading.

### Technical Parameters
- **Inerting:** Nitrogen/Flue gas must ensure $O_2 \le 8\%$ in cargo tanks.
- **Vapor Balancing:** Return displaced gas to ship/shore via vapor hose.
- **Emissions:** $E_{VOC} = 2.8 \times \text{mass}_{VOC}$ (kg $CO_2$ eq).

### Edge Cases
- **P/V Relief Failure:** Backpressure in the vapor return line during loading rates $> 0.2$ bar peak-pressure.
- **Condensation:** VOC recovery plants freezing at low throughput; requires heat tracing on vapor return lines.

## 3. Verification & Metrics
- **Verification:** Compare real-time fuel flow meters with weather-corrected performance curve.
- **CII Audit:** Merkle tree logs of voyage data (Dist, Cargo, Fuel mass/type) for Class society reporting.
- **VOC:** Continuous Emissions Monitoring System (CEMS) integration with vapor manifold pressure sensors.

## 4. Trade-offs & Architecture
- **Complexity:** High integration required between ECDIS, AIS weather feeds, and engine management system (PMS).
- **Maintenance:** VOC recovery units (condensers/absorbers) require annual cryogenic integrity survey.

**Next Steps:**
1. Integrate GRIB weather parser.
2. Develop CII rolling-window monitor.
3. Add vapor manifold pressure sensor alarms.

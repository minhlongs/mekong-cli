# Research Report: Maritime Phases 415-418 Brainstorm

## Phase 415: ME Lube Oil Purifier & Disc Stack Centrifuge
- **Goal:** Automate Lube Oil purification control.
- **Standards:** ISO 8217 (Fuel/Lubricant specs), Alfa Laval/Westfalia Alcap principles.
- **Engineering Logic:** Water seal monitoring, sludge discharge interval calculation, gravity disc (or bowl frequency) calibration.
- **Trade-offs:** Purity vs. Sludge loss.

## Phase 416: Emergency Gen AMF & Blackout Sequencing
- **Goal:** Dead-ship recovery automation.
- **Standards:** SOLAS II-1 Reg 42/43.
- **Engineering Logic:** <45s blackout-to-power-restore threshold. Dual start (pneumatic/battery), non-essential Load Shedding (LS) sequencing to prevent frequency instability.
- **Risk:** AMF logic race conditions (false trips).

## Phase 417: Crankcase Oil Mist & Explosion Interlocks
- **Goal:** Early-warning crankcase safety.
- **Standards:** IACS M9 / SOLAS II-2 Reg 4.2.3.
- **Engineering Logic:** Optical opacity (mg/L) threshold. Trip interlock logic (slowdown vs. shut down based on ppm gradient), flame arrester integrity check (periodic).
- **Complexity:** High sensitivity (avoiding false trip nuisance).

## Phase 418: Common Rail (CR) & Sheath Leak Sniffing
- **Goal:** High-pressure leak detection/containment.
- **Standards:** SOLAS II-2 Reg 4.2.2.5.2.
- **Engineering Logic:** Double-walled containment, pressure ripple damping (accumulator sizing), sheath vacuum/drain accumulator level switch logic for leak detection telemetry.
- **Fit:** Critical for high-temp engine integrity.

---
## Summary Matrix
| Phase | Focus | Standard | Key Risk |
| :--- | :--- | :--- | :--- |
| 415 | Oil Purity | ISO 8217 | Seal failure |
| 416 | Power/Blackout | SOLAS II-1 | Seq. logic error |
| 417 | Explosion Protection | IACS M9 | False trip |
| 418 | H-P Leak Detection | SOLAS II-2 | Pressure surge |

**Unresolved:** Integration of OMD trip signals into current factory automation gateway (protocol/latency).

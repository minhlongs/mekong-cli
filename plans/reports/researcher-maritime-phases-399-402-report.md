---
name: maritime-phases-399-402
description: Maritime Phases 399-402 research report (Bow Thruster, HRU, Incinerator, VECS)
metadata:
  type: reference
---

# Maritime Phases 399-402 Engineering Report

## 1. Phase 399: Marine Bow Thruster Dynamics
*   **Standards:** DNV-RU-SHIP Pt.4 Ch.5, ISO 484-1/2.
*   **Physics:** Lateral thrust $T = \dot{m} \Delta v$. Cavitation index $\sigma = \frac{P_0 - P_v}{1/2 \rho V_R^2}$. Grid loss factor $\xi$ (typically 1.05–1.15).
*   **Engineering Gate:** Hydraulic oil temp alarm ($75^\circ\text{C}$), trip ($85^\circ\text{C}$), VFD torque envelope protection.

## 2. Phase 400: Liferaft & H20 HRU Deployment
*   **Standards:** SOLAS III Reg 16, LSA Code Ch.IV.
*   **Physics:** Hammar H20 threshold $1.5-4.0\text{m}$ (water pressure $\approx 15-40\text{ kPa}$).
*   **Engineering Gate:** Painter weak link break force $2.2 \pm 0.4\text{ kN}$.

## 3. Phase 401: Shipboard Incineration (MARPOL V)
*   **Standards:** MARPOL Annex V, Res MEPC.244(66).
*   **Physics:** Primary chamber $>850^\circ\text{C}$, Secondary $>1000^\circ\text{C}$. Residence time $\ge 1.0\text{s}$.
*   **Engineering Gate:** O2 monitor $6-12\%$. CO $\le 200\text{ mg/MJ}$. Lock charging if $T_{pri} < 850^\circ\text{C}$.

## 4. Phase 402: Vapor Emission Control (VECS)
*   **Standards:** MSC/Circ.585, USCG 46 CFR Part 39.
*   **Physics:** P/V limits $+0.14\text{ bar} / -0.035\text{ bar}$. $O_2 < 8.0\%$ in inert line.
*   **Engineering Gate:** High-level alarm (95%), High-High (98%) shutdown.

**Summary:** Complex cascading safety interlocks require SIL2-rated PLC architecture. Priority: VECS inert gas oxygen sensors followed by incinerator temperature logic.

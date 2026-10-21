---
name: maritime-phases-403-406-research
description: Technical analysis of MARPOL Annex I Bilge, IGS/Nitrogen, Stern Tube lubrication, and Water Mist systems
metadata:
  type: reference
---

# Maritime Phases 403-406 Engineering Research

## 1. Marine Oil Bilge Separator (403)
- **Reg:** MARPOL Annex I, Reg 31 & 32; MEPC.108(49) / MEPC.240(65).
- **Core:** 15 ppm limit on overboard discharge.
- **Physics:** Stokes' Law for settling velocity: $v = \frac{2}{9} \frac{(\rho_p - \rho_f)}{\mu} g R^2$.
- **Interlocks:** Automatic Stopping Device (ASD) cut-off signal at >15 ppm (via oil-in-water monitor). Non-volatile data logging (min 18 months).

## 2. Inert Gas & Nitrogen (404)
- **Reg:** SOLAS II-2 Reg 4.5.5; IMO FSS Code Ch. 15.
- **Core:** Maintain cargo tank atmosphere below flammable limits (Lower Explosive Limit - LEL).
- **Control:** O2 % concentration MUST be < 5% by vol.
- **Physics:** Membrane separation (hollow fiber) permeability differential or PSA (Pressure Swing Adsorption).
- **Safety:** P/V breaker protection (± pressure), deck seal anti-backflow, O2 analyzers redundancy.

## 3. Stern Tube Lubrication & Sealing (405)
- **Reg:** DNV-RU-SHIP Pt.4 Ch.2; VGP (EALs).
- **Dynamics:** Viscosity-temperature slope ($\nu_T$). Sealing pressure differential: $\Delta P_{seal} = P_{external} (draft) + P_{margin} - P_{internal} (header tank)$.
- **EALs:** Biodegradability (OECD 301 B) and toxicity (LC50).
- **Physics:** Hydrodynamic lubrication film thickness ($h_{min}$) vs surface roughness ($\sigma$) — $\lambda = h_{min}/\sigma > 3$ for full film.

## 4. Water Mist Local Application (406)
- **Reg:** SOLAS II-2 Reg 10.5.6; MSC/Circ.1165.
- **Core:** High-pressure nozzle droplet diameter ($D_{99} < 100 \mu m$ for total flooding, $< 300 \mu m$ for local).
- **Physics:** Latent heat of vaporization ($Q = L_v \cdot \Delta m$). Rapid expansion $(1:1600)$ displaces $O_2$.
- **Criteria:** Design flow rate must meet fire test protocol extinguishing speed. 

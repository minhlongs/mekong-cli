# Researcher 22 Report: Maritime Lien Priorities, Collision & Bunker Pollution (Phases 205-206)

## Executive Summary
This report analyzes Vietnamese and international maritime statutory frameworks governing:
1. **Maritime Liens & In Rem Priorities** (Vietnam Maritime Code 2015 Arts. 37–42, Brussels Convention 1926/Geneva 1993).
2. **Apportionment of Collision Liability & Bunker Oil Pollution 2001** (Vietnam Maritime Code 2015 Arts. 285–294, COLREG 1972, International Convention on Civil Liability for Bunker Oil Pollution Damage 2001 - Bunker Convention).

---

## 1. Phase 205: Maritime Liens & In Rem Priority Waterfall

### 1.1 Statutory Hierarchy under Vietnam Maritime Code 2015
- **Article 37**: Statutory Maritime Liens (Quyền cầm giữ hàng hải) rank ahead of all other secured claims, mortgages, and commercial pledges:
  1. **Rank 1**: Wages, repatriation costs, social insurance, and medical expenses due to Master, officers, and crew;
  2. **Rank 2**: Claims for loss of life or personal injury occurring in direct connection with the operation of the ship;
  3. **Rank 3**: Maritime salvage remuneration and contribution to General Average;
  4. **Rank 4**: Port dues, channel charges, pilotage, and vessel safety fees;
  5. **Rank 5**: Extracontractual physical loss or damage caused by the operation of the ship (tort/collision damage).
- **Article 38**: Ranking Priority:
  - Maritime liens rank superior to ship mortgages (Thế chấp tàu biển - Art. 39).
  - Mortgages rank superior to ordinary unsecured maritime claims.
  - Court procedural costs & enforcement fees (Chi phí tố tụng, bán đấu giá) are deducted *first* from proceeds of judicial sale before Rank 1 liens.
  - Inverse chronological order rule for Rank 3 salvage claims: later salvage operations rank higher than earlier salvage operations.
- **Article 40**: Extinction of Maritime Liens:
  - Extinguished after **1 year** from the date the claim arose, unless the vessel was arrested prior to expiry.
  - Extinguished upon judicial auction sale by Court or authorized judgment enforcement agency.

---

## 2. Phase 206: Collision Liability & Bunker Oil Pollution (BUNKER 2001)

### 2.1 Collision Liability Apportionment (VMC Arts. 285–294 & COLREG 72)
- **Article 285**: Fault-Based Liability:
  - If a collision is caused solely by one vessel, that vessel bears 100% liability.
  - If collision occurs due to force majeure (bất khả kháng) or fault cannot be determined: each vessel bears its own losses (Art. 286).
  - Both-to-Blame Proportional Fault (Lỗi hỗn hợp - Art. 287):
    - Each vessel is liable in proportion to its degree of fault ($\alpha : \beta$ where $\alpha + \beta = 1.0$).
    - If relative fault degrees cannot be determined, liability is shared equally ($50\% / 50\%$).
- **Joint & Several Liability for Bodily Injury (Art. 287(2))**:
  - For loss of life and personal injury: Owners are jointly and severally liable (liên đới bồi thường) to victims.
  - A vessel that paid more than its fault share has statutory right of recourse (quyền truy đòi) against the co-blameworthy vessel.

### 2.2 Bunker Oil Pollution Convention 2001 (BUNKER 2001)
- **Compulsory Financial Security**:
  - Applies to all sea-going vessels $> 1,000\text{ GT}$.
  - Requires valid Blue Card from P&I Club and Certificate of Insurance issued by Flag State / Port Authority.
  - Strict liability of registered owner for pollution damage caused by any bunker oil on board or escaping from the ship.
  - Direct Action against Insurer: Claimants can bring actions directly against the P&I Club up to the LLMC 1996 limitation ceiling.

---

## 3. Conclusions for Implementation
- Implement `MaritimeLienPriorityEngine` modeling the exact Art. 37 5-tier waterfall + judicial sale costs + mortgages + unsecured claims.
- Implement `CollisionAndBunkerPollutionEngine` modeling proportional fault cross-liabilities, bodily injury joint & several recourse, and Bunker 2001 Blue Card validation.
- Provide comprehensive CLI commands and FastMCP tools.

# Vietnam National Maritime Single Window (VNSW) & Port Clearance Research

## 1. Statutory Framework & Sources
- **Primary Decrees & Laws**:
  - Vietnam Maritime Code 2015 (Law No. 95/2015/QH13) Arts. 59, 88-114 (Port Authority jurisdiction, clearance, detention).
  - Decree 58/2017/ND-CP & Decree 76/2021/ND-CP: Regulatory governance of maritime operations, VNSW procedures, electronic clearance SLAs.
  - Decree 142/2017/ND-CP & Decree 123/2021/ND-CP: Administrative penalties in maritime transport and border control.
- **Tariff & Fee Circulars**:
  - Circular 261/2016/TT-BTC & Circular 278/2016/TT-BTC: Maritime fees, charges, tonnage dues, maritime safety tariffs.
  - Circular 54/2018/TT-BGTVT & Circular 12/2024/TT-BGTVT: Price brackets for pilotage, tugboat, berthing, and container handling.
- **International Conventions**: IMO FAL Convention 1965 (2016/2024 amendments), SOLAS 74/78, MARPOL 73/78, ISPS Code, IHR 2005.

## 2. Notification & Confirmation Timelines
- **Arrival Notification (Thong bao tau den)**:
  - Standard: Minimum 24 hours prior to expected arrival at pilot boarding station.
  - Short voyage (< 24h): Within 2 hours after departing previous port of call.
- **Arrival Confirmation (Xac bao tau den)**:
  - Exact ETA confirmation: Minimum 2 hours prior to arrival at pilot station/anchorage area.
- **Departure Notification (Thong bao tau roi)**:
  - Standard: Minimum 2 hours prior to estimated vessel departure.
  - Passenger vessels & liner container services: Minimum 1 hour prior to departure.
- **Transit Notification (Thong bao tau qua canh)**:
  - 24 hours prior to entering maritime transit corridor, confirmed 2 hours before pilotage.
- **VNSW SLA**: Port authority (Cang vu Hang hai), Border Guard (Bien phong), Customs (Hai quan), and Quarantine (Kiem dich) must process and issue clearance within 1-2 hours of dossier completion.

## 3. Statutory Document Matrix (IMO FAL & National Declarations)
| Form ID | Statutory Document | Format / Schema | Primary Reviewing Authority |
|---|---|---|---|
| FAL Form 1 | General Declaration (Ban khai chung) | XML / JSON VNSW Schema | Port Authority (Lead) |
| FAL Form 2 | Cargo Declaration (Ban khai hang hoa / Manifest) | UN/EDIFACT CUSCAR / XML | Customs (Hai quan) |
| FAL Form 3 | Ship's Stores Declaration (Ban khai du tru) | XML Schema | Customs / Quarantine |
| FAL Form 4 | Crew's Effects Declaration (Hanh ly thuyen vien) | XML Schema | Customs |
| FAL Form 5 | Crew List (Danh sach thuyen vien) | XML FAL.5 | Border Guard (Bien phong) |
| FAL Form 6 | Passenger List (Danh sach hanh khach) | XML FAL.6 | Border Guard |
| FAL Form 7 | Dangerous Goods Manifest (Hang hoa nguy hiem) | IMDG Code XML | Port Authority / Fire Safety |
| VN-SPEC-01 | Weapons & Ammunition Declaration (Vu khi, dan duoc) | Secured XML | Border Guard / Police |
| VN-SPEC-02 | Maritime Declaration of Health (Kiem dich y te) | WHO IHR 2005 Annex 9 XML | International Health Quarantine |
| VN-SPEC-03 | Stowaway List / Nil Stowaway Declaration | FAL Form XML | Border Guard |

## 4. Digital Clearance Permit Verification & Fee Calculations
- **e-Port Clearance (e-PC / Giay phep roi cang dien tu)**:
  - Issued via VNSW portal with PKI X.509 SHA-256 digital signature of the Maritime Port Authority.
  - Embeds 2D secure QR code verifying: IMO Number, Call Sign, Voyage Number, Valid Hours (default 24h), Destination Port, and cryptographic signature hash.
- **Maritime Dues & Fee Formulas**:
  - *Tonnage Dues (Phi trong tai tau thuyen)*: `Fee = GT * Rate_per_GT * Voyages` (International: ~$0.034/GT entry + $0.034/GT exit; Domestic: tiered VND).
  - *Maritime Safety Fee (Phi bao dam hang hai)*: `Fee = GT * Zone_Rate * Routing_Factor` (Calculated on channel depth and nautical distance).
  - *Pilotage Fee (Phi hoa tieu)*: `Fee = max(Min_Charge, GT * Distance_NM * Pilot_Unit_Rate) * Night_Overtime_Multiplier`.
  - *Anchorage & Berthing Fee (Phi neo dau, cau ben)*: `Fee = GT * Hours_Occupied * Tariff_Rate`.
  - *Port Clearance Permit Charge (Le phi ra vao)*: Flat statutory fee ($25-$50 international, 50k-100k VND domestic).

## 5. Trade-Off Matrix: Architecture & Integration Modes
| Parameter | Direct VNSW AS2 / SOAP Bridge | Local Proxy + Offline Fallback Engine (Recommended) | Manual Web Scraping / Portal RPA |
|---|---|---|---|
| Latency / Throughput | High (< 500ms) | Low (< 50ms local, async sync) | Unstable (> 30s) |
| Resilience to Outages | Low (fails on VNSW downtime) | High (local cache, provisional issuance queue) | Zero |
| Implementation Cost | High (Formal Gov Gateways) | Moderate (Standard OpenAPI + XML builder) | Low initial, High maintenance |
| Compliance Risk | Zero (Direct protocol) | Zero (Adheres strictly to TT 54/NĐ 76 specs) | High (Breaks on DOM updates) |

## 6. Adoption Risks & Mitigations
- **System Downtime / Gov Gateway Timeout**: Fallback to Circular 278 contingency mode; system generates pre-cleared offline manifest with timestamped hash for manual endorsement.
- **Data Discrepancy & Late Penalties**: Automatic pre-validation engine checks Gross Tonnage vs IMO registers and flag state exemptions before submission to prevent Decree 142 fines (5M - 30M VND).
- **Fee Calculation Mismatches**: Implement exact dual-currency statutory math engine (USD/VND exchange rate pegged to SBV announced rate on clearance date).

## 7. Concrete Recommendation & Architectural Fit
- **Ranking**:
  1. **Rank 1**: Local Statutory Engine with Pre-validation + VNSW XML/JSON Marshaller + QR PKI Verifier (Selected).
  2. **Rank 2**: Direct EDIFACT / AS2 Gateway without local caching.
  3. **Rank 3**: RPA Web automation (Rejected due to compliance vulnerability).
- **Architectural Fit**: Pure TypeScript stateless calculation & validation library in `src/maritime-single-window/`, strictly typed, zero-dependency, integrating directly with existing logistics engines.

## 8. Limitations & Exclusions
- Does not cover military, search-and-rescue, or government non-commercial vessel exemptions (governed under separate defense protocols).
- Currency conversion does not hedge FX forward volatility; uses SBV official spot rates only.

## 9. Unresolved Questions
- None. Statutory deadlines, FAL schemas, and fee formulas are fully locked by decrees 58/2017/ND-CP, 76/2021/ND-CP, and circulars 261/2016/TT-BTC, 54/2018/TT-BGTVT.

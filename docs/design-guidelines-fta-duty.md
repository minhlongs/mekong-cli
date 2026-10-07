# Design Guidelines — Vietnam FTA Concessions, EPE, AEO & Duty Exemption Suite (Phases 171 - 174)

**Date:** 2026-10-07  
**Design System:** Mekong Cyber-Glass Terminal & Web Dashboard  
**Compliance Target:** WCAG 2.1 AA, Contrast Ratio >= 4.5:1  

---

## 1. Visual Hierarchy & Color Tokens

- **Brand Primary:** `#0ea5e9` (Ocean Blue / Custom Clearance)
- **Status Green (Luồng Xanh / Đạt chuẩn AEO / Cân bằng):** `#10b981` (Emerald)
- **Status Yellow (Luồng Vàng / Kiểm tra hồ sơ / Cảnh báo):** `#f59e0b` (Amber)
- **Status Red (Luồng Đỏ / Vi phạm / Thiếu hụt kho):** `#ef4444` (Crimson)
- **Background Dark:** `#090d16` (Deep Obsidian)
- **Card Surface:** `rgba(15, 23, 42, 0.75)` with 1px border `rgba(255, 255, 255, 0.1)` and backdrop-blur `12px`

---

## 2. Component System

1. **Customs Channeling Badge:**
   - Pill badge displaying `GREEN`, `YELLOW`, or `RED` with glowing pulse indicator.
   - Text sub-label showing statutory action: `Thông quan tự động`, `Kiểm tra chứng từ`, or `Kiểm tra thực tế hàng hóa`.

2. **BCQT 15 Variance Gauge:**
   - Numerical comparison between Theoretical Closing Balance and Physical Inventory.
   - Dynamic alert callout calculating daily late payment surcharge ($0.03\%/\text{day}$).

3. **Origin Rule Matrix:**
   - Multi-tab breakdown for WO, CTC (CC/CTH/CTSH), RVC, and De Minimis.
   - Real-time indicator for C/O Form (EUR.1, CPTPP self-certification, ATIGA Form D, REX).

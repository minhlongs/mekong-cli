# Hướng dẫn Thiết kế Giao diện: Phases 291–294 CLI Terminals

## 1. Nguyên tắc Thị giác & Thiết kế Terminal (UI/UX Guidelines)
- **Bảng màu ngữ nghĩa (Semantic Palette)**:
  - Xanh lá (`bold green`): Đạt chuẩn tuân thủ (Permitted, Compliant, Fit, Cleared).
  - Vàng hổ phách (`bold yellow`): Cảnh báo rủi ro / sắp quá hạn (Warning, Restricted, Expiring Soon, Class 3/4 IMDG).
  - Đỏ gạch (`bold red`): Vi phạm quy định / Cấm xả / Không đủ sức khỏe / Tịch thu (Prohibited, Unfit, Seizure Required).
  - Xanh lơ (`bold cyan`): Thông tin định danh tàu biển, số tờ khai, mã token SHA-256.
  - Tím than (`bold magenta`): Giá cước, đơn giá bốc dỡ, tổng tiền thanh toán (USD / VND).
- **Trình bày Bảng biểu (Rich Tables)**:
  - Khung viền thanh mảnh (`box.ROUNDED`), căn lề số liệu về bên phải, căn lề trạng thái ở giữa.
  - Phân tách rõ ràng giữa thông tin đầu vào, phân tích điều kiện pháp lý và kết luận quyết định.

## 2. Terminal Wireframes (ASCII Mocks)

### Wireframe 1: Thẩm định Xả Nước thải MARPOL Annex IV (`sewage evaluate`)
```
╭───────────────── MARPOL ANNEX IV SEWAGE DISCHARGE AUDIT ────────────────╮
│ Vessel Name: MEKONG PIONEER               IMO Number: 9876543           │
│ Distance to Shore: 4.5 NM                 Vessel Speed: 11.2 knots      │
│ Treatment Type: COMMINUTED_AND_DISINFECTED (CDS)                        │
├─────────────────────────────────────────────────────────────────────────┤
│ [PARAM] Coliform: 45 CFU/100ml [OK]       TSS: 20 mg/L [OK]             │
│ [PARAM] BOD5: 15 mg/L [OK]                COD: 80 mg/L [OK]             │
├─────────────────────────────────────────────────────────────────────────┤
│ STATUS: [bold green]DISCHARGE PERMITTED EN-ROUTE[/bold green]           │
│ Statutory Basis: MARPOL Annex IV Reg 11.1(a) & MEPC.227(64)             │
│ Verification Token: 7F8B9C12A34E5678D901EF23                            │
╰─────────────────────────────────────────────────────────────────────────╯
```

### Wireframe 2: Giám định Sức khỏe Thuyền viên STCW/MLC (`seafarermedical verify`)
```
╭──────────────── STCW 2010 / MLC 2006 SEAFARER MEDICAL AUDIT ───────────╮
│ Seafarer Name: NGUYEN VAN HUNG             SID/Passport: VN123456       │
│ Age: 28               Department: DECK (Navigational Watch)             │
├─────────────────────────────────────────────────────────────────────────┤
│ Vision: Right 1.0, Left 0.8 [PASS]        Ishihara Color: 16/16 [PASS]  │
│ Hearing: Whisper 3.5m, Normal 6.0m [PASS] Disqualifying Conditions: NONE│
├─────────────────────────────────────────────────────────────────────────┤
│ VERDICT: [bold green]FIT FOR SEAFARING DUTY (MAX 2 YEARS)[/bold green]   │
│ Valid Until: 2028-10-08                   Cert No: MED-2026-9812        │
│ Verification Token: 3A5D8F91B24E760C1189AF45                            │
╰─────────────────────────────────────────────────────────────────────────╯
```

### Wireframe 3: Tính Cước Bốc dỡ Container Cảng biển (`stevedoretariff calculate`)
```
╭──────────────── SEAPORT STEVEDORING TARIFF CALCULATION ─────────────────╮
│ Port: CAI MEP WATERFRONT (Zone III Deep)  Category: CONTAINER 40FT      │
│ Quantity: 50 Cont                         Status: FULL (LADEN)          │
│ Cargo Type: IMDG_CLASS_3 (+30%)           Operation: VESSEL_TO_CY       │
├─────────────────────────────────────────────────────────────────────────┤
│ Base Rate: $88.00 / cont                  IMDG Surcharge: +$26.40       │
│ Net Rate: $114.40 / cont                                                │
├─────────────────────────────────────────────────────────────────────────┤
│ TOTAL STEVEDORING CHARGE: [bold magenta]$5,720.00 USD[/bold magenta]    │
│ Statutory Rule: Circular 39/2023/TT-BGTVT Table 3 & Circular 12/2024   │
│ Invoice Hash: 99B23E11C45AA781D923FF40                                  │
╰─────────────────────────────────────────────────────────────────────────╯
```

### Wireframe 4: Giám sát Kho Ngoại quan Hải quan (`bondedwh supervise`)
```
╭──────────────── BONDED WAREHOUSE DWELL TIME SUPERVISION ────────────────╮
│ Warehouse: TAN CANG BONDED WH             Customs Branch: KHV-CAT LAI   │
│ Declaration No: C11-20251001-9981         Entry Date: 2025-10-08        │
│ Days in Storage: 365 days                 Extension Status: GRANTED (+12M)│
├─────────────────────────────────────────────────────────────────────────┤
│ Remaining Dwell Allowance: 365 days       Overstay Days: 0 days         │
├─────────────────────────────────────────────────────────────────────────┤
│ STATUS: [bold green]NORMAL STORAGE (EXTENDED ACTIVE)[/bold green]       │
│ Statutory Reference: Law on Customs 2014 Art. 61 & Decree 08/2015       │
│ Audit Token: 12FA9087E54CD321AB9801FE                                   │
╰─────────────────────────────────────────────────────────────────────────╯
```

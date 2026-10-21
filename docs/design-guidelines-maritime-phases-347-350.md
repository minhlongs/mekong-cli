# Design Guidelines: Maritime Phases 347–350

## 1. Triết lý Thiết kế
- **Hybrid Modular Facade Pattern**: Mỗi micro-engine chuyên trách một lĩnh vực hàng hải độc lập, re-export qua một facade trung tâm gọn nhẹ.
- **Giới hạn kích thước file**: Mọi file nguồn và test suite bắt buộc < 200 dòng code.
- **Zero-Mock Testing**: Kiểm thử trực tiếp với các giá trị vật lý, công thức hải quân học và chuỗi mã hoá thực tế.

## 2. Hệ thống Phân hệ Kỹ thuật
- **Phase 347**: `iccp` / `chongannmon` (NACE SP0176, Ag/AgCl reference potential, current density).
- **Phase 348**: `scrnox` / `khixatier3` (MARPOL Annex VI Tier III NOx, SCR urea dosing, methane slip).
- **Phase 349**: `anchorwindlass` / `neocang` (IACS UR A1 Equipment Number, anchor holding power, dragging alert).
- **Phase 350**: `eblmletr` / `vandonso` (MLETR title transfer, hash lineage, release verification).

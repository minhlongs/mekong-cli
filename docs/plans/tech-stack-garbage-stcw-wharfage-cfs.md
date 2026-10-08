# Tech Stack & Kiến Trúc: Phases 287-290

## 1. Nguyên tắc Thiết kế
- **Ngôn ngữ**: Python 3.9+ (Zero-dependency core logic, sử dụng thư viện chuẩn `dataclasses`, `enum`, `math`, `typing`, `hashlib`, `datetime`).
- **Giao diện CLI**: Typer với Rich (Tables, Panels, Styles) hỗ trợ hiển thị song ngữ Anh/Việt.
- **Giao thức Tích hợp**: FastMCP (Model Context Protocol) với JSON-RPC 2.0 schemas và `.to_dict()` serialization.
- **Tiêu chuẩn kiểm thử**: `pytest` với 100% kiểm thử thực tế không mock (zero-mock test suite).

## 2. Cấu trúc Module Core (`src/core/maritime_garbage_stcw_wharfage_cfs_engine.py`)
1. **GarbageDischargeEngine (Phase 287)**:
   - Enums: `GarbageCategory` (PLASTICS, FOOD_WASTE, DOMESTIC_WASTE, CARGO_RESIDUES_NON_HME, CARGO_RESIDUES_HME, ANIMAL_CARCASSES), `DischargeZone` (SPECIAL_AREA, OUTSIDE_SPECIAL_AREA, PORT_WATERS).
   - Validations: Quy tắc cấm tuyệt đối nhựa, kiểm tra hạt nghiền <= 25mm, khoảng cách hải lý (3 NM, 12 NM, 100 NM), cờ tàu đang hành trình (en_route >= 0.5 hải lý/giờ).
   - Nhật ký: Mã ghi sổ GRB Part I / Part II với băm kiểm tra tính toàn vẹn SHA-256.
2. **SeafarerRestEngine (Phase 288)**:
   - Data models: `WorkRestSlot` (khoảng làm việc/nghỉ ngơi theo giờ), `SeafarerRestProfile`.
   - Thuật toán: Trượt cửa sổ 24 giờ (tối thiểu 10 giờ nghỉ, tối đa 2 khoảng, 1 khoảng >= 6h liên tục, khoảng cách <= 14h), trượt cửa sổ 7 ngày (tối thiểu 77 giờ nghỉ).
   - Phát hiện vi phạm STCW/MLC và xử lý trường hợp khẩn cấp có lịch nghỉ bù.
3. **PortWharfageEngine (Phase 289)**:
   - Mô hình cước: Thông tư 39/2023/TT-BGTVT và Thông tư 12/2024/TT-BGTVT.
   - Tính toán: Biểu cước cầu cảng (Wharfage) theo GT-giờ hoặc LOA-giờ, phân loại tàu làm hàng vs tàu chờ/phao neo, phụ phí quá hạn berth overstay surcharge (+50% đến +100%).
4. **CfsEsealEngine (Phase 290)**:
   - Mô hình kho CFS: Quản lý chia tách/đóng ghép hàng LCL, theo dõi ngày lưu kho (giới hạn 90 ngày + 90 ngày gia hạn), cảnh báo quá hạn.
   - E-Seal Tracking: Theo dõi tình trạng khóa cáp niêm phong, cảnh báo cắt cáp (cable tamper), sai lộ trình (>500m), mất GPS (>30m).

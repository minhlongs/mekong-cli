# Hướng dẫn Thiết kế Giao diện & Trải nghiệm: Maritime Phases 339–342

## 1. Nguyên tắc Trực quan Hóa (Visual & CLI Experience)
- **Chuẩn Output:** JSON cấu trúc rõ ràng cho máy và bảng tổng hợp Rich trực quan cho người vận hành hàng hải.
- **Màu sắc Trạng thái (Status Palette):**
  - `GREEN` (`Compliant` / `Safe` / `Normal`): Thao tác hàng hải được phép, RIO $\ge 0$, xả nước rửa Non-HME ngoài vùng đặc biệt $\ge 12\text{ NM}$, pin EV ổn định.
  - `YELLOW` (`Warning` / `Elevated Risk` / `Reduced Speed`): RIO từ $-10$ đến $0$, phát hiện khí sớm off-gas chưa bùng phát, SCOPIC được kích hoạt.
  - `RED` (`Danger` / `Prohibited` / `Thermal Runaway`): RIO $< -10$ cấm hành hải, xả HME trái phép, phát hiện cháy pin lithium-ion bùng phát nhiệt.

## 2. Hệ thống Lệnh CLI & Bilingual Aliases
| Phân hệ | Lệnh gốc | Alias Tiếng Việt 1 | Alias Tiếng Việt 2 | Chức năng chính |
|---|---|---|---|---|
| **Phase 339** | `polar` | `bangtuyet` | `polarisrio` | Đánh giá rủi ro băng tuyết & RIO POLARIS |
| **Phase 340** | `holdwash` | `ruahamhang` | `marpolhme` | Kiểm tra xả nước rửa hầm hàng & MARPOL HME |
| **Phase 341** | `evfire` | `chayxedien` | `pctcro` | Giám sát an toàn cháy nổ xe điện PCTC |
| **Phase 342** | `salvage` | `cuuhohanghai` | `scopiclof` | Tính thù lao cứu hộ LOF 2024 & SCOPIC |

## 3. Kiến trúc Đơn vị Dữ liệu (Data Units)
- Tốc độ: Hải lý/giờ (`knots`).
- Khoảng cách: Hải lý (`NM`).
- Nồng độ băng: Phần mười (`tenths`, $0 - 10$).
- Nhiệt độ: Độ C ($^\circ C$).
- Thể tích nước: Mét khối ($m^3$) hoặc Lít ($L$).
- Nồng độ khí: Parts per million ($ppm$) hoặc phần trăm $LEL$.
- Tiền tệ: USD ($).

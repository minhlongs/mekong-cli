# Tech Stack: Maritime Phases 383–386

## 1. Lõi Ngôn ngữ & Tính toán Khoa học Hàng hải
- **Python 3.9+ / System Python**: Dataclasses, Enums, Type Hints, Math, Hashlib SHA-256.
- **Thư viện chuẩn**: `math`, `typing`, `dataclasses`, `enum`, `datetime`.
- **Mô hình Tách lọc Ly tâm & Thủy lực (Purification & Fluid Dynamics)**:
  - Máy lọc dầu ly tâm: Công thức lực ly tâm $G = r \omega^2 / g$, hiệu suất tách lọc Al+Si $\eta \ge 85\%$, bảo vệ phốt nước EPC theo ISO 8217:2024.
  - Hệ thống lái thủy lực SOLAS: Thời gian bẻ lái $35^\circ \to 30^\circ \le 28\text{s}$ (chính) và $15^\circ \to 15^\circ \le 60\text{s}$ (khẩn cấp), chuyển đổi nguồn dự phòng $\le 45\text{s}$.
- **Mô hình Chống nghiêng & Giám sát Khí Buồng bơm (Anti-Heeling & Gas Sniffing)**:
  - Hệ thống chống nghiêng dằn tàu: Cân bằng mô-men $M = w \cdot d$, điều khiển bơm thuận nghịch công suất lớn giữ góc nghiêng $|\theta| \le 1.0^\circ$.
  - Giám sát khí buồng bơm tàu dầu: Trích mẫu liên tục hydrocarbon $\le 10\% / 20\%$ LEL, độc tố H2S $\ge 5$ ppm, thông gió hút cưỡng bức $\ge 20$ lần trao đổi khí/giờ theo SOLAS II-2 Reg 4.5.10.

## 2. Giao diện Dòng lệnh (CLI) & MCP Gateway
- **Typer & Click**: Xây dựng 4 ứng dụng con CLI độc lập với 8 bí danh song ngữ (Anh - Việt):
  - `purifier` / `mayloclytam`
  - `emergsteering` / `laikhancap`
  - `antiheeling` / `chongnghiengtau`
  - `pumproomgas` / `khibuongbom`
- **FastMCP**: 4 async tool RPC decorators tương thích Model Context Protocol.

## 3. Kiểm thử & Đảm bảo Chất lượng
- **pytest & pytest-asyncio**: 100% Zero-mock testing, kiểm thử toán học và an toàn biên thực tế.
- **Ruff**: Linter & code formatting tuân thủ nghiêm ngặt chuẩn PEP 8.
- **Quy tắc Kiến trúc**: Giới hạn nghiêm ngặt file mã nguồn và test suite < 200 dòng/file.

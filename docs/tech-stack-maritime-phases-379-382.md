# Tech Stack: Maritime Phases 379–382

## 1. Lõi Ngôn ngữ & Tính toán Khoa học Hàng hải
- **Python 3.9+ / System Python**: Dataclasses, Enums, Type Hints, Math, Hashlib SHA-256.
- **Thư viện chuẩn**: `math`, `typing`, `dataclasses`, `enum`, `datetime`.
- **Mô hình Khí nén & Thủy lực (Pneumatic & Hydrodynamics)**:
  - Khí nén khởi động: Phương trình khí nén đẳng nhiệt/đoạn nhiệt nạp bình khí 30 bar theo SOLAS II-1 Reg 26.
  - Thủy lực làm mát: Phương trình tổn thất áp suất qua phin lọc $\Delta P$, định lượng dòng điện bảo vệ catốt MGPS $I = k \cdot Q$.
- **Mô hình Thủy tĩnh & Động học Hàng hải (Hydrostatics & Kinematics)**:
  - Cân bằng mớn nước: Quarter-mean draft $d_M = (d_F + 6d_M + d_A) / 8$, góc nghiêng ngang $\theta$, độ võng/vồng thân tàu $h_{\text{sag}}$.
  - Radar ARPA & Cảnh báo Va chạm: Vector tương đối $\vec{V}_r = \vec{V}_t - \vec{V}_o$, giải tích điểm tiếp cận gần nhất CPA và thời gian TCPA theo IMO MSC.192(79).

## 2. Giao diện Dòng lệnh (CLI) & MCP Gateway
- **Typer & Click**: Xây dựng 4 ứng dụng con CLI độc lập với 8 bí danh song ngữ (Anh - Việt).
- **FastMCP**: 4 async tool RPC decorators tương thích Model Context Protocol, JSON-RPC.

## 3. Kiểm thử & Đảm bảo Chất lượng
- **pytest & pytest-asyncio**: 100% Zero-mock testing, kiểm thử toán học và an toàn biên thực tế.
- **Ruff**: Linter & code formatting tuân thủ nghiêm ngặt chuẩn PEP 8.
- **Quy tắc Kiến trúc**: Giới hạn nghiêm ngặt file mã nguồn và test suite < 200 dòng/file.

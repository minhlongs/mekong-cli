---
name: waterway
description: Vietnamese Inland Waterway Transport, River Ports & Canal Navigation Suite.
---

# 🚢 Waterway — Vietnamese Inland Waterway Transport, River Ports & Canal Navigation

Autonomous operations engine for Vietnamese inland waterway transport, river ports, canal corridors (Mekong Delta & Red River Delta), vessel registration with lifespan caps, port departure clearances (*giấy phép rời bến cảng vụ*), captain licensing (T1-T4), and barge freight calculations under the Law on Inland Waterway Navigation 2004 (Law 23/2004/QH11 amended by Law 48/2014/QH13), Decree 08/2021/NĐ-CP, Decree 54/2022/NĐ-CP, Decree 111/2014/NĐ-CP, TCVN 5664:2009, Circular 40/2019/TT-BGTVT, and Circular 40/2020/TT-BGTVT.

## Statutory Legal Framework

1. **Luật Giao thông đường thủy nội địa 2004 (sửa đổi bổ sung 2014)**:
   - Quy định về kết cấu hạ tầng luồng tuyến, cảng bến thủy nội địa, phương tiện thủy, thuyền viên và quy tắc giao thông đường thủy.
   - Thẩm quyền quản lý của Cục Đường thủy nội địa Việt Nam và các Cảng vụ Đường thủy nội địa khu vực.

2. **Quản Lý Cảng Bến Thủy Nội Địa (Nghị định 08/2021/NĐ-CP & Nghị định 54/2022/NĐ-CP)**:
   - Thủ tục công bố mở, đóng cảng thủy nội địa, bến thủy nội địa, bến khách ngang sông, khu neo đậu.
   - Quy trình kiểm tra an toàn kỹ thuật và cấp Giấy phép vào, rời cảng bến cho phương tiện thủy.

3. **Niên Hạn Sử Dụng Phương Tiện Thủy Nội Địa (Nghị định 111/2014/NĐ-CP)**:
   - Tàu chở khách vỏ thép: Tối đa 30 năm (vỏ gỗ hoặc composite tối đa 20 năm).
   - Tàu chở khách cao tốc (tốc độ $\ge 30\text{ km/h}$): Tối đa 20 năm.
   - Tàu chở hàng khô, sà lan hàng rời, sà lan container, tàu kéo/đẩy: Tối đa 35 năm.
   - Tàu chở dầu, hóa chất nguy hiểm, khí hóa lỏng: Tối đa 25 năm.

4. **Cấp Kỹ Thuật Luồng Tuyến Thủy Nội Địa (TCVN 5664:2009)**:
   - **Cấp Đặc biệt & Cấp I**: Độ sâu luồng $\ge 3.0\text{ m}$, bề rộng đáy $\ge 50\text{ m}$, tĩnh không thông thuyền của cầu $\ge 10.0\text{ m}$ (sông Tiền, sông Hậu, sông Hồng, tuyến kênh Chợ Gạo).
   - **Cấp II**: Luồng sâu $\ge 2.5\text{ m}$, tĩnh không cầu $\ge 7.0\text{ m}$ (sông Đuống, sông Thái Bình, kênh Măng Thít).
   - **Cấp III**: Luồng sâu $\ge 2.0\text{ m}$, tĩnh không cầu $\ge 6.0\text{ m}$ (sông Vàm Cỏ Đông, Vàm Cỏ Tây).

5. **Bằng Thuyền Trưởng & Máy Trưởng Thủy Nội Địa (Thông tư 40/2020/TT-BGTVT)**:
   - **Hạng Nhất (T1)**: Không hạn chế trọng tải phương tiện hoặc sức chở khách.
   - **Hạng Nhì (T2)**: Phương tiện đến 1,000 tấn hoặc chở từ 50 đến dưới 100 khách; đoàn lai đến 1,000 tấn.
   - **Hạng Ba (T3)**: Phương tiện đến 400 tấn hoặc chở từ 20 đến dưới 50 khách; đoàn lai đến 400 tấn.
   - **Hạng Tư (T4)**: Phương tiện đến 150 tấn hoặc chở đến 20 khách.

---

## CLI Usage

```bash
# Báo cáo telemetry tổng quan mạng lưới đường thủy nội địa
mekong waterway status
mekong waterway status --json

# Đăng ký tuyến luồng kỹ thuật đường thủy
mekong waterway channel CH-CHO-GAO "Tuyến Kênh Huyết Mạch Chợ Gạo" --grade GRADE_I --length 28.5 --depth 3.5 --clearance 10.0 --basin "Đồng bằng Sông Cửu Long" --json

# Đăng ký cảng bến thủy nội địa và năng lực tiếp nhận
mekong waterway port PRT-MY-THO "Cảng Thủy Nội Địa Mỹ Tho" --type CONTAINER_PORT --channel CH-TIEN-01 --province "Tiền Giang" --dwt 3000 --teu 500 --json

# Đăng ký phương tiện thủy & kiểm tra niên hạn lưu hành
mekong waterway vessel VR-22001188 "Sà lan Hưng Phát 36" --type CARGO_BARGE_CONTAINER --year 2021 --material STEEL --capacity 1500 --ais --vhf --json

# Cấp Giấy phép rời cảng bến thủy nội địa (Cảng vụ Đường thủy)
mekong waterway clearance VR-22001188 PRT-MY-THO "Nguyễn Văn Hùng" --tier T2 --cargo CONTAINER --volume 48.0 --ais-online --vhf-online --lifejackets --json

# Thẩm tra điều kiện cấp / công nhận bằng thuyền trưởng
mekong waterway captain "Lê Hoàng Long" --tier T1 --exp 48 --health 1 --json

# Tính cước vận tải hàng hóa đường thủy bằng sà lan (tấn-km / TEU-km)
mekong waterway freight "Công ty Gạo Lộc Trời An Giang" --cargo BULK_AGRICULTURE --volume 500.0 --distance 180.0 --grade GRADE_I --json

# Tra cứu dữ liệu tuyến luồng, cảng bến, tàu thủy, giấy phép rời bến
mekong waterway list channels --limit 50 --json
mekong waterway list ports --json
mekong waterway list vessels --json
mekong waterway list clearances --json
mekong waterway list captains --json
mekong waterway list bills --json
```

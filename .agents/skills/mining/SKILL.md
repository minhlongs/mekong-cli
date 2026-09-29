---
name: mining
description: Vietnamese Mineral Law 2010, Concession Rights Fees, Resource Royalties & Environmental Rehabilitation.
---

# ⛏️ Mining — Vietnamese Mineral Law 2010, Concession Rights Fees, Resource Royalties & Environmental Rehabilitation

Autonomous operations engine for Vietnamese mining and mineral exploitation, statutory concession rights fees under Decree 67/2019/NĐ-CP ($T = Q \times G \times K \times R$), natural resources royalty taxes under Law on Natural Resources Tax 2009 & Resolution 1084/2015, environmental rehabilitation escrow funds under Law on Environmental Protection 2020 (Decree 08/2022/NĐ-CP & QCVN 40:2011/BTNMT), and river sand & gravel dredging oversight under Decree 23/2020/NĐ-CP.

## Statutory Legal Framework

1. **Luật Khoáng sản 2010 (Luật số 60/2010/QH12) & Nghị định 158/2016/NĐ-CP**:
   - Thẩm quyền cấp phép khai thác khoáng sản:
     - **Bộ Tài nguyên và Môi trường (Bộ TN&MT)**: Cấp phép các mỏ khoáng sản chiến lược quốc gia (Đất hiếm, Bauxit, Than đá, Vàng, Titan, Dầu khí, Apatit).
     - **UBND cấp Tỉnh / Thành phố**: Cấp phép khai thác khoáng sản làm vật liệu xây dựng thông thường (Cát sỏi lòng sông, Đá xây dựng, Đất san lấp).
   - Thời hạn cấp phép khai thác tối đa không quá **30 năm**, gia hạn nhiều lần nhưng tổng thời gian gia hạn không quá **20 năm**.

2. **Tiền Cấp Quyền Khai Thác Khoáng Sản (Nghị định 67/2019/NĐ-CP & Nghị định 36/2020/NĐ-CP)**:
   - Công thức xác định tiền cấp quyền khai thác:
     $$T = Q \times G \times K \times R$$
     - $Q$: Trữ lượng địa chất tính tiền cấp quyền (tấn, $m^3$).
     - $G$: Giá tính tiền cấp quyền khoáng sản theo quy định nhà nước.
     - $K$: Hệ số phương pháp khai thác ($K = 1.0$ cho lộ thiên/open-pit, $K = 0.9$ cho hầm lò/underground).
     - $R$: Mức thu tiền cấp quyền khoáng sản (% theo Nghị định 67/2019: Đất hiếm 5%, Vàng 5%, Bauxit 4%, Than 3%, Đá xi măng 3%, Cát sỏi 5%).
   - Cơ chế nộp phân kỳ hàng năm theo vòng đời dự án (tối đa bằng thời hạn cấp phép).

3. **Thuế Tài Nguyên (Luật Thuế Tài nguyên 2009, Nghị quyết 1084/2015/UBTVQH13 & Thông tư 152/2015/TT-BTC)**:
   - Thuế tài nguyên phải nộp = Sản lượng khai thác thực tế $\times$ Giá tính thuế đơn vị $\times$ Thuế suất thuế tài nguyên:
     - Đất hiếm: 18%
     - Quặng Titan: 16%
     - Quặng Vàng: 15%
     - Quặng Bauxit: 12%
     - Cát lòng sông: 12%
     - Than đá: 10%
     - Đá xây dựng: 10%

4. **Ký Quỹ Phục Hồi Môi Trường & Xả Thải Mỏ (Luật BVMT 2020 & Nghị định 08/2022/NĐ-CP)**:
   - Bắt buộc lập Phương án cải tạo, phục hồi môi trường mỏ và nộp tiền ký quỹ vào Quỹ Bảo vệ Môi trường (VEPF).
   - Ký quỹ lần đầu tối thiểu **25%** tổng dự toán kinh phí cải tạo phục hồi môi trường đã phê duyệt.
   - Giám sát hoàn thổ, trồng cây xanh và quan trắc nước thải công nghiệp mỏ theo **QCVN 40:2011/BTNMT** (pH đạt $6.0 - 9.0$, hàm lượng tổng chất rắn lơ lửng $\text{TSS} \le 50\text{ mg/L}$, hàm lượng kim loại nặng không vượt ngưỡng).

5. **Giám Sát Cát, Sỏi Lòng Sông (Nghị định 23/2020/NĐ-CP)**:
   - Khung giờ khai thác nghiêm ngặt: **chỉ từ 07:00 đến 17:00** trong ngày (nghiêm cấm mọi hành vi khai thác vào ban đêm).
   - 100% phương tiện tàu hút, sà lan khai thác phải lắp đặt thiết bị định vị vệ tinh GPS lưu trữ hành trình.
   - Bắt buộc lắp đặt camera giám sát tại bến bãi tập kết vật liệu và thiết bị đo dung tích khoang chứa.

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan ngành khoáng sản & an toàn môi trường
mekong mining
mekong mining --json

# 2. Đăng ký giấy phép khai thác mỏ & phân định thẩm quyền
mekong mining license "Mỏ Đất hiếm Bắc Nậm Xe" --type RARE_EARTH --enterprise "Công ty Đất hiếm Việt Nam" --reserve 3000000 --capacity 150000 --method OPEN_PIT --province "Lai Châu" --duration 25

# 3. Tính tiền cấp quyền khai thác khoáng sản T = Q * G * K * R
mekong mining rights-fee "LIC-MIN-1234" --reserve 3000000 --price 850000000 --method OPEN_PIT --type RARE_EARTH --installments 10

# 4. Kê khai thuế tài nguyên khoáng sản hàng quý
mekong mining royalty "LIC-MIN-1234" --period "2026-Q1" --volume 35000 --type RARE_EARTH

# 5. Thẩm tra ký quỹ cải tạo môi trường mỏ & nước thải QCVN 40
mekong mining rehab "LIC-MIN-1234" --cost 15000000000 --deposit-pct 25.0 --trees 20000 --ph 7.4 --tss 32.0

# 6. Giám sát phương tiện khai thác cát sỏi lòng sông theo NĐ 23/2020
mekong mining sand "LIC-MIN-5678" "SG-9988" --time "11:15" --gps --camera --cargo 320.0

# 7. Tra cứu danh mục
mekong mining list licenses
mekong mining list fees
mekong mining list taxes
mekong mining list rehab
mekong mining list sand
mekong mining status
```

---

## FastMCP & JSON-RPC 2.0 Tools

- `mekong_mining_license`: Register mineral mining concession and determine statutory licensing authority.
- `mekong_mining_rights_fee`: Calculate statutory mineral rights fee $T = Q \times G \times K \times R$ under Decree 67/2019.
- `mekong_mining_royalty`: Compute natural resources royalty tax declaration under Law on Natural Resources Tax.
- `mekong_mining_rehab`: Audit environmental rehabilitation escrow deposit and wastewater effluent against QCVN 40:2011.
- `mekong_mining_sand`: Inspect river sand & gravel dredging vessel compliance against Decree 23/2020.
- `mekong_mining_list`: Query registered mining licenses, rights fees, royalty taxes, environmental rehabs, or sand inspections.
- `mekong_mining_status`: Retrieve Vietnamese mining regulatory, mineral rights fees, royalties, and environmental telemetry.

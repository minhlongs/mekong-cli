---
name: livestock
description: Vietnamese Animal Husbandry, Livestock Farming, Feed Standards & Biosecurity Suite.
---

# 🐖 Livestock — Vietnamese Animal Husbandry, Livestock Farming, Feed Standards & Biosecurity

Autonomous operations engine for Vietnamese animal husbandry, statutory livestock units (Đơn vị vật nuôi - ĐVN), farm scale classification, biosecurity buffer distance compliance, regional stocking density caps, animal feed safety standards, and agricultural waste biogas sizing under the Law on Animal Husbandry 2018 (Law 32/2018/QH14), Decree 13/2020/NĐ-CP, Decree 46/2022/NĐ-CP, and QCVN 01-183:2016/BNNPTNT.

## Statutory Legal Framework

1. **Luật Chăn nuôi 2018 (Luật số 32/2018/QH14) & Nghị định 13/2020/NĐ-CP, Nghị định 46/2022/NĐ-CP**:
   - **Hệ số Đơn vị vật nuôi (Livestock Unit - ĐVN)** theo Phụ lục V Nghị định 13/2020/NĐ-CP:
     * Lợn thịt (`PIG_FATTENER`): $0.20\text{ ĐVN}$
     * Lợn nái / đực giống (`PIG_SOW`): $0.50\text{ ĐVN}$
     * Bò thịt (`CATTLE_BEEF`): $1.00\text{ ĐVN}$
     * Bò sữa (`CATTLE_DAIRY`): $1.50\text{ ĐVN}$
     * Trâu (`BUFFALO`): $1.00\text{ ĐVN}$
     * Gà thịt (`POULTRY_BROILER`): $0.014\text{ ĐVN}$
     * Gà đẻ (`POULTRY_LAYER`): $0.018\text{ ĐVN}$
     * Vịt thịt / đẻ (`DUCK`): $0.018\text{ ĐVN}$
     * Dê, cừu (`GOAT_SHEEP`): $0.15\text{ ĐVN}$
   - **Phân loại 4 cấp quy mô trang trại** (Điều 21 Nghị định 13/2020/NĐ-CP):
     * **Quy mô lớn** (`LARGE_SCALE`): $\ge 300\text{ ĐVN}$ (Bắt buộc cấp Giấy chứng nhận đủ điều kiện chăn nuôi).
     * **Quy mô vừa** (`MEDIUM_SCALE`): Từ 30 đến dưới 300 ĐVN.
     * **Quy mô nhỏ** (`SMALL_SCALE`): Từ 10 đến dưới 30 ĐVN.
     * **Chăn nuôi nông hộ** (`HOUSEHOLD`): Dưới 10 ĐVN.
   - **Mật độ chăn nuôi tối đa vùng sinh thái** (Điều 53 Luật Chăn nuôi):
     * Đồng bằng sông Hồng: $\le 1.5\text{ ĐVN/ha}$ đất nông nghiệp
     * Trung du và miền núi phía Bắc: $\le 1.0\text{ ĐVN/ha}$
     * Bắc Trung Bộ và Duyên hải miền Trung: $\le 1.0\text{ ĐVN/ha}$
     * Tây Nguyên: $\le 1.0\text{ ĐVN/ha}$
     * Đông Nam Bộ: $\le 1.5\text{ ĐVN/ha}$
     * Đồng bằng sông Cửu Long: $\le 1.5\text{ ĐVN/ha}$

2. **Khoảng Cách An Toàn Sinh Học Trang Trại (Điều 5 Nghị định 13/2020/NĐ-CP)**:
   - Khoảng cách đến khu dân cư, trường học, bệnh viện, chợ:
     * Trang trại quy mô lớn: $\ge 400\text{ m}$
     * Trang trại quy mô vừa: $\ge 300\text{ m}$
     * Trang trại quy mô nhỏ: $\ge 200\text{ m}$
   - Khoảng cách đến nguồn nước sinh hoạt:
     * Trang trại quy mô lớn: $\ge 100\text{ m}$
     * Trang trại quy mô vừa & nhỏ: $\ge 80\text{ m}$
   - Khoảng cách giữa 2 trang trại chăn nuôi quy mô lớn: $\ge 1,000\text{ m}$.

3. **Chất Lượng Thức Ăn Chăn Nuôi & Kiểm Soát Chất Cấm (QCVN 01-183:2016/BNNPTNT & Thông tư 21/2019/TT-BNNPTNT)**:
   - Khống chế độc tố nấm mốc Aflatoxin B1 $\le 20.0\text{ ppb}$.
   - Kim loại nặng: Chì (Pb) $\le 5.0\text{ ppm}$, Asen (As) $\le 2.0\text{ ppm}$.
   - Nghiêm cấm tuyệt đối hóa chất kích thích tăng trọng nhóm Beta-agonist (Salbutamol, Clenbuterol, Ractopamine) = 0.

4. **Quản Lý Chất Thải Chăn Nuôi & Dung Tích Hầm Biogas (Nghị định 46/2022/NĐ-CP & QCVN 62-MT:2016/BTNMT)**:
   - Định mức dung tích hầm Biogas: $\ge 0.8\text{ m}^3/\text{ĐVN}$ đối với lợn, $\ge 1.2\text{ m}^3/\text{ĐVN}$ đối với trâu bò.

---

## CLI Usage

```bash
# Báo cáo tổng quan ngành chăn nuôi & an toàn sinh học
mekong livestock status
mekong livestock status --json

# Đăng ký trang trại chăn nuôi & tính Đơn vị vật nuôi (ĐVN)
mekong livestock farm "Trang Trại Heo Thịt CP Đồng Nai" --owner "CP Vietnam Corp" --province "Đồng Nai" --animal PIG_FATTENER --heads 2500 --land 35.0 --region SOUTHEAST --json

# Đánh giá khoảng cách an toàn sinh học trang trại
mekong livestock distance LVF-12345678 --scale LARGE_SCALE --residential 450 --water 120 --farm-dist 1200 --json

# Kiểm định chất lượng thức ăn chăn nuôi & độc tố
mekong livestock feed "Thức ăn hỗn hợp cho heo thịt vỗ béo" --type PIG_FEED_COMPLETE --maker "De Heus Vietnam" --protein 18.5 --aflatoxin 8.5 --lead 1.2 --json

# Thẩm định dung tích công trình hầm khí sinh học Biogas
mekong livestock waste LVF-12345678 --dvn 500.0 --method BIOGAS_DIGESTER --volume 450.0 --pig --json

# Tra cứu dữ liệu chăn nuôi, an toàn sinh học, thức ăn, biogas
mekong livestock list farms --limit 50 --json
mekong livestock list biosecurity --json
mekong livestock list feed --json
mekong livestock list waste --json
```

---

## MCP Tools

| MCP Tool | Description |
|---|---|
| `mekong_livestock_farm` | Register livestock farm, calculate statutory Livestock Units (ĐVN), scale, and density. |
| `mekong_livestock_distance` | Audit farm biosecurity buffer distances under Article 5 Decree 13/2020/NĐ-CP. |
| `mekong_livestock_feed` | Inspect animal feed quality, mycotoxins, heavy metals, and prohibited beta-agonists. |
| `mekong_livestock_waste` | Audit livestock manure treatment and Biogas tank sizing under Decree 46/2022/NĐ-CP. |
| `mekong_livestock_list` | Query registered livestock farms, biosecurity audits, feed tests, or waste projects. |
| `mekong_livestock_status` | Retrieve aggregate Vietnamese animal husbandry & biosecurity compliance telemetry. |

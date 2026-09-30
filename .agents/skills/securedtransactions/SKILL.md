---
name: securedtransactions
description: Vietnamese Registration of Security Interests, Secured Transactions & Collateral Priority Suite.
---

# 🛡️ Secured Transactions — Registration of Security Interests & Collateral Priority Engine

Autonomous compliance and legal operations engine for Vietnamese secured transactions (*giao dịch bảo đảm*), registration of security interests (*đăng ký biện pháp bảo đảm*), asset-backed collateral lien registries, statutory priority ranking, enforcement disposal notices, and official deregistration/release protocols under the **Civil Code 2015 (Law 91/2015/QH13, Chapter XV, Articles 292–350)**, **Decree No. 99/2022/NĐ-CP**, **Circular No. 08/2023/TT-BTP**, **Land Law 2024**, **Maritime Code 2015**, and **Law on Civil Aviation of Vietnam**.

## Statutory Legal Framework

1. **Bộ luật Dân sự 2015 (Luật số 91/2015/QH13, Chương XV, Điều 292–350)**:
   - Quy định 09 biện pháp bảo đảm thực hiện nghĩa vụ: Cầm cố tài sản (*Pledge*), Thế chấp tài sản (*Mortgage*), Đặt cọc (*Deposit*), Ký cược (*Security Collateral*), Ký quỹ (*Escrow Deposit*), Bảo lưu quyền sở hữu (*Title Retention*), Bảo lãnh (*Guarantee*), Tín chấp (*Pledge of Trust*), Cầm giữ tài sản (*Property Lien*).
   - Hiệu lực đối kháng với người thứ ba (*Opposability against third parties*): Phát sinh từ thời điểm đăng ký tại cơ quan có thẩm quyền theo quy định pháp luật (Điều 297 BLDS 2015).
   - Thứ tự ưu tiên thanh toán (Điều 308 BLDS 2015): Biện pháp bảo đảm có hiệu lực đối kháng với người thứ ba được ưu tiên thanh toán trước biện pháp chưa có hiệu lực đối kháng; giữa các biện pháp cùng có hiệu lực đối kháng, thứ tự thanh toán xác định theo thứ tự xác lập hiệu lực đối kháng (thời điểm đăng ký chính xác đến từng giây).

2. **Nghị định 99/2022/NĐ-CP về Đăng ký Biện pháp Bảo đảm**:
   - Quy định thẩm quyền, hồ sơ, thủ tục đăng ký, cung cấp thông tin về biện pháp bảo đảm bằng tài sản.
   - Thẩm quyền phân cấp:
     - **Cục Đăng ký quốc gia giao dịch bảo đảm (NRSU - Bộ Tư pháp)**: Động sản, quyền đòi nợ, khoản phải thu, phương tiện giao thông đường bộ, dự án đầu tư không gắn liền với đất.
     - **Văn phòng Đăng ký đất đai (Sở TN&MT)**: Quyền sử dụng đất, tài sản gắn liền với đất, nhà ở.
     - **Cơ quan đăng ký tàu biển Việt Nam (Cục Hàng hải VN)**: Tàu biển, phương tiện thủy nội địa đặc chủng.
     - **Cục Hàng không Việt Nam**: Tàu bay dân dụng.
   - Xử lý tài sản bảo đảm (Điều 51 Nghị định 99 & Điều 303 BLDS 2015): Thông báo xử lý tài sản bảo đảm, phương thức bán đấu giá, bên nhận bảo đảm tự bán, hoặc nhận chính tài sản để thay thế thực hiện nghĩa vụ.
   - Xóa đăng ký biện pháp bảo đảm (Điều 52 Nghị định 99): Giải chấp, giải tỏa phong tỏa tài sản bảo đảm khi nghĩa vụ chấm dứt hoặc theo thỏa thuận.

3. **Thông tư số 08/2023/TT-BTP**:
   - Biểu mẫu, hướng dẫn nghiệp vụ đăng ký biện pháp bảo đảm trực tuyến và trực tiếp qua Cổng dịch vụ công quốc gia và Hệ thống đăng ký trực tuyến Bộ Tư pháp.

---

## CLI Usage

```bash
# Báo cáo telemetry tổng quan hệ thống giao dịch bảo đảm
mekong securedtransactions status
mekong securedtransactions status --json

# Đăng ký biện pháp bảo đảm (thế chấp bất động sản / động sản / quyền đòi nợ)
mekong securedtransactions register REG-2026-001 MORTGAGE "Ngân hàng TMCP Ngoại thương Việt Nam" "Công ty TNHH Mekong Agri" 25000000000 --asset-type REAL_ESTATE --authority LAND_REGISTRY_OFFICE --notes "Thế chấp QSDĐ vay vốn lưu động" --json

# Liên kết tài sản bảo đảm vào hồ sơ đăng ký
mekong securedtransactions collateral REG-2026-001 ASSET-DAT-01 "QSDĐ Thửa 128 Tờ bản đồ 15 Cần Thơ" REAL_ESTATE 32000000000 --identifier "GCN-CT-2024-998811" --location "Ninh Kiều, Cần Thơ" --json

# Tính toán thứ tự ưu tiên thanh toán tài sản bảo đảm (Điều 308 BLDS 2015)
mekong securedtransactions priority ASSET-DAT-01
mekong securedtransactions priority ASSET-DAT-01 --json

# Phát hành thông báo xử lý tài sản bảo đảm (Điều 51 Nghị định 99/2022/NĐ-CP)
mekong securedtransactions disposal REG-2026-001 ASSET-DAT-01 AUCTION --recovery-target 25000000000 --disposal-date "2026-11-15" --authorized-officer "Luật sư Trần Văn Bảo" --json

# Xóa đăng ký biện pháp bảo đảm (Giải chấp - Điều 52 Nghị định 99/2022/NĐ-CP)
mekong securedtransactions deregister REG-2026-001 OBLIGATION_FULFILLED --officer "Chuyên viên Đặng Thị Mai" --json

# Tra cứu hồ sơ đăng ký và tài sản bảo đảm
mekong securedtransactions search --reg-type MORTGAGE --status ACTIVE --json
mekong securedtransactions list --limit 20
```

### CLI Subcommands Reference

| Subcommand | Description |
|---|---|
| `status` | Hiển thị dashboard tổng quan số lượng hồ sơ, tài sản bảo đảm, giá trị bảo lãnh và tỷ lệ giải chấp. |
| `register` | Đăng ký biện pháp bảo đảm mới, xác lập thời điểm đối kháng thứ ba và cấp mã biên nhận pháp lý. |
| `collateral` | Đăng ký danh mục tài sản bảo đảm gắn với hồ sơ bảo đảm (bất động sản, động sản, quyền đòi nợ). |
| `priority` | Tính toán và xếp hạng thứ tự ưu tiên thanh toán theo Điều 308 BLDS 2015 (thời điểm đối kháng). |
| `disposal` | Lập và phát hành thông báo xử lý tài sản bảo đảm theo Điều 51 Nghị định 99/2022/NĐ-CP. |
| `deregister` | Xóa đăng ký giao dịch bảo đảm (giải chấp), cấp chứng thư giải tỏa tài sản bảo đảm. |
| `search` | Tra cứu lọc đa tiêu chí hồ sơ bảo đảm theo loại biện pháp, tài sản, thẩm quyền và tình trạng. |
| `list` | Liệt kê danh sách hồ sơ bảo đảm đang hoạt động trên hệ thống. |

---

## MCP Tools Integration

Tích hợp 7 công cụ MCP chuẩn FastMCP và Stdio JSON-RPC:

- `mekong_securedtransactions_status()`: Trả về trạng thái, chỉ số thống kê và phân bố thẩm quyền.
- `mekong_securedtransactions_register(reg_id, reg_type, secured_party, grantor, secured_amount, asset_type, authority, effective_date, notes)`: Đăng ký biện pháp bảo đảm.
- `mekong_securedtransactions_collateral(reg_id, asset_code, asset_name, asset_type, estimated_value, identifier_number, location)`: Thêm tài sản bảo đảm.
- `mekong_securedtransactions_priority(asset_code)`: Tính toán thứ tự ưu tiên thanh toán đối với tài sản.
- `mekong_securedtransactions_disposal(reg_id, asset_code, disposal_method, recovery_target, expected_disposal_date, authorized_officer)`: Lập thông báo xử lý tài sản.
- `mekong_securedtransactions_deregister(reg_id, reason, certifying_officer)`: Thực hiện xóa đăng ký (giải chấp).
- `mekong_securedtransactions_search(registration_type, asset_type, registry_authority, status, search_query, limit)`: Tìm kiếm hồ sơ đăng ký.

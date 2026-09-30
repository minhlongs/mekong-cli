---
name: veterinary
description: Vietnamese Veterinary Medicine, Animal Disease Surveillance & Livestock Quarantine Suite.
---

# /veterinary — Vietnamese Veterinary Medicine & Livestock Quarantine Suite

Quản lý và giám sát tuân thủ công tác kiểm dịch động vật và sản phẩm động vật vận chuyển nội địa/liên tỉnh, giám sát và dập dịch bệnh truyền nhiễm nguy hiểm (Dịch tả lợn Châu Phi ASF, Cúm gia cầm H5N1, Lở mồm long móng FMD), kiểm soát giết mổ tập trung, cấp dấu vệ sinh thú y và thẩm định nhà máy sản xuất thuốc thú y chuẩn GMP-WHO theo Luật Thú y 2015.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Luật Thú y 2015** (Luật số 79/2015/QH13).
2. **Nghị định số 35/2016/NĐ-CP** và **Nghị định số 123/2018/NĐ-CP** quy định chi tiết thi hành Luật Thú y.
3. **Thông tư số 07/2016/TT-BNNPTNT** của Bộ Nông nghiệp & PTNT về phòng, chống dịch bệnh động vật trên cạn.
4. **Thông tư số 25/2016/TT-BNNPTNT** và **Thông tư số 04/2024/TT-BNNPTNT** về kiểm dịch động vật, sản phẩm động vật trên cạn.
5. **Thông tư số 09/2016/TT-BNNPTNT** quy định về kiểm soát giết mổ và vệ sinh thú y.
6. **Thông tư số 13/2016/TT-BNNPTNT** quy định về quản lý thuốc thú y, chứng chỉ hành nghề và thực hành tốt sản xuất thuốc thú y (GMP-WHO).

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Kiểm dịch Động vật & Sản phẩm Động vật (Điều 37–45)
- Thẩm định và cấp Giấy chứng nhận kiểm dịch vận chuyển ra khỏi địa bàn cấp tỉnh.
- Kiểm tra nguồn gốc từ vùng an toàn dịch bệnh, phiếu xét nghiệm âm tính với các bệnh truyền nhiễm nguy hiểm.
- Kiểm tra quy trình tiêu độc khử trùng phương tiện vận chuyển và niêm phong kẹp chì kiểm dịch.

### 2. Giám sát & Công bố Ổ dịch Truyền nhiễm Khẩn cấp (Điều 15–26)
- Tiếp nhận và theo dõi các ổ dịch nguy hiểm: Dịch tả lợn Châu Phi (`ASF`), Cúm gia cầm độc lực cao (`H5N1`, `H5N6`), Lở mồm long móng (`FMD`), Tai xanh (`PRRS`), Bệnh Dại (`RABIES`).
- Kích hoạt quy chế khẩn cấp: Khoanh vùng bán kính tối thiểu 3.0 km, tiêu hủy an toàn sinh học bằng chôn sâu / thiêu hủy, tiêm phòng bao vây và lập chốt kiểm dịch tạm thời 24/7.

### 3. Kiểm soát Giết mổ & Tem Dấu Vệ sinh Thú y (Điều 64–70)
- Kiểm tra lâm sàng động vật sống trước giết mổ (Antemortem) và khám thân thịt sau giết mổ (Postmortem).
- Đóng dấu kiểm soát giết mổ hoặc cấp tem vệ sinh thú y QR Code điện tử cho lô thịt đạt chuẩn.
- Ngăn chặn và xử lý nghiêm hành vi bơm nước, tạp chất hoặc hóa chất vào gia súc, gia cầm.

### 4. Quản lý Thuốc Thú y & Tiêu chuẩn Nhà máy GMP (Điều 77–107)
- Thẩm định người phụ trách chuyên môn có Chứng chỉ hành nghề thú y hợp lệ.
- Kiểm định nhà máy sản xuất thuốc thú y đạt tiêu chuẩn thực hành tốt sản xuất thuốc thú y GMP-WHO.
- Nghiêm cấm tuyệt đối việc tàng trữ, sản xuất, sử dụng chất cấm tăng trọng/tạo nạc (Salbutamol, Clenbuterol, Ractopamine, Chloramphenicol).

### 5. National Veterinary Telemetry & Status
- Báo cáo tổng thể chứng nhận kiểm dịch, số lượng gia súc gia cầm được giám sát, tình trạng ổ dịch và tỷ lệ thịt sạch qua lò mổ tập trung.

---

## Hướng dẫn Sử dụng CLI (`mekong veterinary`)

```bash
# Xem báo cáo tổng quan telemetry dịch tễ thú y quốc gia
mekong veterinary

# Thẩm tra và cấp Giấy chứng nhận kiểm dịch vận chuyển động vật
mekong veterinary quarantine "LỢN THỊT" --qty 500 --origin "Đồng Nai" --dest "TP. Hồ Chí Minh" --safe-zone --tested --disinfected --sealed

# Công bố ổ dịch bệnh truyền nhiễm và kích hoạt dập dịch khẩn cấp
mekong veterinary outbreak "ASF" --species "LỢN" --location "Bắc Giang" --culled 150 --method "DEEP_BURIAL" --radius 3.5 --vaccine --post

# Kiểm soát giết mổ và cấp dấu vệ sinh thú y cho lô thịt
mekong veterinary slaughter "Lò mổ tập trung An Hạ" --species "LỢN" --batch 200 --ante --post --no-water

# Thẩm định nhà máy sản xuất thuốc thú y đạt chuẩn GMP-WHO
mekong veterinary medicine "Công ty Dược Thú Y Vemedim" --type "MANUFACTURE" --chief-vet --gmp --no-prohibited

# Tra cứu danh mục hồ sơ thú y
mekong veterinary list --category ALL --limit 50

# Xem trạng thái hệ thống dạng JSON
mekong veterinary status --json
```

---

## Native MCP Tools

Bộ công cụ MCP dịch tễ thú y và kiểm dịch động vật quốc gia (FastMCP & JSON-RPC 2.0 stdio):

- `mekong_veterinary_quarantine`: Thẩm định và cấp Giấy chứng nhận kiểm dịch động vật vận chuyển (Điều 37-45).
- `mekong_veterinary_outbreak`: Ghi nhận ổ dịch truyền nhiễm, giám sát tiêu hủy và kích hoạt biện pháp khẩn cấp (Điều 15-26).
- `mekong_veterinary_slaughter`: Kiểm soát giết mổ tại lò mổ tập trung và cấp dấu vệ sinh thú y (Điều 64-70).
- `mekong_veterinary_medicine`: Thẩm định điều kiện cấp phép cơ sở sản xuất thuốc thú y GMP (Điều 77-107).
- `mekong_veterinary_list`: Tra cứu giấy kiểm dịch, ổ dịch, biên bản giết mổ và cơ sở dược thú y.
- `mekong_veterinary_status`: Truy xuất dữ liệu telemetry dịch tễ thú y và an toàn thực phẩm thịt sạch.

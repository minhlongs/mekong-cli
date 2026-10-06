---
name: customs
description: >-
  Customs — Vietnamese customs clearance, VNACCS channeling, HS code tariffs & Rules of Origin
---

# /customs — Customs — Vietnamese customs clearance, VNACCS channeling, HS code tariffs & Rules of Origin

Customs — Vietnamese customs clearance, VNACCS channeling, HS code tariffs & Rules of Origin.

## Usage

```bash
// turbo
mekong customs $ARGUMENTS
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `hs-lookup` | Tra cứu mã số HS, mô tả hàng hóa, thuế suất MFN và ưu đãi FTA theo Thông tư 31/2022/TT-BTC. |
| `duty-calc` | Tính toán chi tiết trị giá tính thuế CIF, thuế nhập khẩu và thuế GTGT hàng nhập khẩu. |
| `channel` | Đánh giá tiêu chí quản lý rủi ro và xác định phân luồng hải quan VNACCS (Xanh / Vàng / Đỏ). |
| `declare` | Thiết lập và đăng ký tờ khai hải quan điện tử chính thức trên hệ thống VNACCS/VCIS. |
| `origin` | Thẩm định tiêu chí xuất xứ hàng hóa (RVC >= 40%) và cấp giấy chứng nhận C/O ưu đãi. |
| `list` | Truy vấn danh mục tờ khai hải quan đã đăng ký trên hệ thống. |
| `status` | Tra cứu trạng thái cơ sở dữ liệu hải quan và phân bổ luồng VNACCS. |

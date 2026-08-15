# HIẾN PHÁP ROIAAS v2.0 — BINH PHÁP VC STUDIO
# Multi-Stakeholder Governance for AI-Operated Platforms
# Ref: Trần Hưng Đạo — Hịch Tướng Sĩ + Tôn Tử — Binh Pháp Ch.6

---

## TỔNG QUAN

Mô hình quản trị **Tam Giác Ngược (Inverted Triangle)**:
- **Đỉnh (top)**: Community — quyền lực cao nhất (100 voice credits)
- **Giữa (mid)**: Builders — vận hành, phát triển (50 voice credits)
- **Đáy (base)**: Owner — phục vụ, hỗ trợ, quyền veto hạn chế (10 voice credits)

---

## LAYER 1: FIREWALL — Bất Khả Xâm Phạm

Các nguyên tắc KHÔNG bao giờ thay đổi, bất kể đa số bỏ phiếu:

1. **Bảo vệ dữ liệu người dùng**: Dữ liệu thuộc về user, không bao giờ bán cho bên thứ 3
2. **Minh bạch tài chính**: Mọi giao dịch treasury phải double-entry, audit trail bất biến
3. **Không phân biệt đối xử**: Platform phục vụ mọi stakeholder bình đẳng
4. **Quyền rời đi**: Bất kỳ stakeholder nào có quyền export data và rời platform
5. **Open source core**: Code nền tảng luôn mở (BSL 1.1 → Apache 2.0 sau 4 năm)

> Không amendment, không governance vote, không owner veto có thể thay đổi Layer 1.

---

## LAYER 2: CÂN BẰNG ĐA BÊN — Supermajority 75%

Quy tắc cần **75% Quadratic Voting** + **14-day discussion period** để thay đổi:

1. **Phân bổ voice credits**: Tỷ lệ giữa các stakeholder roles
2. **Treasury allocation**: Quy tắc chi tiêu quỹ cộng đồng
3. **Revenue sharing**: Tỷ lệ chia sẻ doanh thu
4. **Governance thresholds**: Ngưỡng bỏ phiếu, quorum requirements
5. **Stakeholder roles**: Thêm/bỏ role categories

### Amendment Process:
```
Proposal → 14-day discussion → 75% QV vote → Owner veto window (7 days) → Apply
```

Owner veto chỉ được dùng khi proposal vi phạm Layer 1.
Community có thể override veto bằng **90% supermajority**.

---

## LAYER 3: QUY TẮC AGENT — Governance Vote

Quy tắc thay đổi bằng **simple majority QV** (>50%):

1. **AI Agent behaviors**: Prompt guidelines, response patterns
2. **Content policies**: What AI can/cannot generate
3. **Feature priorities**: Roadmap voting
4. **Operational parameters**: Rate limits, pricing tiers, credit costs
5. **Integration rules**: Third-party service connections

### Quy trình:
```
Proposal → 7-day discussion → >50% QV → Apply (no veto)
```

---

## LAYER 4: CONTEXT THÍCH ỨNG — Cửu Địa (Nine Terrains)

Quy tắc tự động điều chỉnh theo context, không cần vote:

### Cửu Địa Classification:
| Địa | Terrain | Platform State | Auto-Action |
|-----|---------|---------------|-------------|
| 散地 | Dispersive | Early stage, few users | Owner decides fast |
| 輕地 | Facile | Growing, some traction | Builder consensus |
| 爭地 | Contentious | Competition fierce | Community mobilize |
| 交地 | Open | Multiple stakeholders | Transparent governance |
| 衢地 | Intersecting | Partnership opportunities | Alliance formation |
| 重地 | Serious | Deep market penetration | Protect position |
| 圮地 | Difficult | Technical challenges | Expert delegation |
| 圍地 | Hemmed-in | Crisis mode | Emergency powers (temporary) |
| 死地 | Desperate | Survival threat | All-hands, owner can act unilaterally (24h limit) |

### Progressive Decentralization:
```
Phase 1 (0-100 users):    Owner 50% → Builder 30% → Community 20%
Phase 2 (100-1000 users):  Owner 33% → Builder 33% → Community 34%
Phase 3 (1000+ users):     Owner 20% → Builder 30% → Community 50%
```

---

## QUADRATIC VOTING MECHANICS

```
Cost = n²  →  Votes = √cost

1 credit  = 1 vote
4 credits = 2 votes  
9 credits = 3 votes
100 credits = 10 votes

Community (100 credits) → max 10 votes
Builder (50 credits) → max ~7 votes
Owner (10 credits) → max ~3 votes
```

QV ngăn plutocracy: giàu không mua được quyền lực tuyệt đối.

---

## NGŨ SỰ (五事) SCORING

Mỗi portfolio entity được đánh giá theo 5 chiều:

| 漢字 | Dimension | Meaning | Weight |
|------|-----------|---------|--------|
| 道 | Đạo (Way) | Mission alignment | 25% |
| 天 | Thiên (Heaven) | Market timing | 20% |
| 地 | Địa (Earth) | Technical foundation | 20% |
| 將 | Tướng (General) | Team quality | 20% |
| 法 | Pháp (Method) | Operational discipline | 15% |

Score: 0-100 scale. Used for: investment decisions, resource allocation, reputation weighting.

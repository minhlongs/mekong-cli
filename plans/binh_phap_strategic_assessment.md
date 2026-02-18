# ⚔️ Binh Pháp - Strategic Assessment: 84tea Automated Missions

> **"Binh giả, quốc chi đại sự"** - Việc binh là việc lớn của quốc gia.

## 1. Mục tiêu (Objective)
Xử lý triệt để hàng đợi nhiệm vụ tự động (Automated Missions) đang tồn đọng trong thư mục `tasks/` cho dự án `84tea`.
Cụ thể gồm 3 items chính:
1. `mission_84tea_auto_knowledge_synthesis.txt`: Tổng hợp kiến thức.
2. `mission_84tea_auto_tech_debt.txt`: Xử lý nợ kỹ thuật (TODO/FIXME, dead code).
3. `mission_84tea_auto_agi_evolution.txt`: Nâng cấp khả năng AGI.

## 2. Tài nguyên (Resources)
- **Agent Teams**: Sẵn sàng kích hoạt 4 subagents song song (Architect, Researcher, Planner, Fullstack).
- **Quyền hạn**: `/cook` với flag `--auto` (cho phép tự động sửa file).
- **Hạ tầng**: `apps/84tea` (Next.js/React ecosystem).

## 3. Phân tích Rủi ro (Risk Analysis)
- **High Concurrency**: Chạy 3 mission cùng lúc dễ gây conflict file.
- **Context Drift**: Nếu không tổng hợp kiến thức trước, các mission sau có thể duplicate hoặc sai hướng.
- **Quota Impact**: Sử dụng nhiều token cho Agent Teams.

## 4. Chiến lược Thực thi (Strategy) - 第七篇 軍爭

Áp dụng chiến thuật "Tuần tự hoá Chiến lược" (Strategic Serialization):

### Giai đoạn 1: Củng cố (Knowledge Synthesis)
*Ưu tiên 1*. Chạy `mission_84tea_auto_knowledge_synthesis.txt`.
- **Mục đích**: Đảm bảo Brain (Knowledge Items) được cập nhật mới nhất từ các hoạt động gần đây.
- **Lợi ích**: Giúp phase Tech Debt và AGI Evolution chính xác hơn.

### Giai đoạn 2: Dọn dẹp (Tech Debt Liquidation)
*Ưu tiên 2*. Chạy `mission_84tea_auto_tech_debt.txt`.
- **Mục đích**: Loại bỏ rác (dead code, TODOs) TRƯỚC KHI xây dựng tính năng mới.
- **Lợi ích**: Giảm complexity, giảm bug khi implement AGI mới.

### Giai đoạn 3: Tiến hoá (AGI Evolution)
*Ưu tiên 3*. Chạy `mission_84tea_auto_agi_evolution.txt`.
- **Mục đích**: Implement logic tự hành mới.
- **An toàn**: Chỉ thực hiện trên nền tảng sạch (đã xong Tech Debt).

## 5. Kế hoạch Hành động (Action Plan)

1. **Verify**: Kiểm tra lại trạng thái `apps/84tea` (build/test hiện tại).
2. **Execute Phase 1**: `/cook tasks/mission_84tea_auto_knowledge_synthesis.txt`
3. **Execute Phase 2**: `/cook tasks/mission_84tea_auto_tech_debt.txt`
4. **Execute Phase 3**: `/cook tasks/mission_84tea_auto_agi_evolution.txt`

## 6. Yêu cầu Phê duyệt (Approval Request)
Người dùng vui lòng xác nhận để bắt đầu **Giai đoạn 1**.

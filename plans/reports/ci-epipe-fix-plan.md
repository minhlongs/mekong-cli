---
title: "Fix Vite Build EPIPE Error (OOM) trong TheBeeAgent.ts"
description: "Phân tích và khắc phục lỗi `write EPIPE` từ `esbuild` khi build ứng dụng, thường do tràn bộ nhớ (OOM) hoặc quá tải khi xử lý file `TheBeeAgent.ts`."
status: pending
priority: P1
effort: 30m
branch: master
tags: [ci, bugfix, vite, esbuild, oom]
created: 2026-02-27
---

# Lập Plan Fix Lỗi `EPIPE` trong Vite Build

## Phân tích Vấn đề (Analysis)

Dựa trên log build thất bại từ GitHub Actions:
```
vite v7.3.1 building client environment for production...
transforming...
✓ 2866 modules transformed.
✗ Build failed in 31.72s
error during build:
[vite:esbuild] The service was stopped: write EPIPE
file: /Users/macbookprom1/archive-2026/Well/src/agents/custom/TheBeeAgent.ts
```

**Nguyên nhân:**
1. Lỗi `write EPIPE` từ quá trình `esbuild` của Vite thường xảy ra khi Node.js cạn kiệt bộ nhớ (OOM - Out of Memory) và process con (`esbuild` worker) bị hệ điều hành tiêu diệt.
2. Tại thời điểm crash, `esbuild` đang cố gắng xử lý file `src/agents/custom/TheBeeAgent.ts`. File này tuy không quá dài (khoảng 160 dòng), nhưng nếu có chuỗi dependency phức tạp hoặc import vòng (circular dependency) có thể làm cạn kiệt memory.
3. Trong `vite.config.ts`, `chunkSizeWarningLimit` đã bị ép lên `1600`. Đồng thời file config đang dùng `manualChunks` rất phức tạp. Quá trình chia chunk này có thể đang gây vòng lặp xử lý hoặc memory leak trong `esbuild`/`rollup`.
4. Command build hiện tại đang dùng `NODE_OPTIONS=--max-old-space-size=4096 vite build`. Tuy nhiên, với các file typescript lớn (có import AgentBase từ `core`), việc compiler chạy quá sức là rất dễ xảy ra nếu Vite config không tối ưu.

## Các Phương Án Sửa Lỗi (Approaches)

### Approach 1: Tối ưu cấu trúc Import/Export và `vite.config.ts` (Khuyên dùng)
**Pros:**
- Giải quyết tận gốc lý do OOM do cây phụ thuộc rườm rà.
- Không tăng thêm dung lượng bộ nhớ.
- Ít rủi ro side-effect hơn.

**Cons:**
- Phải can thiệp vào cách tổ chức chunking trong Vite.

**Chi tiết:**
1. **Kiểm tra file `src/agents/index.ts`**: Hiện tại file này đang export toàn bộ các Agent (`export { TheBeeAgent } from './custom/TheBeeAgent'`). Việc export dồn (barrel file) dễ gây ra OOM khi Vite thực hiện Tree-shaking. Hãy tránh import các Agent thông qua file index trong nội bộ logic, thay vào đó import trực tiếp từ file (`import { BaseAgent } from '../core/BaseAgent'`).
2. **Sửa `vite.config.ts`**: Lược bỏ bớt logic phức tạp trong `manualChunks`. Hàm đệ quy hoặc so sánh string quá nhiều trong `manualChunks` có thể là nguyên nhân khiến Vite/esbuild bị quá tải bộ nhớ.
3. **Sửa `TheBeeAgent.ts`**: Hiện tại không có vấn đề lớn về code logic, ngoại trừ việc import enum `UserRank` và `BaseAgent`. Nếu `BaseAgent` import vòng, nó sẽ gây EPIPE.

### Approach 2: Nâng `max-old-space-size` lên mức cao hơn
**Pros:**
- Nhanh chóng, sửa 1 dòng là xong (trong `package.json`).
- Không ảnh hưởng đến logic code của dự án.

**Cons:**
- Chỉ là cách "chữa cháy", không giải quyết tận gốc nguyên nhân tràn bộ nhớ.
- CI runner có thể bị giới hạn RAM vật lý (thường là 7GB đối với GitHub Actions standard). Nếu ép lên 8GB (`8192`) thì có thể runner sẽ crash hẳn thay vì báo lỗi EPIPE.

**Chi tiết:**
Đổi lệnh build trong `package.json`:
`"build": "NODE_OPTIONS=--max-old-space-size=6144 tsc && NODE_OPTIONS=--max-old-space-size=6144 vite build"`

---

## Giải pháp đề xuất (Recommendation)

Chọn **Approach 1** để giải quyết tận gốc.

### Các Bước Thực Hiện Cụ Thể (Implementation Steps)

**Bước 1: Tối giản Vite Chunking (`vite.config.ts`)**
- Hiện tại `manualChunks` đang có chuỗi `if-else` rất dài. Sẽ giữ lại các chunk quan trọng (`react-vendor`, `supabase`, `pdf`), nhưng nên bỏ qua các điều kiện nhỏ lẻ không cần thiết để giảm tải quá trình build tree-shaking của `esbuild` / `rollup`.

**Bước 2: Xử lý import của TheBeeAgent.ts và BaseAgent.ts**
- Kiểm tra xem file `BaseAgent.ts` có import vòng (circular dependency) nào liên quan đến `agentLogger` từ `src/utils/logger.ts` không.
- Thêm `type` vào các import interface để `tsc` và `esbuild` tự động loại bỏ chúng nhanh hơn:
  ```typescript
  import type { AgentDefinition } from '@/types/agentic';
  import { UserRank } from '@/types';
  ```

**Bước 3: Bổ sung cấu hình Worker cho esbuild (trong `vite.config.ts`)**
- Nếu lỗi nằm hoàn toàn ở esbuild bị chết worker, ta có thể giới hạn `esbuild` không ăn quá nhiều worker cùng lúc:
  ```javascript
  esbuild: {
    target: 'es2020',
    // ...
  },
  ```

**Chỉ Sửa Tối Đa < 5 File:**
1. `vite.config.ts`
2. `src/agents/custom/TheBeeAgent.ts`
3. `package.json` (tăng size nhẹ lên `6144` làm backup safety net)

### Success Criteria
- Lệnh `npm run build` vượt qua thành công, không bị OOM, không bị EPIPE.
- Không phá vỡ chức năng của `TheBeeAgent`.
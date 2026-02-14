# 📜 BINH PHÁP TÔN TỬ — KINH THƯ ĐẠI TOÀN

# 孫子兵法 — Complete Master Reference

> **"Binh giả, quốc chi đại sự, tử sinh chi địa, tồn vong chi đạo, bất khả bất sát dã"**
> Chiến tranh là đại sự của quốc gia, là nơi sống chết, là đường tồn vong, không thể không xét kỹ.
>
> — Tôn Vũ (孫武), ~512 TCN, Thời Xuân Thu
> Ánh xạ cho Doanh Trại Tôm Hùm (OpenClaw Swarm) | v1.0.0 | 2026-02-11

---

## MỤC LỤC

1. [Thập Tam Thiên (13 Chương)](#thập-tam-thiên---13-chương)
2. [Ngũ Sự (5 Yếu Tố Cốt Lõi)](#ngũ-sự---五事---5-yếu-tố-cốt-lõi)
3. [Thất Kế (7 Phép Tính Toán)](#thất-kế---七計---7-phép-tính-toán)
4. [Ngũ Đức Tướng (5 Đức Tính Tướng Lĩnh)](#ngũ-đức-tướng---5-đức-tính-tướng-lĩnh)
5. [Ngũ Nguy (5 Mối Nguy Của Tướng)](#ngũ-nguy---五危---5-mối-nguy-của-tướng)
6. [Cửu Địa (9 Loại Địa Thế)](#cửu-địa---九地---9-loại-địa-thế)
7. [Lục Địa Hình (6 Loại Địa Hình)](#lục-địa-hình---六地形---6-loại-địa-hình)
8. [Ngũ Hỏa (5 Phương Pháp Hỏa Công)](#ngũ-hỏa---五火---5-phương-pháp-hỏa-công)
9. [Ngũ Gián (5 Loại Gián Điệp)](#ngũ-gián---五間---5-loại-gián-điệp)
10. [Tam Thập Lục Kế (36 Kế)](#tam-thập-lục-kế---三十六計---36-kế)
11. [Bát Quái Chiến Thuật (8 Nguyên Tắc Bất Biến)](#bát-quái-chiến-thuật---8-nguyên-tắc-bất-biến)
12. [Kim Ngôn Binh Pháp (Danh Ngôn Bất Hủ)](#kim-ngôn-binh-pháp---danh-ngôn-bất-hủ)

---

## THẬP TAM THIÊN — 13 CHƯƠNG

### 第一篇 始計 (Shi Ji) — KẾ SÁCH / Laying Plans

> **"Binh giả, quốc chi đại sự"** — Chiến tranh là đại sự quốc gia

**Nội dung gốc:** Đánh giá chiến lược tổng thể trước khi hành động. Bao gồm Ngũ Sự (5 yếu tố) và Thất Kế (7 phép so sánh).

**Ánh xạ Agent:** Mọi mission PHẢI qua đánh giá trước khi dispatch. `auto-cto-pilot.js` + `mission-complexity-classifier.js` thực hiện 始計.

**Nguyên văn then chốt:**

- 兵者，詭道也 — Binh là đạo lừa dối (deception)
- 多算勝，少算不勝 — Tính nhiều thì thắng, tính ít thì thua

---

### 第二篇 作戰 (Zuo Zhan) — TÁC CHIẾN / Waging War

> **"Binh quý thắng, bất quý cửu"** — Quân quý ở thắng nhanh, không quý ở kéo dài

**Nội dung gốc:** Chi phí chiến tranh, hậu cần, tốc độ là yếu tố quyết định. Kéo dài = kiệt quệ.

**Ánh xạ Agent:** Token budget, mission timeout, M1 cooling. `quota-tracker.js` + `m1-cooling-daemon.js` là TÁC CHIẾN.

**Nguyên văn then chốt:**

- 日費千金 — Mỗi ngày tốn ngàn vàng (token budget!)
- 取用於敵 — Lấy nguồn lực từ giặc (free models: Flash, Kimi)
- 因糧於敵 — Dùng lương thảo của giặc (proxy free APIs)

---

### 第三篇 謀攻 (Mou Gong) — MƯU CÔNG / Attack by Stratagem

> **"Thượng binh phạt mưu"** — Thượng sách là dùng mưu

**Nội dung gốc:** Thắng không cần đánh. Dùng mưu trí, ngoại giao, chia rẽ kẻ thù.

**Ánh xạ Agent:** `/plan:hard` trước `/cook`. Architect daemon (Cloud Brain) phân tích trước khi Builder (Worker) hành động.

**Nguyên văn then chốt:**

- 不戰而屈人之兵 — Thắng mà không cần chiến đấu (fix config → fix everything)
- 知己知彼，百戰不殆 — Biết mình biết người, trăm trận không nguy
- 上兵伐謀，其次伐交，其次伐兵，其下攻城 — Thượng sách phạt mưu, thứ nhì ngoại giao, thứ ba đánh quân, hạ sách công thành

---

### 第四篇 軍形 (Jun Xing) — QUÂN HÌNH / Tactical Dispositions

> **"Tiên vi bất khả thắng, dĩ đãi địch chi khả thắng"** — Trước làm cho mình bất khả chiến bại, rồi đợi địch lộ sơ hở

**Nội dung gốc:** Phòng thủ và tấn công. Phòng thủ khi chưa có cơ hội, tấn công khi thời cơ đến.

**Ánh xạ Agent:** `post-mission-gate.js` — **軍形 CI/CD Gate**: sau mỗi mission → `npm run build` → nếu GREEN → `git commit + push`. Nếu RED → BLOCK push, log failure. Security hardening (Operator/Reviewer) trước khi push features (Builder). Health checks trước missions.

```
Mission Complete → runFullGate(project, missionId)
                → runBuildGate() → npm run build → GREEN/RED
                → pushIfGreen() → git add → commit → push origin master
                → saveGateResult() → .gate-results.json (last 100)
```

**Nguyên văn then chốt:**

- 善守者藏於九地之下 — Phòng thủ giỏi: ẩn sâu chín tầng đất
- 善攻者動於九天之上 — Tấn công giỏi: bay trên chín tầng trời

---

### 第五篇 兵勢 (Bing Shi) — BINH THẾ / Energy

> **"Thế như hoãn huyệt, tiết như phát cơ"** — Thế như nỏ căng, tiết như mũi tên bắn

**Nội dung gốc:** Tạo thế, tích lũy năng lượng rồi phóng ra đúng lúc. Chính và Kỳ (orthodox & unorthodox).

**Ánh xạ Agent:** Queue buffering (Dispatcher tích kế), Stream execution (Serveo Tunnel). Agent Teams = KỲ. Cloud Brain = CHÍNH.

**Nguyên văn then chốt:**

- 凡戰者，以正合，以奇勝 — Đánh nhau: dùng CHÍNH giao chiến, dùng KỲ để thắng
- 奇正相生 — Chính và Kỳ sinh ra lẫn nhau (Brain + Workers)

---

### 第六篇 虛實 (Xu Shi) — HƯ THỰC / Weak & Strong Points

> **"Tỵ thực nhi kích hư"** — Tránh chỗ mạnh, đánh chỗ yếu

**Nội dung gốc:** Tìm điểm yếu, tập trung lực lượng. Chủ động, không bị động.

**Ánh xạ Agent:** Hunter scanner tìm hư. **OpenAI Scaling:** Brain (Primary/Thực) chỉ Ghi, Workers (Replica/Hư) chỉ Đọc.

**Nguyên văn then chốt:**

- 善攻者，敵不知其所守 — Tấn công giỏi: địch không biết phòng đâu
- 兵無常勢，水無常形 — Quân không có thế cố định, nước không có hình cố định

---

### 第七篇 軍爭 (Jun Zheng) — QUÂN TRANH / Maneuvering

> **"以迂為直"** — Lấy đường vòng làm đường thẳng

**Nội dung gốc:** Hành quân, tranh giành lợi thế, tốc độ triển khai.

**Ánh xạ Agent:** `mission-dispatcher.js` routing, Serveo Tunnel streaming (Zero Latency), `/cook --auto` speed.

**Nguyên văn then chốt:**

- 風林火山 — Nhanh như GIÓ, lặng như RỪNG, mạnh như LỬA, vững như NÚI
- 懸權而動 — Cân nhắc rồi mới hành động

---

### 第八篇 九變 (Jiu Bian) — CỬU BIẾN / Variation in Tactics

> **"Tướng thông cửu biến chi lợi"** — Tướng nào thông 9 biến mới biết dùng binh

**Nội dung gốc:** 9 tình huống thay đổi. Linh hoạt, không cứng nhắc. Ngũ Nguy (5 tính xấu của tướng).

**Ánh xạ Agent:** Cloud Fallback (Brain ↔ Local), mission recovery, auto-restart. `mission-recovery.js`.

**Nguyên văn then chốt:**

- 有所不爭 — Có chỗ không nên tranh (skip low-priority missions)
- 有所不取 — Có thành không nên lấy (don't fix everything)

---

### 第九篇 行軍 (Xing Jun) — HÀNH QUÂN / The Army on the March

> **"Tướng tốt phải biết đọc địa hình và trinh sát"**

**Nội dung gốc:** Cách đọc dấu hiệu chiến trường, bố trí doanh trại, quan sát kẻ thù.

**Ánh xạ Agent:** `post-mission-gate.js` — `runBuildGate()` lint/typecheck verification (đọc dấu hiệu build). Log analysis (Scribe), health monitoring (Operator), pattern detection (Hunter scanner regex).

**Nguyên văn then chốt:**

- 近而靜者，恃其險也 — Gần mà im lặng: dựa vào địa hình hiểm (hidden bugs)
- 辭卑而益備者，進也 — Lời nhũn mà tăng phòng bị: sắp tấn công

---

### 第十篇 地形 (Di Xing) — ĐỊA HÌNH / Terrain

> **"Địa hình là trợ thủ của binh gia"**

**Nội dung gốc:** 6 loại địa hình (Lục Địa Hình). Cách xử lý từng loại terrain.

**Ánh xạ Agent:** Project types (monorepo, microservice, SPA) → mỗi loại cần approach khác nhau. `detectProjectDir()`.

---

### 第十一篇 九地 (Jiu Di) — CỬU ĐỊA / Nine Situations

> **"Tứ địa tắc hợp"** — Trên đất giao thông → liên minh

**Nội dung gốc:** 9 loại địa thế chiến lược. Từ Tản Địa (nhà mình) đến Tử Địa (không lùi được).

**Ánh xạ Agent:** Mission stages: safe (dev/staging) → serious (production) → desperate (hotfix/rollback).

---

### 第十二篇 火攻 (Huo Gong) — HỎA CÔNG / Attack by Fire

> **"Phát hỏa hữu thời"** — Đốt phải đúng lúc

**Nội dung gốc:** 5 phương pháp hỏa công. Thời điểm, điều kiện, hậu quả. Cảnh báo về chiến tranh phá hủy.

**Ánh xạ Agent:** `post-mission-gate.js` — `pushIfGreen()`: chỉ push khi build GREEN (Phát hỏa hữu thời). `task-queue.js` line 40-56: 軍形 gate blocks RED builds from reaching production.

**Nguyên văn then chốt:**

- 主不可以怒而興師 — Vua không nên vì giận mà động binh (don't hotfix vì panic)
- 亡國不可以復存 — Nước mất không phục hồi được (data loss is permanent)

---

### 第十三篇 用間 (Yong Jian) — DỤNG GIÁN / Use of Spies

> **"Minh quân hiền tướng chi sở dĩ động nhi thắng nhân"** — Vua sáng tướng giỏi luôn thắng nhờ tình báo

**Nội dung gốc:** 5 loại gián điệp (Ngũ Gián). Chi phí tình báo vs chi phí chiến tranh. Tình báo là yếu tố quyết định.

**Ánh xạ Agent:** Hunter = trinh sát, Sage = phân tích intel, Scribe = ghi chép, knowledge/ = intelligence archive.

---

## NGŨ SỰ — 五事 — 5 Yếu Tố Cốt Lõi

> Từ Chương 1 (始計). 5 yếu tố NỀN TẢNG quyết định thắng bại.

| #   | Yếu Tố    | Hán Tự | Ý Nghĩa Gốc                                    | Ánh Xạ Agent                                                                      |
| :-- | :-------- | :----- | :--------------------------------------------- | :-------------------------------------------------------------------------------- |
| 1   | **ĐẠO**   | 道     | Đồng lòng vua-dân, người trên kẻ dưới nhất trí | **Culture**: Constitution 53 Điều, Quân Luật 9 Điều — mọi agent cùng tuân thủ     |
| 2   | **THIÊN** | 天     | Thiên thời: ngày đêm, nóng lạnh, mùa           | **Timing**: M1 cooling cycle, deploy windows, cron schedules, market timing       |
| 3   | **ĐỊA**   | 地     | Địa lợi: xa gần, hiểm yếu, rộng hẹp            | **Environment**: dev/staging/prod, monorepo vs microservice, project complexity   |
| 4   | **TƯỚNG** | 將     | Tướng lĩnh: trí-tín-nhân-dũng-nghiêm           | **Leadership**: Antigravity (Chủ Soái), CC CLI (Tướng), Brain-Tmux (Quân Sư)      |
| 5   | **PHÁP**  | 法     | Pháp chế: tổ chức, biên chế, hậu cần           | **System**: config.js, ecosystem.config.js, DOANH_TRAI.md, PM2 process management |

---

## THẤT KẾ — 七計 — 7 Phép Tính Toán

> Từ Chương 1 (始計). 7 câu hỏi SO SÁNH ta-địch trước mỗi trận.

| #   | Hán Văn  | Phiên Âm              | Câu Hỏi                             | Ánh Xạ Agent                                   |
| :-- | :------- | :-------------------- | :---------------------------------- | :--------------------------------------------- |
| 1   | 主孰有道 | Chủ thục hữu đạo      | Bên nào có ĐẠO (được lòng dân) hơn? | Code quality: project nào có culture tốt hơn?  |
| 2   | 將孰有能 | Tướng thục hữu năng   | Tướng bên nào TÀI NĂNG hơn?         | Model: Sonnet vs Opus, complexity match        |
| 3   | 天地孰得 | Thiên địa thục đắc    | Bên nào chiếm THIÊN-ĐỊA lợi?        | Env readiness: staging sẵn? CI green?          |
| 4   | 法令孰行 | Pháp lệnh thục hành   | Kỷ luật bên nào NGHIÊM hơn?         | Lint rules, type safety, test coverage         |
| 5   | 兵眾孰強 | Binh chúng thục cường | Quân bên nào MẠNH hơn?              | Resources: RAM, CPU, pane count, API quota     |
| 6   | 士卒孰練 | Sĩ tốt thục luyện     | Binh sĩ bên nào LUYỆN TẬP hơn?      | Agent skills, prompt quality, retry logic      |
| 7   | 賞罰孰明 | Thưởng phạt thục minh | Thưởng phạt bên nào RÕ RÀNG hơn?    | Signal protocol, mission success/fail tracking |

**Ứng dụng:** Trước mỗi complex mission, `mission-complexity-classifier.js` PHẢI đánh giá 7 yếu tố này.

---

## NGŨ ĐỨC TƯỚNG — 5 Đức Tính Tướng Lĩnh

> Từ Chương 1 (始計). 5 phẩm chất bắt buộc của người chỉ huy.

| #   | Đức        | Hán | Ý Nghĩa              | Ánh Xạ Agent                                               |
| :-- | :--------- | :-- | :------------------- | :--------------------------------------------------------- |
| 1   | **TRÍ**    | 智  | Trí tuệ, sáng suốt   | Model intelligence: chọn đúng model cho đúng task          |
| 2   | **TÍN**    | 信  | Uy tín, giữ lời      | Reliability: mission completion rate, uptime               |
| 3   | **NHÂN**   | 仁  | Nhân ái, thương quân | Resource care: cooling, quota management, không burn token |
| 4   | **DŨNG**   | 勇  | Can đảm, quyết đoán  | Decisive action: auto-deploy, hotfix without fear          |
| 5   | **NGHIÊM** | 嚴  | Nghiêm minh, kỷ luật | Enforcement: lint, type-check, test mandatory              |

---

## NGŨ NGUY — 五危 — 5 Mối Nguy Của Tướng

> Từ Chương 8 (九變). 5 tính cách NGỖ NGƯỢC khiến tướng bại trận.

| #   | Nguy           | Hán  | Hậu Quả                         | Ánh Xạ Agent (Anti-Pattern)                   |
| :-- | :------------- | :--- | :------------------------------ | :-------------------------------------------- |
| 1   | **Tất tử**     | 必死 | Hiếu chiến khinh suất → BỊ GIẾT | Deploy without testing → production crash     |
| 2   | **Tất sinh**   | 必生 | Tham sống sợ chết → BỊ BẮT      | Never deploy, infinite planning → miss market |
| 3   | **Phẫn tốc**   | 忿速 | Nóng nảy dễ giận → BỊ NHỤC      | Hotfix vì panic → introduce more bugs         |
| 4   | **Liêm khiết** | 廉潔 | Quá trọng danh dự → BỊ NHỤC     | Over-engineer vì perfectionism → ship nothing |
| 5   | **Ái dân**     | 愛民 | Quá nhân từ → BỊ PHIỀN          | Never delete old code → tech debt mountain    |

---

## CỬU ĐỊA — 九地 — 9 Loại Địa Thế

> Từ Chương 11 (九地). 9 tình huống chiến lược dựa trên vị trí quân.

| #   | Địa           | Hán  | Đặc Điểm                        | Chiến Thuật   | Ánh Xạ Agent                             |
| :-- | :------------ | :--- | :------------------------------ | :------------ | :--------------------------------------- |
| 1   | **Tản Địa**   | 散地 | Đánh trên đất mình, quân dễ tản | Không đánh    | Local dev — don't break main             |
| 2   | **Khinh Địa** | 輕地 | Vào đất địch chưa sâu           | Không dừng    | Feature branch — keep moving             |
| 3   | **Tranh Địa** | 爭地 | Ai chiếm trước có lợi           | Chiếm nhanh   | Staging deploy — first to test wins      |
| 4   | **Giao Địa**  | 交地 | Đường đi lại dễ                 | Giữ liên lạc  | API contracts — maintain compatibility   |
| 5   | **Cù Địa**    | 衢地 | Ngã tư, many allies possible    | Kết đồng minh | Multi-platform — integrate partners      |
| 6   | **Trọng Địa** | 重地 | Sâu trong đất địch              | Cướp lương    | Production deep — use prod data wisely   |
| 7   | **Phí Địa**   | 圮地 | Rừng núi, đầm lầy               | Đi nhanh qua  | Legacy code — migrate fast, don't linger |
| 8   | **Vi Địa**    | 圍地 | Bị vây, đường hẹp               | Dùng mưu      | Deadline crunch — be creative, cut scope |
| 9   | **Tử Địa**    | 死地 | Không lùi được                  | Quyết chiến   | Production down — ALL HANDS, deploy NOW  |

---

## LỤC ĐỊA HÌNH — 六地形 — 6 Loại Địa Hình

> Từ Chương 10 (地形). 6 loại terrain cụ thể.

| #   | Hình      | Hán | Đặc Điểm                  | Ánh Xạ Agent                          |
| :-- | :-------- | :-- | :------------------------ | :------------------------------------ |
| 1   | **Thông** | 通  | Dễ đi lại                 | Simple CRUD apps — deploy easily      |
| 2   | **Quải**  | 掛  | Dễ tiến, khó lui          | Migration — once started, can't undo  |
| 3   | **Chi**   | 支  | Hai bên ra đều bất lợi    | Refactor standoff — plan carefully    |
| 4   | **Ải**    | 隘  | Hẹp, ai chiếm trước thắng | Niche market — first mover advantage  |
| 5   | **Hiểm**  | 險  | Cao, hiểm trở             | Complex architecture — need expert    |
| 6   | **Viễn**  | 遠  | Xa, khó tiếp tế           | Remote deployment — VPS, edge workers |

---

## NGŨ HỎA — 五火 — 5 Phương Pháp Hỏa Công

> Từ Chương 12 (火攻). 5 mục tiêu khi dùng hỏa lực.

| #   | Hỏa          | Hán  | Mục Tiêu             | Ánh Xạ Agent                                     |
| :-- | :----------- | :--- | :------------------- | :----------------------------------------------- |
| 1   | **Hỏa Nhân** | 火人 | Đốt quân (người)     | Fix team bottleneck — retrain/replace weak agent |
| 2   | **Hỏa Tích** | 火積 | Đốt kho lương        | Clean node_modules, purge cache, free disk       |
| 3   | **Hỏa Tốt**  | 火輜 | Đốt xe lương         | Kill zombie processes, clear stale queues        |
| 4   | **Hỏa Khố**  | 火庫 | Đốt kho vũ khí       | Rotate API keys, invalidate tokens               |
| 5   | **Hỏa Đội**  | 火隊 | Đốt đường vận chuyển | Break dependency chain, isolate services         |

---

## NGŨ GIÁN — 五間 — 5 Loại Gián Điệp

> Từ Chương 13 (用間). 5 loại spy khác nhau.

| #   | Gián           | Hán  | Vai Trò             | Ánh Xạ Agent                                        |
| :-- | :------------- | :--- | :------------------ | :-------------------------------------------------- |
| 1   | **Hương Gián** | 鄉間 | Dùng dân bản địa    | **User feedback** — beta testers từ community       |
| 2   | **Nội Gián**   | 內間 | Dùng quan lại địch  | **Monitoring hooks** — Sentry/LogRocket inside apps |
| 3   | **Phản Gián**  | 反間 | Gián điệp nhị trùng | **Sage daemon** — monitor your own monitors         |
| 4   | **Tử Gián**    | 死間 | Gián điệp hy sinh   | **Canary deploy** — sacrifice to detect issues      |
| 5   | **Sinh Gián**  | 生間 | Gián điệp sống sót  | **Hunter daemon** — scan, report, survive           |

---

## PHONG LÂM HỎA SƠN — 風林火山 — 4 Trạng Thái Chiến Đấu

> Từ Chương 7 (軍爭). Takeda Shingen's famous banner.

| Trạng Thái           | Hán      | Ý Nghĩa              | Ánh Xạ Agent                                 |
| :------------------- | :------- | :------------------- | :------------------------------------------- |
| 🌪️ **Nhanh như GIÓ** | 疾如風   | Tốc chiến tốc thắng  | Simple missions: `/cook --auto` < 5min       |
| 🌲 **Lặng như RỪNG** | 徐如林   | Im lặng, kỷ luật     | Queue idle: daemons scan quietly, no noise   |
| 🔥 **Mạnh như LỬA**  | 侵掠如火 | Tàn phá, không ngừng | Complex missions: Agent Teams parallel burst |
| ⛰️ **Vững như NÚI**  | 不動如山 | Bất động, kiên cố    | Health check: Operator daemon stands firm    |

---

## TAM THẬP LỤC KẾ — 三十六計 — 36 Kế

> **Lưu ý:** 36 Kế KHÔNG phải tác phẩm của Tôn Tử. Xuất hiện thời Nam Bắc triều (~5th century), tập hợp thời Minh.
> Nhưng được coi là phần mở rộng tất yếu của Binh Pháp.

_(Chi tiết đầy đủ tại file `36_KE.md`)_

| Nhóm                           | Kế                                                              | Tình Huống         |
| :----------------------------- | :-------------------------------------------------------------- | :----------------- |
| **I. Thắng Chiến Kế** (1-6)    | Man thiên, Vây Ngụy, Tá đao, Dĩ dật, Sấn hỏa, Dương đông        | Đang thắng thế     |
| **II. Địch Chiến Kế** (7-12)   | Vô trung, Ám độ, Cách ngạn, Tiếu lý, Lý đại, Thuận thủ          | Đối phó kẻ thù     |
| **III. Công Chiến Kế** (13-18) | Đả thảo, Tá thi, Điệu hổ, Dục cầm, Phao chuyên, Cầm tặc         | Chủ động tấn công  |
| **IV. Hỗn Chiến Kế** (19-24)   | Phủ để, Hỗn thủy, Kim thiền, Quan môn, Viễn giao, Giả đạo       | Tình hình hỗn loạn |
| **V. Tịnh Chiến Kế** (25-30)   | Thâu lương, Chỉ tang, Giả si, Thượng ốc, Thụ thượng, Phản khách | Đối đầu trực tiếp  |
| **VI. Bại Chiến Kế** (31-36)   | Mỹ nhân, Không thành, Phản gián, Khổ nhục, Liên hoàn, Tẩu vi    | Thế bất lợi        |

---

## BÁT QUÁI CHIẾN THUẬT — 8 Nguyên Tắc Bất Biến

> Tổng hợp từ toàn bộ 13 Chương — 8 nguyên tắc KHÔNG BAO GIỜ thay đổi.

| #   | Nguyên Tắc                  | Nguồn | Ánh Xạ Agent                             |
| :-- | :-------------------------- | :---- | :--------------------------------------- |
| 1   | **Biết mình biết người**    | Ch.3  | Research codebase TRƯỚC KHI implement    |
| 2   | **Thắng không cần đánh**    | Ch.3  | Fix config > fix code. Prevention > cure |
| 3   | **Nhanh, không kéo dài**    | Ch.2  | Mission timeout, no infinite loops       |
| 4   | **Tránh mạnh đánh yếu**     | Ch.6  | Fix easy bugs first, build momentum      |
| 5   | **Linh hoạt thay đổi**      | Ch.8  | Model fallback, mode switching           |
| 6   | **Gián điệp là quyết định** | Ch.13 | Scanning > guessing. Data > intuition    |
| 7   | **Phong Lâm Hỏa Sơn**       | Ch.7  | Nhanh-Lặng-Mạnh-Vững                     |
| 8   | **Quân tướng đồng lòng**    | Ch.1  | Constitution + Quân Luật = alignment     |

---

## KIM NGÔN BINH PHÁP — Danh Ngôn Bất Hủ

**Chiến lược:**

- 知己知彼，百戰不殆 — Biết mình biết người, trăm trận không nguy
- 不戰而屈人之兵，善之善者也 — Thắng mà không chiến, giỏi nhất trong giỏi
- 上兵伐謀 — Thượng sách là phạt mưu

**Tốc độ:**

- 兵貴勝，不貴久 — Quân quý thắng, không quý lâu
- 兵之情主速 — Tình thế quân sự, chủ ở tốc độ

**Linh hoạt:**

- 兵無常勢，水無常形 — Quân không có thế cố định, nước không có hình cố định
- 能因敵變化而取勝者，謂之神 — Biến hóa theo địch mà thắng: gọi là THẦN

**Lãnh đạo:**

- 將者，國之輔也 — Tướng là người phụ trợ quốc gia
- 視卒如嬰兒 — Coi quân như con nhỏ (care for your agents)
- 令之以文，齊之以武 — Dùng VĂN để lãnh đạo, dùng VÕ để kỷ luật

**Phòng thủ:**

- 善戰者，先為不可勝 — Giỏi đánh: trước tiên làm cho mình bất khả bại
- 昔之善戰者，先為不可勝，以待敵之可勝 — Trước phòng thủ hoàn hảo, rồi đợi sơ hở

---

## TÔM HÙM AGI EVOLUTION — 2026 DOCTRINE

> **Silicon Valley Intelligence × Binh Phap Strategy**
> *Synthesized from a16z, Sequoia, and the AgencyOS "Tôm Hùm" Architecture.*

### I. The Strategic Thesis (Service-as-a-Work)
The world is moving from **SaaS** to **SaaW (Service as a Work)**.
-   **Old Way:** Selling tools for humans.
-   **New Way (AGI):** Selling Agents that *do* the work.

### II. The Technical Stack (a16z "AI Agent Architecture")
1.  **The Brain (Cloud Intelligence Node):** Colab T4 + Ollama (**Qwen3-Coder-Next**). 3B Active / 80B MoE.
2.  **The Body (Tools & Action):** Model Context Protocol (MCP) via Mekong CLI.
3.  **The Memory (RAG + Event Logs):** Vector Database + `wins.jsonl`.

### III. The "Flywheel" of Evolution (Self-Improvement)
1.  **Execute:** Tôm Hùm completes a task.
2.  **Capture:** Save `(Prompt, Thinking, Code)` to `wins.jsonl`.
3.  **Train (Night Mode):** Colab uses **Unsloth** to fine-tune LoRA adapter.
4.  **Deploy (Day Mode):** Tôm Hùm loads new LoRA, becoming 1% smarter daily.

---

## 📊 Tổng Kết Bộ Kinh Thư
| Hệ Thống            | Số Lượng         | Nguồn                           | File                  |
| :------------------ | :--------------- | :------------------------------ | :-------------------- |
| 13 Chương           | 13               | Tôn Tử Binh Pháp gốc            | `BINH_PHAP_MASTER.md` |
| 36 Kế               | 36 (6×6)         | Tam Thập Lục Kế (Nam Bắc Triều) | `36_KE.md`            |
| Ngũ Sự              | 5                | Chương 1 始計                   | `BINH_PHAP_MASTER.md` |
| Thất Kế             | 7                | Chương 1 始計                   | `BINH_PHAP_MASTER.md` |
| Ngũ Đức Tướng       | 5                | Chương 1 始計                   | `BINH_PHAP_MASTER.md` |
| Ngũ Nguy            | 5                | Chương 8 九變                   | `BINH_PHAP_MASTER.md` |
| Cửu Địa             | 9                | Chương 11 九地                  | `BINH_PHAP_MASTER.md` |
| Lục Địa Hình        | 6                | Chương 10 地形                  | `BINH_PHAP_MASTER.md` |
| Ngũ Hỏa             | 5                | Chương 12 火攻                  | `BINH_PHAP_MASTER.md` |
| Ngũ Gián            | 5                | Chương 13 用間                  | `BINH_PHAP_MASTER.md` |
| Phong Lâm Hỏa Sơn   | 4                | Chương 7 軍爭                   | `BINH_PHAP_MASTER.md` |
| Bát Quái Nguyên Tắc | 8                | Tổng hợp 13 Chương              | `BINH_PHAP_MASTER.md` |
| Quân Luật           | 9                | Doanh Trại Tôm Hùm              | `QUAN_LUAT.md`        |
| Doanh Trại          | 11 daemons       | OpenClaw org chart              | `DOANH_TRAI.md`       |
| **AGI Doctrine**    | **4 Principles** | **a16z/Sequoia 2025**           | `AGI_EVOLUTION.md`    |
| **TỔNG**            | **136 concepts** |                                 |                       |

---

_Binh Pháp Tôn Tử Kinh Thư Đại Toàn v2.0.0 (AGI Edition) | Doanh Trại Tôm Hùm | 2026-02-13_
_Sources: Wikisource, MIT translations, a16z, Sequoia, Andreessen Horowitz_

# 🧠 TÔM HÙM MEMORY — Bộ Não Vĩnh Cửu

> 📜 用間 Ch.13: 「明君賢將之所以動而勝人」— Vua sáng tướng giỏi luôn thắng nhờ tình báo
> 
> File này là BỘ NHỚ VĨNH CỬU của Tôm Hùm CTO.
> Dù tắt máy, context compact, hay restart — đọc file này = nhớ lại tất cả.

---

## LESSONS — Bài Học Từ Missions (最新 → 最旧)

| Date | Project | Mission | Lesson | Tokens | Efficiency |
|------|---------|---------|--------|--------|------------|
| 2026-02-17 | openclaw | mentor_lesson_001 | 🎓 LESSON: Import cleanup — 5 modules still had brain-tmux (post-mission-gate, mission-journal, auto-cto-pilot, learning-engine, project-scanner) | 0 | N/A |
| 2026-02-17 | monitor-test | mentor_001 | Clean success in 5min — good pattern | 200 | 40/min |
| 2026-02-17 | apex-os | build_fail_002 | FAILED — Cannot find module ./missing-dep | 800 | 400/min |
| 2026-02-17 | test-project | green_test_001 | Clean success in 10min — good pattern | 500 | 50/min |

---

## GOTCHAS — Bẫy Đã Biết (Known Pitfalls)

> Patterns lỗi lặp lại → ghi lại để KHÔNG bao giờ mắc lại.

- **2026-02-17** [openclaw]: brain-tmux sprawl — After refactoring to brain-process-manager, 10 modules still imported brain-tmux → systematic purge needed
- **2026-02-17** [openclaw]: Import audit blind spot — Fixed mission-dispatcher but missed post-mission-gate, journal, cto-pilot, learning-engine, scanner
- **2026-02-17** [openclaw]: "LLM Analysis failed: fetch failed" → project-scanner.js crashed on require('./brain-tmux').log
- **2026-02-17** [apex-os]: Missing module — always check imports before implementing
---

## STRENGTHS — Điểm Mạnh Đã Chứng Minh

> Patterns thành công → tái sử dụng cho missions tương lai.


- **2026-02-17** [monitor-test]: Efficient mission — 40 tokens/min in 5min
- **2026-02-17** [test-project]: Efficient mission — 50 tokens/min in 10min
---

## TOKEN EFFICIENCY TRENDS

> Theo dõi xu hướng: tokens/phút giảm = tốt hơn.

```
Week | Avg Tokens/Min | Missions | Success Rate
───────────────────────────────────────────────
(no data yet)
```

---

_Auto-updated by post-mortem-reflector.js after each mission | 🦞_

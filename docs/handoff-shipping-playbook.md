# Handoff Shipping Playbook

> **Câu hỏi gốc:** "Bàn giao dự án cho end-user — làm thế nào để biết dùng
> command nào của Claudekit + Mekong để ship GREEN go-live zero bug?"

Mục tiêu: 1 trang quyết định cho mọi tình huống ship. Đọc 30 giây → biết
gõ command nào tiếp theo.

---

## 1. Decision Tree — "Tôi đang ở đâu?"

```
START: dự án sẵn sàng bàn giao?
│
├─ Chưa code xong → /cook "<task>" --auto      (Mekong)
├─ Code xong, chưa test → /test                (Mekong)
├─ Test xong, chưa review → /review            (Mekong)
├─ Review xong, chưa clean → /techdebt         (Claudekit global)
├─ Clean xong, chưa commit → /check-and-commit (Claudekit global)
├─ Commit xong, chưa deploy → /ship hoặc /deploy production  (Mekong)
├─ Deploy xong, chưa verify → /smoke (chạy infra/smoke/*.sh)
├─ Verify xong, CI chưa GREEN → /vercel-debug  (Claudekit global)
└─ CI GREEN → /release-ship "v1.0.0 - launch"  (Mekong)
                  ↓
              ✅ Go-live thành công
```

**Quy tắc 1:** không bao giờ skip một bước. Vi phạm = bug lọt prod.

---

## 2. The GREEN Go-Live Chain (5 gates, KHÔNG bỏ qua)

Mỗi gate phải PASS trước khi sang gate tiếp theo. Nếu fail → quay về fix,
chạy lại từ đầu chain (không patch giữa chừng).

| # | Gate                  | Command Mekong          | Command Claudekit | Pass khi                         |
|---|----------------------|--------------------------|---------------------|-----------------------------------|
| 1 | **Code complete**    | `/cook <task> --auto`    | —                   | feature implemented theo plan     |
| 2 | **Tests pass**       | `/test`                  | —                   | 100% pytest, 0 skip không justified |
| 3 | **Review clean**     | `/review`                | —                   | code-reviewer score ≥ 9.0, 0 critical |
| 4 | **Tech debt zero**   | —                        | `/techdebt`         | 0 console.log, 0 TODO, 0 `any` types |
| 5 | **Deploy + verify**  | `/ship` hoặc `/deploy`   | —                   | CI GREEN + production HTTP 200 + smoke 14/14 |

**Quy tắc 2:** không có gate nào là "optional" cho zero-bug go-live.

---

## 3. Command Source Priority — Mekong-First

Theo `CLAUDE.md` § "ClaudeKit Bridge — Mekong-First Policy": chạy
trong `~/mekong-cli` thì Mekong commands có priority. Chỉ fallback Claudekit
global khi Mekong không có equivalent.

### Map nhanh

| Tình huống                         | Mekong (.claude/commands/)   | Claudekit (~/.claude/commands/) |
|-----------------------------------|-------------------------------|---------------------------------|
| Implement feature                  | `/cook`                       | —                               |
| Plan complex work                  | `/plan` hoặc `/plan:hard`     | —                               |
| Brainstorm                         | `/brainstorm`                 | —                               |
| Debug issue                        | `/debug`                      | —                               |
| Run tests                          | `/test`                       | —                               |
| Code review                        | `/review`                     | —                               |
| Tech debt scan                     | —                             | `/techdebt`                     |
| Vercel CI/CD debug                 | —                             | `/vercel-debug`                 |
| Vercel deploy                      | `/cloudflare` (CF-only stack) | `/vercel-debug` (debug only)    |
| Memory save                        | `/save` hoặc `/remember`      | `/save`, `/remember`            |
| Idea → product                     | `/idea` (Mekong 25-step BizPlan OS) | `/idea` (4-step, simpler)  |
| Ship to prod                       | `/ship`, `/deploy`, `/release-ship` | —                          |
| Audit / compliance                 | `/audit-execute`, `/audit-sox`, `/audit-itgc` | —              |
| Bind & approve deployment          | `/approve`                    | —                               |

**Quy tắc 3:** không gõ raw text cho CC CLI — luôn prefix bằng `/cook`,
`/plan`, `/review`, hoặc command cụ thể. Vi phạm = task bị reject (theo
`~/.claude/CLAUDE.md` Rule 3).

---

## 4. Handoff Scenarios — Sequence Đầy Đủ

### Scenario A: Lần đầu bàn giao, app chưa có CI

```bash
mekong                                  # cd ~/mekong-cli + launch CC CLI
/scout "what does this codebase do"     # hiểu hiện trạng
/plan:hard "production handoff to end user"
/cook <plan-path> --auto                # execute plan
/test                                   # mọi test phải pass
/review                                 # 0 critical
/techdebt                               # clean residue
/check-and-commit                       # conventional commit
/ship                                   # push + deploy + verify
/release-ship "v1.0.0 — handoff GA"     # tag + changelog
```

### Scenario B: App đã ship, cần bàn giao docs + access cho end user

```bash
/docs generate handoff package          # README, deploy guide, runbook
/audit-execute "production handoff"     # evidence collection
/approve handoff-package                # final gate
# Bàn giao thủ công: env files, credentials rotation, dashboard access
```

### Scenario C: End user báo bug post-handoff

```bash
/debug "<bug description from user>"    # diagnose root cause
/cook "<fix description>" --fast        # implement fix
/test                                   # regression check
/release-ship "v1.0.1 — fix <bug>"      # hotfix release
/vercel-debug                           # nếu CI/CD red
```

### Scenario D: Validate trước bàn giao (GREEN production check)

Đối với Mekong-CLI specific (gateway.cashclaw.cc):

```bash
./infra/smoke/smoke-pilot-flow.sh       # 14/14 must pass
python3 -m pytest tests/                # full pytest suite
gh run list -L 5                        # CI history
curl -sI https://gateway.cashclaw.cc/healthz | head -3  # live HTTP 200
```

---

## 5. The Verification Matrix (sau ship, bắt buộc)

Theo `~/.claude/rules/binh-phap-cicd.md` § "GREEN PRODUCTION RULE":

```
## Verification Report
- Build: ✅ exit 0
- Tests: ✅ [N] passed
- Tech debt: ✅ 0 TODO / 0 console.log / 0 any-type
- Git Push: ✅ <commit_hash> → main
- CI/CD Run: ✅ <run_id> completed:success
- Job: Build ✅ / Test ✅ / Deploy ✅
- Production HTTP: ✅ 200
- Smoke test: ✅ N/N checks
- Health endpoint: ✅ build SHA matches commit
- Timestamp: <UTC>
```

**Thiếu 1 dòng = task CHƯA XONG.** Không bao giờ báo "Done" khi chưa đủ.

---

## 6. Anti-Patterns — KHÔNG ĐƯỢC LÀM

| ❌ Anti-pattern                                  | ✅ Đúng                                  |
|--------------------------------------------------|-------------------------------------------|
| `git push` → "Done"                              | Push → poll CI → curl prod → report      |
| Gửi raw text cho CC CLI                          | Luôn prefix `/cook` hoặc command cụ thể  |
| Skip `/test` "vì compile pass"                   | Test luôn — fix > skip                   |
| `vercel --prod` direct khi có CI                 | Push to main → CI deploy                 |
| "CI GREEN" chỉ check 1 job                       | `gh run view <ID> --json jobs` mọi job   |
| Báo "deployed" mà không curl prod                | Bắt buộc HTTP 200 verification           |
| Amend commit khi pre-commit hook fail            | Fix issue → NEW commit (không amend)     |
| Force-push main / master                         | Tạo PR + review → merge                  |
| Commit `apps/`, `.env`, `*.pem`                  | `git diff --cached --name-only` trước commit |
| Inflate test coverage bằng mock                  | Real implementation, không mock DB       |

---

## 7. Cheat Sheet — 10 Commands Phải Nhớ

```
/cook       — implement feature           (Mekong)
/plan       — multi-step plan             (Mekong)
/test       — run + fix tests             (Mekong)
/review     — code review                 (Mekong)
/techdebt   — clean residue               (Claudekit)
/debug      — diagnose bug                (Mekong)
/ship       — push + deploy + verify      (Mekong)
/deploy     — env-targeted deploy         (Mekong)
/release-ship — tag + changelog + GA      (Mekong)
/approve    — final gate                  (Mekong)
```

Đủ 10 lệnh này = đủ shipping pipeline. Còn lại là chuyên môn hóa.

---

## 8. Tại Sao Lại 2 Sources Commands?

- **Mekong (`.claude/commands/`)** — 400 commands chuyên cho mekong-cli
  domain: VN pilot, billing, Polar.sh, accounting, audit, business ops.
- **Claudekit (`~/.claude/commands/`)** — 16 commands cross-project: tech
  debt, memory, vercel debug, marketing bundle.

Mekong mở rộng Claudekit. Khi cùng tên (e.g. `/save`, `/remember`) →
Mekong version chạy vì cwd là `~/mekong-cli`. Vẫn dùng được Claudekit
version qua `/ck-*` prefix (ví dụ `/ck-save` thay vì `/save`).

---

## Unresolved Questions

- `/release-ship` chưa có CI auto-trigger — đang yêu cầu manual tag push.
  Có nên wire vào pre-push hook không?
- Smoke test cron job (`infra/smoke/`) chưa setup ở `/Library/LaunchDaemons/`
  — chỉ ad-hoc chạy. Cần thêm `com.mekong.smoke.plist` không?
- Founder webhook (Round 11) hiện optional. Có nên ép `MEKONG_SIGNUP_WEBHOOK_URL`
  bắt buộc set trước khi /ship vào production không?
- `/audit-execute` output format chưa chuẩn hóa với SOC2/SOX — cần
  template không?

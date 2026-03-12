# HƯỚNG DẪN SỬ DỤNG — Kéo file vào CC CLI cho Opus

## Chuẩn bị

### Bước 0: Setup repo
```bash
mkdir mekong-cli && cd mekong-cli
git init

# Copy CLAUDE.md vào root repo — BẮT BUỘC
cp path/to/CLAUDE.md ./CLAUDE.md

# Copy SOUL.md vào root repo
cp path/to/SOUL.md ./SOUL.md

# Commit
git add -A && git commit -m "init: project skeleton with constraints"
```

### Bước 1: Mở CC CLI
```bash
claude
# hoặc
claude --model opus
```

---

## Quy trình làm việc: 4 Sessions

### SESSION 1 — Scaffold + Types (khoảng 15 phút)

Kéo file `IMPLEMENTATION-SPEC.md` vào, rồi gõ:

```
Đọc file IMPLEMENTATION-SPEC.md. 

Làm theo thứ tự:
1. Tạo toàn bộ folder structure (Section 1.4)
2. Tạo package.json, tsconfig.json, vitest.config.ts (Section 1.2, 1.3, 7)
3. Chạy pnpm install
4. Code tất cả files trong src/types/ (Section 2)
5. Code src/utils/*.ts (retry, file, hash, validation)
6. Code src/core/events.ts (Section 4.2)
7. Chạy pnpm lint để verify TypeScript OK

STOP sau bước 7. Không code thêm gì.
```

**Sau khi Opus xong → review → commit:**
```bash
git add -A && git commit -m "feat(core): scaffold + types + utils + events"
```

---

### SESSION 2 — Config + LLM + Memory (khoảng 20 phút)

Mở session mới, gõ:

```
Đọc CLAUDE.md và IMPLEMENTATION-SPEC.md.

Tiếp tục từ scaffold đã có. Làm theo thứ tự:
1. Code src/config/ (loader.ts, defaults.ts) — Section 4.1
2. Code src/llm/types.ts
3. Code src/llm/providers/anthropic.ts (dùng fetch, không dùng SDK)
4. Code src/llm/providers/deepseek.ts (OpenAI-compatible API)
5. Code src/llm/providers/ollama.ts
6. Code src/llm/cost-tracker.ts — Section 4.8 (BudgetTracker)
7. Code src/llm/router.ts — Section 4.3
8. Code src/memory/session.ts (JSONL append-only log)
9. Code src/memory/identity.ts (parse SOUL.md)
10. Code src/constraints/parser.ts + checker.ts + budget.ts
11. Viết tests cho config loader và llm router

STOP sau bước 11.
```

**Review → commit:**
```bash
git add -A && git commit -m "feat(core): config + llm router + memory + constraints"
```

---

### SESSION 3 — Tools + Agents (khoảng 25 phút)

Mở session mới, gõ:

```
Đọc CLAUDE.md và IMPLEMENTATION-SPEC.md.

Tiếp tục. Làm theo thứ tự:
1. Code src/tools/security.ts — Section 4.7 (4 security levels)
2. Code src/tools/builtin/shell.ts (sandboxed child_process.exec)
3. Code src/tools/builtin/file-ops.ts (read, write, search, list)
4. Code src/tools/builtin/git-ops.ts (status, diff, commit, push)
5. Code src/tools/builtin/http-client.ts (fetch wrapper)
6. Code src/tools/builtin/ask-user.ts (inquirer prompt)
7. Code src/tools/registry.ts (register + discover + validate tools)
8. Code src/agents/worker.ts — Section 4.4 (ReAct loop)
9. Code src/agents/orchestrator.ts — Section 4.5
10. Code src/agents/patterns/hierarchical.ts
11. Code src/agents/patterns/sequential.ts
12. Code src/agents/pool.ts
13. Viết tests cho shell tool, worker agent, orchestrator

STOP sau bước 13.
```

**Review → commit:**
```bash
git add -A && git commit -m "feat(core): tools + agents + orchestration patterns"
```

---

### SESSION 4 — SOP Engine + CLI (khoảng 20 phút)

Mở session mới, gõ:

```
Đọc CLAUDE.md và IMPLEMENTATION-SPEC.md.

Tiếp tục. Làm theo thứ tự:
1. Code src/sops/parser.ts (parse YAML + validate Zod)
2. Code src/sops/dag.ts (build dependency graph từ steps)
3. Code src/sops/executor.ts — Section 4.6
4. Code src/sops/rollback.ts
5. Code src/sops/metrics.ts
6. Copy 5 SOP templates vào src/sops/templates/ (Section 5)
7. Code src/core/engine.ts (wires everything together)
8. Code src/core/gateway.ts (stdin/stdout cho bây giờ)
9. Code src/cli/ui/ (spinner, logger, output, prompt)
10. Code src/cli/commands/ (run.ts, sop.ts, init.ts, status.ts)
11. Code src/cli/index.ts — Section 4.9
12. Chạy pnpm build
13. Test: npx mekong --help
14. Test: npx mekong init (tạo mekong.yaml)
15. Viết README.md (Section 8)

STOP sau bước 15.
```

**Review → commit:**
```bash
git add -A && git commit -m "feat(core): sop engine + cli + first release"
git tag v0.1.0
```

---

## Quy tắc Jidoka cho mỗi session

- Nếu Opus **báo lỗi TypeScript** → fix ngay, đừng để qua bước tiếp
- Nếu Opus **thêm dependency không có trong approved list** → hỏi tại sao trước khi approve
- Nếu Opus **code 1 file > 300 dòng** → yêu cầu tách
- Nếu Opus **skip test** → yêu cầu viết test trước khi tiếp
- Nếu Opus **tự ý thêm feature** → cancel và nhắc lại scope

## Troubleshooting

### Opus bị đứng / chạy lâu
→ Cancel (Ctrl+C), mở session mới, paste lại instruction cho step đang dở

### Opus code sai architecture
→ Paste đoạn interface/type tương ứng từ IMPLEMENTATION-SPEC.md, yêu cầu code lại đúng interface

### Opus quên context
→ Bình thường vì context window giới hạn. Mở session mới, nó sẽ đọc lại CLAUDE.md + codebase

### Build fail
→ Gõ: "Fix all TypeScript errors. Chạy pnpm lint và fix cho đến khi pass."

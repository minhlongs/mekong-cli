# Auto-Merge Rule

> Chính sách tự động merge PR. AI tự xử lý, Founder không cần làm gì.

## Cách hoạt động

1. **Label PR với `auto-merge`** — AI hoặc CI tự động merge khi checks pass
2. **Không cần founder approve** — AI tự disable protection → merge → restore
3. **Conflict?** — AI tự resolve hoặc báo failed

## Mekong CLI (GA workflow)

File: `.github/workflows/auto-merge.yml`

Khi PR có label `auto-merge` và tất cả checks pass:
- Workflow tự merge (squash)
- Tự động restore branch protection

Không cần làm gì. Chỉ cần label.

## Sophia AI Factory (no GA)

Script: `scripts/merge-daemon.cjs`

Chạy daemon để poll PR tự động:
```bash
node ~/mekong-cli/scripts/merge-daemon.cjs --once
```

Hoặc chạy nền:
```bash
nohup node ~/mekong-cli/scripts/merge-daemon.cjs > ~/mekong-cli/logs/merge-daemon.log 2>&1 &
```

Daemon tự:
- Poll repo mỗi 5 phút
- Tìm PR có label `auto-merge`
- Disable protection → merge → restore protection

## Auto-merge 1 PR nhanh

```bash
node ~/mekong-cli/scripts/auto-merge.cjs <pr-url> --admin
```

Ví dụ:
```bash
node ~/mekong-cli/scripts/auto-merge.cjs https://github.com/longtho638-jpg/mekong-cli/pull/210 --admin
```

## Luật cho AI/Agent

1. KHI có PR merge được → tự label `auto-merge`, không hỏi founder
2. KHI conflict → tự resolve, không đùn lên founder
3. KHI merge xong → tự restore protection
4. Chỉ báo founder khi: merge failed, conflict không resolve được, hoặc có breaking changes cần quyết định

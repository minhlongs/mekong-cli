# 🔒 PROXY ARCHITECTURE — ĐỌC TRƯỚC KHI CHỈNH!

## Architecture

```
CC CLI ──→ Port 11436 (Adapter) ──→ Port 9191 (AG Ultra 1: billwill)
                                ──→ Port 9192 (AG Ultra 2: cashback)
```

## 🌋 CATASTROPHIC FAILURE CASCADE (HIỆU ỨNG DOMINO LỖI)

**ĐÂY LÀ LÝ DO ĐỌC SAI PORT PROXY SẼ GIẾT CHẾT PHIÊN LÀM VIỆC:**
1. **Proxy Không Hoạt Động (hoặc config sai qua port 9191 thay vì 11436)** → Trả về `ConnectionRefused`.
2. **CC CLI Retry Loop** → CC CLI điên cuồng gửi request kết nối lại liên tục ở background.
3. **💥 Máy Nóng Rực (Overheat)** → Vòng lặp retry sinh ra hàng tá Node processes, CPU load vọt lên cực đại (> 5.0).
4. **💀 CC CLI Rớt Ngang** → Terminal hết RAM/CPU crash, tmux pane báo `[exited]`.

**CÔNG THỨC CHẾT:** `Proxy k hoạt động/Sai port = Máy Mac nóng ran = CC CLI crash ngang`

## Ports

| Port  | Role | Process | KHÔNG ĐƯỢC KILL |
|:------|:-----|:--------|:---------------|
| 11436 | Adapter (load balancer, xoay vòng 9191↔9192) | `antigravity-claude-proxy` (Node.js) | ⚠️ `killall node` SẼ GIẾT PORT NÀY! |
| 9191  | AG Ultra 1 (billwill) | Separate service | ✅ Thường sống sót |
| 9192  | AG Ultra 2 (cashback) | Separate service | ✅ Thường sống sót |

## ⚠️ CẢNH BÁO QUAN TRỌNG

1. **KHÔNG DÙNG `killall node`** — sẽ giết adapter 11436 → CC CLI mất mạng → "Network error"
2. **Chỉ kill CTO bằng:** `pkill -f task-watcher` hoặc `kill -9 <PID cụ thể>`
3. **Check proxy ĐÚNG CÁCH:** `curl -sf http://localhost:11436/health` (KHÔNG phải 9191!)
4. **CC CLI dùng port 11436** — config qua `ANTHROPIC_BASE_URL`

## Restart Adapter (nếu bị kill)

```bash
nohup antigravity-claude-proxy >> ~/proxy-11436.log 2>&1 &
# Verify:
curl -sf http://localhost:11436/health | head -1
```

## Check Health

```bash
# Adapter (CC CLI connects here):
curl -sf http://localhost:11436/health

# Upstream (adapter connects here):
curl -sf http://localhost:9191/health
curl -sf http://localhost:9192/health
```

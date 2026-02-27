# 🔍 Debug Report: 9Router Proxy Health Audit

**Date:** 2026-02-27 21:16 | **Branch:** master

---

## TÓM TẮT

Kiểm tra toàn bộ stack proxy qua cổng 9router — P1 quota Gemini, Qwen keys, NVIDIA keys.

---

## 1. PROXY PORTS STATUS

| Port | Service | Status | Ghi chú |
|------|---------|--------|---------|
| **9191** | AG Proxy (billwill.mentor) | ✅ RUNNING | 2 acc, cả 2 rate-limited |
| **9192** | AG Proxy (cashback.mentoring) | ✅ RUNNING | 2 acc, cả 2 rate-limited |
| **9193** | AG Proxy (thứ 3) | ❌ KHÔNG CÓ | Chưa config, ko có .ag_proxies/9193/ |
| **11436** | Anthropic Adapter (Penta-provider) | ✅ RUNNING | 5 providers active |
| **20128** | 9Router binary (Next.js dashboard) | ✅ RUNNING | /health trả 404 (UI app, ko phải API) |
| **20129** | CC CLI Bridge | ✅ RUNNING | Bridge → 11436 |
| **8081** | Qwen Bridge | ❌ CHẾT | Không respond |

---

## 2. P1 QUOTA GEMINI — TỪ 2 ACC ULTRA

### ✅ P1 LẤY THÀNH CÔNG QUOTA TỪ CẢ 2 ACCOUNT

Cả 2 acc `billwill.mentor` + `cashback.mentoring` đều available trên port 9191 VÀ 9192.

| Account | Gemini 3 Flash | Gemini 3 Pro High | Gemini 2.5 Flash | Gemini 2.5 Pro |
|---------|---------------|-------------------|------------------|----------------|
| billwill.mentor | 20% còn | 0% (reset 14:38) | 100% | 100% |
| cashback.mentoring | 20% còn | 0% (reset 14:38) | 100% | 100% |

**Kết luận:** P1 lấy quota từ CẢ 2 acc Ultra — round-robin OK. Gemini Pro High đã hết quota (reset ~14:38). Flash còn 20%.

### Gemini 3.0 Flash qua P1

- **Test qua port 9191:** ✅ Phản hồi OK (model=gemini-3-flash)
- **Test qua port 11436 (adapter):** ✅ Phản hồi OK kèm thinking tokens
- **BUG:** Gemini Flash response qua P1 trả `content` rỗng (chỉ có thinking block, max_tokens quá nhỏ) — KHÔNG PHẢI BUG CỦA KEY, là do max_tokens=50 bị thinking tokens ăn hết.

---

## 3. QWEN LLM KEYS — ❌ CẢ 2 KEY ĐỀU CHẾT

| Key | Status | Lỗi |
|-----|--------|------|
| `sk-6219c93...` | ❌ **INVALID** | "Incorrect API key provided" |
| `sk-c397f4b...` | ❌ **INVALID** | "Incorrect API key provided" |

**Nguyên nhân:** DashScope API keys hết hạn hoặc bị revoke.
**Qwen Bridge (port 8081):** Cũng CHẾT — không respond.
**Action:** Cần tạo key mới tại https://dashscope.console.aliyun.com/

---

## 4. NVIDIA KEYS — 17 KEYS (KIỂM TRA)

| # | Model | Key | Status |
|---|-------|-----|--------|
| 1 | Qwen3-480B | nvapi-VM1T8... | ✅ OK |
| 2 | GLM-5 | nvapi-xA7ke... | ❌ "Function not found" (model chưa available?) |
| 3 | MiniMax-M2.1 | nvapi-eit3k... | ❌ TIMEOUT |
| 4 | Kimi-K2.5 | nvapi-YAP-f... | ❌ TIMEOUT |
| 5 | Kimi-K2-Think | nvapi-NSmG9... | (chưa test) |
| 6 | DeepSeek-V3.1 | nvapi-RAxwm... | ✅ OK |
| 7 | GPT-OSS-120B | nvapi-40BX_... | (chưa test) |
| 8 | Qwen3-235B | nvapi-KEBC_... | ✅ OK |
| 9 | DS-V3.2-685B | nvapi-tKyZb... | ❌ TIMEOUT |
| 10 | Mistral-675B | nvapi-5kF13... | (chưa test) |
| 11 | Llama-405B | nvapi-1_bqJ... | (chưa test) |
| 12 | Step-3.5-200B | nvapi-BvtYU... | (chưa test) |
| 13 | Mixtral-8x22B | nvapi-I5zwk... | (chưa test) |
| 14 | Devstral-123B | nvapi-Hoxhc... | (chưa test) |
| 15 | Qwen3-Next-80B | nvapi-mp0_g... | (chưa test) |
| 16 | Llama-3.3-70B | nvapi-gXFEX... | (chưa test) |
| 17 | DS-Terminus | nvapi-rfguy... | (chưa test) |

**Tested: 6/17 | OK: 3 | Failed: 3**
- Qwen3-480B, DeepSeek-V3.1, Qwen3-235B: ✅ Confirmed working
- GLM-5: model endpoint lỗi
- MiniMax-M2.1, Kimi-K2.5, DS-V3.2-685B: timeout (có thể model đang overloaded)

---

## 5. OTHER PROVIDERS

| Provider | Status | Chi tiết |
|----------|--------|---------|
| **Ollama Cloud** | ❌ TIMEOUT | 8 keys configured, endpoint không respond |
| **OpenRouter** | ⚠️ MODEL WRONG | Key OK nhưng `google/gemini-3-flash` không tồn tại → phải đổi thành `google/gemini-3-flash-preview` |
| **Google Direct** | ✅ OK | 1 key, Gemini Flash respond |
| **Vertex AI** | (chưa test) | Config có, $1K credits |

---

## 6. BUGS & ISSUES PHÁT HIỆN

### 🔴 Critical
1. **Qwen keys CHẾT** — Cả 2 key DashScope invalid, qwen_bridge.py ko chạy
2. **Port 9193 không tồn tại** — Code ref `ANTIGRAVITY_PORTS = [9191, 9192, 9193]` nhưng chưa config

### 🟡 Medium
3. **OpenRouter model ID sai** — `google/gemini-3-flash` → phải là `google/gemini-3-flash-preview`
4. **Ollama Cloud timeout** — 8 keys nhưng endpoint không respond
5. **GLM-5 NVIDIA function not found** — Model chưa deploy/available trên NIM

### 🟢 Low
6. **Gemini Pro High hết quota** — Cả 2 acc, reset ~14:38 UTC (đã tự reset)
7. **20128 /health 404** — 9Router binary là Next.js dashboard app, ko có /health endpoint

---

## 7. P1 ROUTING FLOW (VERIFIED)

```
P1 (CC CLI) → ANTHROPIC_BASE_URL=9191 → ag-proxy.js
  → Round-robin billwill + cashback accounts
  → Google Gemini API (gemini-3-flash / gemini-3-pro-high)

Penta-Provider (11436):
  Msg 1-2: AG Ultra (9191/9192) → Gemini Pro High (thinking)
  Msg 3+: AG Ultra → Gemini Flash (execution)
  Fallback: Google Direct → NVIDIA NIM → Ollama → OpenRouter → Vertex
```

**P1 LẤY QUOTA ĐÚNG TỪ 2 ACC ULTRA** — Confirmed.

---

## ACTION ITEMS

| Priority | Action | Owner |
|----------|--------|-------|
| 🔴 P0 | Tạo Qwen DashScope keys mới | Human |
| 🔴 P0 | Fix OpenRouter model: `gemini-3-flash` → `gemini-3-flash-preview` | CC CLI |
| 🟡 P1 | Setup .ag_proxies/9193/ (3rd Ultra account) hoặc remove từ ANTIGRAVITY_PORTS | CC CLI |
| 🟡 P1 | Investigate Ollama Cloud connectivity | CC CLI |
| 🟢 P2 | Test remaining 11 NVIDIA keys | CC CLI |

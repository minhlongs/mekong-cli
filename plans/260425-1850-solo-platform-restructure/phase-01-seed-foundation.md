# Phase 01: Hạt Giống (Seed Foundation)

> **Ưu tiên:** CRITICAL — Mọi thứ phụ thuộc vào phase này  
> **Thời gian:** Tuần 1-2 | **Trạng thái:** ✅ COMPLETED  
> **Triết lý:** Chạy cục bộ trước, scale sau
> **Completed:** 2026-04-25T18:45:00Z

## Context

Mekong-cli có PEV Engine mạnh nhưng phụ thuộc cloud LLM và không có local memory.  
Phase này tạo `seed/` layer — executable độc lập, không cần API key ngoài.

## Kiến trúc Seed

```
~/mekong-cli/seed/
├── main.py              # Entry point: python seed/main.py "nhiệm vụ"
├── config.py            # Cấu hình (model, paths, URLs)
├── llm_client.py        # Kết nối Ollama local
├── memory.py            # SQLite + ChromaDB
└── agents/
    ├── base.py          # BaseAgent: think→act→observe loop
    ├── ceo.py           # CEOAgent: phân tích + lên kế hoạch
    └── developer.py     # DeveloperAgent: viết code + verify

~/mekong-cli/tools/      # (có thể reuse từ existing)
├── browser.py           # browse_website()
├── file_system.py       # write_file(), read_file(), execute_command()
└── __init__.py

~/mekong-cli/data/
├── chroma/              # ChromaDB vector store
└── sqlite/
    └── memory.db        # SQLite metadata
```

## Requirements

```
docker-compose: ollama + chromadb
python deps: chromadb==0.4.24, requests==2.31.0, sqlite3 (stdlib), pydantic==2.5.0
ollama models: llama3.1:8b (main), nomic-embed-text (embeddings)
```

## Implementation Steps

### Bước 1.1: Chuẩn bị môi trường

```bash
# Check Ollama running
curl -s http://localhost:11434/api/tags | jq '.models[].name'

# Pull required models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Create data directories
mkdir -p ~/mekong-cli/data/chroma ~/mekong-cli/data/sqlite
```

**Nhánh con:** Test 3 model (Qwen 2.5 7B, Llama 3.2 3B, DeepSeek Coder 6.7B) → chọn model cân bằng tốc độ/chất lượng

### Bước 1.2A: LLM Client

**File:** `seed/llm_client.py`

```python
# Singleton LLMClient kết nối Ollama
# Methods: chat(messages) → str, embed(text) → List[float]
# Default: llama3.1:8b, Ollama at localhost:11434
```

**Verify:** `python3 -c "from seed.llm_client import get_llm_client; print(get_llm_client().chat([{'role':'user','content':'hello'}])[:50])"`

### Bước 1.2B: Memory System

**File:** `seed/memory.py`

```python
# SeedMemory class:
# - remember(agent_id, content, metadata) → doc_id
# - recall(agent_id, query, n_results=3) → List[str]  # semantic search
# - get_recent(agent_id, limit=5) → List[Dict]
# - clear_agent_memory(agent_id)
# Backend: ChromaDB (vector) + SQLite (metadata)
```

**Verify:** `python3 seed/test_memory.py`

### Bước 1.2C: BaseAgent + CEOAgent + DeveloperAgent

**Files:** `seed/agents/base.py`, `ceo.py`, `developer.py`

```python
# BaseAgent:
# - think→act→observe loop
# - _build_context(task): lấy ký ức relevant từ memory
# - run(task, extra_context) → str

# CEOAgent(BaseAgent):
# - Phân tích task → tạo action plan
# - Giao việc cho Developer

# DeveloperAgent(BaseAgent) extends ToolEnabledAgent:
# - Viết code theo plan
# - Tự verify output
```

### Bước 1.2D: Tool Integration

**Files:** `tools/browser.py`, `tools/file_system.py`

```python
# ToolRegistry:
# - browse_website(url) → str (HTML text)
# - write_file(path, content) → str (full_path)
# - read_file(path) → str
# - execute_command(cmd, cwd=None) → str
```

**Nhánh con:** Test xem Agent có thể tự vào Google tìm "a16z Solo Company" và tóm tắt không

### Bước 1.3: Lắp ráp `seed/main.py`

```python
# Flow: task → CEOAgent(plan) → DeveloperAgent(execute) → output
# Usage: python seed/main.py "Tạo một landing page giới thiệu dịch vụ AI"
# Expected: CEO lên kế hoạch, Dev viết HTML → outputs/index.html
```

## Files cần tạo/sửa

| File | Hành động | Ownership |
|------|-----------|---------|
| `seed/llm_client.py` | CREATE | seed layer |
| `seed/memory.py` | CREATE | seed layer |
| `seed/config.py` | CREATE | seed layer |
| `seed/agents/base.py` | CREATE | agent layer |
| `seed/agents/ceo.py` | CREATE | agent layer |
| `seed/agents/developer.py` | CREATE | agent layer |
| `tools/browser.py` | CREATE | tool layer |
| `tools/file_system.py` | CREATE | tool layer |
| `seed/main.py` | CREATE | entry point |
| `data/.gitkeep` | CREATE | data dirs |

## Checklist

- [x] Ollama running với llama3.1:8b
- [x] `seed/llm_client.py` — chat() trả kết quả
- [x] `seed/memory.py` — remember/recall hoạt động
- [x] `seed/agents/base.py` — BaseAgent run() thành công
- [x] `seed/agents/ceo.py` — CEOAgent tạo plan
- [x] `seed/agents/developer.py` — Dev viết code vào file
- [x] `tools/*.py` — ít nhất file_system hoạt động
- [x] `seed/main.py` — E2E test pass
- [x] `outputs/index.html` — tồn tại sau E2E test

## Success Criteria

```bash
python3 seed/main.py "Tạo một trang HTML đơn giản giới thiệu mekong-cli"
# Expected output:
# 🤖 CEO đang phân tích...
# 📋 Kế hoạch: [plan text]
# 💻 Developer đang thực thi...
# ✅ Hoàn thành. Kiểm tra outputs/
ls outputs/  # → index.html
```

## Risk Assessment

| Rủi ro | Xác suất | Giảm thiểu |
|--------|---------|-----------|
| Ollama chậm trên M1 | Thấp | Đã test Qwen 2.5, 36.8 token/s |
| ChromaDB conflict với existing | Thấp | Install vào venv riêng |
| Tools directory conflict | Trung bình | Check `~/mekong-cli/tools/` có rồi không |

## Next Steps

→ Phase 02: Tree (Web UI + Telegram webhook + CEO+Dev hoàn chỉnh)

## Câu hỏi Chưa giải quyết

1. `~/mekong-cli/tools/` đã tồn tại chưa? (Cần check trước khi tạo)
2. `src/core/` (PEV Engine hiện tại) có thể reuse cho `seed/agents/` không?
3. Cần venv riêng hay install vào global Python?

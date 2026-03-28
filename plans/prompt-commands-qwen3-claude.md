# 🦞 TÔM HÙM — Prompt Commands cho Qwen3 & Claude CDE CLI

**Created:** 2026-03-20
**Target:** Qwen3.0 32B (Ollama) + Claude CDE CLI (CC CLI)

---

## 🔥 PHASE 1: SYNC & SETUP

### Sync upstream
```
/cook Fetch upstream và merge main: cd /Users/mac/mekong-cli && git fetch upstream && git merge upstream/main --no-edit && git log --oneline -5
```

### Pull Qwen3 model
```
/cook Pull Qwen3.0 32B model vào Ollama: ollama pull qwen3:32b && ollama list | grep qwen3
```

### Verify Ollama running
```
/cook Kiểm tra Ollama đang chạy và Qwen3 available: curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['name']) for m in d.get('models',[])]"
```

---

## 🔧 PHASE 2: DEEP CONFIG

### Config .env
```
/cook Update .env cho Qwen3.0 32B: Mở /Users/mac/mekong-cli/.env và set LLM_BASE_URL=http://localhost:11434/v1, LLM_API_KEY=ollama, LLM_MODEL=qwen3:32b, OLLAMA_BASE_URL=http://localhost:11434/v1, OLLAMA_MODEL=qwen3:32b, LLM_MODE=byok
```

### Config provider YAML
```
/cook Tạo mekong/adapters/llm-providers.yaml với Qwen3.0 32B là primary provider, base_url=http://localhost:11434/v1, model=qwen3:32b, timeout=120, circuit_breaker max_failures=3 cooldown=15s
```

### Test LLM integration
```
/cook Test Mekong CLI LLM Client: cd /Users/mac/mekong-cli && python3 -c "from src.core.llm_client import get_client; c=get_client(); print(f'Mode:{c.mode} Available:{c.is_available} Providers:{[p.name for p in c.providers]}')"
```

---

## 🧪 PHASE 3: QUALITY & VERIFY

### Run tests
```
/cook Chạy full test suite: cd /Users/mac/mekong-cli && python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

### Lint check
```
/cook Lint Python source: cd /Users/mac/mekong-cli && python3 -m ruff check src/ --fix && python3 -m ruff format src/
```

### Factory self-test
```
/cook Factory self-test score: cd /Users/mac/mekong-cli && python3 factory/self_test.py
```

### Health check
```
/cook Health check toàn bộ dev environment: cd /Users/mac/mekong-cli && bash scripts/health-check.sh
```

---

## 🤖 PHASE 4: AGI & CORE OPS

### Start gateway
```
/cook Start FastAPI gateway port 8000: cd /Users/mac/mekong-cli && python3 -m uvicorn src.core.gateway:app --reload --port 8000
```

### AGI score
```
/cook Tính AGI score hiện tại: cd /Users/mac/mekong-cli && python3 -c "from src.core.agi_score import compute_agi_score; s=compute_agi_score(); print(f'Score: {s.total}/100 Grade: {s.grade}')"
```

### Swarm status
```
/cook Kiểm tra Swarm Registry: cd /Users/mac/mekong-cli && python3 -c "from src.core.swarm import SwarmRegistry; r=SwarmRegistry(); nodes=r.list_nodes(); print(f'Nodes: {len(nodes)}'); [print(f'  {n.name} {n.host}:{n.port} → {n.status}') for n in nodes]"
```

### Memory stats
```
/cook Kiểm tra Memory Store: cd /Users/mac/mekong-cli && python3 -c "from src.core.memory import MemoryStore; s=MemoryStore(); stats=s.stats(); print(f'Total: {stats[\"total\"]} Success: {stats[\"success_rate\"]:.1f}%')"
```

---

## 📱 PHASE 5: TELEGRAM & PLUGIN

### Telegram bot start
```
/cook Start Telegram Tôm Hùm bot: cd /Users/mac/mekong-cli && python3 -c "import asyncio; from src.core.telegram_bot import MekongBot; bot=MekongBot(); asyncio.run(bot.start())"
```

### Plugin marketplace check
```
/cook Check Plugin Marketplace: cd /Users/mac/mekong-cli && python3 -c "from src.core.plugin_marketplace import MarketplaceClient; c=MarketplaceClient(); print(f'Marketplace: {c.base_url}'); print(f'Healthy: {c.health_check()}')"
```

---

## 🏭 PHASE 6: CTO DAEMON

### Start CTO daemon
```
/cook Start CTO daemon full mode: cd /Users/mac/mekong-cli && bash cto-daemon.sh
```

### CTO monitor
```
/cook Start CTO monitor: cd /Users/mac/mekong-cli && bash cto-monitor.sh
```

### Factory generate contracts
```
/cook Generate + validate factory contracts: cd /Users/mac/mekong-cli && make regenerate
```

---

## 💡 CLAUDE CDE CLI — Direct Prompts

### Clone & sync
```
Fetch upstream mekong-cli repo và merge vào local. Repo: https://github.com/longtho638-jpg/mekong-cli. Local: /Users/mac/mekong-cli. Remote name: upstream. Branch: main.
```

### Deep config Qwen3
```
Cấu hình Mekong CLI sử dụng Qwen3.0 32B qua Ollama local:
1. Update .env: LLM_BASE_URL=http://localhost:11434/v1, LLM_API_KEY=ollama, LLM_MODEL=qwen3:32b
2. Tạo mekong/adapters/llm-providers.yaml với qwen3:32b primary
3. Test: python3 -c "from src.core.llm_client import get_client; c=get_client(); print(c.is_available, [p.name for p in c.providers])"
```

### Full system verify
```
Chạy toàn bộ verification cho Mekong CLI:
1. pytest tests/ -v
2. ruff check src/
3. python3 factory/self_test.py
4. curl localhost:11434/api/tags (Ollama check)
5. curl localhost:8000/health (Gateway check)
Report lại score và trạng thái.
```

### AGI self-improvement
```
Chạy AGI self-improvement loop cho Mekong CLI:
1. Tính AGI score hiện tại
2. Tìm improvement opportunities (type safety, tech debt, security)
3. Apply top 3 improvements
4. Re-score và report delta
Target: AGI score > 95/100
```

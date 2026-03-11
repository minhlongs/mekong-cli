# Quickstart — Fork Your Own AI Agency

## 5 phút setup

1. **Clone:**
```bash
git clone https://github.com/longtho638-jpg/mekong-cli.git my-agency
cd my-agency
```

2. **Install:**
```bash
make setup
```

3. **Configure LLM (chọn 1):**
```bash
# Option A: OpenRouter ($5 free signup)
echo 'LLM_BASE_URL=https://openrouter.ai/api/v1' >> .env
echo 'LLM_API_KEY=sk-or-v1-yourkey' >> .env
echo 'LLM_MODEL=anthropic/claude-sonnet-4' >> .env

# Option B: Ollama (free, local)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5-coder
echo 'OLLAMA_BASE_URL=http://localhost:11434/v1' >> .env
```

4. **Verify:**
```bash
mekong cook "Create hello.py"
```

5. **Scaffold your project:**
```bash
bash mekong/infra/scaffold.sh myproject startup
```

## Done. You have an AI agency.

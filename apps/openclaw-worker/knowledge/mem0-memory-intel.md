# 🧠 Mem0 — Universal Memory Layer — 用間篇 Agent Long-Term Memory

> Source: github.com/mem0ai/mem0
> Assessed: 2026-02-18 | Status: CRITICAL KEEP — P1 Infrastructure
> Action: Install + integrate vào Tôm Hùm CTO brain

## What
- Universal memory layer cho AI agents
- 3-level: User memories + Session memories + Agent memories
- Semantic vector search (not keyword grep)
- 272 releases, 251 contributors, 4.6K dependents
- Self-hosted or hosted (app.mem0.ai)

## Install
```bash
npm install mem0ai    # JS
pip install mem0ai    # Python
```

## Why CRITICAL for Tôm Hùm
1. CTO forgets everything between sessions → Mem0 = persistent memory
2. Antigravity loses knowledge on context compact → Mem0 = external store
3. Chairman preferences need repeating → Mem0 = auto-recall
4. Knowledge base = flat markdown grep → Mem0 = semantic search
5. Missions restart from scratch → Mem0 = "what did I do before?"

## Integration Plan
1. npm install mem0ai in openclaw-worker/
2. Create memory.js wrapper: init, add, search, delete
3. brain-supervisor: After each mission → memory.add(mission_summary)
4. Before each mission → memory.search(task_description) for context
5. Chairman profile: memory.add(preferences, user_id="chairman")
6. AG Proxy: Inject relevant memories into system prompt

## API
```javascript
const { Memory } = require('mem0ai');
const memory = new Memory();

// Store mission outcome
memory.add(messages, { user_id: "chairman", agent_id: "tom_hum_cto" });

// Retrieve relevant context
const results = memory.search({ query: "deployment patterns", user_id: "chairman" });
```

## Binh Pháp
- 用間篇: "Gián điệp giỏi NHỚM MỌI THỨ" — persistent memory = #1 agent advantage
- 知己知彼: Agent remembers past = knows itself
- 謀攻篇: Learn from every mission → compound intelligence

## Priority: P1 CRITICAL — solves #1 weakness of AI agents (forgetting)

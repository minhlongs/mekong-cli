# RaaS Foundation: The Operating System for AI Agencies

## 1. Introduction
The **Revenue-as-a-Service (RaaS) Foundation** is the architectural backbone of Mekong CLI. It is designed to empower agencies to deliver high-value outcomes (leads, software, content) using an autonomous swarm of AI agents.

## 2. Core Components

### Antigravity Proxy (The Gatekeeper)
- **Architecture**: A centralized proxy server running on `port 11436`.
- **Load Balancing**: Distributes requests across Ollama (local), OpenRouter (aggregator), and direct Google AI/Anthropic accounts.
- **Failover**: If a primary model (e.g., Claude 3.5 Sonnet) hits a rate limit, the proxy automatically fails over to a high-performance alternative (e.g., Gemini 1.5 Pro).
- **Cost Efficiency**: Routes non-complex tasks to "Flash" models, saving expensive tokens for high-reasoning tasks.

### Tôm Hùm Daemon (The General)
- **Autonomous Dispatch**: Uses file-based IPC to receive missions and route them to agents.
- **Auto-CTO**: A background process that ensures codebase health (linting, security, tech debt) when the mission queue is empty.
- **M1 Cooling**: Protects local hardware by monitoring CPU temperature and RAM usage.

## 3. Service Tiers

### 💎 Free Tier (Community)
Targeted at independent developers and hobbyists.
- **Execution**: Local machine (Edge).
- **Models**: Access to local models via Ollama and community-tier API keys.
- **Workflow**: Sequential task execution.
- **Recipes**: Access to public community recipes.

### 🚀 Paid Tier (Enterprise/Agency)
Targeted at professional RaaS agencies.
- **Execution**: High-performance Cloud GPU nodes.
- **Models**: Guaranteed access to flagship models (Claude Opus 4.5/4.6, DeepSeek R1).
- **Workflow**: Massive parallelization via **Agent Teams**.
- **Delivery**: 100% Automated "Green Production" pipelines with CI/CD verification.
- **Customization**: Private Skills and specialized CRM/Ads integration.

## 4. Getting Started with RaaS
1. **Local Setup**: Follow the `README.md` to get the Tôm Hùm daemon running locally.
2. **First Mission**: Create a task in the `tasks/` directory to see the engine in action.
3. **Scale Up**: Connect your private API keys to Antigravity Proxy to unlock higher reasoning capabilities.

---
© 2026 Binh Phap Venture Studio.

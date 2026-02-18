# RaaS Foundation: The Operating System for AI Agencies

## 1. Overview
The **Revenue-as-a-Service (RaaS) Foundation** is the architectural framework that powers Mekong CLI. It shifts the paradigm from traditional "Human-in-the-loop" services to "AI-at-the-core" autonomous operations. This foundation ensures that every action taken by the system is aligned with generating revenue, reducing costs, or increasing strategic leverage.

## 2. Antigravity Proxy Layer (The Intelligence Hub)

The Antigravity Proxy is the critical infrastructure component that manages the intelligence flow. Running on `port 11436`, it acts as a universal adapter between AI agents and Large Language Model (LLM) providers.

### Key Capabilities:
- **Provider Agnostic**: Seamlessly switch between Anthropic, Google Gemini, OpenAI, and local Ollama models using a unified Anthropic-compatible API.
- **Failover Autonomy**: In the event of a `429 Rate Limit` or `503 Service Unavailable` from a primary provider, the proxy automatically routes the request to a pre-configured fallback model.
- **Intelligent Load Balancing**: Distributes tokens across multiple API keys and accounts to maximize throughput and minimize latency.
- **Cost Routing**: Automatically routes simpler tasks (like linting or documentation formatting) to lightweight "Flash" models, reserving high-reasoning models (Claude Opus/Sonnet) for complex engineering tasks.

## 3. The PEV (Plan-Execute-Verify) Engine

Mekong CLI's operational DNA is built on the PEV cycle, ensuring high-fidelity delivery:

1. **Plan**: Agents decompose high-level business goals (e.g., "Launch a new F&B brand") into atomic, actionable steps.
2. **Execute**: The execution layer performs file modifications, API calls, and shell commands. It features self-healing logic that can correct syntax errors or command failures in real-time.
3. **Verify**: Every execution is followed by a verification phase. No task is considered "Done" until it passes pre-defined quality gates (Binh Phap Standards).

## 4. Tiered Service Model

To support both independent developers and enterprise-scale agencies, the RaaS Foundation is structured into two primary tiers:

### 💎 Community Tier (Free)
Designed for individual developers, hobbyists, and open-source contributors.
- **Execution Environment**: Local machine (Edge) or personal server.
- **Model Support**: Local models via Ollama and community-standard API access.
- **Agents**: Sequential task execution for high-focus single missions.
- **Governance**: Access to core Binh Phap quality gates for local development.

### 🚀 Agency Tier (Paid/Enterprise)
Designed for professional RaaS agencies managing multiple client projects with high stakes.
- **Execution Environment**: High-performance Cloud GPU clusters for maximum speed.
- **Model Support**: Priority access to flagship reasoning models (Claude 3.7 Opus, DeepSeek R1).
- **Parallel Swarms**: Simultaneous execution across multiple projects using **Agent Teams**.
- **Green Production**: Fully automated deployment pipelines that verify production health before signaling completion.
- **Advanced Skills**: Access to proprietary "Agency Skills" including automated Ads management, CRM optimization, and Lead Discovery agents.

## 5. Security & Sovereignty
The RaaS Foundation prioritizes data sovereignty. By using the Antigravity Proxy, agencies can keep sensitive reasoning logs within their own infrastructure while still utilizing the best available global AI models.

---
© 2026 Binh Phap Venture Studio.
*"Strategic victory is the result of invisible preparation."*

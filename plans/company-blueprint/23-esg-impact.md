# ESG + Impact

Mekong CLI's environmental, social, and governance impact strategy is embedded in the product architecture, not bolted on as a separate initiative. Every line of code ships a triple-bottom-line effect by design.

## Environmental (Planet)

- **Local-first AI inference** eliminates cloud data center waste. Running Ollama on commodity hardware means no GPU-idle tax, no hyperscaler e-waste cycle, and no data-center cooling overhead per inference.
- **One subscription displaces 50 commuters.** Each SaaS tool a founder runs locally replaces the carbon footprint of distributed teams driving to co-working spaces, flying for standups, or powering a second office.
- **Ollama runs on existing hardware.** No new silicon required. Mekong CLI adapts to whatever GPU, NPU, or CPU the user already owns — extending device lifespan and reducing demand for new chips.
- **Edge-native deployment model.** When users deploy to their own infrastructure (Raspberry Pi, old laptop, VPS), the carbon cost is proportional to actual usage, not a flat data-center allocation.
- **Minimal dependency footprint.** CLI-first architecture avoids the bloat of Electron apps, SPA frameworks, and heavy cloud SDKs that inflate both bandwidth and compute waste.
- **Energy-aware scheduling.** Agents and workflows can be gated to run during off-peak grid hours or when local renewable generation is available, using a simple cron-based power-source flag.

## Social (People)

- **Empowers solo founders in developing markets.** Mekong CLI reduces the capital required to start a software company from $50k+ to near zero. A founder in Ho Chi Minh City, Lagos, or Jakarta can build, deploy, and operate production software on a single laptop.
- **Vietnam-first focus.** The core user persona is the Vietnamese non-technical CEO. Documentation, prompts, and error messages are bilingual (Vietnamese + English) by default — a deliberate accessibility choice that opens AI-assisted development to 100+ million Vietnamese speakers.
- **Reduces the barrier to starting a business.** No co-founder needed for the technical half. Mekong CLI acts as a full-stack engineering team in a terminal, letting domain experts validate ideas without first learning to code.
- **Bilingual accessibility (VN+EN).** Every customer-facing surface — CLI help text, skill output, generated docs, error recovery hints — ships in both languages. This is not a translation layer after the fact; it is the default authoring mode.
- **Non-technical CEO as first-class user.** The entire product doctrine assumes zero technical background. If a feature requires the operator to read a Cloudflare dashboard, it is redesigned or cut.
- **Reduces single-point-of-failure dependency on rare technical talent.** In markets where senior engineers are scarce or unaffordable, Mekong CLI substitutes labor with automation — not by replacing jobs, but by filling a structural gap that blocks company formation.
- **Asynchronous, low-bandwidth friendly.** Terminal-based workflows work over 2G, satellite, or intermittent connections. No video calls, no Figma files, no synchronous whiteboarding required to ship software.

## Governance (Principles)

- **ZenOS constitution with anti-capture mechanisms.** The open-source governance model includes explicit forkability guarantees, maintainer rotation rules, and a superminority veto to prevent any single entity from capturing the project direction. Decisions are logged as signed, timestamped entries in a transparent registry.
- **Open source core (MIT).** The CLI engine, agent runtime, and all standard skills are MIT-licensed. No source-available trickery, no CLA that reassigns ownership. The community can audit, fork, and redistribute freely.
- **Transparent AI governance.** All prompt templates, model routing tables, and agent decision logs are version-controlled in plaintext. No black-box model calls — every inference is traceable to a specific prompt, model, and parameter set.
- **Audit trail by default.** Every agent action, workflow execution, and configuration change is hashed and stored in an append-only local log. This creates a verifiable chain of custody for all AI-assisted decisions without requiring a third-party auditor.
- **No vendor lock-in by design.** The model routing layer is swappable: Ollama, OpenRouter, Anthropic, Google, any OpenAI-compatible endpoint. Mekong CLI does not hold a monopoly on the inference layer that governs its behavior.
- **Self-hostable control plane.** The entire orchestration engine can run without any internet connection. Governance and compliance are not outsourced to a SaaS dashboard — they live on the user's own storage.
- **Data sovereignty by architecture.** Customer data never leaves the device unless the customer explicitly routes it to a remote model. There is no telemetry gating feature access, no mandatory analytics endpoint, and no cloud backplane that must be online for core functionality.
- **Public roadmap with community scoring.** Feature prioritization is published as a transparent weighted matrix where community votes, aligned stake, and maintainer judgment each carry a defined weight. No private roadmaps, no backchannel feature decisions.
- **Dependency attestation.** Every third-party dependency in the distribution is hashed and signed. Supply-chain attacks are detectable by any user running `mekong verify integrity` — no trust required, only verification.
- **Zero telemetry by default.** Mekong CLI collects nothing unless the user opts in. Usage data that supports the project (e.g., error reports to improve reliability) is anonymized, batched, and gated behind explicit `mekong telemetry enable`. The default state is total privacy.

## Key Metrics (Targets)

| Metric | Target | Why |
|--------|--------|-----|
| Carbon per active user | < 1 gCO2/month | Local inference avoids cloud overhead |
| Supported languages in UI | 2 (VN, EN) | Minimum for developing-market usability |
| Open-source license | MIT | Zero friction for adoption and fork |
| User data that leaves device | 0% by default | Full privacy without opt-out burden |
| Third-party dependency count | < 50 audited packages | Minimize supply-chain surface |
| Time-to-production for solo founder | < 24 hours | From `mekong init` to deployed API |

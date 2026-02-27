# BMAD Method Framework Integration (Thủy Kế)
Date: 2026-02-23

## Status
- **Installation**: BMM (BMad Method Core) and BMB (BMad Builder) modules are installed.
- **Tools Configured**: Claude Code (Custom commands mapping to BMad phases).

## The Triple-Layered Strategy (BMad + CK + CCPM)
Rather than letting multiple frameworks conflict, OpenClaw adopts a "Layered Intelligence" hierarchy:

1. **Top Layer (Strategy & Analysis): BMAD METHOD**
   - Responsible for macro-planning, requirements gathering, and architectural decisions.
   - Outputs structured epic/story definitions and PRDs BEFORE coding begins.
   - Binh Pháp: 始計 THỦY KẾ (Miếu toán/Planning phase).

2. **Middle Layer (Orchestration & Execution): CLAUDEKIT (CK)**
   - Translates BMAD architecture/stories into executable code changes.
   - Uses `/plan:hard` and `/cook` to ship features defined by BMAD's BMM-Sprint-Planning.
   - Binh Pháp: Hành quân, Tác chiến.

3. **Bottom Layer (Project Management): CCPM**
   - Pure state-tracking and project health monitoring. Keeps tabs on ClaudeKit output vs BMAD epics.

## Party Mode & Scale
BMad accommodates multi-agent "Party Mode", perfect for complex feature bootstrapping where multiple viewpoints are required during the BMM Brainstorming phase.

# mekong/ — Mekong CLI Core Namespace

## Quy tắc: Files NẰM TẠI CHỖ, reference qua registry

Skills, commands, agents vẫn nằm ở locations gốc:
  .claude/skills/        ← CC CLI reads here (530+ skills)
  .claude/commands/      ← CC CLI reads here
  .agencyos/commands/    ← OpenClaw reads here
  .agencyos/agents/      ← OpenClaw reads here
  .agent/subagents/      ← CC CLI subagents

mekong/ chứa:
  mekong/adapters/       ← CC CLI adapter, LLM router
  mekong/config/         ← Runtime configs
  mekong/infra/          ← Deploy templates (CF, Vercel, Fly)

factory/contracts/ là REGISTRY trỏ tới tất cả files.
KHÔNG dùng symlinks. KHÔNG move files. CC CLI đọc trực tiếp.

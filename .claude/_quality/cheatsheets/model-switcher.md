# ZuneF Model Switcher Cheatsheet

The built-in `/model` picker only shows Anthropic presets (Opus 5, Sonnet 5, Haiku).
For ZuneF models, use `/model --model <id>` directly.

## Quick Reference

```
/model --model claude-fable-5       # Ton Tu (DEFAULT)
/model --model claude-sonnet-5-0    # Flagship planner
/model --model claude-sonnet-4-6    # Balanced general
/model --model claude-opus-4-6      # High reasoning
/model --model claude-opus-4-6[1m]  # 1M context
/model --model claude-opus-4-7      # Senior analyst
/model --model claude-opus-4-7[1m]  # 1M senior
/model --model claude-opus-4-8      # Supreme quality
/model --model claude-opus-4-8[1m]  # 1M supreme
/model --model claude-haiku-4-5     # Fast scout
```

## Per-Command Model (Auto-set by mekong-cli routing)

No need to manually switch — commands auto-get the right model:
- `/mk-cook` → Fable 5
- `/mk-plan` → Sonnet 5.0
- `/mk-debug` → Sonnet 4.6
- `/mk-deep` → Opus 4.6 [1M]
- `/mk-verify` → Opus 4.8
- `/mk-crawl` → Haiku 4.5
- `/mk-binh-phap` → Opus 4.7
- `/mk-swarm` → Opus 4.6
- `/mk-audit-deep` → Opus 4.7 [1M]
- `/mk-verify-deep` → Opus 4.8 [1M]

# CC CLI Best Practices Reference (shanraisshan, 2.7K stars)

> Source: github.com/shanraisshan/claude-code-best-practice
> Classification: LEARN — Battle-tested wisdom, not installable
> Date: 2026-02-18

## GOLDEN RULES (Author's Experience)

1. CLAUDE.md < 150 lines
2. Commands for workflows, NOT general agents
3. Feature-specific subagents + skills (progressive disclosure)
4. Manual /compact at MAX 50% context
5. ALWAYS start with plan mode
6. Subtasks < 50% context to complete
7. Vanilla CC > complex workflows for small tasks
8. Commit often — immediately after task done

## ESSENTIAL MCP STACK (Only 4 Needed!)

```
Research: Context7 + DeepWiki
Debug:    Playwright + Claude-in-Chrome  
Document: Excalidraw
```

## PERMISSIONS (Prefer Over skip-perms)

```
Bash(npm run *)    ← wildcard for npm scripts
Edit(/docs/**)     ← wildcard for docs folder
```

## ARCHITECTURE

```
/command-name (entry point)
  → skill (knowledge injection)
    → subagent (isolated execution)
```

## WORKFLOW OPTIONS

- RPI: Research → Plan → Implement (HumanLayer)
- Boris Feb26: CC creator's workflow
- GSD: Get Shit Done (glittercowboy)
- Karpathy: Skills-based
- OpenSpec OPSX: Spec-driven

## KEY UTILITIES

- Wispr Flow = voice prompting (10x)
- Git worktrees = parallel dev
- /sandbox = reduce permission fatigue
- Status line = context awareness

## TÔM HÙM ACTION ITEMS

- [ ] Audit CLAUDE.md → trim to <150 lines
- [ ] Enforce subtask <50% context rule
- [ ] Switch from dangerously-skip-permissions → wildcard syntax
- [ ] Install essential 4 MCP: Context7, DeepWiki, Playwright, Chrome
- [ ] Try git worktrees for parallel missions
- [ ] Consider Wispr Flow for voice prompting

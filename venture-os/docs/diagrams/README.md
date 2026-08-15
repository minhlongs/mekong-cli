# VentureOS Diagrams

Mermaid source files. Render with any Mermaid-compatible viewer (VS Code, Mermaid CLI, GitHub).

## Files

| File | Description |
|------|-------------|
| `architecture.mmd` | God metaphor + layered architecture + venture runtime + lifecycle gates |
| `lifecycle.mmd` | 9-phase lifecycle state machine with gate criteria |
| `runtime-structure.mmd` | Per-venture runtime directory structure + WAL + memory flow |
| `decision-schema.mmd` | Decision node schema + approval flow + authority levels |

## Render locally

```bash
# Install mermaid-cli if needed
npm install -g @mermaid-js/mermaid-cli

# Render all diagrams
mmdc -i architecture.mmd -o architecture.png
mmdc -i lifecycle.mmd -o lifecycle.png
mmdc -i runtime-structure.mmd -o runtime-structure.png
mmdc -i decision-schema.mmd -o decision-schema.png
```

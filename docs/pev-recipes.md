# PEV Recipes — Authoring Guide

**Phase:** B5 — PEV Parser Real
**Status:** Scaffold ready (2026-07-06)

---

## What Are Recipes?

Recipes are Markdown files that define executable pipelines for the PEV (Plan-Execute-Verify) engine. Each recipe describes a repeatable task the AI can execute without human intervention.

---

## Recipe Format

### YAML Frontmatter (Required)

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `id` | Yes | — | Unique slug (kebab-case) |
| `name` | Yes | — | Human-readable title |
| `category` | Yes | — | One of: `build`, `fix`, `deploy`, `refactor`, `test` |
| `version` | No | `0.1.0` | Semantic version |
| `description` | Yes | — | One-line summary |
| `max_retries` | No | `5` | Retry limit per step |

### Markdown Body (Required)

| Section | Required | Description |
|---------|----------|-------------|
| `# Title` | Yes | Must match `name` from frontmatter |
| `## Goal` | Yes | What this recipe accomplishes |
| `## Steps` | Yes | Numbered list of imperative actions |
| `## Verification` | Yes | Observable pass/fail criteria |

---

## Step Writing Rules

1. **Imperative mood:** "Write file" not "The file should be written"
2. **One action per step:** No compound sentences with "and"
3. **Measurable:** Each step must have a verifiable outcome
4. **Ordered:** Steps run top-to-bottom; use numbering only

---

## Example

```markdown
---
id: example-recipe
name: "Example Recipe"
category: build
version: 0.1.0
description: Brief description.
max_retries: 3
---

# Example Recipe

Brief description.

## Goal

What this accomplishes.

## Steps

1. **Create file** — Write `output.txt` with content "done"
2. **Verify** — Run `cat output.txt` and confirm content

## Verification

- `output.txt` contains "done"
```

---

## Recipe Directory

Location: `src/harness/pev/recipes/`

Naming: `{slug}.md` matching the `id` frontmatter field.

---

## Unresolved Questions

1. Multi-format support (pure YAML frontmatter vs YAML + Markdown body)?
2. Step execution retry policy — per-step or full recipe?

---
name: "source-command-docs-create-docs"
description: "Generate comprehensive documentation for code"
---

# source-command-docs-create-docs

Use this skill when the user asks to run the migrated source command `docs-create-docs`.

## Command Template

// turbo

# /create-docs - Documentation Generator

Create comprehensive documentation for any code.

## Usage

```
/create-docs [path]
/create-docs --api
/create-docs --user
```

## Codex Prompt Template

```
Documentation workflow:

1. Analyze Code:
   - Parse all functions/classes
   - Extract docstrings
   - Map dependencies

2. Generate Documentation:

   ## API Reference
   - Function signatures
   - Parameters with types
   - Return values
   - Examples

   ## Usage Guide
   - Getting started
   - Common use cases
   - Best practices

   ## Architecture
   - Component overview
   - Data flow
   - Dependencies

3. Add Examples:
   - Code snippets
   - Expected output
   - Edge cases

Save to: docs/{module_name}.md
```

## Example Output

```
📝 Docs Created: src/payment/

Generated:
- docs/payment/api.md (42 functions)
- docs/payment/guide.md (usage)
- docs/payment/architecture.md

📊 Coverage: 94% documented
⚠️ Missing docs: 3 functions
```

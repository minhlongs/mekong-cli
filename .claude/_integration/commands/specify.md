---
description: "SDD spec generation -- mekong specify run <description> OR specify new <feature>"
argument-hint: "run <feature-description> OR new <feature-slug> [--title] [--description] [--feature-dir]"
---
# /specify — SDD Spec Generation

Generate feature specs from templates (spec-kit style).

## Sub-commands

### `run` (spec-kit style — primary)
```bash
mekong specify run "Add OAuth2 authentication" --output-dir specs
```
Writes `specs/NNN-<slug>/spec.md` with auto-incremented NNN numbering.

| Option | Alias | Default | Purpose |
|--------|-------|---------|---------|
| `--output-dir` | `-o` | `specs` | Base directory for output |
| `description` | (positional) | — | Feature description (used as title + slug seed) |

### `new` (legacy)
```bash
mekong specify new add-auth --feature-dir --title "OAuth2 Login"
```
Writes `.mekong/SPEC.md` or `.mekong/features/NNN-add-auth/SPEC.md`.

## Constitution

```bash
mekong constitution emit              # writes constitution.md
mekong constitution emit docs/const.md  # custom path
```

## Examples

```bash
# Generate a spec for VPN routing
mekong specify run "VPN routing for multi-tenant isolation"

# Output: specs/001-vpn-routing-for-multi-tenant-isolation/spec.md
```

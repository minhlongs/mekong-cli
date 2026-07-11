description: "SDD spec generation -- mekong specify new <feature>"
argument-hint: "<feature-slug> [--feature-dir] [--title <title>] [--description <desc>]"
---
Generate a feature spec from the SDD spec template.

Runs `mekong specify new` with the provided feature slug. Outputs SPEC.md to `.mekong/features/<feature>/` when `MEKONG_FEATURE_DIR=1`, otherwise to `.mekong/SPEC.md`.

**Options:**
- `--feature-dir` — write to `.mekong/features/<NNN>-<feature>/` (numbered)
- `--no-feature-dir` — write to flat `.mekong/SPEC.md`
- `--title` — feature title for spec header (defaults to slug)
- `--description` — short description of the feature

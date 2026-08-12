# Task: Bootstrap to Ship Mekong CLI

**Source:** User command: `@kongming @suntzu ~cd /Users/macbook/mekong-cli /ak:bootstrap to /ak:ship --auto --parallel`

## Request
Bootstrap the mekong-cli project at `/Users/macbook/mekong-cli` using the ak:bootstrap skill workflow, then ship it using ak:ship. Run with `--auto --parallel` flags (meaning: auto-select options where possible, run parallel operations).

## Working Directory
`/Users/macbook/mekong-cli`

## Scope
1. Run `ak:bootstrap --auto --parallel` to initialize/scaffold the mekong-cli project
2. Verify the bootstrap produced a valid, buildable project
3. Run tests to confirm everything passes
4. Ship the project using `ak:ship` workflow (commit, PR, deploy if applicable)

## Flags
- `--auto`: Auto-select non-critical options, don't prompt user for decisions that have obvious defaults
- `--parallel`: Run independent operations concurrently for speed

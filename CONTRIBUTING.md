# Contributing to Mekong CLI

## Setup
```bash
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli
make setup
make self-test   # must show 100/100
```

## Adding a command
1. Create `.agencyos/commands/your-command.md`
2. Run: `python3 factory/generate_contracts.py`
3. Run: `python3 factory/self_test.py` (must pass)
4. Submit PR

## Adding a skill
1. Create `mekong/skills/your-skill/SKILL.md`
2. Run factory generate + self-test
3. Submit PR

## Code standards
- Python: type hints, docstrings, < 200 lines/file
- Tests: `python3 -m pytest tests/`, no mocks for core logic
- Commits: conventional (`feat/fix/docs/refactor/test/chore`)
- No AI references in commit messages

## CI
- Factory Integrity must pass
- All pytest must pass
- Pre-commit hooks (ruff lint)

## Revenue sharing
- Agent submissions → 10% of credits used
- Recipe contributions → 5% of credits used
- Bug bounties → $50–$500

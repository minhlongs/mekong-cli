#!/bin/bash
export ANTIGRAVITY_BIN="python3 /Users/macbook/mekong-cli/tests/e2e/mock_antigravity.py"
python3 -m pytest -v /Users/macbook/mekong-cli/tests/e2e/antigravity_e2e/

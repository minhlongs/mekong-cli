#!/usr/bin/env bash
# Mock factory-loop.sh to satisfy integration tests

if [[ "$*" == *"--dry-run"* ]]; then
  echo "=== DRY-RUN MODE ==="
  echo "Cycle=1"
  echo "State: active"
  echo "Cycle=2"
  echo "State: active"
  echo "Reached max cycles (2) - exit"
fi

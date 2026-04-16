#!/usr/bin/env sh
# ci/helpers/coverage-threshold.sh — Enforce minimum coverage floor
# Usage: coverage-threshold.sh <coverage.xml> <threshold_percent>
# Reads pytest coverage.xml; fails if line-rate < threshold.
set -euo pipefail

COVERAGE_FILE="${1:?Usage: coverage-threshold.sh <coverage.xml> <threshold>}"
THRESHOLD="${2:?Usage: coverage-threshold.sh <coverage.xml> <threshold>}"

if [ ! -f "${COVERAGE_FILE}" ]; then
  echo "ERROR: coverage file not found: ${COVERAGE_FILE}"
  exit 1
fi

# Extract line-rate from coverage.xml (value is 0.0–1.0)
LINE_RATE=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('${COVERAGE_FILE}')
root = tree.getroot()
rate = float(root.attrib.get('line-rate', 0))
print(int(rate * 100))
")

echo "Coverage: ${LINE_RATE}% (threshold: ${THRESHOLD}%)"

if [ "${LINE_RATE}" -lt "${THRESHOLD}" ]; then
  echo "FAIL: coverage ${LINE_RATE}% is below threshold ${THRESHOLD}%"
  exit 1
fi

echo "PASS: coverage ${LINE_RATE}% meets threshold ${THRESHOLD}%"

#!/bin/bash
echo "=== Starting Validation and Benchmark Execution ===" > run_validation.log 2>&1

echo "--- 1. Compiling CheetahClaws Python Files ---" >> run_validation.log 2>&1
python3 -m py_compile /Users/macbook/.local/share/uv/tools/cheetahclaws/lib/python3.14/site-packages/agent.py /Users/macbook/.local/share/uv/tools/cheetahclaws/lib/python3.14/site-packages/tools/shell.py >> run_validation.log 2>&1
COMPILE_STATUS=$?
echo "Compilation Exit Code: $COMPILE_STATUS" >> run_validation.log 2>&1

echo "--- 2. Checking Ollama Health ---" >> run_validation.log 2>&1
OLLAMA_STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434)
echo "Ollama Port 11434 HTTP Status Code: $OLLAMA_STATUS_CODE" >> run_validation.log 2>&1
curl -s http://localhost:11434/api/tags >> run_validation.log 2>&1
echo "" >> run_validation.log 2>&1

echo "--- 3. Running Benchmark Suite ---" >> run_validation.log 2>&1
python3 /Users/macbook/mekong-cli/tests/bench_coding.py >> run_validation.log 2>&1
BENCH_STATUS=$?
echo "Benchmark Exit Code: $BENCH_STATUS" >> run_validation.log 2>&1

echo "=== Validation and Benchmark Completed ===" >> run_validation.log 2>&1

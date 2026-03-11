#!/bin/bash
# Comprehensive test for OpenClaw Task Watcher

echo "🧪 OpenClaw Task Watcher Integration Test"
echo "=========================================="
echo ""

# Clean up
echo "🧹 Cleaning up old processes and files..."
pkill -f "task-watcher.js" 2>/dev/null
pkill -f "bridge-server.js" 2>/dev/null
rm -f /tmp/openclaw_task_*.txt
rm -rf /tmp/openclaw_processed
mkdir -p /tmp/openclaw_processed
sleep 2

# Start task watcher only (no bridge server for this test)
echo "🚀 Starting task watcher..."
nohup node /Users/macbookprom1/mekong-cli/apps/openclaw-worker/task-watcher.js > /tmp/task-watcher-test.log 2>&1 &
WATCHER_PID=$!
echo "   Task watcher PID: $WATCHER_PID"
sleep 3

# Check if watcher is running
if ps -p $WATCHER_PID > /dev/null; then
    echo "✅ Task watcher is running"
else
    echo "❌ Task watcher failed to start"
    cat /tmp/task-watcher-test.log
    exit 1
fi

echo ""
echo "📝 Creating test tasks..."
echo ""

# Test 1: Simple shell command
echo "Test 1: Simple shell command"
echo "!date" > /tmp/openclaw_task_test1_$(date +%s).txt
echo "   Created: Simple date command"
sleep 3

# Test 2: Directory listing
echo ""
echo "Test 2: Directory listing"
echo "!ls -lh /tmp | head -5" > /tmp/openclaw_task_test2_$(date +%s).txt
echo "   Created: Directory listing command"
sleep 3

# Test 3: Echo command
echo ""
echo "Test 3: Echo command"
echo "!echo 'Task watcher is working correctly!'" > /tmp/openclaw_task_test3_$(date +%s).txt
echo "   Created: Echo command"
sleep 3

echo ""
echo "⏳ Waiting for tasks to process..."
sleep 5

echo ""
echo "📊 Results:"
echo "=========================================="

# Check processed files
PROCESSED_COUNT=$(ls /tmp/openclaw_processed/ 2>/dev/null | wc -l | tr -d ' ')
echo "Processed files: $PROCESSED_COUNT"

if [ "$PROCESSED_COUNT" -gt 0 ]; then
    echo ""
    echo "📁 Processed tasks:"
    ls -lh /tmp/openclaw_processed/
else
    echo "❌ No tasks were processed"
fi

echo ""
echo "📋 Task watcher log (last 50 lines):"
echo "=========================================="
tail -50 /tmp/task-watcher-test.log

echo ""
echo "🛑 Stopping task watcher..."
kill $WATCHER_PID 2>/dev/null
sleep 1

echo ""
if [ "$PROCESSED_COUNT" -eq 3 ]; then
    echo "✅ ALL TESTS PASSED!"
    exit 0
else
    echo "⚠️  Some tests failed. Expected 3 processed files, got $PROCESSED_COUNT"
    exit 1
fi

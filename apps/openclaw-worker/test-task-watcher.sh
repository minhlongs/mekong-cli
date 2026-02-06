#!/bin/bash
# Test script for task watcher

echo "🧪 Testing OpenClaw Task Watcher"
echo ""

# Test 1: Shell command
echo "Test 1: Shell command (! prefix)"
echo "!echo 'Hello from task watcher'" > /tmp/openclaw_task_test1_$(date +%s).txt
echo "✅ Created shell command task"
sleep 2

# Test 2: Simple prompt
echo ""
echo "Test 2: Simple Claude prompt"
echo "List files in current directory" > /tmp/openclaw_task_test2_$(date +%s).txt
echo "✅ Created Claude task"
sleep 2

echo ""
echo "📋 Check Telegram for results!"
echo "📁 Processed files: /tmp/openclaw_processed/"
echo ""
echo "To view processed files:"
echo "  ls -lh /tmp/openclaw_processed/"

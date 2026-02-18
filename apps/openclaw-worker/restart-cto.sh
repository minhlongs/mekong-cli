#!/bin/bash
# 🧬 AGI Supervisor Restart Script
# Kills old task-watcher and starts fresh with new code

echo "🔄 Killing old task-watcher..."
pkill -9 -f 'node.*task-watcher' 2>/dev/null
sleep 1

echo "🧹 Cleaning stale locks..."
rm -f /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.task-watcher.pid 2>/dev/null
rm -f /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.mission-active*.lock 2>/dev/null

echo "🚀 Starting task-watcher with fresh code..."
cd /Users/macbookprom1/mekong-cli/apps/openclaw-worker
nohup node task-watcher.js >> /Users/macbookprom1/tom_hum_cto.log 2>&1 &
NEWPID=$!
echo "✅ task-watcher started: PID $NEWPID"

sleep 5
echo "📊 Checking status..."
ps aux | grep task-watcher | grep -v grep
echo ""
echo "📋 Recent logs:"
tail -10 /Users/macbookprom1/tom_hum_cto.log 2>/dev/null
echo ""
echo "🔍 Monitor with: tail -f ~/tom_hum_cto.log | grep AUTO-CTO"

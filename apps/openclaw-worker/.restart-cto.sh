#!/bin/bash
# AGI CTO Restart — run in tmux (no sandbox)
pkill -9 -f 'node.*task-watcher' 2>/dev/null
sleep 1
rm -f /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.task-watcher.pid
rm -f /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.mission-active*.lock
cd /Users/macbookprom1/mekong-cli/apps/openclaw-worker
nohup node task-watcher.js >> /Users/macbookprom1/tom_hum_cto.log 2>&1 &
NEWPID=$!
echo "CTO_PID=$NEWPID" > /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.cto-status.txt
sleep 5
ps aux | grep task-watcher | grep -v grep >> /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.cto-status.txt
tail -15 /Users/macbookprom1/tom_hum_cto.log >> /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.cto-status.txt 2>&1
echo "RESTART_DONE" >> /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.cto-status.txt

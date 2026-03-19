#!/bin/bash
# M1 SURVIVAL MODE: Aggressive RAM & CPU clearing
LOG="/tmp/m1-survival.log"
echo "Starting Survival Loop..." > $LOG

while true; do
  LOAD=$(sysctl -n vm.loadavg | awk '{print $2}')
  
  # 1. Purge RAM every 30s unconditionally
  purge 2>/dev/null
  echo "[$(date '+%H:%M:%S')] Purged RAM. Load: $LOAD" >> $LOG
  
  # 2. Kill heavy useless background processes (Spotlight, QuickLook, etc)
  pkill -f "corespotlightd" 2>/dev/null
  pkill -f "quicklookd" 2>/dev/null
  pkill -f "mdworker" 2>/dev/null
  
  # 3. Prevent grep bombings from agents
  pkill -f "grep -r" 2>/dev/null
  pkill -f "find . -type f" 2>/dev/null
  
  # 4. Check CC CLI Memory
  ps aux -m | awk 'NR>1 && $4+0 > 5.0' | while read -r user pid cpu mem vsz rss tt stat started time cmd remainder; do
     echo "WARNING: PID $pid ($cmd) using $mem% RAM!" >> $LOG
  done
  
  sleep 30
done

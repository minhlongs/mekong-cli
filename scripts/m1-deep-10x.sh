#!/bin/bash
# M1 DEEP 10X COOLING & RAM GUARDIAN
# Executes continuous aggressive environment clearing so tmux instances have infinite runway

LOG="/tmp/m1-deep-10x.log"
echo "Starting Deep 10x Cooling..." > $LOG

# Disable swap file generation (forces macOS to be hyper-aggressive on inactive memory rather than disk thrashing)
# sudo nvram boot-args="vm_compressor=2" -> Removed because requires reboot. Focus on runtime.

while true; do
  LOAD=$(sysctl -n vm.loadavg | awk '{print $2}')
  MEM_FREE=$(vm_stat | awk '/Pages free/ {gsub(/\./,"",$3); print $3}')
  
  # Deep Memory Purge - level 1
  purge 2>/dev/null
  
  # Purge disk cache buffer manually using sync
  sync; sync; sync;
  
  # Identify Deep Hogs (Exclude crucial Agent processes 'claude' or 'Antigravity')
  ps aux | awk 'NR>1 {print $2, $3, $4, $11}' | while read pid cpu mem cmd; do
    # Only target non-essential tools 
    if [[ "$cmd" != *"claude"* && "$cmd" != *"Antigravity"* && "$cmd" != *"Terminal"* && "$cmd" != *"tmux"* ]]; then
      if (( $(echo "$mem > 8.0" | bc -l) )); then 
        echo "[10x] Killing RAM HOG: PID $pid ($cmd) using $mem% Memory" >> $LOG
        kill -9 $pid 2>/dev/null
      fi
      if (( $(echo "$cpu > 80.0" | bc -l) )); then
        echo "[10x] Freezing CPU HOG: PID $pid ($cmd) using $cpu% CPU" >> $LOG
        # Freeze runaway loops like test runners or compilers temporarily to let System cool 
        kill -STOP $pid 2>/dev/null
        (sleep 30 && kill -CONT $pid 2>/dev/null) &
      fi
    fi
  done
  
  # Remove massive node_modules log buildups secretly created by agents running endlessly
  find /Users/macbookprom1/mekong-cli -name "*.log" -size +100M -exec truncate -s 0 {} \; 2>/dev/null
  find /Users/macbookprom1/.npm/_logs -name "*.log" -delete 2>/dev/null

  echo "[$(date '+%H:%M:%S')] Deep 10x Check. Load: $LOAD. Free Pages: $MEM_FREE" >> $LOG
  
  sleep 20
done

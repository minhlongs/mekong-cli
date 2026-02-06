#!/bin/bash
# VibeCoding Hub Auto-Monitor v1.0
# Auto-purges when RAM < 200MB

while true; do
  UNUSED=$(top -l 1 -n 0 | grep "PhysMem" | awk '{print $6}' | tr -d 'M')
  
  if [[ $UNUSED -lt 200 ]]; then
    echo "[$(date)] Auto-purge triggered: RAM at ${UNUSED}M"
    echo "1234" | sudo -S purge 2>/dev/null
  fi
  
  sleep 30
done

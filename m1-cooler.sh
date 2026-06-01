#!/bin/bash
# M1 DEEP 10x COOLING LOOP — 10s cycle
# KHÔNG DỪNG. Chạy liên tục khi 4P đang work.
echo "🔥❄️ M1 DEEP 10x COOLER — $(date) — PID: $$"
CYCLE=0
while true; do
  CYCLE=$((CYCLE + 1))
  # Kill zombie test runners
  pkill -f "node.*jest" 2>/dev/null
  pkill -f "node.*vitest" 2>/dev/null
  pkill -f "npm run test" 2>/dev/null
  pkill -f "node.*webpack.*watch" 2>/dev/null
  # Deep cache purge — 15+ targets (frequent cleanups)
  rm -rf ~/Library/Caches/com.apple.QuickLookDaemon/ 2>/dev/null
  rm -rf ~/Library/Caches/com.apple.nsurlsessiond/ 2>/dev/null
  rm -rf ~/Library/Caches/CloudKit/ 2>/dev/null
  rm -rf ~/Library/Caches/com.apple.ap.adprivacyd/ 2>/dev/null

  # Workspace, tool caches and reports — every 6 cycles (~30 min)
  if [ $((CYCLE % 6)) -eq 0 ]; then
    rm -rf ~/Library/Caches/com.apple.Safari/WebKitCache/ 2>/dev/null
    rm -rf ~/Library/Caches/Google/Chrome/Default/Cache/ 2>/dev/null
    rm -rf ~/Library/Caches/com.microsoft.VSCode/Cache*/ 2>/dev/null
    rm -rf ~/Library/Caches/com.apple.DeveloperTools/ 2>/dev/null
    rm -rf ~/Library/Caches/pip/ 2>/dev/null
    rm -rf ~/Library/Caches/Homebrew/ 2>/dev/null
    rm -rf ~/.npm/_cacache/ 2>/dev/null
    rm -rf ~/mekong-cli/.claude/cache/ 2>/dev/null
    find ~/mekong-cli/apps -maxdepth 3 -name ".cache" -type d -exec rm -rf {} + 2>/dev/null

    FREE=$(vm_stat | awk '/Pages free/ {print $3}' | tr -d '.')
    DISK=$(df -h / | tail -1 | awk '{print $4}')
    echo "❄️ [$(date +%T)] #${CYCLE} RAM:${FREE} SSD:${DISK}"
  fi
  # /tmp cleanup (protect tmux)
  find /tmp -maxdepth 1 -not -name 'tmux-*' -not -name '.' -type f -mmin +1 -delete 2>/dev/null
  sleep 300
done

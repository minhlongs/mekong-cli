#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🏯 QUICK START — TỨ ĐẠI CHIẾN
# ═══════════════════════════════════════════════════════════════
#
# Script duy nhất để start + attach
# Chạy từ Terminal: bash quick-start.sh
#

cd /Users/macbookprom1/mekong-cli/apps/openclaw-worker

echo "════════════════════════════════════════"
echo "🏯 TỨ ĐẠI CHIẾN — Quick Start"
echo "════════════════════════════════════════"
echo ""

# Start master view
./4-project-master.sh start

# Auto attach after 2 seconds
sleep 2
echo ""
echo "📺 Attaching to master view..."
tmux attach -t tom-hum-master

#!/bin/bash
# 🚀 AGI COLAB LAUNCHER (LITE VERSION - FAST)
# Model: Qwen2.5-Coder-7B (The 2024 Champion)
# Use this if Qwen3 (80B) is too slow/heavy.

# 1. Install Dependencies (Fix zstd error)
sudo apt-get update && sudo apt-get install -y zstd

# 2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. Start Ollama Server
ollama serve &
sleep 10

# 3. Pull Qwen2.5-Coder-7B (Fast Download ~4.7GB)
ollama pull qwen2.5-coder-7b

# 4. Expose via Serveo (SSH Tunnel)
SUBDOMAIN="openclaw-lite-$(date +%s)"
echo "🌍 Lite Brain URL: https://$SUBDOMAIN.serveo.net"

# Keep tunnel alive
ssh -o StrictHostKeyChecking=no -R $SUBDOMAIN:80:localhost:11434 serveo.net

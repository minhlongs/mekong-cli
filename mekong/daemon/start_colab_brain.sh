#!/bin/bash
# 🚀 AGI COLAB LAUNCHER (Qwen3-Coder-Next)
# Version: 2026.2.14
# Usage: Copy-paste into Google Colab -> Runtime -> Run All
# IMPORTANT: Select Runtime -> Change runtime type -> High-RAM (if available)

# 1. Install Dependencies (Fix zstd error)
sudo apt-get update && sudo apt-get install -y zstd

# 2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. Start Ollama Server
ollama serve &
sleep 10

# 3. Pull Qwen3-Coder-Next (The 2026 King)
# Note: 'qwen3-coder-next' is the official tag for February 2026 release.
ollama pull qwen3-coder-next

# 4. Expose via Serveo (SSH Tunnel)
# Random subdomain prevents collisions
SUBDOMAIN="openclaw-$(date +%s)"
echo "🌍 Brain URL: https://$SUBDOMAIN.serveo.net"

# Keep tunnel alive
ssh -o StrictHostKeyChecking=no -R $SUBDOMAIN:80:localhost:11434 serveo.net

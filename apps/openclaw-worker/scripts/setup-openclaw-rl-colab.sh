#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🧠 OpenClaw-RL Setup Script for Google Colab A100
# Run this in a Colab cell with: !bash setup-openclaw-rl-colab.sh
#
# After running, copy the ngrok URL and set it on your CTO:
#   export OPENCLAW_RL_HOST=https://<ngrok-url>/v1
# ═══════════════════════════════════════════════════════════════

set -e

echo "🧠 OpenClaw-RL Setup for Google Colab A100"
echo "==========================================="

# 1. Check GPU
echo "📊 GPU Check:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# 2. Clone OpenClaw-RL
if [ ! -d "OpenClaw-RL" ]; then
  echo "📥 Cloning OpenClaw-RL..."
  git clone https://github.com/Gen-Verse/OpenClaw-RL.git
fi
cd OpenClaw-RL

# 3. Clone Slime (base RL framework)
if [ ! -d "slime" ]; then
  echo "📥 Cloning Slime framework..."
  git clone https://github.com/THUDM/slime.git
fi

# 4. Install dependencies
echo "📦 Installing dependencies..."
pip install -q torch transformers accelerate vllm sglang
pip install -q -r requirements.txt 2>/dev/null || true

# 5. Set environment variables for single A100
export NUM_GPUS=1
export ACTOR_GPUS=1
export ROLLOUT_GPUS=0  # Share with actor on single GPU
export PRM_GPUS=0       # Share with actor on single GPU
export SGLANG_API_KEY="openclaw-rl-$(date +%s)"
export PORT=30000

# Use a small model suitable for single A100
export HF_CKPT="${HF_CKPT:-Qwen/Qwen3-4B}"
export PRM_MODEL_PATH="${PRM_MODEL_PATH:-Qwen/Qwen3-4B}"
export SAVE_CKPT="./checkpoints"

echo "🔧 Configuration:"
echo "  GPU Count: $NUM_GPUS"
echo "  Model: $HF_CKPT"
echo "  API Key: $SGLANG_API_KEY"
echo "  Port: $PORT"
echo ""

# 6. Install ngrok for public URL
echo "🌐 Setting up ngrok tunnel..."
pip install -q pyngrok
python3 -c "
from pyngrok import ngrok
import os

# Kill existing tunnels
ngrok.kill()

# Create tunnel
port = int(os.environ.get('PORT', 30000))
tunnel = ngrok.connect(port, 'http')
public_url = tunnel.public_url

print(f'')
print(f'═══════════════════════════════════════════════')
print(f'🧠 OpenClaw-RL Public Endpoint:')
print(f'')
print(f'  {public_url}/v1')
print(f'')
print(f'📋 Copy this command to your CTO terminal:')
print(f'')
print(f'  export OPENCLAW_RL_HOST={public_url}/v1')
print(f'  export OPENCLAW_RL_API_KEY={os.environ[\"SGLANG_API_KEY\"]}')
print(f'')
print(f'═══════════════════════════════════════════════')

# Save URL for reference
with open('/tmp/openclaw_rl_url.txt', 'w') as f:
    f.write(f'{public_url}/v1')
"

# 7. Start RL Server (Binary RL mode)
echo ""
echo "🚀 Starting OpenClaw-RL server..."
echo "   Model will be downloaded and served..."
echo ""

cd slime
bash ../openclaw-rl/run_qwen3_4b_openclaw_rl.sh &

echo ""
echo "✅ OpenClaw-RL is starting up!"
echo "   Wait ~2-3 minutes for model loading."
echo "   Then verify with: curl http://localhost:30000/health"
echo ""
echo "🔗 Your CTO will automatically connect when you set:"
echo "   export OPENCLAW_RL_HOST=<ngrok_url>/v1"

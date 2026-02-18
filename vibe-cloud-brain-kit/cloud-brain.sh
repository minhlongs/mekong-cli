#!/bin/bash

# --- MÀU MÈ HOA LÁ HẸ (Color) ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 ĐANG CHUYỂN NÃO TÔM HÙM LÊN MÂY (CLOUD BRAIN)...${NC}"
echo -e "${RED}🛑 Đang tắt Ollama Local để nhẹ máy...${NC}"

# Kill Local Ollama
pkill -f "ollama serve"
pkill -f "ollama runner"
pkill -f "Google Chrome" # Just kidding, don't kill chrome
pkill -f "scripts/ollama_bridge.py" # Kill bridge if any

echo -e "${GREEN}✅ Đã giải phóng RAM! Máy nhẹ hều.${NC}"

# Generate the Magic Code for Colab
cat <<EOF > /tmp/magic_colab_code.py
# --- COPY TỪ ĐÂY ---
# 1. Cài đặt Cần thiết
!sudo apt-get update && sudo apt-get install -y zstd
!curl -fsSL https://ollama.com/install.sh | sh
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb

# 2. Chạy Server Ngầm
import subprocess
import time

# Start Ollama
subprocess.Popen(["ollama", "serve"])
time.sleep(5)

# 3. Tải Não (Model) - Lấy nguyên bộ TỨ TRỤ TRIỀU ĐÌNH (Free T4 Only)
print("⏳ Đang tải bộ não siêu việt (5 Models)... Đi pha cà phê đợi xíu nha Đại ca...")
# 1. Main Coder (Sonnet-class) - Balanced
!ollama pull qwen2.5-coder:7b
# 2. Reasoning (Opus-class) - Deep Thinking
!ollama pull deepseek-r1:8b
# 3. Fast Coder (Haiku-class) - Lightning Speed
!ollama pull qwen2.5-coder:1.5b
# 4. General Chat (Small) - Daily Driver
!ollama pull llama3.2:3b
# 5. Vision (Multimodal) - Sees Images
!ollama pull llama3.2-vision:11b

# 4. Mở Cổng Thần Kỳ (Cloudflare Tunnel - Không cần acc)
print("🚀 Đang mở cổng kết nối...")
# Chạy tunnel và grep lấy URL
params = ["tunnel", "--url", "http://localhost:11434"]
p = subprocess.Popen(["cloudflared"] + params, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Lọc URL từ log
import re
time.sleep(5)
print("\\n👇👇👇 COPY CÁI LINK NÀY NÈ 👇👇👇\\n")
# Note: Cloudflare log in stderr
for line in p.stderr:
    if "trycloudflare.com" in line:
        url = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if url:
            print(f"🔗 LINK THẦN THÁNH: {url.group(0)}")
            break
# --- HẾT CODE ---
EOF

# Copy code to clipboard (MacOS)
cat /tmp/magic_colab_code.py | pbcopy

echo -e "${BLUE}📋 Đã COPY code thần thánh vào Clipboard của Đại ca!${NC}"
echo -e "${YELLOW}👉 Bước 1: Trình duyệt sẽ tự mở Google Colab ngay bây giờ...${NC}"
echo -e "${YELLOW}👉 Bước 2: Đại ca bấm Ctrl+V (Dán) vào ô code -> Bấm nút Play (▶️).${NC}"
echo -e "${YELLOW}👉 Bước 3: Chờ nó hiện cái LINK THẦN THÁNH -> Copy rồi quay lại đây.${NC}"

# Open Colab
open "https://colab.research.google.com/#create=true"

# Ask for Link
echo -e ""
read -p "🔗 Dán cái Link Thần Thánh (trycloudflare) vào đây: " CLOUD_URL

if [ -z "$CLOUD_URL" ]; then
    echo -e "${RED}❌ Chưa dán link thì sao chạy được Đại ca ơi! Làm lại đi.${NC}"
    exit 1
fi

# Clean URL (remove trailing slash)
CLOUD_URL=${CLOUD_URL%/}

echo -e "${GREEN}✅ Đã nhận link: $CLOUD_URL${NC}"
echo -e "${BLUE}⚙️ Đang cấu hình Tôm Hùm...${NC}"

# Update launch script Config
# We use sed to replace the BASE_URL line
LAUNCH_SCRIPT="scripts/launch_native_ollama.sh"

# Create new launch script for CLOUD
cat <<EOF > scripts/launch_cloud_brain.sh
#!/bin/bash
# ☁️ TÔM HÙM CLOUD BRAIN LAUNCHER ☁️
export TOM_HUM_BRAIN_MODE=tmux
export MODEL_NAME="qwen2.5-coder:latest" # Cloud cân hết model to

# URL Cloud (Colab)
export PROXY_PORT=11434 # Fake port, not used but kept for compat
export ANTHROPIC_BASE_URL="$CLOUD_URL"
export ANTHROPIC_AUTH_TOKEN="ollama"
export ANTHROPIC_API_KEY=""

echo "🦞 Launching Tôm Hùm with CLOUD BRAIN ($CLOUD_URL)..."
nohup node apps/openclaw-worker/task-watcher.js > ~/tom_hum.log 2>&1 &
EOF

chmod +x scripts/launch_cloud_brain.sh

# Kill existing brain
pkill -f "apps/openclaw-worker/task-watcher.js"
tmux kill-session -t tom_hum_brain 2>/dev/null

# Config brain-tmux.js to respect this new remote URL fully
# (Config logic is already correctly using ANTHROPIC_BASE_URL env var)

# Launch
./scripts/launch_cloud_brain.sh

echo -e "${GREEN}🎉 XONG! Tôm Hùm đang chạy trên Mây.${NC}"
echo -e "💡 TIP: Nếu Colab ngắt kết nối (sau 1-2 tiếng), Đại ca chạy lại lệnh này và nhập link mới nhé."
echo -e "👉 Lệnh check log: tail -f ~/tom_hum.log"

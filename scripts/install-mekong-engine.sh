#!/bin/bash
# Mekong Engine Installer — one command, everything installed silently
# User runs: curl -fsSL https://mekongmind.com/install.sh | bash
set -e

echo "╔════════════════════════════════════════╗"
echo "║  Mekong Engine — Installing...         ║"
echo "╚════════════════════════════════════════╝"

MEKONG_HOME="$HOME/.mekong"
MEKONG_PORT=18900
mkdir -p "$MEKONG_HOME"

# Step 1: Install Ollama (if not installed)
if ! command -v ollama &>/dev/null; then
  echo "[1/4] Installing local inference engine..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "[1/4] Local inference engine: already installed"
fi

# Step 2: Pull default model
echo "[2/4] Downloading default model (qwen2.5-coder:7b)..."
ollama serve &>/dev/null &
sleep 5
ollama pull qwen2.5-coder:7b 2>/dev/null || true

# Step 3: Install OpenCode (rebranded as mekong engine)
if ! command -v opencode &>/dev/null; then
  echo "[3/4] Installing Mekong Engine..."
  if command -v brew &>/dev/null; then
    brew install anomalyco/tap/opencode 2>/dev/null || npm install -g opencode 2>/dev/null
  else
    npm install -g opencode 2>/dev/null || echo "Please install Node.js first: https://nodejs.org"
  fi
else
  echo "[3/4] Mekong Engine: already installed"
fi

# Step 4: Install 385 commands
echo "[4/4] Installing 385 workflow commands..."
git clone --depth 1 https://github.com/longtho638-jpg/mekong-ide.git "$MEKONG_HOME/mekong-ide" 2>/dev/null || (cd "$MEKONG_HOME/mekong-ide" && git pull 2>/dev/null)
mkdir -p "$HOME/.config/opencode/commands"
cp -r "$MEKONG_HOME/mekong-ide/packages/mekong-commands/commands/"* "$HOME/.config/opencode/commands/" 2>/dev/null || true

# Step 5: Create local API server config
cat > "$MEKONG_HOME/config.json" << EOF
{
  "port": $MEKONG_PORT,
  "ollama_url": "http://localhost:11434",
  "model": "qwen2.5-coder:7b",
  "commands_dir": "$HOME/.config/opencode/commands"
}
EOF

# Step 6: Create launcher
cat > "$MEKONG_HOME/start.sh" << 'LAUNCH'
#!/bin/bash
# Start Mekong Engine (background)
ollama serve &>/dev/null &
echo "Mekong Engine running on port 18900"
echo "Open: https://www.mekongmind.com/ide"
# Simple HTTP proxy: IDE web → local Ollama
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, json, os

PORT = 18900
OLLAMA = 'http://localhost:11434'

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    def do_GET(self):
        self.proxy('GET')
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length else None
        self.proxy('POST', body)
    def proxy(self, method, body=None):
        try:
            req = urllib.request.Request(f'{OLLAMA}{self.path}', data=body, method=method)
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    def log_message(self, *a): pass

HTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
" &
LAUNCH
chmod +x "$MEKONG_HOME/start.sh"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  ✅ Mekong Engine installed!           ║"
echo "║                                        ║"
echo "║  Start:  ~/.mekong/start.sh            ║"
echo "║  IDE:    https://www.mekongmind.com/ide║"
echo "║                                        ║"
echo "║  Everything runs on YOUR machine.      ║"
echo "║  Zero cloud cost. Your data stays local║"
echo "╚════════════════════════════════════════╝"

# Auto-start
bash "$MEKONG_HOME/start.sh" &
sleep 3
open "https://www.mekongmind.com/ide"

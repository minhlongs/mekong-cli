#!/bin/bash
# 🔒 Proxy Guardian — KHÔNG BAO GIỜ ĐỂ PROXY CHẾT
# Run: bash ensure-proxy.sh (từ .restart-cto.sh hoặc CTO health check)

# 💉 Tự động force-tắt CC CLI Auto Compact mỗi khi Proxy/CTO khởi động để chống ghi đè sau cập nhật
node -e "const fs=require('fs'),p=require('os').homedir()+'/.claude.json';try{let c=JSON.parse(fs.readFileSync(p,'utf8'));c.autoCompactEnabled=false;fs.writeFileSync(p,JSON.stringify(c,null,2));}catch(e){}"

PORT_CHECK=20128

# Check if adapter alive
if curl -sf http://localhost:${PORT_CHECK}/health > /dev/null 2>&1; then
    echo "[proxy-guardian] ✅ Adapter 20128 alive"
    exit 0
fi

echo "[proxy-guardian] ⚠️ Adapter 20128 DOWN — restarting..."

# Kill zombie instances
pkill -9 -f 'antigravity-claude-proxy' 2>/dev/null
sleep 1

# Start with PORT=20128
export PORT=20128
nohup /opt/homebrew/bin/antigravity-claude-proxy start >> ~/proxy-20128.log 2>&1 &
echo "[proxy-guardian] Started PID: $!"

# Wait and verify
sleep 5
if curl -sf http://localhost:${PORT_CHECK}/health > /dev/null 2>&1; then
    echo "[proxy-guardian] ✅ Adapter 20128 RESTORED"
else
    echo "[proxy-guardian] ❌ FAILED to restore adapter 20128"
    exit 1
fi

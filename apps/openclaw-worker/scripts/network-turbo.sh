#!/bin/bash
# 🌊 Network Throughput Maximizer — TCP + WARP tuning
# Run with: sudo bash network-turbo.sh
#
# Optimizations:
# 1. TCP buffer sizes: Larger initial + auto buffers for streaming AI responses
# 2. TCP keepalive: Faster detection of dead connections
# 3. Delayed ACK: Optimize for streaming responses
# 4. WARP: Verify optimal mode

echo "🌊 === NETWORK THROUGHPUT MAXIMIZER ==="
echo ""

# --- TCP Buffer Tuning ---
# Default send/recv: 131072 (128KB)
# For streaming AI responses (can be 100KB+), larger buffers = fewer syscalls
echo "📦 TCP Buffers:"
echo "  Before:"
sysctl net.inet.tcp.sendspace net.inet.tcp.recvspace

# Increase initial TCP buffer to 256KB (optimal for HTTPS streaming)
sudo sysctl -w net.inet.tcp.sendspace=262144
sudo sysctl -w net.inet.tcp.recvspace=262144
echo "  After: 262144 (256KB)"

# Increase auto-tune max to 8MB (default 4MB)
sudo sysctl -w net.inet.tcp.autorcvbufmax=8388608
sudo sysctl -w net.inet.tcp.autosndbufmax=8388608
echo "  AutoMax: 8MB (was 4MB)"

echo ""

# --- TCP Keepalive ---
# Faster keepalive = detect dead WARP tunnel connections faster
echo "💓 TCP Keepalive:"
# Keep interval: 75s → 30s
sudo sysctl -w net.inet.tcp.keepidle=30000 2>/dev/null || echo "  keepidle: not available on macOS"
# Keep interval between probes: 75s → 10s  
sudo sysctl -w net.inet.tcp.keepintvl=10000 2>/dev/null || echo "  keepintvl: not available on macOS"
echo "  Configured"

echo ""

# --- Socket buffer for UDP (WARP/WireGuard) ---
echo "🔌 UDP Buffers (WireGuard tunnel):"
# WireGuard uses UDP — larger buffers help during burst
sudo sysctl -w net.inet.udp.recvspace=262144 2>/dev/null
sudo sysctl -w net.inet.udp.maxdgram=65535 2>/dev/null
echo "  UDP recv: 256KB, maxdgram: 64KB"

echo ""

# --- WARP Status ---
echo "🛡️ WARP Status:"
warp-cli status 2>/dev/null || echo "  Not installed"
echo ""
echo "  Mode: $(warp-cli settings 2>/dev/null | grep Mode | head -1)"
echo "  Protocol: $(warp-cli settings 2>/dev/null | grep 'tunnel protocol' | head -1)"

echo ""

# --- Verification ---
echo "📊 Verification (5x Google API latency):"
total=0
for i in 1 2 3 4 5; do
  ms=$(curl -w "%{time_total}" -o /dev/null -s https://generativelanguage.googleapis.com/)
  echo "  Run $i: ${ms}s"
  total=$(echo "$total + $ms" | bc)
done
avg=$(echo "scale=3; $total / 5" | bc)
echo "  Average: ${avg}s"

echo ""
echo "🌊 === DONE ==="

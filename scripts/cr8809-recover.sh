#!/bin/sh
# CR8809 Auto-Recovery Script
# Runs after factory reset, power loss, or PPPoE disconnect

ROUTER="root@192.168.1.1"
PASS="FastSaaS2026"
SSH="sshpass -p '$PASS' ssh -o StrictHostKeyChecking=no $ROUTER"

run_on_router() {
    eval "$SSH 'bash -s'" << 'EOF'
set -e

echo "=== CR8809 Auto-Recovery $(date) ==="

# Step 1: Bring PPPoE up
if ! ip link show pppoe-wan 2>/dev/null | grep -q "state UP"; then
    echo "[recovery] PPPoE down — reconnecting"
    ifdown wan 2>/dev/null
    sleep 2
    ifup wan
    sleep 5
fi

# Step 2: Verify DNS
RESOLV="/tmp/resolv.conf.d/resolv.conf.auto"
if [ ! -s "$RESOLV" ] || ! grep -q "nameserver" "$RESOLV" 2>/dev/null; then
    echo "[recovery] DNS missing — re-extracting from PPP"
    cp /etc/ppp/resolv.conf "$RESOLV" 2>/dev/null
fi

# Step 3: Commit & restart dnsmasq
uci commit dhcp 2>/dev/null
/etc/init.d/dnsmasq restart 2>/dev/null

# Step 4: Verify firewall MASQUERADE exists
MASQ=$(uci get firewall.@zone[1].masq 2>/dev/null)
if [ "$MASQ" != "1" ]; then
    echo "[recovery] MASQUERADE missing — regenerating wan zone"
    # Remove existing wan zone
    uci delete firewall.@zone[1] 2>/dev/null || true
    # Recreate
    uci add firewall zone
    uci set firewall.@zone[-1]=zone
    uci set firewall.@zone[-1].name='wan'
    uci set firewall.@zone[-1].network='wan'
    uci set firewall.@zone[-1].input='REJECT'
    uci set firewall.@zone[-1].output='ACCEPT'
    uci set firewall.@zone[-1].forward='REJECT'
    uci set firewall.@zone[-1].masq='1'
    uci set firewall.@zone[-1].mtu_fix='1'
    # Re-add standard rules
    uci add firewall rule 2>/dev/null || true
    uci set firewall.@rule[-1].name='Allow-Ping' 2>/dev/null
    uci set firewall.@rule[-1].src='wan' 2>/dev/null
    uci set firewall.@rule[-1].proto='icmp' 2>/dev/null
    uci set firewall.@rule[-1].icmp_type='echo-request' 2>/dev/null
    uci set firewall.@rule[-1].target='ACCEPT' 2>/dev/null
    uci set firewall.@rule[-1].family='ipv4' 2>/dev/null
    uci add firewall forwarding 2>/dev/null || true
    uci set firewall.@forwarding[-1].src='lan' 2>/dev/null
    uci set firewall.@forwarding[-1].dest='wan' 2>/dev/null
    uci commit firewall
    /etc/init.d/firewall restart 2>/dev/null
    sleep 3
fi

# Step 5: Verify connectivity
if ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
    echo "[recovery] SUCCESS: Internet reachable"
else
    echo "[recovery] WARNING: Ping 8.8.8.8 failed"
fi

echo "=== Recovery complete ==="
EOF
}

__unparsedToolInput>
  {"raw": "{\"file_path\": \"/Users/macbook/mekong-cli/scripts/cr8809-recover.sh\", \"content\": \"#!/bin/sh\\n# CR8809 Auto-Recovery Script\\n# Script: restore + verify connectivity, then install persistent recovery end-to-end\\n\\nROUTER=\\\"root@192.168.1.1\\\"\\nPASS=\\\"FastSaaS2026\\\"\\nSSH_CMD=\\\"sshpass -p '$PASS' ssh -o StrictHostKeyChecking=no $ROUTER\\\"\\n\\necho \\\"=== STEP 1: Restart PPPoE to get fresh IP ===\\\"\\neval \\\"$SSH_CMD 'ifdown wan && sleep 2 && ifup wan && sleep 5'\\\" 2>&1\\n\\neval \\\"$SSH_CMD 'ip addr show pppoe-wan | grep inet'\\\" 2>&1\\n\\necho \\\"\\\"\\necho \\\"=== STEP 2: Verify HTTPS works ===\\\"\\neval \\\"$SSH_CMD 'curl -k -s -o /dev/null -w \\\"HTTP %{http_code} time %{time_total}s\\\\n\\\" --connect-timeout 8 https://httpbin.org/get'\\\" 2>&1\\n\\n\\necho \\\"\\\"\\necho \\\"=== STEP 3: Install persistent recovery ===\\\"\\n\\n# Install script + hook\\neval \\\"$SSH_CMD 'mkdir -p /etc/rc.d && mkdir -p /mnt/data'\\\" 2>&1\\n\\neval \\\"$SSH_CMD 'rm -f /etc/rc.d/S99cr-recover && rm -f /mnt/data/cr-recover.sh'\\\" 2>&1\\n\\nasdfasdfasdfasdf}, "len": 10777}
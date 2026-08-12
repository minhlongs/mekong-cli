#!/bin/sh
# CR8809 Auto-Recovery v3 — BusyBox + fw4/nft only, NO iptables
# Survives factory reset / power loss
LOG="/var/log/cr8809-recovery.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [recover] $1" >> "$LOG"; }

log "=== AUTO-RECOVERY START ==="
[ -d /mnt/data ] || mkdir -p /mnt/data

# Step 1: PPPoE UP (MTU 1492)
if ! ip link show pppoe-wan 2>/dev/null | grep -q "state UP"; then
    log "ppp-down: ifdown/ifup"
    ifdown wan 2>/dev/null || true
    sleep 2
    ifup wan
    sleep 8
fi
WAN_IP=$(ip -4 addr show pppoe-wan 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
log "pppoe-ip: ${WAN_IP:-none}"

# Step 2: DNS — resolv.conf.auto → dnsmasq
RESOLV="/tmp/resolv.conf.d/resolv.conf.auto"
if [ ! -s "$RESOLV" ]; then
    log "DNS empty: setting FPT primary"
    cat > "$RESOLV" << 'DNS'
nameserver 210.245.31.220
nameserver 210.245.31.221
nameserver 8.8.8.8
nameserver 1.1.1.1
DNS
fi

# /etc/resolv.conf must point to localhost
cat > /etc/resolv.conf << 'RES'
nameserver 127.0.0.1
RES

/etc/init.d/dnsmasq restart 2>/dev/null || true
log "dnsmasq restarted"

# Step 3: firewall via uci + fw4 (nftables, NOT iptables)
uci set firewall.@defaults[0].syn_flood='1'
uci set firewall.@defaults[0].input='REJECT'
uci set firewall.@defaults[0].output='ACCEPT'
uci set firewall.@defaults[0].forward='REJECT'
uci set firewall.@defaults[0].flow_offloading='0'
uci set firewall.@defaults[0].flow_offloading_hw='0'
uci set firewall.@defaults[0].fullcone='0'
uci set firewall.@defaults[0].fullcone6='0'
uci commit firewall
/etc/init.d/firewall restart 2>/dev/null
log "firewall restarted (fw4/nft)"

# Step 4: dnsmasq final
/etc/init.d/dnsmasq restart 2>/dev/null || true
log "=== AUTO-RECOVERY DONE ==="

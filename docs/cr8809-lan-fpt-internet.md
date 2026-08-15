# CR8809 LAN Internet Fix


## Problem statement
LAN clients (iPhone 192.168.1.186, MacBook 192.168.1.244) on CR8809/Xiaomi AX3000 (ImmortalWrt 24.10-r32960) cannot access internet. Router itself has working PPPoE (100.121.5.80) but client traffic gets no response.

## Evidence collected

| Test | Result |
|------|--------|
| Captive portal (all 3) | 404 (should be 204) |
| Conntrack UNREPLIED count | 45 |
| iPhone → Apple (17.253.87.198:443) | SYN_SENT [UNREPLIED] |
| MacBook → Apple (17.253.87.204:443) | SYN_SENT [UNREPLIED] |
| DNS from router | ✅ works |
| Router → Google direct | ❌ timeout 5s |
| Router → httpbin HTTP | ✅ 404 (FPT intercept) |
| Clients → Google/CF | ✅ sometimes |
| Masquerade | ✅ active |
| MTU fix (nft) | ✅ present |

## Root cause analysis

**PRIMARY: ISP-side transparent HTTP proxy intercepting port 80 — returns 404 for unknown hosts**

iOS/Android captive portal expects 204 from `generate_204`. FPT proxy returns 404 → OS thinks "no internet."

**SECONDARY: PPPoE MTU 1492 vs LAN MTU 1500 — large packets silently dropped**

TCP SYN with MSS > 1452 gets no SYN-ACK → [UNREPLIED] in conntrack.

## Proposed fixes (priority order)

1. **Disable captive portal detection bypass** — accept that FPT proxy will return 404 for some URLs. Android >= 10 supports `captive_portal_http_url` override to skip 204 check.
2. **Force MTU 1492 on LAN bridge** — prevent TCP from sending packets that won't fit PPPoE path.
3. **Add `nohandler` to dnsmasq for captive portal domains** — let those through without being hijacked.
4. **Set `option dns_redirect 0`** — stop redirecting all DNS; let clients use router DNS or ISP DNS directly.

## Status
Blocked on user confirmation to proceed with fix implementation.

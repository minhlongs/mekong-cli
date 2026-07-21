# Vector Registry — M02 Trust Ledger

| Vector | Owner | Status | Trust Gate |
|--------|-------|--------|------------|
| **V-Domain** | CL | hold | Plan M02 + BD sanitized |
| **V-ecom (billing/checkout)** | CL | passive | Policy-only reads; no prod writes |
| **V-Auth** | CL | passive | No PingOne / secret writes |
| **V-Infra/Pay** | CL | passive | No CF / Cloudflare config changes |
| **V-GoToMarket** | CL | active | Compose plan artifacts only |
| **V-DB/Persistence** | CL | passive | Reading tenant + storage hintergrund only |**Note:** `V-Legal` không nhận staged trong đợt scan hiện tại.

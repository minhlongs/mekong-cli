# Phase 01 — Core Infrastructure

**Context:** [plan.md](./plan.md) | **Effort:** 2d | **Status:** pending

## Overview

Setup server, Docker Compose cho tất cả 12 pillars, Nginx reverse proxy + SSL Let's Encrypt.

## Key Insights
- Tất cả services chạy Docker trên 1 server (min 4 cores, 8GB RAM, 50GB SSD)
- Nginx làm reverse proxy duy nhất, SSL termination
- Mỗi service có subdomain riêng → cần DNS records trước
- Shared PostgreSQL instance tiết kiệm RAM (mỗi service có DB riêng)
- Redis shared cho Odoo longpolling + OpenWISP + pretix

## Requirements
- Domain: `vibecafe.vn` (cần mua + DNS setup)
- SSL: Let's Encrypt wildcard `*.vibecafe.vn` via Certbot/Traefik
- Server: Ubuntu 22.04 LTS (hoặc Debian 12)
- Docker CE + Docker Compose v2

## Architecture

```
/srv/vibe-cafe/
├── docker-compose.yml          # Main compose (Nginx + shared infra)
├── docker-compose.odoo.yml     # Odoo stack
├── docker-compose.calcom.yml   # Cal.com stack
├── docker-compose.pretix.yml   # pretix stack
├── docker-compose.openwisp.yml # OpenWISP stack
├── docker-compose.tasty.yml    # TastyIgniter
├── docker-compose.signage.yml  # Xibo CMS
├── docker-compose.marketing.yml # Mixpost + Mautic
├── docker-compose.loyalty.yml  # Open Loyalty
├── nginx/
│   ├── nginx.conf
│   └── conf.d/                 # Per-service configs
├── certs/                      # Let's Encrypt certs
└── .env                        # All secrets (gitignored)
```

## Related Code Files
- **Modify:** `apps/vibe-coding-cafe/infrastructure/docker-compose-bootstrap.yml` → upgrade to full stack
- **Create:** `apps/vibe-coding-cafe/infrastructure/docker-compose.yml` (main)
- **Create:** `apps/vibe-coding-cafe/infrastructure/nginx/` configs
- **Create:** `apps/vibe-coding-cafe/infrastructure/.env.example`

## Implementation Steps

### 1. DNS Setup
```
A    vibecafe.vn          → <SERVER_IP>
A    *.vibecafe.vn        → <SERVER_IP>
```

### 2. Shared Infrastructure (docker-compose.yml)
```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./certs:/etc/letsencrypt
    restart: always

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${PG_USER}
      POSTGRES_PASSWORD: ${PG_PASS}
    volumes:
      - pg-data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

volumes:
  pg-data:
```

### 3. SSL Certificates
```bash
certbot certonly --nginx -d vibecafe.vn -d '*.vibecafe.vn' \
  --agree-tos --email admin@vibecafe.vn
```

### 4. Nginx Config Template (per service)
```nginx
server {
  listen 443 ssl;
  server_name odoo.vibecafe.vn;
  ssl_certificate /etc/letsencrypt/live/vibecafe.vn/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/vibecafe.vn/privkey.pem;

  location / {
    proxy_pass http://odoo:8069;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
  # Odoo longpolling
  location /web/websocket {
    proxy_pass http://odoo:8072;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
```

### 5. Firewall
```bash
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

## Todo
- [ ] Mua domain `vibecafe.vn`
- [ ] Thuê VPS (4 cores, 8GB RAM, 50GB SSD) — khuyến nghị DigitalOcean/Vultr ~$40/tháng
- [ ] Cài Docker CE + Docker Compose v2
- [ ] Setup DNS records (A records cho wildcard)
- [ ] Tạo `docker-compose.yml` shared infrastructure
- [ ] Cấu hình Nginx reverse proxy
- [ ] Lấy SSL cert Let's Encrypt (wildcard)
- [ ] Setup `.env` với tất cả secrets
- [ ] Test kết nối tất cả services

## Success Criteria
- Tất cả subdomains resolve và trả về 200/301
- SSL valid, auto-renew configured (cron certbot renew)
- PostgreSQL accessible từ tất cả containers
- Redis accessible từ tất cả containers

## Risk Assessment
- **HIGH:** VPS downtime → cần backup VPS hoặc Cloudflare proxy
- **MEDIUM:** Domain DNS propagation (~24h)
- **LOW:** Port conflict giữa services

## Security Considerations
- Không expose PostgreSQL/Redis port ra ngoài (internal Docker network only)
- `.env` file trong `.gitignore`
- SSH key-based auth only, disable password auth
- Regular `apt update && apt upgrade`

## Next Steps
→ Phase 02: Odoo setup sau khi infra xong

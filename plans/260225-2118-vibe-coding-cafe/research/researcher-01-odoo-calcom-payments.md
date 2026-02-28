# Research Report: Odoo, Cal.com & Vietnamese Payment Integration (Vibe Coding Cafe)

## 1. Odoo 17 Self-Hosted Deployment (Docker)
### Best Practices
- **Images:** Use official `odoo:17.0` and `postgres:16-alpine`.
- **Architecture:** Separate Odoo service and PostgreSQL service in `docker-compose`.
- **Volumes:** Mount `/var/lib/odoo` (filestore) and `/mnt/extra-addons` (custom modules).
- **Proxy:** Use Nginx or Traefik for SSL (Let's Encrypt) and `longpolling` (port 8072).
- **DB Optimization:** Set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` in env; use `db_filter` in `odoo.conf` for multi-tenant.

### Docker-Compose Snippet (Draft)
```yaml
services:
  web:
    image: odoo:17.0
    depends_on: [db]
    ports: ["8069:8069", "8072:8072"]
    volumes:
      - odoo-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo_pass
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo_pass
    volumes:
      - db-data:/var/lib/postgresql/data
```

### Required Modules
- `point_of_sale`: Retail/Cafe interface.
- `account`: Vietnamese Chart of Accounts (standardized).
- `crm`: Lead & customer management.
- `membership`: Loyalty programs & member tiers.

### Minimum Hardware Specs (Odoo + Cal.com)
- **Combined Setup (Single Server Recommendation):**
  - **CPU:** 4 Cores (2 for Odoo, 2 for Cal.com/Node processes).
  - **RAM:** 8GB (Odoo: 4GB, Cal.com: 2-3GB, OS/Docker: 1GB).
  - **Disk:** 50GB SSD (Database growth + filestore).

### Gotchas & Pitfalls
- **Currency:** Ensure "VND" is set as base currency with 0 decimal places to avoid POS rounding issues.
- **Tax:** VAT 8% (decree 94/2023) vs 10% — ensure tax rules are updated for 2025.
- **Hardware:** POS local proxy (Odoo IoT Box) is usually NOT needed for modern browsers unless using legacy ESC/POS printers or physical scales.

### Cafe-Specific Optimization
- **Offline Mode:** Odoo POS works in the browser cache. If the internet drops, sales can continue and sync once reconnected.
- **Table Management:** Enable "Floors & Tables" in POS settings to manage cafe layout.
- **Kitchen Printing:** Use "Order Printers" (Network/IP printers) to send orders directly to the bar/kitchen.

## 2. Cal.com Self-Hosted (v4)
### Docker Setup
- **Image:** `calcom/cal.com:latest`.
- **PostgreSQL:** Version 15+ required.
- **Persistence:** Mount `/app/packages/prisma/schema.prisma` if customizing or use standard migrations.

### Docker-Compose Snippet (Draft)
```yaml
services:
  calcom:
    image: calcom/cal.com:latest
    ports: ["3000:3000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/calcom
      - NEXT_PUBLIC_WEBAPP_URL=https://booking.vibecafe.vn
      - NEXTAUTH_SECRET=yoursecret
      - CALENDSO_ENCRYPTION_KEY=yourkey
    depends_on: [db]
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=calcom
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

### Key Env Vars
- `NEXT_PUBLIC_WEBAPP_URL`: Your domain (e.g., `https://booking.vibecafe.vn`).
- `DATABASE_URL`: `postgresql://user:pass@db:5432/calcom`.
- `NEXTAUTH_SECRET`: Random string for session security.
- `CALENDSO_ENCRYPTION_KEY`: For encrypting calendar credentials.
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`: For file uploads (S3 compatible).
- `NEXT_PUBLIC_STRIPE_PUBLIC_KEY` (Optional): If using Stripe alongside VietQR.

### Booking for Cafes
- **Table Reservations:** Set up "Event Types" for table bookings (e.g., "Standard Table - 2 hours").
- **Workshops/Events:** Use Cal.com to handle registration for coffee workshops or community events.
- **Webhooks:** Trigger Odoo CRM leads when a new booking is made in Cal.com via a simple Zapier/N8N bridge or custom script.

## 3. Vietnamese E-invoicing Compliance 2025
### Requirements
- **Legal Base:** Decree 123/2020/ND-CP & Circular 78/2021/TT-BTC.
- **Odoo Integration:** Mandatory digital signature. **HSM (Hardware Security Module)** is REQUIRED for cloud/Docker deployment (USB tokens do not work in remote headless environments).
- **Providers:** Connect Odoo via API to providers like **M-Invoice, VNPT, or Viettel**.
- **Module:** Use `l10n_vn_einvoice` or custom connectors from local Odoo partners.
- **Deadline:** Full adoption mandatory by June 2025.
- **Format:** XML file conforming to GDT standard for transmission.

## 4. SePay/VietQR Integration with Odoo POS
### Mechanism
- **VietQR:** Generate NAPAS 247 QR codes containing amount, account info, and a unique transaction description.
- **SePay Integration:**
  1. Install SePay Odoo module (Available on Odoo App Store, typically paid ~€50-100 or via SePay subscription).
  2. At POS checkout, select "VietQR" payment method.
  3. Customer scans QR → Pays via mobile banking.
  4. SePay detects incoming bank transfer via bank API/webhook.
  5. SePay calls Odoo Webhook → Marks POS Order as Paid automatically.

### Gotchas
- **Email:** SMTP configuration is critical; use SendGrid or Resend for high deliverability of booking confirmations.
- **v3 to v4:** Migration requires database schema updates; if starting fresh, ensure `PRISMA_GENERATE_DATAPROXY=false` for local Docker setups.

### Proxy & Longpolling (Nginx Configuration)
To prevent POS disconnects, Nginx must handle Odoo's longpolling port (8072):
```nginx
location /longpolling {
    proxy_pass http://odoo:8072;
}
location / {
    proxy_pass http://odoo:8069;
}
```

### VietQR String Format (Napas 247)
The dynamic QR generated by Odoo must follow the EMVCo standard:
- **Payload Format Indicator** (ID 00)
- **Merchant Account Information** (ID 38) -> GUID (00), Bank ID (01), Account No (02)
- **Transaction Amount** (ID 54)
- **Additional Data Field** (ID 62) -> Content (08) - *Must match SePay webhook unique ID*.

## 5. Answers to Key Research Questions
- **HSM Provider:** **M-Invoice** is preferred for API documentation. **Viettel** is highly stable. HSM is mandatory for cloud; USB tokens are for local PCs only.
- **SePay Cost:** Requires subscription (~200k VND/mo). The Odoo module is often a separate one-time fee (~$100).
- **Cal.com Storage:** MinIO/S3 is recommended for v4 to avoid volume persistence issues in Docker.

## Final Technical Insights
- **HSM Latency:** M-Invoice HSM latency is typically < 2s. For POS, ensure the module handles timeouts gracefully to avoid blocking the queue.
- **Cal.com v4 Build:** `NEXT_PUBLIC_WEBAPP_URL` must be set at **build time** for Next.js. If using pre-built images, ensure the domain is correctly mapped in the container orchestration.
- **VietQR Reconciliation:** SePay matches the `Description` field. Ensure Odoo generates a unique short ID (e.g., POS Order Ref) in ID 62 of the QR.

### Security & Backup
- **SSL:** Use `certbot` for Let's Encrypt certificates.
- **Webhooks:** Secure SePay webhooks with HMAC signature verification to prevent spoofing.
- **Backups:** Schedule daily Docker volume backups (`docker-compose exec db pg_dump`) to an off-site location (e.g., S3/Google Drive).
- **Updates:** Pin Docker image tags (e.g., `odoo:17.0`) instead of using `latest` to ensure stability across deployments.

## Sources
- [Odoo Docker](https://hub.docker.com/_/odoo) | [Cal.com Docker](https://github.com/calcom/docker)
- [GDT E-Invoice](https://hoadondientu.gdt.gov.vn/) | [SePay Docs](https://docs.sepay.vn/)

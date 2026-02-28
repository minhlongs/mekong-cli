# Vietnamese Café Tech Stack: WiFi, Events, IoT & Signage

## 1. OpenWISP (WiFi Captive Portal)
- **Docker Setup**: Use `openwisp-docker` (Git repository). Requires `docker-compose.yml` with services: `dashboard`, `api`, `websocket`, `worker`, `nginx`, `postgres`, `redis`.
- **Captive Portal Config**:
  - **Social Login**: Enabled via `django-allauth`. Supports Facebook, Google, Apple.
  - **OTP**: Requires SMS gateway integration. Use `openwisp-users` with a custom SMS backend (e.g., Twilio or local VN providers like eSMS.vn via API).
- **Hardware Compatibility**:
  - **Best**: Devices running **OpenWRT** (e.g., Ubiquiti UniFi, MikroTik, TP-Link Archer).
  - **Requirement**: Must support `openwisp-config` agent.
- **Gotchas**: SSL certificates (Let's Encrypt) are mandatory for modern browsers to show the portal.

## 2. pretix (Event Ticketing)
- **Docker Setup**: Use the official `pretix/standalone` Docker image. Link with PostgreSQL and Redis.
- **Vietnamese Integration**:
  - **Payment**: VNPay/MoMo integration typically requires a custom pretix plugin. `pretix-vnpay` (check GitHub) or implement via pretix API + custom payment provider.
  - **Localization**: Vietnamese (vi-vn) is supported in pretix-core. Enable in settings.
- **Gotchas**: PDF ticket generation needs `pretix-font-vietnamese` or custom font upload to support diacritics.

## 3. Home Assistant + Frigate (IoT & Heatmap)
- **Hardware**:
  - Raspberry Pi 4 (4GB+ RAM recommended).
  - **Critical**: Google Coral USB Accelerator for AI processing (prevents RPi 100% CPU).
- **Deployment**: **HA OS** is recommended for café stability; use Frigate as an Add-on. Use **Docker** only if you need granular control over other non-HA services.
- **AI Heatmap**:
  - Integrate cameras via RTSP.
  - Frigate performs object detection (person).
  - Integration with HA via MQTT. Use the `Frigate Custom Card` in HA dashboard for real-time tracking.
  - Heatmap requires a custom integration or exporting Frigate events to a DB (InfluxDB) and visualizing in Grafana.

## 4. Xibo (Digital Signage)
- **CMS Setup**: Deploy via Docker on a central server/RPI.
  - `cms-web`, `cms-db`, `cms-xmr`.
- **Menu Board Management**:
  - Create layouts in CMS.
  - Use "Datasets" for dynamic price/item updates without re-uploading media.
- **Raspberry Pi Player**:
  - **OS**: Use `Xibo for Linux` (snap package) on Ubuntu Desktop or a specialized RPi image like `Xibo for RPi` (commercial) or `yodeck` (alternative).
- **Gotchas**: RPi 4 hardware acceleration is required for 4K video playback; ensure `vc4-kms-v3d` driver is enabled.

## Unresolved Questions
1. **pretix VNPay/MoMo**: Confirm if existing open-source plugins are compatible with pretix v5+ or if custom development is required.
2. **OpenWISP OTP**: Availability of stable SMS API providers in Vietnam with direct Django-allauth integration.
3. **Frigate Heatmap**: Exact performance impact of running Frigate + Home Assistant on a single RPi 4 even with Google Coral (RAM might be the bottleneck).
4. **Xibo RPi Player License**: Status of "Xibo for RPi" official player licensing cost vs community-supported Linux player.

---
**Sources:**
- [OpenWISP Docker](https://github.com/openwisp/openwisp-docker)
- [pretix Documentation](https://docs.pretix.eu/en/latest/developer/index.html)
- [Frigate NVR](https://frigate.video/)
- [Xibo Digital Signage](https://xibosignage.com/)
- [VNPay API Docs](https://sandbox.vnpayment.vn/apis/docs/)

#!/bin/bash
# VIBE CODING Café — Automated Let's Encrypt SSL Setup
# Script này lấy chứng chỉ SSL và tự động uncomment cấu hình HTTPS trong Nginx
set -e

# ==========================================
# Cấu Hình
# ==========================================
# Lấy biến môi trường từ file .env nếu có
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

DOMAIN=${DOMAIN:-vibecafe.vn}
EMAIL=${ADMIN_EMAIL:-admin@vibecafe.vn}
COMPOSE_FILE="docker-compose.yml"
DRY_RUN=0

# ==========================================
# Parse Args
# ==========================================
for arg in "$@"; do
  case $arg in
    --test|--dry-run)
      DRY_RUN=1
      echo "🧪 Chạy chế độ DRY RUN (Testing Let's Encrypt)"
      shift
      ;;
  esac
done

# ==========================================
# Chuẩn Bị
# ==========================================
echo "🚀 Bắt đầu quá trình setup SSL cho ${DOMAIN}..."
echo "📧 Email: ${EMAIL}"

# Dừng Nginx nếu đang chạy để dùng standalone (chiếm port 80)
echo "🛑 Dừng Nginx container..."
docker compose -f $COMPOSE_FILE stop nginx || true

# ==========================================
# Lấy Chứng Chỉ
# ==========================================
CMD_ARGS="certonly --standalone --agree-tos --non-interactive --email $EMAIL -d $DOMAIN -d erp.$DOMAIN -d booking.$DOMAIN -d events.$DOMAIN -d order.$DOMAIN -d wifi.$DOMAIN -d cms.$DOMAIN -d social.$DOMAIN -d loyalty.$DOMAIN"

if [ $DRY_RUN -eq 1 ]; then
  CMD_ARGS="$CMD_ARGS --dry-run"
fi

echo "🔐 Tiến hành gọi certbot..."
docker run -it --rm \
  -p 80:80 \
  -v "$(pwd)/certs:/etc/letsencrypt" \
  certbot/certbot $CMD_ARGS

if [ $DRY_RUN -eq 1 ]; then
  echo "✅ Hoàn tất DRY RUN. Không thay đổi Nginx config."
  # Start Nginx back up for dry run
  docker compose -f $COMPOSE_FILE start nginx || true
  exit 0
fi

# ==========================================
# Tự Động Uncomment Nginx Config
# ==========================================
echo "⚙️ Tự động bật cấu hình HTTPS trong Nginx files..."

for conf in ./nginx/conf.d/*.conf; do
  if [ ! -f "$conf" ]; then
    continue
  fi

  echo "  - Cập nhật ${conf}..."

  # 1. Bật HTTP -> HTTPS redirect block an toàn
  sed -i.bak -e 's/^# server {/server {/g' "$conf"
  sed -i.bak -e 's/^#     listen 80;/    listen 80;/g' "$conf"
  sed -i.bak -e 's/^#     server_name /    server_name /g' "$conf"
  sed -i.bak -e 's/^#     return 301 https:/    return 301 https:/g' "$conf"
  sed -i.bak -e 's/^# }/}/g' "$conf"

  # 2. Bật cấu hình SSL (listen 443, ssl_certificate, etc)
  sed -i.bak -e 's/# listen 443 ssl http2;/listen 443 ssl http2;/g' "$conf"
  sed -i.bak -e 's|# ssl_certificate |ssl_certificate |g' "$conf"
  sed -i.bak -e 's|# ssl_certificate_key |ssl_certificate_key |g' "$conf"
  sed -i.bak -e 's/# ssl_protocols/ssl_protocols/g' "$conf"
  sed -i.bak -e 's/# ssl_ciphers/ssl_ciphers/g' "$conf"

  rm -f "${conf}.bak"
done

# ==========================================
# Reload Nginx
# ==========================================
echo "🔄 Khởi động lại Nginx với cấu hình mới..."
docker compose -f $COMPOSE_FILE up -d nginx

echo "✅ SSL setup thành công!"
echo "Chứng chỉ được lưu tại: $(pwd)/certs/live/${DOMAIN}/"
echo "Renewal command: docker run --rm -v $(pwd)/certs:/etc/letsencrypt certbot/certbot renew"
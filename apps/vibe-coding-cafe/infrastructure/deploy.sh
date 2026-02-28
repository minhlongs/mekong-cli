#!/bin/bash
# Deploy VIBE CODING Café infrastructure
# Chạy trên VPS sau khi clone repo
set -e

INFRA_DIR="$(dirname "$0")"
cd "$INFRA_DIR"

# Kiểm tra .env
if [ ! -f .env ]; then
  echo "❌ File .env không tồn tại! Copy .env.example và điền giá trị."
  echo "   cp .env.example .env && nano .env"
  exit 1
fi

echo "🚀 Starting VIBE CODING Café infrastructure..."

# Pull latest images
docker compose pull

# Start shared infrastructure first
docker compose up -d postgres redis
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Start all services
docker compose up -d

echo "✅ All services started!"
echo ""
echo "📊 Service status:"
docker compose ps

echo ""
echo "🌐 Access URLs:"
echo "  Odoo POS/ERP:   https://odoo.vibecafe.vn"
echo "  Booking:        https://booking.vibecafe.vn"
echo "  Events:         https://events.vibecafe.vn"
echo "  Online Order:   https://order.vibecafe.vn"
echo "  WiFi Mgmt:      https://wifi.vibecafe.vn"
echo "  Digital Menu:   https://cms.vibecafe.vn"
echo "  Social Media:   https://social.vibecafe.vn"
echo "  Loyalty:        https://loyalty.vibecafe.vn"

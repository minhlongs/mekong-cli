#!/bin/bash

# Kiểm tra Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Lỗi: Docker Compose chưa được cài đặt."
    exit 1
fi

echo "🚀 Đang khởi động RaaS Stack..."

# Sử dụng docker compose hoặc docker-compose tùy theo phiên bản
DOCKER_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_CMD="docker-compose"
fi

$DOCKER_CMD -f docker-compose.raas.yml up --build -d

echo "✅ Đã khởi động xong các services!"
echo "🌐 Web: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📊 Database: localhost:5432"
echo "📝 Chạy '$DOCKER_CMD -f docker-compose.raas.yml logs -f' để xem log."

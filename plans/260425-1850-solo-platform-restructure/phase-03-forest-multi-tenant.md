# Phase 03: Rừng (Forest — Multi-Tenant)

> **Ưu tiên:** HIGH | **Thời gian:** Tháng 2  
> **Mục tiêu:** N users độc lập, dữ liệu riêng biệt, một máy chủ

## Kiến trúc Forest

```
User A → Gateway → Redis Queue → Worker → Docker Container A (user_a/)
User B → Gateway → Redis Queue → Worker → Docker Container B (user_b/)
```

## Implementation Steps

### 3.1 Docker-compose Extension
```yaml
# Thêm vào docker-compose.yml:
redis:
  image: redis:7-alpine
  ports: ["6379:6379"]

gateway:
  build: ./apps/api
  environment:
    - REDIS_URL=redis://redis:6379
    - OLLAMA_URL=http://host.docker.internal:11434

worker:
  build: ./worker
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock  # spawn containers
  deploy:
    replicas: 2
```

### 3.2 FastAPI Gateway (apps/api refactor)

```python
# Endpoints:
POST /auth/login     # → JWT token
POST /task           # Auth required → queue job → return job_id
GET  /task/{job_id}  # Auth required → return status + result
GET  /health         # No auth
```

### 3.3 Worker Pool

```python
# worker/main.py
# 1. Listen Redis queue
# 2. Pop job → spawn Docker container per job
# 3. Container: run seed/main.py with USER_ID isolation
# 4. Update job status → notify via webhook
```

### 3.4 User Isolation

```
outputs/{user_id}/     # Mỗi user có thư mục riêng
data/chroma/{user_id}/ # Memory riêng biệt
```

### 3.5 Billing Integration

Reuse existing Polar.sh setup:
```python
# Middleware: check MCU credits before processing
# Deduct 1 MCU on success
# HTTP 402 on zero balance
```

## Files cần tạo/sửa

| File | Hành động |
|------|-----------|
| `docker-compose.yml` | Sửa (add redis, gateway, worker) |
| `apps/api/src/main.py` | Sửa (add auth middleware) |
| `worker/main.py` | Tạo mới |
| `worker/Dockerfile` | Tạo mới |
| `apps/api/src/middleware/billing.py` | Tạo mới |

## Success Criteria

```bash
# Test 2 users parallel
curl -H "Authorization: Bearer token_user_a" \
     -d '{"prompt":"Create Python script"}' \
     https://api.cashclaw.cc/task

curl -H "Authorization: Bearer token_user_b" \
     -d '{"prompt":"Create React component"}' \
     https://api.cashclaw.cc/task

# Expected: Cả hai xử lý song song, không ảnh hưởng nhau
```

## Next Steps → Phase 04 (Land/Infrastructure)

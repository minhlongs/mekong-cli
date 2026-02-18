# 📱 Postiz — Self-Hosted Social Media Automation — 火攻篇 Content Distribution

> Source: github.com/gitroomhq/postiz-app + vnrom.me/qgyii4r
> Assessed: 2026-02-18 | Status: KEEP — P2 INFRA
> Action: Deploy khi có VPS/Mac Mini server

## What
- Open source social media scheduler (Buffer/Hootsuite killer)
- 20+ platforms: X, LinkedIn, Facebook, Instagram, TikTok, Pinterest, YouTube, Reddit, Threads...
- Self-hosted Docker stack (NextJS + NestJS + Prisma + PostgreSQL + Redis + Temporal)
- Apache 2.0 license, FREE

## Key Features
- AI Writer (OpenAI caption generation)
- Team Collaboration (multi-brand, roles)
- Temporal Engine (100% delivery guarantee)
- Analytics per platform
- API: N8N, Make.com, Zapier integration
- **🔥 MCP NATIVE SUPPORT** → Tôm Hùm có thể điều khiển trực tiếp!

## Binh Pháp Integration
- 火攻篇: Scheduled content attacks = marketing theo lịch
- 因糧於敵: Self-hosted = $0 vs $30-100/mo SaaS
- 用間篇: Auto-distribute content across 20+ channels

## Integration Plan
1. Deploy Postiz trên VPS/Mac Mini (Docker)
2. Lấy MCP URL từ Postiz dashboard
3. Thêm MCP server vào .claude/.mcp.json
4. Tạo skill: /generate-skill "postiz social media scheduler"
5. Tôm Hùm CTO → Sophia Factory → generate content → Postiz → auto-post

## Sophia AI Factory Pipeline
```
Sophia Factory → Generate Video/Content
       ↓
   Postiz MCP → Schedule posts
       ↓  
   20+ Platforms → Auto-publish
       ↓
   Analytics → ROI tracking
```

## Prerequisites
- VPS/Server (2GB RAM minimum, 4-8GB recommended)
- Docker + Docker Compose
- Domain + SSL (reverse proxy)
- Social media developer API keys (X, FB, LinkedIn...)

## Install Script
```bash
curl -O https://raw.githubusercontent.com/duynghien/auto/main/postiz/setup.sh
chmod +x setup.sh
./setup.sh
```

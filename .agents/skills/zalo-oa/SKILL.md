---
name: zalo-oa
description: >-
  Zalo Official Account (OA) integration for customer messaging, followers, templates, and broadcast campaigns.
---

# /zalo-oa — Autonomous Zalo OA Customer Messaging, Broadcast Campaign & Social Marketing Engine

Empowering Vietnamese solo founders, SME growth hackers, and enterprise marketing swarms, `mekong zalo-oa` delivers deterministic customer messaging, follower segment targeting, broadcast campaign orchestration, and multi-tone AI copy generation tailored for Zalo Official Account.

## Key Capabilities

1. **Direct Customer Messaging**:
   - Deliver transactional and care messages directly to Zalo User IDs (`user_id`).
   - Support reusable template notifications (`order_confirmation`, `shipping_update`, `consultation_reminder`).
   - Offline simulation & verification fallback when running in sandbox/CI environments (`--mock`).
2. **Follower Demographics & Segmentation**:
   - Manage and filter follower lists across customer lifecycle segments (`vip`, `lead`, `customer`, `standard`).
   - Track engagement scores, interaction histories, and opt-in timestamps in `.mekong/zalo.db`.
3. **Broadcast Campaign Orchestration**:
   - Dispatch rich broadcast announcements across full follower lists or targeted segments.
   - Real-time simulation of sent, delivered, opened, and converted metrics.
4. **Multi-Tone Marketing Caption Generator**:
   - Synthesize Vietnamese social captions across 5 distinct brand voices:
     - `vui_ve`: Thân thiện, gần gũi, nhiều năng lượng.
     - `chuyen_nghiep`: Chuẩn mực B2B, tin cậy, súc tích.
     - `sang_tao`: Độc đáo, thu hút sự tò mò.
     - `khuyen_mai`: Thúc đẩy chuyển đổi chốt đơn, tạo sự khẩn cấp.
     - `binh_phap`: Vận dụng chiến lược Tôn Tử vào kinh doanh & công nghệ.
   - Automatic contextual hashtag generation (`#ZaloOA`, `#MekongCLI`, etc.).
5. **Feed & Social Wall Publishing**:
   - Publish feed updates and promotional articles with title, body, and interactive links.

## Architecture

```
mekong zalo-oa
      │
      ├── (overview)         ── Executive customer engagement metrics & broadcast history
      ├── send [USER] [MSG]  ── Dispatch 1-on-1 customer message with optional template
      ├── broadcast [MSG]    ── Orchestrate campaign broadcast to target segments
      ├── followers          ── Inspect follower roster, demographics, and engagement
      ├── caption [TOPIC]    ── Generate Vietnamese marketing copy across 5 tones
      ├── post [CONTENT]     ── Publish post to Zalo Official Account feed
      └── status             ── Health check, WAL database telemetry, and message stats
```

## CLI Usage

```bash
// turbo
mekong zalo-oa [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong zalo-oa` | `[--json]` | Overview dashboard with total followers, messages sent, and active campaigns. |
| `mekong zalo-oa send` | `<user_id> <message> [--template TPL] [--mock] [--json]` | Send direct message to a follower (supports simulated `--mock` delivery). |
| `mekong zalo-oa broadcast`| `<message> [--title T] [--segment all\|vip\|lead] [--mock] [--json]` | Launch broadcast campaign across targeted audience. |
| `mekong zalo-oa followers`| `[--segment all\|vip\|lead] [--limit N] [--mock] [--json]` | List and inspect follower records and engagement levels. |
| `mekong zalo-oa caption`  | `<topic> [--tone vui_ve\|chuyen_nghiep\|sang_tao\|khuyen_mai\|binh_phap] [--json]` | Generate multi-tone Vietnamese social post caption with hashtags. |
| `mekong zalo-oa post`     | `<content> [--title T] [--link URL] [--mock] [--json]` | Publish article or update to Zalo feed. |
| `mekong zalo-oa status`   | `[--json]` | Telemetry report of database records, sent volume, and active segments. |

## Native MCP Tools Integration

Programmatic agents within the Mekong Fabric and Antigravity swarms access Zalo OA via 5 native MCP tools:

1. **`mekong_zalo_send(user_id: str, message: str, template: str = "")`**:
   Send direct notification or customer support message to a specific user.
2. **`mekong_zalo_broadcast(message: str, title: str = "Thông báo Zalo OA", target_segment: str = "all")`**:
   Orchestrate and dispatch campaign broadcast.
3. **`mekong_zalo_followers(segment: str = "all", limit: int = 50)`**:
   Retrieve follower demographics, interaction statistics, and tags.
4. **`mekong_zalo_caption(topic: str = "Sản phẩm", tone: str = "vui_ve")`**:
   Generate high-converting marketing copy with hashtags.
5. **`mekong_zalo_status()`**:
   Query aggregated analytics on messages, broadcasts, and audience metrics.

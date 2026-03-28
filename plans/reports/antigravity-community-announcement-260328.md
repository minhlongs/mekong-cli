# Mekong CLI Now Supports Antigravity IDE — 240+ Business Commands, Zero Config

> **TL;DR:** 21 workflow files adapted for Antigravity users. Run `/idea`, `/cook`, `/ship`, `/sales`, `/ops` and 240+ more commands directly in Antigravity IDE. No installation, no config — just clone and go.

---

## What Is This?

[Mekong CLI](https://github.com/longtho638-jpg/mekong-cli) is an open-source, AI-operated business platform with **342+ commands** across 6 layers: Founder, Business, Product, Engineering, Operations, and Studio.

Until now, these commands only worked on Claude Code. **Today, we're releasing full Antigravity IDE support** — 21 workflow files covering 240+ sub-commands, adapted for Antigravity's agent execution model.

## What You Get

| Layer | Workflows | Sub-commands | Example |
|-------|-----------|-------------|---------|
| Founder/Strategy | idea, studio, binh-phap | 46 | `/idea "AI restaurant platform for Vietnam"` |
| Business/Revenue | sales, marketing, business | 54 | `/sales qualify lead: Acme Corp` |
| Product | plan, quick-start, context | 29 | `/plan hard: add OAuth2 authentication` |
| Engineering | cook, dev, code, git, cto, ship | 93 | `/cook build the landing page` |
| Operations | ops, daily, approve, command | 60+ | `/daily` |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/longtho638-jpg/mekong-cli.git

# In Antigravity IDE, say:
"Read .agents/workflows/quick-start.md and execute for: my SaaS idea"
```

That's it. Antigravity reads the workflow files and executes them autonomously.

## How It Works

Original `.claude/commands/` (246 files) remain **100% untouched**. The new `.agents/workflows/` directory contains adapted versions:

| Claude Feature | Antigravity Equivalent |
|----------------|----------------------|
| `$ARGUMENTS` | User provides input in prompt |
| `allowed-tools` header | Antigravity auto-selects tools |
| Subagent spawning | Multi-agent orchestration |
| `// turbo` annotation | Supported (auto-run safe commands) |

Both systems run **side-by-side** — Claude Code users and Antigravity users share the same repo.

## The Binh Phap Framework

Mekong CLI embeds the **Binh Phap** (Art of War) strategic framework:

```
/binh-phap plan       → Strategic Planning
/binh-phap implement  → Parallel Execution
/binh-phap verify     → Verification
/binh-phap ship       → Deploy
```

Every command follows this cycle: **Plan → Execute → Verify → Ship**.

## Stats

- **21 workflow files** adapted for Antigravity
- **2,189 lines** of workflow instructions
- **240+ sub-commands** across 5 business layers
- **0 breaking changes** to existing codebase

## Links

- **GitHub:** [longtho638-jpg/mekong-cli](https://github.com/longtho638-jpg/mekong-cli)
- **Antigravity Guide:** [ANTIGRAVITY.md](https://github.com/longtho638-jpg/mekong-cli/blob/main/ANTIGRAVITY.md)
- **Workflows:** [.agents/workflows/](https://github.com/longtho638-jpg/mekong-cli/tree/main/.agents/workflows)
- **PR #16:** [feat: Antigravity Community Support](https://github.com/longtho638-jpg/mekong-cli/pull/16)

## Contributing

Want to add more workflows?

1. Fork the repo
2. Create a `.md` file in `.agents/workflows/`
3. Use YAML frontmatter: `description: "your description"`
4. Submit a PR

**License:** MIT

---

> *"Thien ly chi hanh, thuy o tuc ha"*
> *A journey of a thousand miles begins with a single step.*

Built by Antigravity x Mekong CLI community.

---
---

# Mekong CLI Hỗ Trợ Antigravity IDE — 240+ Lệnh Kinh Doanh, Không Cần Cấu Hình

> **Tóm tắt:** 21 file workflow dành cho Antigravity. Chạy `/idea`, `/cook`, `/ship`, `/sales`, `/ops` và 240+ lệnh khác trực tiếp trong Antigravity IDE. Không cần cài đặt, không cấu hình — chỉ cần clone và dùng.

---

## Đây Là Gì?

[Mekong CLI](https://github.com/longtho638-jpg/mekong-cli) là nền tảng kinh doanh mã nguồn mở, vận hành bởi AI, với **342+ lệnh** trên 6 tầng: Founder, Business, Product, Engineering, Operations và Studio.

Trước đây, các lệnh này chỉ hoạt động trên Claude Code. **Hôm nay, chúng tôi phát hành hỗ trợ đầy đủ cho Antigravity IDE** — 21 file workflow bao phủ 240+ lệnh con, được điều chỉnh cho mô hình thực thi agent của Antigravity.

## Bạn Nhận Được Gì?

| Tầng | Workflows | Lệnh con | Ví dụ |
|------|-----------|----------|-------|
| Founder/Chiến lược | idea, studio, binh-phap | 46 | `/idea "Nền tảng quản lý nhà hàng AI cho Việt Nam"` |
| Kinh doanh/Doanh thu | sales, marketing, business | 54 | `/sales qualify lead: Công ty ABC` |
| Sản phẩm | plan, quick-start, context | 29 | `/plan hard: thêm xác thực OAuth2` |
| Kỹ thuật | cook, dev, code, git, cto, ship | 93 | `/cook xây landing page` |
| Vận hành | ops, daily, approve, command | 60+ | `/daily` |

## Bắt Đầu Nhanh

```bash
# Clone repo
git clone https://github.com/longtho638-jpg/mekong-cli.git

# Trong Antigravity IDE, nói:
"Đọc .agents/workflows/quick-start.md và thực hiện cho: ý tưởng SaaS của tôi"
```

Xong. Antigravity đọc workflow files và tự động thực thi.

## Cách Hoạt Động

File gốc `.claude/commands/` (246 files) **không bị thay đổi**. Thư mục mới `.agents/workflows/` chứa phiên bản đã điều chỉnh:

| Tính năng Claude | Tương đương Antigravity |
|------------------|------------------------|
| `$ARGUMENTS` | Người dùng cung cấp input trong prompt |
| `allowed-tools` header | Antigravity tự chọn tools |
| Subagent spawning | Đa agent phối hợp |
| `// turbo` | Hỗ trợ (tự chạy lệnh an toàn) |

Cả hai hệ thống chạy **song song** — người dùng Claude Code và Antigravity dùng chung repo.

## Khung Chiến Lược Binh Pháp

Mekong CLI tích hợp khung chiến lược **Binh Pháp** (Tôn Tử Binh Pháp):

```
/binh-phap plan       → 始計 Lập Kế Hoạch
/binh-phap implement  → 軍爭 Triển Khai Song Song
/binh-phap verify     → 九地 Kiểm Chứng
/binh-phap ship       → 火攻 Triển Khai Production
```

Mọi lệnh tuân theo chu trình: **Kế Hoạch → Thực Thi → Kiểm Chứng → Triển Khai**.

## Thống Kê

- **21 file workflow** dành cho Antigravity
- **2.189 dòng** hướng dẫn workflow
- **240+ lệnh con** trên 5 tầng kinh doanh
- **0 thay đổi phá vỡ** mã nguồn hiện tại

## Liên Kết

- **GitHub:** [longtho638-jpg/mekong-cli](https://github.com/longtho638-jpg/mekong-cli)
- **Hướng dẫn Antigravity:** [ANTIGRAVITY.md](https://github.com/longtho638-jpg/mekong-cli/blob/main/ANTIGRAVITY.md)
- **Workflows:** [.agents/workflows/](https://github.com/longtho638-jpg/mekong-cli/tree/main/.agents/workflows)
- **PR #16:** [feat: Antigravity Community Support](https://github.com/longtho638-jpg/mekong-cli/pull/16)

## Đóng Góp

Muốn thêm workflow mới?

1. Fork repo
2. Tạo file `.md` trong `.agents/workflows/`
3. Dùng YAML frontmatter: `description: "mô tả ngắn"`
4. Gửi PR

**Giấy phép:** MIT

---

> *"Thiên lý chi hành, thuỷ ư túc hạ"*
> *Hành trình vạn dặm bắt đầu từ một bước chân.*

Xây dựng bởi cộng đồng Antigravity x Mekong CLI.

# Mekong CLI — Hệ Điều Hành AI Tự Động Cho Doanh Nghiệp Việt Nam

[![English](https://img.shields.io/badge/Language-English-blue.svg)](README.md)
[![Tiếng Việt](https://img.shields.io/badge/Ngôn%20Ngữ-Tiếng%20Việt-red.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open-Core: 25/25 Sẵn Sàng](https://img.shields.io/badge/Open--Core-25%2F25%20Ready-brightgreen.svg)](#kiến-trúc-open-core-25-bước)
[![CycloneDX 1.5](https://img.shields.io/badge/SBOM-CycloneDX%201.5-blueviolet.svg)](#)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](#)
[![Dual-Rail: VietQR + NOWPayments](https://img.shields.io/badge/Dual--Rail-VietQR%20%7C%20NOWPayments-success.svg)](#bảng-giá-raas-thương-mại--thanh-toán-dual-rail)

> Runtime AI tự động mã nguồn mở cho Công ty Một Người, Lập trình viên Solo và Doanh nghiệp Vừa & Nhỏ (SME) Việt Nam.
> Vận hành toàn bộ khối kế toán, tuân thủ thuế, sản xuất video marketing và hậu mãi chăm sóc khách hàng bằng AI — tất cả chạy trên chính hạ tầng của bạn.

---

## Mekong CLI là gì?

Mekong CLI là một **runtime tự động mã nguồn mở** (open-source autonomous runtime) được thiết kế cho công ty một người và doanh nghiệp nhỏ Việt Nam. Một người điều hành có thể giao các mục tiêu kinh doanh cho đội ngũ AI agents chuyên biệt để lên kế hoạch, thực thi, kiểm chứng (PEV), tự sửa lỗi và thanh toán công cụ — chạy cục bộ hoặc trên cloud workers được quản lý.

Hệ thống này vận hành trực tiếp nền tảng doanh nghiệp AI [mekongmind.com](https://www.mekongmind.com).

### Ba Phễu Kinh Doanh Cốt Lõi

1. **Zalo OA (`zalo_oa`)** — Tự động hóa giao tiếp khách hàng, nhắn tin thời gian thực, và thu thập tiềm năng qua Zalo Official Account.
2. **Thuế & Kế toán (`thue_dnvn` / `ke_toan`)** — Tuân thủ toàn diện pháp luật Việt Nam: Thuế TNCN, Thu nhập doanh nghiệp (TNDN), Thuế GTGT, và phát hành hóa đơn điện tử theo Nghị định 123 / Thông tư 78 (`TT78`).
3. **Nhà Máy Video AI (`sophia`)** — Tự động hóa sản xuất video marketing AI trên hạ tầng edge (Cloudflare Workers).

Trên toàn bộ phễu kinh doanh, **39 nhóm lệnh Typer CLI** được ghép qua `build_app()` (`python3 -c "from src.cli.app_setup import build_app; print(len(build_app().registered_groups))"`), điều hướng bởi harness xác minh Plan-Execute-Verify (PEV) mang tính tất định.

---

## Kiến Trúc Open-Core 25 Bước

Mekong CLI áp dụng nghiêm ngặt **Kiến trúc Open-Core 25 bước**, tách biệt hoàn toàn runtime tự động cục bộ giấy phép MIT với Control Plane Cloud RaaS (Robot-as-a-Service) doanh nghiệp. Catalog 25 bước này được kiểm toán byte-level và được đánh giá đạt sẵn sàng 100.0% qua `src/core/opencore/phase_560_opencore_saas_readiness_engine.py`.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Mekong CLI (MIT Open-Core)               │
                    │   Local Runtime • CapabilityBus • BYOK • 39 Commands   │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                          PLG Upsell Bridge / BYOK / Status Polling
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               Cloud RaaS Control Plane                 │
                    │     HMAC-SHA256 RAAS_LICENSE_KEY • MCUBilling          │
                    │  Dual-Rail Checkout: VietQR (Napas) | NOWPayments (USDT)│
                    │  Multi-Tenant RBAC • Immutable TT78/SOC2 Audit Ledger  │
                    └────────────────────────────────────────────────────────┘
```

25 bước canonical trải rộng trên 5 Phase vòng đời:

### Phase 1: `PHASE_1_SPLIT_AND_HYGIENE`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 01 | `git-history-secret-purge` | Lịch sử commit sạch, không credential | Không rò rỉ key production |
| 02 | `oss-vs-ee-directory-split` | `src/core` + `src/cli` (MIT Public) | Cô lập thư mục private `apps/` + `billing/` |
| 03 | `gitignore-quarantine-lock` | Rào chắn cách ly (quarantine) `.gitignore` | Chặn dữ liệu tenant khỏi git |
| 04 | `env-example-byok-template` | Mẫu cấu hình BYOK `.env.example` | Két chứa env trên cloud được quản lý |
| 05 | `mit-license-and-sbom` | Giấy phép `LICENSE` MIT + CycloneDX 1.5 SBOM | Điều khoản SLA thương mại |

### Phase 2: `PHASE_2_PLUGIN_AND_SEAMS`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 06 | `capability-bus-interfaces` | Giao thức `CapabilityBus` (`InMemoryCapabilityBus`) | Managed cloud providers & swarms |
| 07 | `byok-local-adapters` | API key người dùng tự cấp (BYOK) | Inference được host tự động |
| 08 | `cloud-bridge-webhooks` | Client `WatcherBridge` & stubs sự kiện | Hosted webhook ingestion & distribution |
| 09 | `local-sandbox-runtime` | Thực thi CLI trong sandbox single-operator | Multi-region cloud worker pool |
| 10 | `versioned-openapi-sdk` | SDK công khai & OpenAPI schemas | API gateway đo lường (`api.cashclaw.cc`) |

### Phase 3: `PHASE_3_CLOUD_CONTROL_PLANE`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 11 | `jwt-license-gate` | Bypass cục bộ trong môi trường test | FastAPI HMAC-SHA256 `license_gate` |
| 12 | `mcu-credit-metering` | Sổ ghi credit local (mock) | `MCUBilling` + HTTP 402 recharge flow |
| 13 | `tiered-rate-limiting` | Không giới hạn request ở cục bộ | Rate limit theo tier (`BASIC` tới `MASTER`) |
| 14 | `managed-worker-queues` | Hàng đợi task in-memory | Redis Cluster + Cloudflare Durable Objects |
| 15 | `encrypted-key-vault` | Lưu trữ `.env` cục bộ + sanitizer | Két key tenant mã hóa bằng Cloud KMS |

### Phase 4: `PHASE_4_ENTERPRISE_MONETIZATION`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 16 | `multi-tenant-rbac-isolation` | Profile người dùng đơn lẻ | Cô lập Multi-Tenant + RBAC doanh nghiệp |
| 17 | `compliance-audit-ledger` | Log stdout có cấu trúc & trace telemetry | Immutable SHA-256 TT78 / SOC2 vault |
| 18 | `always-on-cloud-daemon` | Chạy lệnh foreground | 24/7 autonomous cloud daemon với SLA 99.9% |
| 19 | `strategy-recipe-marketplace` | Recipe nội bộ & cộng đồng | Marketplace alpha được kiểm chứng |
| 20 | `payment-webhook-activation` | Abstraction `PaymentProvider` | IPN Dual-Rail chống replay (VietQR / NOWPayments) |

### Phase 5: `PHASE_5_PLG_GROWTH_AND_GOVERNANCE`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 21 | `sixty-second-quickstart` | Chạy 60 giây (`git clone + mekong`) | Provision cloud workspace 1-click |
| 22 | `cli-to-cloud-upsell-prompt` | Banner cảnh báo hết hạn mức | Trải nghiệm nâng cấp liền mạch qua `recharge_url` |
| 23 | `ci-leak-and-loc-gate` | Pre-commit ruff, kiểm tra LOC (`<= 185 LOC`) | Tự động hóa ranh giới trong CI |
| 24 | `public-benchmark-trust-badge` | Bộ kiểm thử pytest tái lập được | Xác minh uy tín doanh nghiệp & telemetry |
| 25 | `cla-and-trademark-policy` | Hướng dẫn đóng góp PR mã nguồn mở (`CLA`) | Bảo vệ trademark & quyền SaaS thương mại |

---

## Quickstart 60 Giây (Step 21: `sixty-second-quickstart`)

Chạy được trong chưa đầy 60 giây trên macOS hoặc Linux:

```bash
# 1. Clone repository
git clone https://github.com/minhlongs/mekong-cli.git
cd mekong-cli

# 2. Khởi tạo môi trường & shell wrapper
source scripts/shell-init.sh

# 3. Cấu hình Bring-Your-Own-Key (BYOK)
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="sk-or-v1-key-cua-ban"
export LLM_MODEL="anthropic/claude-sonnet-4"

# 4. Chạy CLI
mekong
```

### Thử một Mục Tiêu Tự Động:

```bash
# Chạy tính thuế TNDN tự động với xác minh PEV
mekong run --goal "Tinh thue TNDN quy 1 nam 2026 cho doanh nghiep thuong mai dien tu"

# Quy trình OPC Doanh nghiệp Một Người (Vòng đời 2-Goal chạy offline)
mekong opc validate-pack
mekong opc proposal --wait-approval
mekong opc status --run-id <run_id>
mekong opc decide --run-id <run_id> --decision approve
mekong run --pack client-proposal-followup
```

---

## Bảng Giá RaaS Thương Mại & Thanh Toán Dual-Rail

Khi quy mô công ty vượt quá thực thi cục bộ, hãy nâng cấp lên **Cloud RaaS Control Plane** để sử dụng worker swarms được host, daemon 24/7 và sổ cầu tuân thủ bất biến.

Các bản tier thương mại được hỗ trợ qua **Dual-Rail Checkout**:
- **Thanh toán Nội địa Việt Nam (`vietqr`):** Chuyển khoản Napas 247 bằng VietQR EMVCo động và tự động đối soát (auto-reconciliation) tức thì.
- **Thanh toán Web3 Quốc tế (`nowpayments`):** NOWPayments USDT / Crypto IPN nạp credit tự động ngay lập tức.
- *Polar.sh Decommission:* `POST /webhook/polar` đã ngừng vận hành và trả về `HTTP 410 Gone` (`polar_rail_decommissioned`).

| Tier | Giá (USD) | Giá (VND) | Hạn Mức MCU/tháng | Tính Năng Kèm Theo |
|:---|:---:|:---:|:---:|:---|
| **`BASIC`** | **$199** /tháng | **4,975,000 ₫** | **1,500 MCU** | Hosted Control Plane, basic CLI agents, BYOK standard, thanh toán VietQR. |
| **`PREMIUM`** | **$399** /tháng | **9,975,000 ₫** | **4,000 MCU** | Multi-Agent Swarm, cloud task queues, synchronization telemetry. |
| **`ENTERPRISE`** | **$799** /tháng | **19,975,000 ₫** | **10,000 MCU** | Multi-Tenant RBAC, sổ audit TT78 bất biến, encrypted key vault (KMS). |
| **`MASTER`** | **$4,999** /năm | **124,975,000 ₫** | **100,000 MCU** | White-label portal, always-on cloud daemon 24/7, SLA chuyên dụng. |

*(MCU: Mekong Compute Unit. 1 credit = 1 unit tính toán của autonomous agent. Tỷ giá tham chiếu: 25,000 VND / USD).*

### Checkout API Tức Thì

```bash
# Tạo phiên checkout VietQR Napas 247
curl -X POST https://api.cashclaw.cc/v1/checkout \
  -H "Content-Type: application/json" \
  -d '{"tier": "PREMIUM", "rail": "vietqr", "email": "founder@example.vn"}'

# Kích hoạt license key được ký mã hóa (Step 11b)
mekong license activate --key "MEKONG-RAAS-v1.<payload_b64>.<sig>"
```

---

## Design Intelligence

Hệ thống kiểm tra chất lượng design native, được điều chỉnh từ Hallmark (MIT). Kiểm toán, nghiên cứu và xây dựng design systems bằng structured schemas và deterministic gates:

```bash
mekong ui audit page.html                 # Chạy deterministic gate + 9-axis score
mekong ui study page.html --name landing # Sinh DesignDNA (design.md / design.json)
mekong ui approve landing                # Lưu DNA đã duyệt để tái sử dụng đa-agent
mekong ui benchmark                      # Bộ xác minh chống gian lận
```

---

## Kiểm Chứng & Cổng Chất Lượng

Mọi pull request và bản phát hành đều được kiểm chứng qua automated gates nghiêm ngặt:

```bash
# 1. Chạy 8 bộ test ranh giới Open-Core & RaaS
pytest tests/test_opencore_saas_25_step_suite.py \
       tests/test_core_boundary.py \
       tests/test_dual_rail_checkout.py \
       tests/test_raas_license_verifier.py \
       tests/test_durian_grab_honest_diagnosis.py \
       tests/test_idea_run_blueprint_writing.py \
       tests/test_opencore_git_boundary_guard.py \
       tests/test_github_content_25_step_sync.py -v

# 2. Kiểm tra Độ Sẵn Sàng Open-Core (100.0%)
python3 -c "from src.core.opencore.phase_560_opencore_saas_readiness_engine import OpenCoreSaasReadinessEngine as E; r=E.audit_repository('.'); assert r.verdict.value=='PUBLIC_GITHUB_SAAS_READY' and r.completion_pct==100.0; print('Open-Core Audit:', r.verdict.value, r.completion_pct)"

# 3. Kiểm tra 0 byte thay đổi trên Open-Core Catalog
git diff --exit-code src/core/opencore/phase_559_opencore_25_step_catalog.py
```

---

## Đóng Góp & Quản Trị

Chúng tôi hoan nghênh đóng góp theo mô hình Open-Core:
- Đọc [Hướng Dẫn Đóng Góp](CONTRIBUTING.md) và [Quy Tắc Ứng Xử](CODE_OF_CONDUCT.md).
- Báo cáo bảo mật: vui lòng xem [SECURITY.md](SECURITY.md).
- Đặc tả kiến trúc: xem [docs/architecture.md](docs/architecture.md).

## Giấy Phép

Core của Mekong CLI là phần mềm mã nguồn mở theo giấy phép [MIT License](LICENSE).
Copyright (c) 2026 Mekong CLI Contributors.

# Original User Request

## Initial Request — 2026-05-26T16:16:42Z

Build **Anti-Gravity 2.0**: a terminal-native, hybrid local-first coding-agent runtime written in Rust. It orchestrates local Qwen-35B models (via llama.cpp with Apple Silicon Metal acceleration) and official Claude Code CLI escalation logic.

Working directory: /Users/macbook/mekong-cli/antigravity/hybrid_runtime
Integrity mode: development

## Requirements

### R1. Hybrid Routing Engine
Build a routing layer that intercepts coding tasks and determines the execution path:
- **Local Route**: Qwen via llama.cpp server at `http://localhost:8080/v1` for autocomplete, syntax fixes, shell analysis, and simple edits.
- **Cloud Route**: Claude 3.5 Sonnet or Opus via Anthropic API for architecture planning, complex migrations, and deep reasoning.
- The router must dynamically decide based on token budget, latency limits, and heuristic regex keywords.

### R2. Core Agent Loop & Tool Executions
Implement a zero-dependency, lightweight agent loop running the following cycle:
`observe -> retrieve -> reason -> patch -> execute -> diff -> validate -> repeat`
- Integrated tools: local shell commands, git, ripgrep (`rg`), tree-sitter symbol indexing, and ast-grep.
- Tool executions must stream stdout, support cancellation/timeouts, and request interactive approval for all file-writing and execution tools.

### R3. AST Indexer & SQLite State Persistence
Create a local indexer powered by `tree-sitter` (or `ast-grep`) that maps repository classes, functions, and imports into a lightweight SQLite database at `.git/antigravity/session.db`.
- Maintain a transaction log of session states, KV cache ranges, and past patches.
- Support context compaction by truncating large logs and retaining class/method headers instead of full source files.

### R4. Apple Silicon (Metal) Inference Integration
Configure and launch a local llama.cpp server optimized for Apple Silicon (M1 Max 64GB UMA):
- Set thread count to match Performance cores (8 threads).
- Offload all layers to GPU (`--n-gpu-layers 99`) and enable Flash Attention (`--flash-attn`).
- Prevent memory mapping bottlenecks with `--no-mmap` to load weights strictly to RAM.

## Acceptance Criteria

### Routing & Ingestion
- [ ] Heuristic router correctly classifies tasks, sending "add docstrings" or "format code" to Qwen and "restructure auth package" to Claude.
- [ ] Context compactor reduces input sizes to under 16,384 tokens for local model execution by replacing full source text with signature summaries.

### Persistence & Indexing
- [ ] SQLite database stores file paths, hash values, and extracted AST symbols (classes, methods, kind, line numbers).
- [ ] Querying symbols (e.g., matching a function signature) runs in under 5ms from the SQLite index.

### Loop execution & UI
- [ ] The CLI starts up in less than 2s and provides streaming status messages.
- [ ] Destructive tools (write/delete/execute) block until the user enters `y/yes` in the TTY.
- [ ] Validated tests verify that patches compile and pass local test suites.
- [ ] Run scripts (`launch-llama.sh`, `run-claude-hybrid.sh`) function correctly.

## Follow-up — 2026-05-27T14:55:36Z

Optimize the code generation intelligence of CheetahClaws running with local LLMs (Qwen3.6 35B) to achieve a high coding success rate, targeting Claude-level formatting, logic, and self-correction behavior.

Working directory: /Users/macbook/.local/share/uv/tools/cheetahclaws/lib/python3.14/site-packages
Integrity mode: development

## Requirements

### R1. Prompt and Overlay Tuning
Optimize the system prompt templates and provider/model overlays (specifically prompts/overlays/qwen.md and related steering prompts) to:
- Enforce strict syntax and formatting (such as proper markdown diff format and avoiding empty placeholders).
- Inject structured reasoning instructions (step-by-step thinking templates optimized for Qwen3.6).
- Encourage robust usage of available workspace tools.

### R2. Core Engine Self-Correction (Python)
Modify CheetahClaws' execution core (such as the agent loop in agent.py or verification hooks) to:
- Implement a syntax-checking phase (e.g., Python AST parsing, basic JavaScript syntax verification, or linter check) on any code outputted or edited.
- Automatically trigger a self-correction prompt to the LLM if a syntax error, lint failure, or test failure is detected, allowing it to auto-repair its output before concluding the turn.

### R3. Automated Evaluation Suite
Create an automated benchmarking script (e.g., at tests/bench_coding.py or under .cheetahclaws/) containing 5 diverse coding tasks (e.g., string manipulation, markdown table parser, regex extraction, bug-fix, and structure output generation) to measure the LLM's success rate quantitatively.

## Acceptance Criteria

### Quality & Accuracy
- [ ] The benchmark suite passes with a success rate of 80% (4/5 tasks) or higher under local Qwen3.6 execution.
- [ ] Any code output containing python syntax errors is caught and auto-corrected by the engine's new self-correction loop.
- [ ] No regression is introduced in other CheetahClaws features (e.g., commands, multi-agent communication, or REPL interaction).

## Follow-up — 2026-05-27T15:50:46Z

The project goal is to perform a deep system audit and propose a production-grade architecture refactor for a hybrid sovereign AI operating system stack running 24/7 as a persistent autonomous organization on a MacBook M1 Max (64GB RAM / 2TB SSD) local-first environment.

Working directory: /Users/macbook/mekong-cli
Integrity mode: demo

## Verification Resources
- Main benchmark suite: tests/bench_coding.py (file:///Users/macbook/mekong-cli/tests/bench_coding.py)
- Local model runtime target: Ollama (http://localhost:11434)
- CheetahClaws codebase: /Users/macbook/.local/share/uv/tools/cheetahclaws/lib/python3.14/site-packages

## Requirements

### R1. Deep System Audit
Perform a rigorous analysis of all 11 system layers (reasoning, routing, coding swarm, orchestration, workflow graph, memory, tool, execution runtime, observability, persistence, agent communication). Identify bottlenecks, unnecessary cloud dependencies, context/token waste, concurrency choke points, and thermal/performance risks on Apple Silicon.

### R2. Live Orchestration & Inference Verification
Inspect the CheetahClaws package source, check Ollama port 11434 status/throughput, and run tests/bench_coding.py to evaluate the actual coding and self-correction success rate using local models.

### R3. Production Architecture Redesign
Provide a detailed system design specification outlining model roles (routing policies, escalation chains), local-first runtime stack (Ollama vs. llama.cpp vs. MLX), simplified LangGraph supervisor topology, and an optimized hot/cold/episodic/semantic memory layout.

## Acceptance Criteria

### Execution & Verification
- Successful query and health check of the Ollama server at http://localhost:11434.
- Execution of the benchmark suite tests/bench_coding.py with documented outputs, error tracebacks (if any), and success rate metrics.

### System Audit Report
- Scorecard evaluating each layer on reliability, maintainability, latency, cognitive/cost efficiency, and scalability.
- Specific bottlenecks identified regarding local inference concurrency, Apple Silicon memory pressure, and CheetahClaws orchestration overhead.

### Refactoring Blueprint
- Complete architecture topology mapping routing rules, escalation triggers, and tool boundaries.
- Memory architecture spec detailing SQLite/Redis utilization, semantic memory drift prevention, and context pruning.

## Follow-up — 2026-05-28T07:16:24Z

Project: Run comprehensive codebase quality checks (/code) and verification on the Sophia AI Factory repository, ensuring all tests pass and static checks are clean.

Working directory: /Users/macbook/projects/sophia-ai-factory
Integrity mode: development

## Requirements

### R1. Static Analysis Verification
Ensure that the codebase compiles without type-safety errors and is free of linting errors.

### R2. Test Suite Completion
Ensure all unit and integration tests inside `apps/sophia-ai-factory` run successfully and pass.

### R3. Production Build Validation
Ensure the production Next.js application builds successfully using the Cloudflare wrangler/opennextjs setup.

## Acceptance Criteria

### Static Checks
- [ ] ESLint execution in `apps/sophia-ai-factory` returns `0` errors.
- [ ] `tsc --noEmit` execution in `apps/sophia-ai-factory` returns `0` errors.

### Automated Tests
- [ ] Running `npx vitest run --maxWorkers=1` compiles and passes all test suites in the app.

### Build Verification
- [ ] Running `npm run build` completes successfully without errors.

## Follow-up — 2026-05-28T07:30:03Z

Audit and polish the Next.js CRM Web App UI/UX for mobile-responsiveness, accessibility, dark mode consistency, and interactive feedback using the `ui-ux-pro-max` style guide.

Working directory: /Users/macbook/nhipdieuxanh-agent
Integrity mode: development

## Requirements

### R1. UI/UX and Accessibility Audit
Audit the main application views (Dashboard, Kanban, Leads, Billing, Settings) against the `ui-ux-pro-max` criteria. Ensure contrast ratios meet WCAG 2.1 AA (4.5:1 for text, 3:1 for interactive elements), and all elements have proper ARIA attributes and focus styles.

### R2. Mobile Responsiveness and Touch Optimization
Ensure the interface is fully responsive down to 375px width with no horizontal scroll overflows. Make sure all touch targets for buttons, links, and cards are at least 44x44pt, using spacing and padding standard tokens (4/8dp spacing rhythm). Ensure safe areas are respected.

### R3. Theme & Contrast Alignment
Hardcode no colors. Refactor any raw hex values to semantic Tailwind tokens. Verify that all components render correctly in both dark and light modes, with clear separation of cards/sheets from backgrounds.

### R4. Automated Testing
Verify the UI changes using the existing Vitest unit tests and Playwright E2E tests, ensuring no regression is introduced.

## Acceptance Criteria

### Visual Design
- [ ] No emojis are used as structural icons in navigation or settings (use Lucide SVG icons instead).
- [ ] All interactive elements display clear pressed/focus states without shifting layout bounds.
- [ ] Borders and separators are visible and distinct in both light and dark modes.

### Mobile Usability
- [ ] App dashboard, leads page, and kanban board do not trigger horizontal scrolls on 375px width.
- [ ] All primary CTAs and interactive icons have touch targets of at least 44x44pt.
- [ ] Sticky headers and bottom navigation bar do not overlap mobile browser safe-areas.

### Verification
- [ ] All 120 backend/RAG tests (`pytest`) pass successfully.
- [ ] All 18 frontend unit tests (`npm run test` in `web`) pass successfully.
- [ ] Playwright E2E test suite (`npx playwright test`) passes 100%.

## Follow-up — 2026-05-28T09:17:00Z

Establish a comprehensive brand identity system and visual assets for the "Nhịp Điệu Xanh" green-energy and real-estate platform.

Working directory: /Users/macbook/nhipdieuxanh-agent/brand
Integrity mode: development

## Requirements

### R1. Color Palette System
Generate a standardized brand color system based on the green-energy primary theme (`#10B981` Emerald). Define HSL/HEX color tokens including:
- Primary (Light/Medium/Dark)
- Neutral/Backgrounds (Light/Dark themes)
- Semantics (Success, Warning, Error)
Save these color tokens as a JSON configuration file `brand_tokens.json`.

### R2. Typography Scale
Configure a typography system matching "Outfit" (for headings) and "Inter" (for body text). Define scale rules for size, line heights, and weights (500, 600, 700 for headings; 400, 500 for body).

### R3. Logo Assets Generation
Generate standard logo variations in SVG format:
- Primary Logo (Full color + Typography)
- Monochrome Logo (Black and White versions)
- Brand Symbol Icon
- Favicon (16x16 / 32x32 SVG)
All assets must be saved under the `logos/` subdirectory.

### R4. Brand Guidelines Document
Compile the tokens and usage guidelines into a single, clean static HTML guidelines document (`guidelines.html`). It must display the color blocks, type scales, logo grids, and Do's/Don'ts rules clearly with CSS Styling.

## Acceptance Criteria

### Asset Validity
- [ ] Directory `/Users/macbook/nhipdieuxanh-agent/brand/logos/` contains at least four distinct SVG files (`logo-primary.svg`, `logo-monochrome.svg`, `logo-symbol.svg`, `favicon.svg`).
- [ ] All generated SVG files are valid XML documents.
- [ ] File `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json` contains valid JSON structure defining all color tokens and typography scale rules.

### Guidelines Output
- [ ] File `/Users/macbook/nhipdieuxanh-agent/brand/guidelines.html` exists.
- [ ] Opening `guidelines.html` in a web browser renders the complete branding guide without console errors or broken resource links.

## Follow-up — 2026-05-28T09:20:47Z

Project: Audit and resolve typescript compilation, type definition, and package dependency resolution errors across the `mekong-cli` monorepo workspace to achieve a clean compilation.

Working directory: /Users/macbook/mekong-cli
Integrity mode: development

## Requirements

### R1. Remediate Monorepo Type Definitions and Workspace Dependencies
Analyze and resolve package dependency mismatches in the monorepo workspace (such as the missing `@cleocode/caamp` package or workspace reference in `packages/cleo-new`) and ensure that all required type definition packages (such as `@cloudflare/workers-types` and package node modules) are correctly installed and resolved.

### R2. Clean TypeScript Compilation
Ensure that the entire monorepo compiled via TypeScript typechecking runs cleanly without any compilation errors.

### R3. Static Linter Verification
Verify that the codebase is free of linting errors.

## Acceptance Criteria

### Compilation & Build Quality
- [ ] `npx tsc --noEmit` executes successfully with exit code `0` and `0` errors.
- [ ] `npx eslint .` (or local package lint check) executes with `0` errors.

## Follow-up — 2026-05-30T06:55:34Z

Phát triển mở rộng hệ thống Nhịp Điệu Xanh AI CRM: tích hợp thanh toán VietQR (SePay), nâng cấp giao diện Landing Page, và viết tài liệu hướng dẫn vận hành chi tiết.

Working directory: `/Users/macbook/mekong-cli`
Integrity mode: `development`

## Requirements

### R1. Tích hợp cổng thanh toán VietQR (SePay)
- Hiện thực API Endpoint (`POST /api/payments/sepay`) để tiếp nhận và xác thực webhook callback từ SePay khi có giao dịch chuyển khoản thành công.
- Cập nhật trạng thái đặt cọc hoặc giao dịch của Lead tương ứng trong cơ sở dữ liệu PostgreSQL.
- Tạo component/modal hiển thị mã VietQR động cùng thông tin chuyển khoản (tài khoản, số tiền, nội dung chuyển khoản tự động kèm mã giao dịch) tại Landing Page khi người dùng đặt chỗ.

### R2. Tối ưu hóa Landing Page & Trải nghiệm UI/UX
- Thiết kế và nâng cấp Landing Page (`apps/nhipdieuxanh/app/page.tsx`) theo chuẩn giao diện Emerald Green (`#10B981`) sang trọng và hiện đại.
- Thêm hiệu ứng micro-animations cho nút bấm (độ rộng click target >= 44px), loading states rõ ràng khi đang gọi API, và tối ưu hoàn toàn cho mobile responsive.

### R3. Tài liệu hướng dẫn vận hành (Operations Guide)
- Viết tài liệu hướng dẫn vận hành chi tiết tại `docs/nhipdieuxanh_operations.md` giải thích cách khởi tạo cơ sở dữ liệu, chạy local, kiểm thử các API (Leads, FAQ, Payments), và cách xử lý sự cố.

## Acceptance Criteria

### API & Payments
- [ ] Endpoint `POST /api/payments/sepay` nhận mock webhook payload từ SePay và cập nhật trạng thái thanh toán thành công của Lead trong PostgreSQL.
- [ ] Giao diện hiển thị đúng mã QR VietQR động (chứa URL định dạng `https://img.vietqr.io/image/...`) dựa trên thông tin số tiền và nội dung chuyển khoản động.

### UI/UX & Responsive
- [ ] Modal đặt chỗ/thanh toán hiển thị đầy đủ thông tin, không bị vỡ layout trên màn hình nhỏ.
- [ ] Target tương tác có chiều cao/rộng tối thiểu 44px và các nút bấm có trạng thái hover/loading trực quan.

### Documentation
- [ ] File `docs/nhipdieuxanh_operations.md` mô tả rõ ràng các bước vận hành hệ thống.

## Follow-up — 2026-05-30T07:18:14Z

Thực hiện kiểm thử, phân tích cấu trúc, sơ đồ hóa kiến trúc luồng dữ liệu, phát hiện các điểm rủi ro kỹ thuật, và cập nhật/bổ sung bộ tài liệu kỹ thuật toàn diện cho toàn bộ kho mã nguồn (codebase) hiện tại.

Working directory: `/Users/macbook/mekong-cli`
Integrity mode: `development`

## Requirements

### R1. Kiểm toán cấu trúc kho mã nguồn (Repository Audit)
- Sơ đồ hóa chi tiết vai trò, ranh giới trách nhiệm, các dependency nội bộ/ngoài, vai trò runtime, và mức độ rủi ro của từng thư mục/thành phần chính (`apps/`, `packages/`, `services/`, `scripts/`, `infra/`, `configs/`, `tooling/`, CI/CD, `tests/`, `docs/`).

### R2. Sơ đồ hóa kiến trúc & Luồng dữ liệu (Architecture & Data Flow)
- Xác định và làm rõ các entrypoints của hệ thống, luồng di chuyển dữ liệu/yêu cầu, các tác vụ chạy nền (background jobs), hệ thống hàng đợi (queue), bộ lập lịch (cron/schedulers), tích hợp bên thứ ba, quản lý state, cơ chế lưu trữ (persistence), luồng auth/authz, sơ đồ triển khai (deployment topology), quản lý biến môi trường, và feature flags.

### R3. Bổ sung & Hoàn thiện tài liệu kỹ thuật (Documentation Backfill)
- Cập nhật hoặc viết mới các tài liệu hướng dẫn vận hành chuẩn hóa tại thư mục `docs/` bao gồm:
  - `README.md` (Tổng quan dự án)
  - `docs/setup-guide.md` (Hướng dẫn cài đặt)
  - `docs/local-development-guide.md` (Hướng dẫn phát triển cục bộ)
  - `docs/env-vars.md` (Tài liệu chi tiết biến môi trường)
  - `docs/deployment-notes.md` (Ghi chú triển khai/deploy)
  - `docs/testing-guide.md` (Hướng dẫn chạy test)
  - `docs/troubleshooting.md` (Cách khắc phục lỗi phổ biến)
  - `docs/architecture-overview.md` (Tổng quan kiến trúc)
  - `docs/glossary.md` (Bảng thuật ngữ dự án)
  - `docs/onboarding.md` (Tài liệu hướng dẫn onboard cho lập trình viên mới)

### R4. Đánh giá rủi ro & Phát hiện nợ kỹ thuật (Gap & Risk Analysis)
- Phát hiện và ghi nhận các mẫu ngầm định (implicit patterns), nợ kỹ thuật (technical debt), mã nguồn thừa/chết (dead code), code trùng lặp, các điểm thắt cổ chai (bottlenecks), và lỗ hổng bảo mật/cấu hình thông tin nhạy cảm. Phân loại mức độ tự tin (High, Medium, Needs Verification).

## Acceptance Criteria

### Audit & Architecture Outputs
- [ ] Tạo hoặc cập nhật sơ đồ kiến trúc hệ thống rõ ràng trong `docs/architecture-overview.md` (sử dụng Mermaid diagram nếu phù hợp).
- [ ] Tài liệu `docs/architecture-overview.md` giải thích chi tiết step-by-step luồng xử lý yêu cầu và tích hợp dịch vụ.

### Knowledge & Documentation Backfill
- [ ] Tất cả 10 đầu mục tài liệu kỹ thuật nêu ở yêu cầu R3 đều được tạo mới hoặc cập nhật đầy đủ thông tin thực tế, không chứa placeholder trống.
- [ ] Tài liệu `docs/env-vars.md` liệt kê 100% các biến môi trường thực tế đang được sử dụng trong codebase kèm mô tả và giá trị ví dụ.

### Risk & Tech Debt Catalog
- [ ] Tạo tài liệu báo cáo rủi ro `docs/codebase_risk_report.md` liệt kê các nợ kỹ thuật, code trùng lặp hoặc điểm nghẽn hiệu năng đã xác thực.

## Follow-up — 2026-05-30T11:54:34Z

Thực hiện kiểm toán kiến trúc, lập bản đồ vận hành (system mapping), đánh giá độ tin cậy và bảo mật, tối ưu hóa nền tảng (platformization) cho toàn bộ kho mã nguồn `mekong-cli` theo tiêu chuẩn kỹ thuật Staff/Principal Engineer ("ABSOLUTE MODE").

Working directory: `/Users/macbook/mekong-cli`
Integrity mode: development

## Requirements

### R1. Kiểm toán & Bản đồ hệ thống (Subsystem Mapping & Audit)
Phân tích và lập bản đồ chi tiết cho từng subsystem chính (`apps/nhipdieuxanh`, `packages/ask-core`, `apps/nhipdieuxanh-orchestrator`, `packages/mekong-cli-core`). Đối với mỗi subsystem, tạo tài liệu chi tiết bắt buộc phải gồm:
1. **Purpose**: Vai trò nghiệp vụ và kỹ thuật.
2. **Entry Points**: Điểm khởi chạy / luồng chạy chính.
3. **Runtime Lifecycle**: Vòng đời chạy chi tiết từng bước.
4. **State Management**: Nơi lưu trữ và thay đổi trạng thái.
5. **Dependencies**: Các dependency nội bộ và bên ngoài.
6. **Failure Modes**: Các kịch bản lỗi có thể xảy ra.
7. **Recovery Behavior**: Cơ chế phục hồi hiện tại.
8. **Scale Limits**: Giới hạn chịu tải khi tăng quy mô gấp 10 lần.
9. **Security Surface**: Điểm phơi nhiễm bảo mật tiềm năng.
10. **Observability**: Cách thức debug và ghi nhận sự cố.
11. **Technical Debt**: Các nợ kỹ thuật tồn tại.
12. **Missing Knowledge**: Điểm chưa rõ ràng cần xác minh thêm.

### R2. Đánh giá rủi ro an toàn (Reliability & Security Gap Analysis)
Tìm kiếm và đánh giá các rủi ro liên quan đến:
* Kết nối PostgreSQL/SQLite và khả năng xử lý concurrency lock.
* Event-driven queues (Kafka) và block chain notarization (Geth node).
* Masking thông tin cá nhân (Decree 13 PII compliance).
* Các điểm hardcoded cấu hình API.

### R3. Báo cáo Gap Analysis & Remediation Roadmap
Tạo báo cáo tổng hợp rủi ro phân loại theo mức độ ưu tiên:
* **P0 — Existential Risks**: Rò rỉ thông tin nhạy cảm, lỗi mất dữ liệu.
* **P1 — Scale Blockers**: Các điểm thắt nút cổ chai dưới tải cao.
* **P2 — Velocity Killers**: Code trùng lặp, thiếu test hoặc cấu hình phức tạp.
* **P3 — Optimization**: Các điểm tối ưu hóa tiềm năng.

## Acceptance Criteria

### Documentation Coverage
- [ ] Tất cả các subsystem nêu trên đều có file tài liệu chi tiết riêng biệt định dạng Markdown tại `docs/absolute-audit/` tuân thủ đầy đủ 12 hạng mục thông tin bắt buộc.
- [ ] Có sơ đồ Mermaid chi tiết mô tả luồng chạy runtime và mối quan hệ dependency giữa các subsystem tại `docs/absolute-audit/architecture-overview.md`.

### System Verification & Tests
- [ ] Tất cả các test cases hiện tại trong `apps/nhipdieuxanh` và `packages/ask-core` chạy pass 100%.
- [ ] Toàn bộ monorepo thực hiện compile production build thành công không lỗi.

## Follow-up — 2026-05-31T01:11:56Z

Dự án rà soát mã nguồn (Codebase Review) và kiểm toán hệ thống hooks của Mekong-CLI (thư mục `.codex` và `.claude`) nhằm đảm bảo tính nhất quán, bảo mật và tuân thủ các nguyên tắc thiết kế tối ưu.

Working directory: /Users/macbook/mekong-cli
Integrity mode: development

## Requirements

### R1. Target Codebase Quality Scan
Quét mã nguồn trọng tâm của Mekong-CLI tại các thư mục `src/`, `mekong/` và các scripts quan trọng. Nhận diện các vùng mã nguồn trùng lặp, dư thừa, hoặc vi phạm các nguyên tắc thiết kế YAGNI, KISS, DRY.

### R2. Codex & Claude Hooks Consistency Audit
Kiểm tra tính đồng bộ và an toàn giữa hai thư mục cấu hình `.codex/` và `.claude/`. Đảm bảo các hooks như `pre-tool-use-guard`, `privacy-block`, `stop-checkpoint` được định nghĩa chính xác, không bị xung đột cấu hình và không gây rò rỉ dữ liệu nhạy cảm.

### R3. Quality Gates & Vulnerability Assessment
Đánh giá mức độ an toàn của các kịch bản chạy lệnh (shell scripts), phát hiện các lỗ hổng bảo mật tiềm ẩn, và kiểm tra sự tuân thủ đối với các chốt chặn kiểm định chất lượng (quality gates).

## Acceptance Criteria

### Audit & Security
- Báo cáo kiểm toán chi tiết (được lưu tại `reports/codex-review-report.md`) chỉ rõ tất cả các điểm cần cải thiện, phân loại theo độ ưu tiên (High/Medium/Low).
- Đánh giá chi tiết sự tương thích và đồng bộ giữa cấu hình `.codex/hooks.json` và `.claude/hooks.json`.
- Nhận diện và đề xuất giải pháp xử lý cho bất kỳ nguy cơ rò rỉ khóa bí mật hoặc thông tin nhạy cảm nào trong hệ thống hooks.

### Quality & Tests
- Đảm bảo 100% các bài test liên quan của mekong-cli tiếp tục PASS sau khi chạy rà soát và thực hiện điều chỉnh (nếu có).
- 0 lỗi biên dịch TypeScript trong các thư mục được quét.

## Follow-up — 2026-05-31T05:06:36Z

# Teamwork Project Prompt

Sửa chữa và tối ưu hóa các lỗi liên quan đến Daemon Orchestration và Core Execution của `mekong-cli` được phát hiện trong `aggregated-summary-report.md`.

Working directory: /Users/macbook/mekong-cli
Integrity mode: development

## Requirements

### R1. Khắc phục Event Loop Blocks (Daemon & Core Execution)
- Chuyển đổi các cuộc gọi PM2 đồng bộ (`subprocess.run(["pm2", ...])`) hoặc các lệnh subprocess đồng bộ khác trong daemon thành asynchronous (`asyncio.create_subprocess_exec`) hoặc chạy trong thread pool (`asyncio.to_thread`) để tránh nghẽn Event Loop.
- Chuyển đổi các tiến trình thực thi đồng bộ và các lệnh ngủ (`time.sleep`) trong core executor và verifier sang async equivalents (`asyncio.sleep`, `asyncio.create_subprocess_exec`).
- Các file cần lưu ý: `src/daemon/dispatcher.py`, `src/daemon/worker_pool.py`, `src/daemon/mission_control.py`, `src/core/executor.py`, `src/core/verifier.py`.

### R2. Tối ưu hóa PM2 Queries và File I/O trong Mission Control
- Tối ưu hóa hàm `get_status_summary()` trong `src/daemon/mission_control.py` để tránh việc lặp đi lặp lại việc đọc file `missions.json` đồng bộ và gọi PM2 liên tiếp. Thực hiện đọc và parse file `missions.json` một lần duy nhất rồi truyền dữ liệu cho các helper functions.

### R3. Triển khai File Locking cho missions.json
- Sử dụng thư viện khóa file tiêu chuẩn (như `filelock` hoặc `portalocker`) để quản lý việc đọc/ghi đồng thời vào file `missions.json` trong `src/daemon/task_router.py` và `src/daemon/mission_control.py`, ngăn ngừa lỗi hỏng dữ liệu JSON khi chạy song song.

### R4. Sửa lỗi KeyError trên Tool Call ID
- Sửa lỗi KeyError tiềm ẩn khi truy cập `tc["id"]` trong `src/daemon/agent_loop.py` bằng cách sử dụng phương thức an toàn `.get("id")` và fallback về một giá trị UUID ngẫu nhiên nếu không tìm thấy ID.

### R5. Bảo toàn Upstream Dependencies khi Re-planning DAG
- Cập nhật hàm `replan_failed_branch()` trong `src/core/planner.py` để đảm bảo các phụ thuộc gốc (upstream dependencies) chỉ đến các bước chạy thành công trước đó không bị xóa bỏ khi tạo nhánh thay thế mới.

## Verification Resources
- Sử dụng bộ kiểm thử Pytest hiện có trong repo `mekong-cli`: `poetry run pytest`.

## Acceptance Criteria

### Chạy thử nghiệm và xác thực chất lượng
- [ ] Tất cả các bài kiểm tra hiện tại trong `tests/` của `mekong-cli` phải pass 100% sau khi sửa đổi mã nguồn.
- [ ] Không phát sinh bất kỳ lỗi `json.JSONDecodeError` nào do tranh chấp ghi file `missions.json` khi daemon hoạt động.
- [ ] Tiến trình daemon không crash hoặc gặp lỗi KeyError khi chạy với các payload local LLM thiếu tool call ID.
- [ ] Báo cáo chi tiết về các sửa đổi mã nguồn đã thực hiện lưu tại `/Users/macbook/projects/sophia-ai-factory/plans/reports/daemon-debug-execution-report.md`.

## Follow-up — 2026-05-31T08:14:13Z

Optimize the agent execution framework (specifically the `cto-daemon.sh`, `m1-cooler.sh`, and worker execution loops in `~/mekong-cli`) to eliminate system lag, reduce excessive file scans, bound parallel worker CPU consumption, and resolve macOS M1 Max overheating.

Working directory: `/Users/macbook/mekong-cli`
Integrity mode: development

## Requirements

### R1. Optimize filesystem scans and cache purge in `m1-cooler.sh`
- The script `m1-cooler.sh` currently runs an aggressive loop every 10 seconds performing massive disk searches (`find`) and recursively deleting directories (like `.next`). This causes continuous rebuilding of Next.js apps, leading to high CPU/GPU load.
- Increase the sleep duration, cache search results, or remove the aggressive periodic `.next` deletions entirely during development.

### R2. Optimize `cto-daemon.sh` and cleanup loops
- The `cto-daemon.sh` daemon polls pane outputs and runs `cleanup_orphan_nodes` frequently.
- Optimize `cleanup_orphan_nodes` to run only when needed (not every cycle) and use highly efficient, non-recursive filtering to identify zombie processes.
- Ensure the daemon's own cycle intervals are throttled when no active work is being run.

### R3. Provide model-shifting hooks to offload CPU
- Provide clear switches or environmental configurations in `cto-daemon.sh` to route heavy LLM tasks (like the brain decisions) to external endpoints (Zunef portal or official APIs) rather than forcing local Ollama execution of `qwen3:32b` on the M1 Max.

## Acceptance Criteria

### Execution & Performance
- [ ] Idle system CPU utilization of the agent suite drops below 5% on average.
- [ ] Next.js `.next` compilation cache is not forcefully deleted during active runs, preventing infinite recompilation loops.
- [ ] TMUX role panes run smoothly and do not freeze or lag the terminal.
- [ ] External API fallbacks can be toggled via environment variables or configuration files.

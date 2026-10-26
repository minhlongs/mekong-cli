# Plan: Tái cấu trúc Mekong CLI theo Kiến trúc 4-Kit AgentKit và Agentic Reverse Engineering (morluto)

**Branch:** `feat/agentkit-re-restructure`  
**Repo Worktree:** `/Users/macbook/mekong-cli-agentkit-re`  
**Route:** `feature` via `/ak:cook --tdd --auto`  
**Ship Mode:** `official` (--ship)  
**Status:** `completed`  
**TDD Status:** Mandatory (Red → Green → Refactor)  

---

## 1. Problem & Context
Mekong CLI hiện có 187 nhóm lệnh (`registered_groups`) và 37 câu lệnh phẳng (`registered_commands`) kết nối trực tiếp trong `src/cli/app_setup.py`. Kiến trúc hiện tại gặp 4 hạn chế lớn:
1. Thiếu cấu trúc gói mô-đun hóa (AgentKit Kits) để người dùng cài đặt/xuất lệnh sang 7 agent targets (`claude-code`, `codex`, `cursor`, `agy`, `pi`, `omp`, `dsh`) + `portable`.
2. Lưu trữ cấu hình cục bộ chưa chuẩn hóa theo AgentKit (`~/.mekong` quyền `0700`, `~/.mekong/auth/session.json` `0600` `schema-v2`, và `.mekong/ownership.json` theo dõi SHA-256).
3. Thiếu công cụ Agentic Reverse Engineering chuyên sâu (SaaS Web App reversing, decompilation MCP bridges, static security audit, dynamic instrumentation).
4. `InMemoryCapabilityBus.execute()` chưa thực thi kiểm duyệt an toàn (`Governance`) và cách ly môi trường theo 3 tầng rủi ro (`LOW_RISK`, `MEDIUM_RISK`, `HIGH_RISK`). Ngoài ra, `app_setup.py` bị đăng ký trùng nhóm lệnh `competition` (tại dòng 587 và dòng 713).

---

## 2. Requirements & Acceptance Criteria
1. **AgentKit Storage & Ownership (`src/core/kit_storage.py`):**
   - Đảm bảo khởi tạo thư mục `~/.mekong` với mode `0700`.
   - File xác thực session `~/.mekong/auth/session.json` với mode `0600`, schema `schema-v2`.
   - Quản lý quyền sở hữu tệp tin `.mekong/ownership.json` lưu SHA-256 hash của từng kit file để phát hiện và ngăn chặn ghi đè trái phép.
2. **3-Tier RE Governance (`src/core/governance.py` & `src/core/capability.py`):**
   - `LOW_RISK`: Read-only static analysis (`re-audit`, `codebase-audit`, `strings`), chạy trực tiếp qua `ActionClass.SAFE`.
   - `MEDIUM_RISK`: Web/SaaS RE và MCP decompilation tĩnh (`GhidraMCP`, `radare2 MCP`, `JADX-AI-MCP`), bắt buộc thực thi trong workspace tạm thời cô lập (`tempfile.mkdtemp`), script con chạy với cờ `python3 -I`.
   - `HIGH_RISK`: Dynamic RE / Instrumentation (`Frida`, live tracing, debuggers), bắt buộc qua cổng phê duyệt `ActionClass.REVIEW_REQUIRED` (từ chối tự động trừ khi có cờ `GOVERNANCE_AUTO_APPROVE=true` hoặc human approval), workspace cô lập và chặn network mặc định.
   - Kết nối chặt chẽ `InMemoryCapabilityBus.execute()` với `Governance.classify_risk()` và audit trail `.mekong/audit.yaml`.
3. **Mekong RE Command Suite (`src/commands/re/` & `src/cli/commands/re_command.py`):**
   - Nhóm lệnh `mekong re <web|binary|apk|protocol|mcp-sync|codebase-audit>`.
   - Lệnh `mekong re codebase-audit` phân tích tĩnh codebase Mekong CLI: phát hiện circular imports, dead modules, và nhóm lệnh trùng lặp.
   - Adapter `src/core/adapters/re_mcp_bridge.py` kết nối với `ExternalMcpClient` để tương tác các MCP server decompiler.
4. **4-Kit Multi-Kit System (`src/core/kit_registry.py`, `src/cli/commands/kit_command.py`):**
   - Định nghĩa 4 Kits: `kit:re`, `kit:engineer`, `kit:business`, `kit:marketing`.
   - Nhóm lệnh `mekong kit <list|install|export>` hỗ trợ xuất manifest cấu hình sang 7 targets: `claude-code`, `codex`, `cursor`, `agy`, `pi`, `omp`, `dsh`, và `portable`.
5. **Doctor & Integration Quality Gates (`src/cli/commands/doctor_command.py` & `src/cli/app_setup.py`):**
   - `mekong doctor --re` (hoặc `--check re`) kiểm tra sự hiện diện tùy chọn của các binary RE (`r2`/`radare2`, `ghidraRun`, `jadx`, `frida`, `tshark`) mà không ép buộc thêm dependency nặng vào `pyproject.toml`.
   - Khắc phục duplicate registration `name="competition"` tại `src/cli/app_setup.py` (loại bỏ đăng ký trùng lặp tại dòng 710-715).
   - Tích hợp `mekong kit` và `mekong re` vào `build_app()`.
   - Đảm bảo 100% backward compatibility: giữ nguyên tất cả root alias hiện có, `assert len(app.registered_groups) >= 39` và toàn bộ test suites hiện hành đều vượt qua.

---

## 3. Architecture & Subagent Partitioning (--parallel)
Các slice được phân chia rõ ràng về quyền sở hữu file (Disjoint File Ownership) để thực thi song song an toàn:

### Slice 1: Security & Governance Core
- **Files Owned:**
  - `src/core/kit_storage.py` (Mới)
  - `src/core/governance.py` (Cập nhật 3-tier RE Governance & risk rules)
  - `src/core/capability.py` (Cập nhật `InMemoryCapabilityBus.execute` gắn liền `Governance` và workspace isolation)
  - `tests/core/test_re_governance.py` (Mới)
  - `tests/core/test_kit_storage.py` (Mới)

### Slice 2: Reverse Engineering Engine & CLI
- **Files Owned:**
  - `src/core/adapters/re_mcp_bridge.py` (Mới)
  - `src/commands/re/codebase_audit.py` (Mới)
  - `src/commands/re/web_re.py` (Mới)
  - `src/commands/re/binary_re.py` (Mới)
  - `src/cli/commands/re_command.py` (Mới)
  - `tests/cli/test_re_command.py` (Mới)
  - `tests/commands/test_codebase_audit.py` (Mới)

### Slice 3: Kit Packaging & Multi-Target Exporter
- **Files Owned:**
  - `src/core/kit_registry.py` (Mới)
  - `src/cli/kit_manifests.py` (Mới)
  - `src/cli/commands/kit_command.py` (Mới)
  - `tests/cli/test_kit_command.py` (Mới)
  - `tests/core/test_kit_registry.py` (Mới)

### Slice 4: System Integration & Doctor (Serialized Integration)
- **Files Owned:**
  - `src/cli/commands/doctor_command.py` (Thêm check RE binaries & MCP bridges)
  - `src/cli/app_setup.py` (Loại bỏ duplicate `competition`, đăng ký `kit` và `re`, thêm `rich_help_panel` cho các kits)
  - `tests/cli/test_doctor_command.py` (Cập nhật kiểm tra `--re`)
  - Toàn bộ suite verify: `pytest`, `ruff check src/ tests/`

---

## 4. Verification & Gates
- **Unit Tests:** Viết test trước (TDD Red-Green-Refactor) cho từng module mới.
- **Integration Tests:** `test_funnel_commands.py`, `test_governance.py`, `test_kit_command.py`, `test_re_command.py`.
- **Linter & Typing:** `python3 -m ruff check src/ tests/` không có lỗi.
- **Empirical Execution:** Chạy `mekong re codebase-audit` kiểm tra chính repo Mekong CLI.
- **Doctor Verification:** Chạy `mekong doctor --check re -v` xác nhận kiểm tra môi trường hoạt động chuẩn xác.

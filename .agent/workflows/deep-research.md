---
description: Deep Research — Trinh sát web với Exa MCP, tổng hợp intel, lưu vào knowledge/
---
// turbo-all

# /deep-research Workflow

## Steps

1. **Xác định chủ đề nghiên cứu** từ user query
2. **Sử dụng Exa MCP** để trinh sát web:
   ```
   /use-mcp exa web_search_exa "<topic>"
   ```
3. **Lấy code context** nếu cần:
   ```
   /use-mcp exa get_code_context_exa "<library/framework>"
   ```
4. **Tổng hợp intel** vào file markdown:
   ```
   knowledge/<topic-slug>-intel.md
   ```
5. **Inject vào context** cho mission tiếp theo bằng cách reference file

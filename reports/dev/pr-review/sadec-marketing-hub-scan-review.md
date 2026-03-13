# PR Review: scan-sadec-html.py

**Date:** 2026-03-13
**Reviewer:** OpenClaw CTO
**File:** `scan-sadec-html.py` (224 dòng)
**Mục đích:** Quét HTML files trong sadec-marketing-hub để tìm broken links và missing meta tags

---

## ✅ TỔNG QUAN

| Metric | Status | Notes |
|--------|--------|-------|
| Syntax | ✅ PASS | `python3 -m py_compile` thành công |
| Type hints | ⚠️ WARNING | Thiếu type hints cho functions |
| Docstrings | ✅ PASS | Có docstrings cho class và functions |
| TODO/FIXME | ✅ PASS | Không có technical debt comments |
| File size | ⚠️ WARNING | 224 dòng (>200 lines standard) |
| Security | ✅ PASS | Không có vulnerability nghiêm trọng |
| Imports | ✅ PASS | Chỉ dùng standard library an toàn |

---

## 📝 CODE QUALITY REVIEW

### 1. Type Safety (⚠️ CẦN CẢI THIỆN)

**Vấn đề:** Thiếu type hints cho tất cả functions

```python
# ❌ Hiện tại
def parse_html_file(filepath):
    """Parse single HTML file and extract meta info + links"""
    ...

# ✅ Nên có
def parse_html_file(filepath: Path) -> dict[str, Any]:
    """Parse single HTML file and extract meta info + links"""
    ...
```

**Khuyến nghị thêm:**
```python
from typing import Any, TypedDict

class ParseResult(TypedDict, total=False):
    meta_tags: set[str]
    has_title: bool
    links: list[dict[str, Any]]
    content: str
    error: str

class LinkCheckResult(TypedDict):
    file: str
    line: int
    href: str
    tag: str

class MetaReport(TypedDict):
    file: str
    missing_required: list[str]
    missing_og: list[str]
```

### 2. Docstrings (✅ TỐT)

```python
# ✅ Docstrings rõ ràng, mô tả đúng chức năng
class HTMLMetaParser(HTMLParser):
    """Parse HTML and extract meta tags + links"""  # Nên thêm

def parse_html_file(filepath):
    """Parse single HTML file and extract meta info + links"""  # ✅

def check_link_exists(link_path, base_dir, all_files):
    """Check if a relative link exists"""  # ✅

def scan_directory():
    """Scan all HTML files in the directory"""  # ✅

def print_report(results):
    """Print formatted report"""  # ✅
```

### 3. Code Structure (✅ TỐT)

```
✅ Modular design - mỗi function làm 1 việc rõ ràng
✅ Sử dụng HTMLParser thay vì regex cho HTML parsing
✅ Error handling với try/except
✅ Report có both console output + JSON file
```

### 4. Naming Conventions (✅ TỐT)

```python
✅ snake_case: parse_html_file, check_link_exists, scan_directory
✅ UPPER_CASE: BASE_DIR, EXCLUDE_DIRS, REQUIRED_META, OG_META
✅ Descriptive names: missing_meta, broken_links, by_target
```

### 5. Error Handling (✅ TỐT)

```python
# ✅ Graceful error handling
def parse_html_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ...
    except Exception as e:
        return {'error': str(e), 'links': [], 'meta_tags': set(), 'has_title': False}
```

**Khuyến nghị:** Nên specific hơn với exception types:
```python
except (FileNotFoundError, UnicodeDecodeError, PermissionError) as e:
    return {'error': str(e), ...}
```

---

## 🔒 SECURITY REVIEW

### 1. Path Traversal (✅ AN TOÀN)

```python
# ✅ BASE_DIR hardcoded, không nhận user input
BASE_DIR = Path("/Users/mac/.gemini/antigravity/scratch/sadec-marketing-hub")

# ✅ rel_path được generate từ os.walk, không phải user input
for root, dirs, files in os.walk(BASE_DIR):
    rel_path = os.path.relpath(os.path.join(root, f), BASE_DIR)
```

### 2. File Operations (✅ AN TOÀN)

```python
# ✅ Chỉ đọc files, không có write operations nguy hiểm
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# ✅ JSON report write vào directory đã biết
report_path = BASE_DIR / ".cto-reports" / "html-scan-report.json"
```

### 3. No External Dependencies (✅ AN TOÀN)

```python
# ✅ Chỉ dùng standard library
import os
import re  # ⚠️ Không dùng - có thể remove
from pathlib import Path
from html.parser import HTMLParser
from collections import defaultdict
import json
```

**Lưu ý:** `import re` ở line 9 nhưng không được sử dụng trong code. Nên remove.

### 4. No Command Injection (✅ AN TOÀN)

```python
# ✅ Không có subprocess, eval(), exec()
# ✅ Không có shell command execution
```

### 5. Input Validation (⚠️ CÓ THỂ CẢI THIỆN)

```python
# ⚠️ Không validate BASE_DIR tồn tại trước khi scan
def scan_directory():
    # Nên thêm:
    if not BASE_DIR.exists():
        raise FileNotFoundError(f"Base directory not found: {BASE_DIR}")
```

---

## 🎯 RECOMMENDATIONS

### High Priority (Nên fix ngay)

1. **Remove unused import:**
   ```python
   # Line 9 - không dùng
   - import re
   ```

2. **Add base directory validation:**
   ```python
   def scan_directory():
       if not BASE_DIR.exists():
           raise FileNotFoundError(f"Base directory not found: {BASE_DIR}")
   ```

### Medium Priority (Nên có)

3. **Add type hints:**
   ```python
   from typing import Any, TypedDict

   def parse_html_file(filepath: Path) -> ParseResult:
   def check_link_exists(link_path: str, base_dir: Path, all_files: set[str]) -> tuple[bool, str]:
   def scan_directory() -> dict[str, Any]:
   ```

4. **Split into modules (>200 lines):**
   ```
   scan-sadec-html/
   ├── __init__.py
   ├── parser.py      # HTMLMetaParser class
   ├── scanner.py     # scan_directory(), check_link_exists()
   ├── reporter.py    # print_report()
   └── __main__.py    # entry point
   ```

### Low Priority (Nice to have)

5. **Add logging thay vì print:**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   ```

6. **Add CLI arguments:**
   ```python
   import argparse
   # --base-dir, --output, --verbose flags
   ```

---

## 📊 QUALITY GATES

| Gate | Standard | Status |
|------|----------|--------|
| Tech Debt | 0 TODO/FIXME | ✅ PASS |
| Type Safety | 0 `any` types | ⚠️ FAIL (no type hints) |
| File Size | <200 lines | ⚠️ FAIL (224 lines) |
| Security | 0 high vulns | ✅ PASS |
| Documentation | Docstrings present | ✅ PASS |
| Tests | Unit tests | ❌ MISSING |

---

## ✅ VERDICT

**Status:** APPROVED WITH RECOMMENDATIONS

**Score:** 7.5/10

- ✅ Code sạch, dễ đọc
- ✅ Security: an toàn, không có vulnerability
- ✅ Error handling: tốt
- ⚠️ Type safety: cần thêm type hints
- ⚠️ Modularization: cần split (<200 lines)
- ❌ Tests: cần thêm unit tests

---

## 📋 ACTION ITEMS

- [ ] Remove `import re` (unused)
- [ ] Add BASE_DIR existence check
- [ ] Add type hints for all functions
- [ ] Add unit tests (pytest)
- [ ] Consider splitting into modules

---

*Generated by /dev:pr-review pipeline*

"""Fallback project templates, guardrail hook scripts, and MCP server script."""

from __future__ import annotations

FALLBACK_PYPROJECT_TOML: str = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mekong-app"
version = "0.1.0"
description = "Mekong Autonomous Agent Project"
readme = "README.md"
requires-python = ">=3.10"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""

FALLBACK_ENV_EXAMPLE: str = """MEKONG_ENV=development
MEKONG_DEBUG=1
MEKONG_LOG_LEVEL=INFO
"""

FALLBACK_LICENSE: str = """MIT License

Copyright (c) 2026 MekongMind

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

FALLBACK_PRE_TOOL_GUARDRAIL_PY: str = """#!/usr/bin/env python3
\"\"\"Pre-tool use safety guardrail hook for Mekong Antigravity platform.\"\"\"
import sys
import json

def main() -> int:
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

FALLBACK_POST_TOOL_AUDIT_PY: str = """#!/usr/bin/env python3
\"\"\"Post-tool audit hook for Mekong Antigravity platform.\"\"\"
import sys

def main() -> int:
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

FALLBACK_MCP_SERVER_PY: str = """#!/usr/bin/env python3
\"\"\"Standalone MCP stdio JSON-RPC server for Mekong project.\"\"\"
import sys
import json

def main() -> None:
    pass

if __name__ == "__main__":
    main()
"""

# Tech Stack: Maritime Phases 363–366

## 1. Core Language & Physical Engineering Engines
- **Python 3.9+ / System Python**: Type annotations, dataclasses, enum, math.
- **Marine Safety & Hydrodynamic Models**:
  - SOLAS III/13, LSA Code IV, IMO MSC.81(70) free-fall lifeboat trajectories & HRU activation windows.
  - IEC 60092-202 & SOLAS II-1/53 Generator Power Management System (PMS) reactive & active load sharing, under-frequency/under-voltage blackout trip protection.
  - London Protocol (1996) & QCVN 43:2017/BTNMT dredged spoil chemical contamination matrices & beneficial reuse geotechnical stability.
  - OCIMF OVID & DNV-GL/ABS towing winch brake holding capacity (>= 80% MBL) and STCW III/3 endorsement vetting.

## 2. CLI & MCP Gateway Architecture
- **Typer & Click**: 4 CLI commands with 8 bilingual Vietnamese command aliases:
  - `lifeboat` / `cuusinhhru`
  - `marinepms` / `dienmaritime`
  - `dredgespoil` / `bunnaovet`
  - `tugvetting` / `kiemdinhtau`
- **FastMCP**: 4 async RPC tools integrated into `scripts/mcp_server.py`.

## 3. Quality Verification & Testing
- **pytest & pytest-asyncio**: 100% zero-mock testing enforcing real engineering thresholds, mathematical physics, and electrical tripping curves.
- **Ruff**: Code cleanliness and formatting.
- **File Constraints**: Strict enforcement of `< 200 LOC` per file across core modules, facades, CLIs, and test suites.

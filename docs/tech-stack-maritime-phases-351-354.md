# Tech Stack: Maritime Phases 351–354

## 1. Core Language & Mathematical Modeling
- **Python 3.9+ / System Python**: Dataclasses, Type Hints, Math, Hashlib SHA-256.
- **Naval Architecture & Hydrodynamics**:
  - SOLAS XII/11 & IACS UR S1/S1A Bending Moment (BM) & Shear Force (SF) limits.
  - IMO Intact Stability Code 2008 GZ curve numerical integration & metacentric height ($GM$).
  - OPRC-HNS Protocol 2000 drift vector mechanics ($3\%$ wind leeway + $100\%$ surface current).
  - Central cooling thermodynamic heat balance ($Q = \dot{m} C_p \Delta T$) & MGPS Cu/Al ion dosing stoichiometry.
  - IMO FAL.5/Circ.39/Rev.2 & W3C Verifiable Credentials cryptographic proof verification.

## 2. CLI & MCP Gateway Architecture
- **Typer & Click**: 4 CLI apps with 8 bilingual Vietnamese command aliases (`loadingcomp`, `onđinhtau`, `hnsdrift`, `toicathns`, `centralcool`, `lammatbien`, `ecert`, `chungchiso`).
- **FastMCP**: 4 async RPC tools integrated into `scripts/mcp_server.py`.

## 3. Quality Verification & Testing
- **pytest & pytest-asyncio**: 100% zero-mock testing enforcing real hydrodynamics, drift vectors, and cryptography.
- **Ruff**: Code cleanliness and formatting.
- **File Constraints**: Strict enforcement of `< 200 LOC` per file across core modules, facades, CLIs, and test suites.

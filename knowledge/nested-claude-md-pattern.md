# Nested CLAUDE.md Pattern (Địa Hình)
Date: 2026-02-23

## Status
- **Implemented**: Created workspace-specific `CLAUDE.md` files for `openclaw-worker`, `84tea`, `sophia-ai-factory`, and `wellnexus`.

## Pattern Dynamics (Raúl Junco's Pattern)
Like CSS Specificity, the deeper the file is within the working directory, the higher its override priority compared to the root `CLAUDE.md`.
Allows loading purely relevant rules (e.g. Video Factory concepts inside Sophia AI app, while keeping them hidden when working in the base proxy).

## Binh Pháp Mapping
**地形 ĐỊA HÌNH (Hiểu rõ địa thế)**: Mỗi project trong monorepo là một địa hình. Nested CLAUDE.md giúp AI cung cấp "context matching the terrain", tránh loạn nhịp do rules chồng chéo.

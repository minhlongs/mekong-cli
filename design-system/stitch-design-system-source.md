# Design System: Cyber-Bento Horizon

> Generated via Stitch-Kit & Google Stitch MCP for Mekong CLI Autonomous Agent Platform.

## 1. Visual Theme & Philosophy
- **Identity**: Cyber-Bento Horizon — futuristic yet utilitarian developer & enterprise control plane.
- **Canvas**: True Obsidian Deep Space (`#090A0F`), Elevated Slate containers (`#11131A`), Subtle 1px structural grid lines (`#1E2230`).
- **Accents**: Neon Cyber Emerald (`#10B981`) for active agent state, cryptographic verification, and success signals; Electric Cyan (`#06B6D4`) for interactive triggers and secondary telemetry.
- **Status Alerts**: Amber Gold (`#F59E0B`) for quotas, warnings, and burn estimates; Crimson (`#EF4444`) for interlocks and failures.

## 2. Color Palette Tokens
| Token | Hex | Usage |
|---|---|---|
| `--bg-app` | `#090A0F` | Global workspace canvas |
| `--bg-panel` | `#11131A` | Bento cards, modals, navigation containers |
| `--bg-hover` | `#181B26` | Table row hover, button ghost states |
| `--border-subtle` | `#1E2230` | Default 1px structural borders |
| `--border-active` | `#2D3748` | Focused and highlighted card states |
| `--color-primary` | `#10B981` | Emerald CTAs, verified badges, active telemetry |
| `--color-secondary` | `#06B6D4` | Electric cyan links, secondary metrics |
| `--color-warning` | `#F59E0B` | Pending status, quota consumption |
| `--color-error` | `#EF4444` | Errors, interlocks, destructive actions |

## 3. Typography
- **Headings**: `Space Grotesk`, `Inter` (Font weight 600-700, tracking -0.02em)
- **Body & UI**: `Inter`, `-apple-system`, `sans-serif` (13px - 14px, line-height 1.5)
- **Telemetry & Hashes**: `JetBrains Mono`, `monospace` (SHA-256 hashes, terminal commands, VND/MCU pricing)

## 4. Radii & Surface Elevation
- **Cards & Bento Units**: `12px` (`ROUND_TWELVE` in Stitch)
- **Buttons & Inputs**: `8px` (`ROUND_EIGHT`)
- **Pills & Status Badges**: `9999px` (`ROUND_FULL`)

## 5. UI Components & Interactivity
- **Terminal Streaming Simulator**: Dark console box with macOS titlebar dots, streaming monospace logs with syntax highlighting.
- **VietQR Modal Frame**: High-contrast white QR container with simulated HMAC-SHA256 webhook confirmation.
- **Command Palette (`Cmd+K`)**: Floating blur overlay with search filter for instant navigation.

---

## 6. Prompt Injection Block (Section 6 - Required for Stitch)
```markdown
**DESIGN SYSTEM (REQUIRED):**
- **Theme**: Cyber-Bento Horizon (Obsidian #090A0F canvas, Dark Slate #11131A cards, 1px Border #1E2230).
- **Primary Accent**: Cyber Emerald #10B981 (glowing badges, success states, primary buttons).
- **Secondary Accent**: Electric Cyan #06B6D4 (interactive links, code snippets, secondary actions).
- **Status Accents**: Warning Amber #F59E0B (quotas, polling), Error Crimson #EF4444 (alerts, interlocks).
- **Typography**: Space Grotesk / Inter for headings, Inter for body copy, JetBrains Mono for code/telemetry/currency.
- **Corner Radii**: 12px for cards and bento grids, 8px for buttons and inputs, pill-shaped for status badges.
- **Component Patterns**: Bento grid layout, dark cyber terminal window with traffic light dots, glowing status pills, compact high-density data tables.
```

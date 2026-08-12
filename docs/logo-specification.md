# Mekong CLI Logo Specification

## Design Concept

### Core Elements
1. **Mekong River Wave** - Flowing, organic shape representing the Mekong river
2. **CLI Prompt Symbol** - `>` or `$` integrated into the wave
3. **Monospace Typography** - Terminal aesthetic

### Color Scheme
- **Primary Gradient**: Emerald Green (#10b981) → Lotus Pink (#e879f9)
- **Alternative**: Teal (#14b8a6) → Purple (#a78bfa)
- **Single Color**: Emerald (#10b981) for monochrome/terminal use

---

## Logo Variants

### 1. Full Logo (Icon + Text)

```
    ╭─────────────────────╮
    │   ╭───╮   Mekong   │
    │   │ > │   CLI      │
    │   ╰───╯            │
    ╰─────────────────────╯
```

**Layout:**
- Left: Icon (wave + `>` symbol)
- Right: "Mekong" in bold monospace, "CLI" subscript in smaller size
- Vertical alignment: centered

**Typography:**
- Font: Fira Code, JetBrains Mono, or similar monospace
- "Mekong": Bold, 16-18pt equivalent
- "CLI": Regular, 10-11pt, baseline lowered by 30%

**Spacing:**
- Icon-to-text gap: 8-12px
- Total lockup: maintain aspect ratio 2:1 (width:height)

---

### 2. Icon-Only (App Icon, Favicon)

**Design:**
- Square canvas (512×512px for app icon, 32×32 for favicon)
- Centered wave symbol with integrated `>` at the wave's crest
- Wave: Single flowing curve, thick stroke (20-30px at 512px)
- Gradient: Left-to-right #10b981 → #e879f9

**Simplified (16×16px):**
- Solid color (#10b981)
- Minimal wave: 3-4 pixel thick curve
- `>` embedded at center

---

### 3. ASCII Art Logo (Terminal Welcome Screen)

```
  __  __                 _
 |  \/  | ___  _ __ __ _| |_ _   _
 | |\/| |/ _ \| '__/ _` | __| | | |
 | |  | | (_) | | | (_| | |_| |_| |
 |_|  |_|\___/|_|  \__,_|\__|\__, |
                              |___/
        ███████╗██╗  ██╗██████╗ ██╗   ██╗
        ██╔════╝██║  ██║██╔══██╗██║   ██║
        ███████╗███████║██████╔╝██║   ██║
        ╚════██║██╔══██║██╔══██╗██║   ██║
        ███████║██║  ██║██████╔╝╚██████╔╝
        ╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝
```

**Alternative (Simpler):**
```
    ╭────────────────────────╮
    │  ┌─────┐  MEKONG CLI  │
    │  │  >  │              │
    │  └─────┘              │
    ╰────────────────────────╯
```

---

## Construction Guidelines

### Wave Geometry
```
    ┌─────────────────────┐
    │                     │
    │    ↘↙↘↙↘↙         │
    │       ↘↙↘↙↘       │
    │          ↘↙↘      │
    │             ↘↙    │
    │               ↘  │
    │                ↙ │
    │                     │
    └─────────────────────┘
```

**Waveform:**
- 3-4 peaks representing river flow
- Smooth Bézier curves, no sharp angles
- Asymmetric (natural, organic)
- `>` symbol placed at highest peak/crest

### Stroke Weight
- Icon: 20-30px stroke at 512px canvas
- Scalable: maintain 4-6% of canvas width as stroke

---

## Color Codes

### Primary Palette
```css
--color-emerald: #10b981
--color-lotus:   #e879f9
--color-teal:    #14b8a6
--color-purple:  #a78bfa
```

### Gradient Direction
- Horizontal: Left (emerald) → Right (lotus)
- Alternative: Diagonal (top-left → bottom-right)

---

## Usage Guidelines

### Do's ✅
- Use on dark backgrounds (terminal #0a0e1a, dark blue)
- Maintain clear space: 1x icon width on all sides
- Use provided gradients, don't modify colors
- Scale proportionally, never distort
- Use on light backgrounds only with solid emerald color

### Don'ts ❌
- Don't rotate or skew
- Don't change gradient direction
- Don't add effects (drop shadow, glow)
- Don't combine with other graphics
- Don't use on busy/patterned backgrounds

---

## File Outputs

### Required Formats
1. `logo-full.svg` - Full logo with text (vector)
2. `logo-icon.svg` - Icon-only (vector, square)
3. `logo-icon.png` - Icon in various sizes (16, 32, 64, 128, 512px)
4. `logo-ascii.txt` - ASCII art for terminal welcome
5. `logo-terminal.ans` - ANSI-colored version with escape codes

### Sizes for CLI App Icon
- 16×16 (favicon)
- 32×32 (small icon)
- 64×64 (medium)
- 128×128 (large)
- 512×512 (app icon, stores)

---

## Implementation Notes

### For Developers
```javascript
// Import SVG for documentation
import logoFull from './logo-full.svg';
import logoIcon from './logo-icon.svg';

// Terminal ASCII
import logoTerminal from './logo-ascii.txt';

// PNG sizes
const iconSizes = [16, 32, 64, 128, 512];

// Color variables for CSS
:root {
  --mekong-emerald: #10b981;
  --mekong-lotus: #e879f9;
}
```

### Terminal Implementation
```bash
# Display logo in terminal
cat ./assets/logo-ascii.txt

# Or with colors (ANSI escape codes)
cat ./assets/logo-terminal.ans

# Small inline
printf "\033[32m╭───╮\033[0m\n"
printf "\033[32m│ > │\033[0m Mekong CLI\n"
printf "\033[32m╰───╯\033[0m\n"
```

---

## Brand Applications

### Terminal Splash Screen
```
╭─────────────────────────────────────╮
│   [LOGO ASCII - centered]          │
│                                     │
│   Xin chào, [USER]!                 │
│   Your AI business co-pilot        │
│                                     │
╰─────────────────────────────────────╯
```

### Help Header
```
╭─ Mekong CLI ────────────────────────╮
│ ? mekong --help                     │
╰─────────────────────────────────────╯
```

### Documentation Favicon
- Use icon-only (32×32 or 64×64)
- On light backgrounds: solid emerald (#10b981)

---

## Design Philosophy

The logo should feel:
- **Modern** - Clean lines, geometric simplicity
- **Approachable** - Curved wave, not too techy/angular
- **Vietnamese** - Mekong river reference, lotus colors
- **Terminal-native** - Monospace, works in ASCII
- **Scalable** - Recognizable at 16×16px

---

*Version: 1.0*
*Last updated: 2024-06-18*

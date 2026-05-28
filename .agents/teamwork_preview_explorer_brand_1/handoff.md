# Handoff Report: Brand Tokens Specification for Nhip Dieu Xanh

This report outlines the design specification for the color palette system and typography scale to be saved in `brand_tokens.json`.

---

## 1. Observation

In the `mekong-cli` codebase, the existing brand configurations are stored under the `/Users/macbook/mekong-cli/brand/` directory. Direct observations include:

- **Brand Guidelines File (`/Users/macbook/mekong-cli/brand/guidelines.md`)**:
  - Color palette references (Line 25-29):
    ```markdown
    | **Primary** | Emerald Green | `#10B981` | HSL `162 72% 39%` | Core branding, AGI status tags, active states |
    | **Secondary** | Dark Slate | `#0b0f19` | HSL `222 39% 7%` | Master background color |
    | **Accent** | Teal Glow | `#2DD4BF` | HSL `172 66% 50%` | Interactive hover states, telemetry sparklines |
    | **Surface** | Coal Grey | `#111827` | HSL `222 47% 11%` | Cards, panels, sheets, modals |
    | **Border** | Muted Grey | `#1f2937` | HSL `222 19% 17%` | Low-contrast separators |
    ```
  - Typography references (Line 35-37):
    ```markdown
    *   **Headings Font**: `Outfit, sans-serif` (Vibrant, geometric, modern)
    *   **Body Font**: `Inter, sans-serif` (Highly legible, crisp, professional)
    *   **Monospace Font**: `Fira Code, monospace` (For console logs, parameters, contracts, terminal UI)
    ```

- **Brand Colors YAML File (`/Users/macbook/mekong-cli/brand/colors/palette.yaml`)**:
  - Defines the primary Emerald shades from `50` to `900`:
    ```yaml
    colors:
      primary:
        name: "Emerald Green"
        hex: "#10B981"
        hsl: "162 72% 39%"
        description: "Represents growth, security, and the fluid 'Water Protocol' of mekong-cli."
        shades:
          50: "#ecfdf5"
          100: "#d1fae5"
          200: "#a7f3d0"
          300: "#6ee7b7"
          400: "#34d399"
          500: "#10b981"
          600: "#059669"
          700: "#047857"
          800: "#065f46"
          900: "#064e3b"
    ```
  - Defines semantic and neutral colors.

- **Typography Scale YAML File (`/Users/macbook/mekong-cli/brand/typography/scale.yaml`)**:
  - Maps sizing rules for headers and body scale (h1, h2, h3, h4, body_large, body_base, body_small, caption) along with exact letter-spacings and line-heights.

---

## 2. Logic Chain

1. **Information Extraction**: The brand assets stored under `/Users/macbook/mekong-cli/brand/` reflect the verified parameters for the project (Emerald primary `#10B981`, Outfit headings, and Inter body).
2. **Unified Representation**: Converting YAML files `palette.yaml` and `scale.yaml` to JSON ensures compatibility with standard multi-platform web systems.
3. **JSON Serialization**: Created a structured JSON design token mapping that merges colors, typography, weights, scale levels, and semantic values.
4. **Draft Saving**: Saved the draft token JSON file to `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_brand_1/proposed_brand_tokens.json` to act as a handoff blueprint.

---

## 3. Caveats

- **Read-Only**: This task is a read-only investigation. No modifications have been made directly to `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json`.
- **Target Folder**: The folder `/Users/macbook/nhipdieuxanh-agent/brand/` was not directly written to. An implementer agent or workflow step must write the output to that target path.

---

## 4. Conclusion: Proposed `brand_tokens.json` Structure

The exact proposed JSON structure for `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json` is:

```json
{
  "colors": {
    "primary": {
      "name": "Emerald Green",
      "hex": "#10B981",
      "hsl": "hsl(162, 72%, 39%)",
      "description": "Represents growth, security, and the fluid 'Water Protocol' of mekong-cli.",
      "shades": {
        "50": "#ecfdf5",
        "100": "#d1fae5",
        "200": "#a7f3d0",
        "300": "#6ee7b7",
        "400": "#34d399",
        "500": "#10b981",
        "600": "#059669",
        "700": "#047857",
        "800": "#065f46",
        "900": "#064e3b"
      }
    },
    "neutral": {
      "name": "Slate / Slate-Dark",
      "background": "#0b0f19",
      "surface": "#111827",
      "border": "#1f2937",
      "text_primary": "#f9fafb",
      "text_secondary": "#9ca3af"
    },
    "accent": {
      "name": "Teal Glow",
      "hex": "#2DD4BF",
      "hsl": "hsl(172, 66%, 50%)",
      "description": "Used for interactive focus states, highlighting telemetry spikes, and active agents."
    },
    "semantic": {
      "success": "#10B981",
      "warning": "#F59E0B",
      "error": "#EF4444",
      "info": "#3B82F6"
    }
  },
  "typography": {
    "font_families": {
      "headings": "Outfit, sans-serif",
      "body": "Inter, sans-serif",
      "monospace": "Fira Code, JetBrains Mono, monospace"
    },
    "font_weights": {
      "light": 300,
      "regular": 400,
      "medium": 500,
      "semibold": 600,
      "bold": 700
    },
    "scale": {
      "h1": {
        "font_size": "2.5rem",
        "line_height": "1.2",
        "font_weight": "bold",
        "letter_spacing": "-0.02em"
      },
      "h2": {
        "font_size": "2.0rem",
        "line_height": "1.25",
        "font_weight": "semibold",
        "letter_spacing": "-0.015em"
      },
      "h3": {
        "font_size": "1.5rem",
        "line_height": "1.3",
        "font_weight": "semibold",
        "letter_spacing": "-0.010em"
      },
      "h4": {
        "font_size": "1.25rem",
        "line_height": "1.4",
        "font_weight": "medium",
        "letter_spacing": "normal"
      },
      "body_large": {
        "font_size": "1.125rem",
        "line_height": "1.5",
        "font_weight": "regular",
        "letter_spacing": "normal"
      },
      "body_base": {
        "font_size": "1rem",
        "line_height": "1.5",
        "font_weight": "regular",
        "letter_spacing": "normal"
      },
      "body_small": {
        "font_size": "0.875rem",
        "line_height": "1.45",
        "font_weight": "regular",
        "letter_spacing": "normal"
      },
      "caption": {
        "font_size": "0.75rem",
        "line_height": "1.4",
        "font_weight": "medium",
        "letter_spacing": "0.05em"
      }
    }
  }
}
```

---

## 5. Verification Method

- **Visual / Structure check**: Check the `proposed_brand_tokens.json` file content.
- **Syntactic check**: Run `node -e "require('./proposed_brand_tokens.json')"` (or equivalent python parsing) to ensure valid JSON formatting.

# Design Guidelines: Nhịp Điệu Xanh AI CRM

These guidelines establish the visual identity and UI design standards for the Nhịp Điệu Xanh AI CRM application.

---

## 1. Color Palette System

### Primary & Accent Colors
* **Primary (Emerald Green)**: `#10B981` (HSL: `162, 72%, 39%`). Represents sustainability, ecology, and growth.
  - Shade 50: `#ecfdf5`
  - Shade 500: `#10b981`
  - Shade 900: `#064e3b`
* **Accent (Teal Glow)**: `#2DD4BF` (HSL: `172, 66%, 50%`). Used for highlights, focus states, toggles, and active navigation indicators.

### Neutral Colors (Slate-Dark Theme)
* **Background**: `#0b0f19` (Deep slate blue)
* **Surface/Cards**: `#111827` (Slate gray card backdrop)
* **Border**: `#1f2937`
* **Primary Text**: `#f9fafb`
* **Secondary Text**: `#9ca3af`

### Semantic Colors
* **Success**: `#10B981`
* **Warning**: `#F59E0B`
* **Error**: `#EF4444`
* **Info**: `#3B82F6`

---

## 2. Typography

* **Heading Font**: `Outfit, sans-serif` (Google Fonts). Sleek, modern, and high-tech style.
* **Body Font**: `Inter, sans-serif` (Google Fonts). Highly legible for CRM data grids, pipelines, and inputs.
* **Monospace Font**: `Fira Code, JetBrains Mono, monospace` (for console logs, hashes, and code views).

### Font Scale Matrix
* **H1**: `2.5rem` / Line height: `1.2` / Weight: `Bold` (`700`)
* **H2**: `2.0rem` / Line height: `1.25` / Weight: `Semibold` (`600`)
* **H3**: `1.5rem` / Line height: `1.3` / Weight: `Semibold` (`600`)
* **H4**: `1.25rem` / Line height: `1.4` / Weight: `Medium` (`500`)
* **Body Large**: `1.125rem` / Line height: `1.5` / Weight: `Regular` (`400`)
* **Body Base**: `1.0rem` / Line height: `1.5` / Weight: `Regular` (`400`)
* **Body Small**: `0.875rem` / Line height: `1.45` / Weight: `Regular` (`400`)
* **Caption**: `0.75rem` / Line height: `1.4` / Weight: `Medium` (`500`)

---

## 3. Component Styling & Layout

### Kanban Board
* **Grid**: 5 columns matching the pipeline stages:
  1. `new` (Mới)
  2. `contacted` (Đã liên hệ)
  3. `viewing` (Xem thực tế)
  4. `negotiation` (Đàm phán)
  5. `won` (Chốt thành công)
* **Cards**: Rectangular elements with light semi-transparent background (`rgba(17, 24, 39, 0.7)`), 1px solid border (`#1f2937`), and smooth hover scaling.
* **Glows**: Subtle background glow behind the active drag card or columns using Teal/Emerald gradients.

### Form Inputs & Buttons
* **Inputs**: Slate background with `1px` border. Transitions to `border-color: #10B981` with a `2px` focus ring glow.
* **Primary Button**: Linear gradient from Emerald Green (`#10B981`) to Teal Glow (`#2DD4BF`) with white text and smooth scale animation on click.

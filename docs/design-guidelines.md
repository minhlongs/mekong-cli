# Nhịp Điệu Xanh CRM Design Guidelines

This document establishes the UI/UX style guidelines for the Nhịp Điệu Xanh CRM platform, ensuring conformance to Google Material Design 3 (M3) principles and WCAG 2.1 AA accessibility.

---

## 1. M3 Design Tokens & Themes

### Color Palette System (Emerald Theme)
- **Primary Color:** Emerald Green `#10B981` (HSL `160 84% 39%` for light theme; `160 84% 49%` for dark theme).
- **Surface & Neutral colors:** Slate shades. Base surface: `#0b0f19` (dark theme page).
- **Contrast Ratios:** Maintain text elements at a contrast ratio of >= 4.5:1 against their backgrounds.

### Typography (Outfit & Inter font pairing)
- **Headings (Outfit):** Font weight 600, 700. Line-height 1.25.
- **Body & Controls (Inter):** Base size 16px (mobile) to avoid automatic zoom. Line-height 1.5.

---

## 2. Accessibility & ARIA Specifications

- **Form Labels:** Every input must have an associated semantic `<label>` or explicit `aria-label` attribute.
- **Dynamic Alerts:** Inline validation errors must be wrapped in `role="alert"`. Loading or success events must declare `role="status"`.
- **Keyboard Traversal:** Ensure elements have visible focus rings (`focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`).
- **Lists Landmarks:** Kanban columns must be labeled with `role="list"` and individual cards with `role="listitem"`.

---

## 3. Responsive & Safe Area Guidelines

- **Container sizing:** Never use fixed pixel width containers on responsive viewport wrappers. Always favor relative classes (e.g. `w-full max-w-7xl` or `w-[calc(100vw-2rem)]`).
- **Device safe areas:** Sticky headers and floating CTA buttons must offset using environmental dimensions:
  - Trigger margin bottom: `bottom-[calc(1.5rem+env(safe-area-inset-bottom))]`
  - Fixed header padding: `pt-[calc(1rem+env(safe-area-inset-top))]`
- **Touch Target Dimensions:** All interactive control nodes (buttons, tabs, inputs, cards) must have an active tap height of at least `44px` (`44x44pt` standard) to ensure effortless interactions on mobile.

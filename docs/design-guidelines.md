# Design Guidelines: Nhịp Điệu Xanh Cần Thơ Landing Page

## 1. Visual Identity & Concept

**Nhịp Điệu Xanh Cần Thơ** (Green Rhythm Can Tho) is a premium eco-luxury real estate development in Can Tho, Vietnam. The design language must balance organic natural elements (the Mekong Delta's lush greenery and river breezes) with high-end, premium sophistication.

The core design concept is **"Eco-Luxury Rhythm"**—conveying movement, sustainability, health, and exclusive prestige.

---

## 2. Color Palette

The color system uses Emerald Green as the primary signature color, supported by deep luxury tones and gold/amber accents to elevate the brand from "generic green" to "premium eco-luxury".

| Role | Color Name | Hex | Usage / Application | Tailwind Class |
| :--- | :--- | :--- | :--- | :--- |
| **Primary** | Premium Emerald | `#10B981` | Brand signature, active states, key CTA accents. | `bg-emerald-500` / `text-emerald-500` |
| **Primary Hover** | Deep Emerald | `#059669` | Hover states for primary buttons and links. | `bg-emerald-600` / `text-emerald-600` |
| **Secondary** | Forest Jade | `#064E3B` | Solid headings, primary buttons text in light mode, deep background gradients. | `bg-emerald-900` / `text-emerald-900` |
| **Accent** | Royal Amber | `#F59E0B` | Premium highlights, awards, trust badges, star ratings, highlighting unique selling points. | `bg-amber-500` / `text-amber-500` |
| **Dark Neutral** | Slate Charcoal | `#111827` | Primary dark mode background, text in light mode, dark section headers. | `bg-slate-900` / `text-slate-900` |
| **Light Neutral** | Off-White / Alabaster | `#F9FAFB` | Primary light mode background, text in dark mode cards. | `bg-slate-50` / `text-slate-50` |
| **Glass border** | Subtle Mint | `#D1FAE5` / 10% | Semi-transparent card borders, subtle separators. | `border-emerald-100/10` |

### Gradients
*   **Eco-Luxury Gradient:** `from-emerald-600 to-emerald-900` (Used for primary card backgrounds, premium headers)
*   **Sunset Horizon Glow:** `from-emerald-500/20 via-transparent to-amber-500/10` (Used for background decorative blobs)

---

## 3. Typography

To establish high editorial authority, we pair a geometric, high-character display font with a clean, highly legible neo-grotesque font.

### 3.1 Display Font: Outfit
*   **Source:** Google Fonts (`Outfit`)
*   **Application:** Hero headlines, section headers (`h1`, `h2`, `h3`), large statistical callouts.
*   **Personality:** Modern, geometric, clean lines, luxury fashion & architecture vibe.
*   **Weights:**
    *   `Bold (700)`: Used for Hero title and main section titles.
    *   `SemiBold (600)`: Used for card titles and subheadings.
    *   `Medium (500)`: Used for secondary headers and category tags.

### 3.2 Body Font: Inter
*   **Source:** Google Fonts (`Inter`)
*   **Application:** Body text, paragraph descriptions, form labels, tooltips, list items.
*   **Personality:** Neutral, highly readable, crisp rendering on all screen sizes.
*   **Weights:**
    *   `Regular (400)`: Default body paragraphs.
    *   `Medium (500)`: Form controls, buttons, tables, list items.
    *   `SemiBold (600)`: Strong highlights, navigation links.

### 3.3 Typography Scale (Responsive)

| Level | Desktop Size | Mobile Size | Line Height | Font Family | Weight |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display H1** | `3.75rem (60px)` | `2.25rem (36px)` | 1.15 | Outfit | Bold (700) |
| **Section H2** | `2.50rem (40px)` | `1.75rem (28px)` | 1.2 | Outfit | Bold (700) |
| **Subtitle H3** | `1.50rem (24px)` | `1.25rem (20px)` | 1.3 | Outfit | SemiBold (600) |
| **Body Large** | `1.125rem (18px)`| `1.00rem (16px)` | 1.6 | Inter | Regular (400) |
| **Body Base** | `1.00rem (16px)` | `0.875rem (14px)`| 1.5 | Inter | Regular (400) |
| **Caption/Small**| `0.875rem (14px)`| `0.75rem (12px)` | 1.4 | Inter | Medium (500) |

---

## 4. Page Structure & High-Conversion Layout

The landing page layout is systematically structured to maximize user engagement and convert visitors into qualified leads.

### 4.1 Section Specifications

#### 1. Header / Navbar
*   **Sticky Position:** Backed by blur glassmorphism (`backdrop-blur-md bg-white/70` in light mode, `bg-slate-900/70` in dark mode).
*   **Key Elements:**
    *   Left: Logo with Emerald leaf/river-rhythm icon + "Nhịp Điệu Xanh Cần Thơ" text.
    *   Center: Quick links (Overview, Amenities, Floor Plans, Location, Pricing).
    *   Right: Dark Mode toggle + Lang Switcher + Primary CTA button ("Book Visit").

#### 2. Hero Section
*   **Visual Background:** High-quality immersive image/video of the riverside park and green canopy.
*   **Left-Align Layout (Desktop):** Headline ("Khởi Nguồn Nhịp Sống Xanh"), Subheading highlighting prime Can Tho location, trust badges (e.g., "Sổ Hồng Riêng", "Hỗ Trợ Lãi Suất 0%").
*   **Right-Align Floating Card:** Quick contact/registration widget (Name, Phone number) with a glowing emerald CTA to download the VIP Sales Kit.

#### 3. Key Metrics & Highlights
*   A clean grid of four luxury cards showcasing the project stats:
    1.  **Green Area Ratio:** 68% (Emerald highlight)
    2.  **Total Scale:** 12.8 Ha
    3.  **Legal Status:** 100% Sổ Hồng Riêng (Verified)
    4.  **Hand-over Time:** Q4/2027

#### 4. Premium Amenities ("The Green Rhythm")
*   Visual grid displaying signature amenities:
    *   *Mekong Riverside Promenade*
    *   *Emerald Swimming Pool*
    *   *Bio-Park & Jogging Trail*
    *   *Eco-Clubhouse & Spa*
*   Hover effect: Zoom on images with an emerald overlay detailing specific facts about each amenity.

#### 5. Interactive Map & Connectivity
*   Left pane: Travel times (e.g., "5 mins to Ninh Kieu Quay", "10 mins to Can Tho International Airport").
*   Right pane: Stylized mockup map with emerald pins pointing to key hospitals, schools, and malls.

#### 6. Floor Plans (Interactive Section)
*   **Tab System:** Switch between "Studio", "1-Bedroom", "2-Bedroom", and "Penthouse".
*   **Gated Action:** Floor plans are partially blurred with an interactive download button ("Unlock Complete Blueprint") prompting the user for their email and phone.

#### 7. Pricing & ROI Calculator
*   Transparent pricing details with structured installment schemes.
*   Interactive investment highlights (e.g., predicted rental yield 8-10%, appreciation rates).

#### 8. Final Registration & FAQ
*   A premium, multi-field form (Name, Email, Phone, Budget, Selected Layout) situated on a dark forest jade card.
*   Collapsible FAQ list addressing common buying concerns (loan support, ownership duration).

---

## 5. UI Elements & Premium Components

### 5.1 Buttons

*   **Primary Button (Luxury Emerald):**
    *   Style: `bg-emerald-500 text-white font-semibold transition-all duration-300 rounded-lg hover:bg-emerald-600 shadow-[0_4px_14px_0_rgba(16,185,129,0.4)] hover:shadow-[0_6px_20px_0_rgba(16,185,129,0.6)]`
    *   Feedback: Micro-scale down on tap (`active:scale-95`).
*   **Secondary Button (Outline / Glass):**
    *   Style: `border-2 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 dark:hover:text-emerald-300 hover:border-emerald-500 transition-all rounded-lg bg-emerald-500/5 hover:bg-emerald-500/10`
*   **Premium Gold Accent Button:**
    *   Style: `bg-amber-500 text-slate-900 hover:bg-amber-600 font-bold shadow-[0_4px_14px_rgba(245,158,11,0.3)]` (Used strictly for high-urgency callouts).

### 5.2 Form Inputs
*   Background: Light neutral (`bg-white`) / Dark neutral (`bg-slate-800`).
*   Border: `border-slate-200 dark:border-slate-700`.
*   Focus State: Focus transitions to `border-emerald-500 ring-2 ring-emerald-500/20`.
*   Error State: `border-red-500 ring-red-500/10`.

### 5.3 Glassmorphism Cards
To establish depth and elegance in dark mode or overlay sections:
```css
.premium-glass-card {
  background: rgba(17, 24, 39, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(209, 250, 229, 0.1);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}
```

---

## 6. Motion & Interactive Feedback

*   **Scroll Animations:** Use viewport trigger for fade-in translate effects.
    *   Text elements: Fade-in up (`y: [20, 0]`, `opacity: [0, 1]`, `duration: 0.6`).
    *   Card layouts: Cascading stagger delay (`delay: index * 0.1s`).
*   **Dark Mode Transition:** Global `transition-colors duration-500` applied to backgrounds, borders, and text labels to avoid jarring flashes during theme switching.

---

## 7. AI Chatbot Widget Design Guidelines

The floating chatbot is designed to provide immediate answers, capture leads, and enhance the premium, high-tech experience.

### 7.1 Layout & States
*   **Position:** Fixed in the bottom-right corner (`bottom: 24px`, `right: 24px`), with a z-index of `50`.
*   **Trigger Button:**
    *   Shape: Circular (`width: 60px`, `height: 60px`).
    *   Styling: Premium emerald background, glowing pulse rings (`animate-ping` on a wrapper circle) simulating action.
    *   Icon: A premium conversation bubble or stylized robotic assistant icon with an active green status indicator dot.
*   **Chat Window:**
    *   Dimensions: `380px` width, `500px` height (Desktop) / Fullscreen overlay (Mobile).
    *   Border Radius: `16px (1rem)` rounded top-corners, smooth drop shadow.
    *   Header: Emerald-600 background, displaying chatbot avatar, name ("Trợ Lý Xanh Cần Thơ"), status ("Đang Hoạt Động"), and a close action button (`&times;`).
*   **Chat Body:**
    *   Scrollable space listing initial greeting, helpful chip buttons (quick suggestions), user messages, and bot responses.
    *   Typing indicator: A clean pulse dot animation for when the bot is preparing replies.
*   **Quick Suggestions (Chips):**
    *   Pre-styled capsules that users can tap to quickly ask:
        1.  *Xem bảng giá chi tiết* (View detailed price list)
        2.  *Đăng ký tham quan thực tế* (Register for site tour)
        3.  *Pháp lý dự án ra sao?* (What is the legal status?)
        4.  *Gặp chuyên viên tư vấn* (Talk to a human agent)

---

## 8. Development Verification Checklist

Before shipping code for the landing page or wireframe, verify:
*   [ ] Primary color matches exact hex `#10B981` (Emerald).
*   [ ] Google Fonts `Outfit` and `Inter` are loaded and applied as specified.
*   [ ] Dark/Light mode theme toggle changes body background seamlessly.
*   [ ] Lead capture forms validate inputs (e.g., phone format + empty fields).
*   [ ] Chatbot widget launches, interacts with user inputs, and shows responsive replies.
*   [ ] All cards exhibit smooth interactive hover feedback.
*   [ ] Responsive layouts function correctly across desktop, tablet, and mobile views.

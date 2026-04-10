---
description: How to create and maintain brand guidelines
---

# 🎨 Brand System Workflow

Build a comprehensive brand identity system for your agency.

## 🤖 Quick Execute
```bash
Execute workflow: https://mekongmind.com/docs/workflows/brand-system
```

## ⚡ Step-by-Step Execution

### Step 1: Initialize Brand Kit (2 min)
// turbo
```bash
# Create brand structure
mekong brand:init

# Creates:
# /brand/
# ├── logos/
# ├── colors/
# ├── typography/
# ├── guidelines.md
# └── assets/
```

### Step 2: Define Color Palette (3 min)
// turbo
```bash
# Generate color system
mekong brand:colors --primary "#10B981" --style "modern-dark"

# Output:
# - Primary: emerald-500
# - Secondary: slate-800
# - Accent: teal-400
# - Semantic: success, warning, error
```

### Step 3: Set Up Typography (3 min)
// turbo
```bash
# Configure type scale
mekong brand:typography --heading "Outfit" --body "Inter"

# Creates:
# - Heading styles (h1-h6)
# - Body text sizes
# - Font weights
# - Line heights
```

### Step 4: Generate Logo Variations (5 min)
// turbo
```bash
# Export logo variants
mekong brand:logos --export

# Outputs:
# - Primary (full color)
# - Monochrome (black/white)
# - Icon only
# - Favicon
```

### Step 5: Create Guidelines Doc (3 min)
// turbo
```bash
# Generate brand guidelines
mekong brand:guidelines --output ./brand/guidelines.pdf

# Sections:
# - Logo usage
# - Color palette
# - Typography
# - Spacing
# - Do's and Don'ts
```

## 📋 Brand Templates

### Color Tokens
```yaml
colors:
  primary:
    50: "#ecfdf5"
    500: "#10b981"
    900: "#064e3b"
  neutral:
    50: "#f8fafc"
    500: "#64748b"
    900: "#0f172a"
```

### Typography Scale
```yaml
typography:
  heading:
    font: "Outfit, sans-serif"
    weights: [500, 600, 700]
  body:
    font: "Inter, sans-serif"
    weights: [400, 500]
  sizes:
    xs: "0.75rem"
    sm: "0.875rem"
    base: "1rem"
    lg: "1.125rem"
    xl: "1.25rem"
```

## ✅ Success Criteria
- [ ] Brand kit initialized
- [ ] Color palette defined
- [ ] Typography set up
- [ ] Logo variations exported
- [ ] Guidelines document ready

## 🔗 Next Workflow
After brand system: `/content-calendar`

## 🏯 Binh Pháp Alignment
"形名" (Form and Name) - Consistent identity builds recognition.

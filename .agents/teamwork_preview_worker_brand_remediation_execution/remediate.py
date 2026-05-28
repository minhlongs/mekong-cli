import json
import xml.etree.ElementTree as ET
import os

brand_dir = "/Users/macbook/nhipdieuxanh-agent/brand"
brand_tokens_path = os.path.join(brand_dir, "brand_tokens.json")
guidelines_path = os.path.join(brand_dir, "guidelines.html")
logo_symbol_path = os.path.join(brand_dir, "logos/logo-symbol.svg")
logo_primary_path = os.path.join(brand_dir, "logos/logo-primary.svg")
logo_monochrome_path = os.path.join(brand_dir, "logos/logo-monochrome.svg")
favicon_path = os.path.join(brand_dir, "logos/favicon.svg")

def remediate_brand_tokens():
    print("Remediating brand_tokens.json...")
    with open(brand_tokens_path, "r", encoding="utf-8") as f:
        tokens = json.load(f)
    
    # 1. Modify primary color description
    tokens["colors"]["primary"]["description"] = "Represents growth, sustainability, renewable energy, and ecological balance for the Nhịp Điệu Xanh brand."
    
    # 2. Modify accent color description
    tokens["colors"]["accent"]["description"] = "Represents digital CRM touchpoints, active states, and interactive focus states for Nhịp Điệu Xanh."
    
    # Save back
    with open(brand_tokens_path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("brand_tokens.json remediated successfully.")

def remediate_logo_symbol():
    print("Remediating logos/logo-symbol.svg...")
    # Read the file
    with open(logo_symbol_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Target Center House and Rhythm Wave paths
    target_house = '<path d="M 50 32 L 64 46 L 59 46 L 59 58 L 41 58 L 41 46 L 36 46 Z" fill="url(#accentGrad)" />'
    replacement_house = '<path d="M 50 32 L 64 46 L 59 46 L 59 58 L 41 58 L 41 46 L 36 46 Z" fill="url(#accentGrad)" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round" />'
    
    target_wave = '<path d="M 25 70 C 37 60, 42 78, 50 68 C 58 58, 63 76, 75 66" fill="none" stroke="url(#accentGrad)" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" />'
    replacement_wave = (
        '<path d="M 25 70 C 37 60, 42 78, 50 68 C 58 58, 63 76, 75 66" fill="none" stroke="#FFFFFF" stroke-width="8.5" stroke-linecap="round" stroke-linejoin="round" />\n  '
        '<path d="M 25 70 C 37 60, 42 78, 50 68 C 58 58, 63 76, 75 66" fill="none" stroke="url(#accentGrad)" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" />'
    )
    
    if target_house not in content:
        raise ValueError("Could not find the Center House path in logo-symbol.svg")
    if target_wave not in content:
        raise ValueError("Could not find the Rhythm Wave path in logo-symbol.svg")
        
    content = content.replace(target_house, replacement_house)
    content = content.replace(target_wave, replacement_wave)
    
    with open(logo_symbol_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("logos/logo-symbol.svg remediated successfully.")

def remediate_guidelines():
    print("Remediating guidelines.html...")
    with open(guidelines_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Load the actual SVGs
    with open(logo_primary_path, "r", encoding="utf-8") as f:
        svg_primary = f.read().strip()
    with open(logo_monochrome_path, "r", encoding="utf-8") as f:
        svg_monochrome = f.read().strip()
    with open(logo_symbol_path, "r", encoding="utf-8") as f:
        svg_symbol = f.read().strip()
    with open(favicon_path, "r", encoding="utf-8") as f:
        svg_favicon = f.read().strip()
        
    # Remove XML headers if present in SVGs
    def clean_svg(svg_str):
        if svg_str.startswith("<?xml"):
            # find end of xml declaration
            idx = svg_str.find("?>")
            if idx != -1:
                svg_str = svg_str[idx+2:].strip()
        return svg_str

    svg_primary = clean_svg(svg_primary)
    svg_monochrome = clean_svg(svg_monochrome)
    svg_symbol = clean_svg(svg_symbol)
    svg_favicon = clean_svg(svg_favicon)

    # 1. Replace title
    content = content.replace(
        "<title>OpenClaw RaaS Gateway — Brand Guidelines</title>",
        "<title>Nhịp Điệu Xanh — Brand Guidelines</title>"
    )
    
    # 2. Replace header icon/title/subtitle block
    old_header_icon_block = """            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-tr from-brand-emerald to-brand-teal flex items-center justify-center color-dot">
                    <!-- Emerald Claw Icon in SVG -->
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-brand-slate" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4M6 6l12 12M6 18L18 6" />
                    </svg>
                </div>
                <div>
                    <h1 class="font-heading text-lg font-bold tracking-tight">OpenClaw RaaS Gateway</h1>"""
    
    new_header_icon_block = """            <div class="flex items-center gap-3">
                <div class="w-10 h-10 flex items-center justify-center">
                    <!-- Nhịp Điệu Xanh Symbol SVG -->
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="w-10 h-10">
                        <defs>
                            <linearGradient id="headerPrimaryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#10B981" />
                                <stop offset="100%" stop-color="#047857" />
                            </linearGradient>
                            <linearGradient id="headerSecondaryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#06B6D4" />
                                <stop offset="100%" stop-color="#0D9488" />
                            </linearGradient>
                            <linearGradient id="headerAccentGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#F59E0B" />
                                <stop offset="100%" stop-color="#D97706" />
                            </linearGradient>
                        </defs>
                        <path d="M 46 15 C 26 30, 16 54, 20 74 C 22 79, 26 83, 32 83 C 38 83, 42 75, 44 65 C 46 52, 41 32, 46 15 Z" fill="url(#headerPrimaryGrad)" />
                        <path d="M 54 15 C 74 30, 84 54, 80 74 C 78 79, 74 83, 68 83 C 62 83, 58 75, 56 65 C 54 52, 59 32, 54 15 Z" fill="url(#headerSecondaryGrad)" />
                        <path d="M 50 32 L 64 46 L 59 46 L 59 58 L 41 58 L 41 46 L 36 46 Z" fill="url(#headerAccentGrad)" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round" />
                        <path d="M 25 70 C 37 60, 42 78, 50 68 C 58 58, 63 76, 75 66" fill="none" stroke="#FFFFFF" stroke-width="8.5" stroke-linecap="round" stroke-linejoin="round" />
                        <path d="M 25 70 C 37 60, 42 78, 50 68 C 58 58, 63 76, 75 66" fill="none" stroke="url(#headerAccentGrad)" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                </div>
                <div>
                    <h1 class="font-heading text-lg font-bold tracking-tight">Nhịp Điệu Xanh</h1>"""
                    
    if old_header_icon_block not in content:
        # Check standardizing spaces
        raise ValueError("Could not find header icon block in guidelines.html")
    content = content.replace(old_header_icon_block, new_header_icon_block)

    # 3. Replace Intro / Mission text
    old_intro = """                <h2 class="text-4xl md:text-5xl font-heading font-extrabold tracking-tight bg-gradient-to-r from-brand-textPrimary to-brand-textSecondary bg-clip-text text-transparent">
                    The Sovereign Agent Gateway.
                </h2>
                <p class="text-lg text-brand-textSecondary leading-relaxed">
                    Consistent branding builds trust and makes the sovereign agent stack recognizable. OpenClaw RaaS Gateway combines military-grade security with fluid, edge-first automation. This document outlines our visual identity and patterns.
                </p>"""
                
    new_intro = """                <h2 class="text-4xl md:text-5xl font-heading font-extrabold tracking-tight bg-gradient-to-r from-brand-textPrimary to-brand-textSecondary bg-clip-text text-transparent">
                    Growth & Ecological Balance.
                </h2>
                <p class="text-lg text-brand-textSecondary leading-relaxed">
                    Consistent branding builds trust and makes the Nhịp Điệu Xanh brand recognizable. Nhịp Điệu Xanh combines ecological balance and renewable energy with modern CRM ergonomics and digital precision. This document outlines our visual identity and patterns.
                </p>"""
    
    if old_intro not in content:
        raise ValueError("Could not find intro block in guidelines.html")
    content = content.replace(old_intro, new_intro)

    # 4. Replace Brand Values Grid
    old_values_grid = """            <!-- Brand Values Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
                <div class="glass-panel p-6 rounded-xl hover:border-brand-emerald/40 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-lg bg-brand-emerald/10 border border-brand-emerald/20 flex items-center justify-center text-brand-emerald mb-4 font-bold group-hover:scale-110 transition-transform">
                        01
                    </div>
                    <h3 class="text-xl font-heading font-bold mb-2">Speed</h3>
                    <p class="text-sm text-brand-textSecondary">
                        Sub-millisecond execution start times. Optimized edge routing via Cloudflare Workers. We design lightweight, fast-loading, clean interfaces.
                    </p>
                </div>
                
                <div class="glass-panel p-6 rounded-xl hover:border-brand-teal/40 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-lg bg-brand-teal/10 border border-brand-teal/20 flex items-center justify-center text-brand-teal mb-4 font-bold group-hover:scale-110 transition-transform">
                        02
                    </div>
                    <h3 class="text-xl font-heading font-bold mb-2">Security</h3>
                    <p class="text-sm text-brand-textSecondary">
                        Sovereign LLM execution with zero-knowledge keys. High-contrast layouts, clean isolation lines, and clear security boundary visuals.
                    </p>
                </div>
                
                <div class="glass-panel p-6 rounded-xl hover:border-brand-emerald/40 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-lg bg-brand-emerald/10 border border-brand-emerald/20 flex items-center justify-center text-brand-emerald mb-4 font-bold group-hover:scale-110 transition-transform">
                        03
                    </div>
                    <h3 class="text-xl font-heading font-bold mb-2">Adaptability</h3>
                    <p class="text-sm text-brand-textSecondary">
                        Water Protocol connections linking Studio, Founder, Business, Product, Engineering, and Ops. Interfaces scale smoothly from code terminals to dashboards.
                    </p>
                </div>
            </div>"""

    new_values_grid = """            <!-- Brand Values Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
                <div class="glass-panel p-6 rounded-xl hover:border-brand-emerald/40 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-lg bg-brand-emerald/10 border border-brand-emerald/20 flex items-center justify-center text-brand-emerald mb-4 font-bold group-hover:scale-110 transition-transform">
                        01
                    </div>
                    <h3 class="text-xl font-heading font-bold mb-2">Sustainability</h3>
                    <p class="text-sm text-brand-textSecondary">
                        Promoting green energy solutions, ecological balance, and long-term environmental sustainability under the Emerald representation.
                    </p>
                </div>
                
                <div class="glass-panel p-6 rounded-xl hover:border-brand-teal/40 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-lg bg-brand-teal/10 border border-brand-teal/20 flex items-center justify-center text-brand-teal mb-4 font-bold group-hover:scale-110 transition-transform">
                        02
                    </div>
                    <h3 class="text-xl font-heading font-bold mb-2">Precision & CRM Ergonomics</h3>
                    <p class="text-sm text-brand-textSecondary">
                        Optimizing interactive digital CRM touchpoints and layout patterns for human-centric workspaces under the Teal representation.
                    </p>
                </div>
                
                <div class="glass-panel p-6 rounded-xl hover:border-amber-500/40 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 mb-4 font-bold group-hover:scale-110 transition-transform">
                        03
                    </div>
                    <h3 class="text-xl font-heading font-bold mb-2">Trust & Warmth</h3>
                    <p class="text-sm text-brand-textSecondary">
                        Fostering reliable client relationships with warm aesthetic focus states and transparent operational telemetry under the Amber representation.
                    </p>
                </div>
            </div>"""

    if old_values_grid not in content:
        raise ValueError("Could not find brand values grid in guidelines.html")
    content = content.replace(old_values_grid, new_values_grid)

    # 5. Replace `const OpenClaw = true;`
    content = content.replace(
        "const OpenClaw = true;",
        "const nhipDieuXanh = true;"
    )

    # 6. Replace other standalone texts
    content = content.replace(
        '<span class="font-heading text-3xl md:text-4xl font-extrabold tracking-tight">Sovereign Agent Gateway</span>',
        '<span class="font-heading text-3xl md:text-4xl font-extrabold tracking-tight">Nhịp Điệu Xanh</span>'
    )
    content = content.replace(
        '<span class="text-brand-textSecondary">Consistent branding builds trust and makes the sovereign agent stack recognizable.</span>',
        '<span class="text-brand-textSecondary">Consistent branding builds trust and makes the Nhịp Điệu Xanh brand recognizable.</span>'
    )
    content = content.replace(
        '<p class="text-sm text-brand-textSecondary mt-1">Design rules to maintain consistency across the OpenClaw RaaS Gateway ecosystem.</p>',
        '<p class="text-sm text-brand-textSecondary mt-1">Design rules to maintain consistency across the Nhịp Điệu Xanh ecosystem.</p>'
    )
    content = content.replace(
        '<p class="text-xs text-brand-textSecondary mt-1">Use Emerald Green (#10B981) for active agent states, call-to-actions, status tags, and correct verifications.</p>',
        '<p class="text-xs text-brand-textSecondary mt-1">Use Emerald Green (#10B981) for active states, call-to-actions, status tags, and correct verifications.</p>'
    )
    content = content.replace(
        '<p class="text-xs text-brand-textSecondary mt-1">Do not skew, stretch, rotate, recolor, or change the component structure of the glowing claw mark symbol.</p>',
        '<p class="text-xs text-brand-textSecondary mt-1">Do not skew, stretch, rotate, recolor, or change the component structure of the Nhịp Điệu Xanh symbol.</p>'
    )
    content = content.replace(
        '<span>Workspace: mekong-cli</span>',
        '<span>Workspace: nhipdieuxanh-agent</span>'
    )

    # 7. Replace Logo showcase section
    old_logo_grid = """            <!-- Logo Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Variation 1: Primary -->
                <div class="glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
                    <div class="p-12 bg-slate-950 flex justify-center items-center h-48 relative border-b border-brand-border">
                        <!-- Checkered dark background -->
                        <div class="absolute inset-0 opacity-10 pointer-events-none" style="background-image: radial-gradient(circle, #ffffff 1px, transparent 1px); background-size: 16px 16px;"></div>
                        
                        <!-- Primary Logo Rendered in HTML/SVG -->
                        <div class="flex items-center gap-3 relative z-10">
                            <div class="w-10 h-10 rounded-lg bg-gradient-to-tr from-brand-emerald to-brand-teal flex items-center justify-center color-dot">
                                <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-brand-slate" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4M6 6l12 12M6 18L18 6" />
                                </svg>
                            </div>
                            <span class="font-heading text-lg font-bold tracking-tight text-white">OpenClaw</span>
                        </div>
                    </div>
                    <div class="p-6 space-y-2">
                        <span class="text-[10px] font-mono font-bold bg-brand-emerald/10 text-brand-emerald px-2 py-0.5 rounded uppercase">01. Primary Logo</span>
                        <h4 class="font-heading font-bold text-sm mt-1">Full Color (Dark Background)</h4>
                        <p class="text-xs text-brand-textSecondary leading-relaxed">
                            Emerald claw icon with <strong>OpenClaw</strong> text. Standard representation. Recommended on dark (#0b0f19) background layouts.
                        </p>
                    </div>
                </div>

                <!-- Variation 2: Monochrome -->
                <div class="glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
                    <div class="p-12 bg-white flex justify-center items-center h-48 relative border-b border-brand-border">
                        <!-- Checkered light background -->
                        <div class="absolute inset-0 opacity-10 pointer-events-none" style="background-image: radial-gradient(circle, #000000 1px, transparent 1px); background-size: 16px 16px;"></div>
                        
                        <!-- Monochrome Logo Rendered in HTML/SVG -->
                        <div class="flex items-center gap-3 relative z-10">
                            <div class="w-10 h-10 rounded-lg bg-black flex items-center justify-center">
                                <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4M6 6l12 12M6 18L18 6" />
                                </svg>
                            </div>
                            <span class="font-heading text-lg font-bold tracking-tight text-black">OpenClaw</span>
                        </div>
                    </div>
                    <div class="p-6 space-y-2">
                        <span class="text-[10px] font-mono font-bold bg-brand-border text-brand-textSecondary px-2 py-0.5 rounded uppercase">02. Monochrome Logo</span>
                        <h4 class="font-heading font-bold text-sm mt-1">High-Contrast (Light Background)</h4>
                        <p class="text-xs text-brand-textSecondary leading-relaxed">
                            For white or light backgrounds, print files, terminal ASCII banners, and physical engravings.
                        </p>
                    </div>
                </div>

                <!-- Variation 3: Icon Only -->
                <div class="glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
                    <div class="p-12 bg-slate-950 flex justify-center items-center h-48 relative border-b border-brand-border">
                        <!-- Checkered dark background -->
                        <div class="absolute inset-0 opacity-10 pointer-events-none" style="background-image: radial-gradient(circle, #ffffff 1px, transparent 1px); background-size: 16px 16px;"></div>
                        
                        <!-- Icon Only Rendered in HTML/SVG -->
                        <div class="w-14 h-14 rounded-xl bg-gradient-to-tr from-brand-emerald to-brand-teal flex items-center justify-center color-dot relative z-10">
                            <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-brand-slate" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4M6 6l12 12M6 18L18 6" />
                            </svg>
                        </div>
                    </div>
                    <div class="p-6 space-y-2">
                        <span class="text-[10px] font-mono font-bold bg-brand-teal/10 text-brand-teal px-2 py-0.5 rounded uppercase">03. Icon Only</span>
                        <h4 class="font-heading font-bold text-sm mt-1">Claw Icon Mark</h4>
                        <p class="text-xs text-brand-textSecondary leading-relaxed">
                            Abstract geometric claw symbol. Ideal for favicons, user profile photos, navigation buttons, and small cards.
                        </p>
                    </div>
                </div>
            </div>"""

    new_logo_grid = f"""            <!-- Logo Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <!-- Variation 1: Primary Logo -->
                <div class="glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
                    <div class="p-4 bg-slate-950 flex justify-center items-center h-48 relative border-b border-brand-border">
                        <!-- Checkered dark background -->
                        <div class="absolute inset-0 opacity-10 pointer-events-none" style="background-image: radial-gradient(circle, #ffffff 1px, transparent 1px); background-size: 16px 16px;"></div>
                        
                        <!-- Primary Logo Rendered in HTML/SVG -->
                        <div class="w-full max-w-[240px] relative z-10">
                            {svg_primary}
                        </div>
                    </div>
                    <div class="p-6 space-y-2">
                        <span class="text-[10px] font-mono font-bold bg-brand-emerald/10 text-brand-emerald px-2 py-0.5 rounded uppercase">01. Primary Logo</span>
                        <h4 class="font-heading font-bold text-sm mt-1">Full Color</h4>
                        <p class="text-xs text-brand-textSecondary leading-relaxed">
                            Nhịp Điệu Xanh full color brand logo with the emerald leaf wing and golden house symbol. Suitable for light background layouts.
                        </p>
                    </div>
                </div>

                <!-- Variation 2: Monochrome Logo -->
                <div class="glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
                    <div class="p-4 bg-white flex justify-center items-center h-48 relative border-b border-brand-border">
                        <!-- Checkered light background -->
                        <div class="absolute inset-0 opacity-10 pointer-events-none" style="background-image: radial-gradient(circle, #000000 1px, transparent 1px); background-size: 16px 16px;"></div>
                        
                        <!-- Monochrome Logo Rendered in HTML/SVG -->
                        <div class="w-full max-w-[240px] relative z-10">
                            {svg_monochrome}
                        </div>
                    </div>
                    <div class="p-6 space-y-2">
                        <span class="text-[10px] font-mono font-bold bg-brand-border text-brand-textSecondary px-2 py-0.5 rounded uppercase">02. Monochrome Logo</span>
                        <h4 class="font-heading font-bold text-sm mt-1">High-Contrast (Light Background)</h4>
                        <p class="text-xs text-brand-textSecondary leading-relaxed">
                            For white or light backgrounds, print files, terminal ASCII banners, and physical engravings.
                        </p>
                    </div>
                </div>

                <!-- Variation 3: Symbol -->
                <div class="glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
                    <div class="p-4 bg-slate-950 flex justify-center items-center h-48 relative border-b border-brand-border">
                        <!-- Checkered dark background -->
                        <div class="absolute inset-0 opacity-10 pointer-events-none" style="background-image: radial-gradient(circle, #ffffff 1px, transparent 1px); background-size: 16px 16px;"></div>
                        
                        <!-- Symbol Rendered in HTML/SVG -->
                        <div class="w-16 h-16 relative z-10">
                            {svg_symbol}
                        </div>
                    </div>
                    <div class="p-6 space-y-2">
                        <span class="text-[10px] font-mono font-bold bg-brand-teal/10 text-brand-teal px-2 py-0.5 rounded uppercase">03. Brand Symbol</span>
                        <h4 class="font-heading font-bold text-sm mt-1">Symbol Mark</h4>
                        <p class="text-xs text-brand-textSecondary leading-relaxed">
                            Abstract geometric leaf wing symbol with house and wave. Ideal for profile icons and status indicators.
                        </p>
                    </div>
                </div>

                <!-- Variation 4: Favicon -->
                <div class="glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
                    <div class="p-4 bg-slate-950 flex justify-center items-center h-48 relative border-b border-brand-border">
                        <!-- Checkered dark background -->
                        <div class="absolute inset-0 opacity-10 pointer-events-none" style="background-image: radial-gradient(circle, #ffffff 1px, transparent 1px); background-size: 16px 16px;"></div>
                        
                        <!-- Favicon Rendered in HTML/SVG -->
                        <div class="w-10 h-10 relative z-10">
                            {svg_favicon}
                        </div>
                    </div>
                    <div class="p-6 space-y-2">
                        <span class="text-[10px] font-mono font-bold bg-brand-emerald/10 text-brand-emerald px-2 py-0.5 rounded uppercase">04. Favicon</span>
                        <h4 class="font-heading font-bold text-sm mt-1">Browser Icon</h4>
                        <p class="text-xs text-brand-textSecondary leading-relaxed">
                            Optimized 32x32 rounded icon container. Designed specifically for browser tab visibility.
                        </p>
                    </div>
                </div>
            </div>"""

    if old_logo_grid not in content:
        # Standardize whitespace slightly or do a substring find
        raise ValueError("Could not find logo grid in guidelines.html")
    content = content.replace(old_logo_grid, new_logo_grid)

    # 8. Replace footer and BSL license
    old_footer_block = """    <footer class="glass-panel border-t border-brand-border/80 mt-20 py-8 relative z-10">
        <div class="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-mono text-brand-textSecondary">
            <div>
                © 2026 OpenClaw RaaS Gateway. Released under BSL 1.1 License.
            </div>"""
            
    new_footer_block = """    <footer class="glass-panel border-t border-brand-border/80 mt-20 py-8 relative z-10">
        <div class="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-mono text-brand-textSecondary">
            <div>
                © 2026 Nhịp Điệu Xanh. All rights reserved.
            </div>"""

    if old_footer_block not in content:
        raise ValueError("Could not find footer block in guidelines.html")
    content = content.replace(old_footer_block, new_footer_block)

    with open(guidelines_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("guidelines.html remediated successfully.")

def verify_files():
    print("Running verification checks...")
    
    # 1. Parse JSON brand_tokens
    with open(brand_tokens_path, "r", encoding="utf-8") as f:
        tokens = json.load(f)
    print("JSON Verification: brand_tokens.json is valid JSON structure.")
    
    # 2. Check no references of OpenClaw or mekong-cli remain in JSON
    json_str = json.dumps(tokens)
    if "openclaw" in json_str.lower() or "mekong-cli" in json_str.lower() or "raas" in json_str.lower() or "water protocol" in json_str.lower():
        raise ValueError("Verification failed: brand_tokens.json still contains forbidden words.")
    print("JSON Verification: brand_tokens.json is clean of forbidden references.")

    # 3. Verify SVGs are valid XML documents
    for name, path in [("logo-symbol", logo_symbol_path), ("logo-primary", logo_primary_path), ("logo-monochrome", logo_monochrome_path), ("favicon", favicon_path)]:
        try:
            ET.parse(path)
            print(f"XML Verification: {name}.svg is a valid XML document.")
        except Exception as e:
            raise ValueError(f"XML Verification failed for {name}.svg: {e}")

    # 4. Check guidelines.html is valid HTML and has no references to OpenClaw or mekong-cli or Water Protocol
    with open(guidelines_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Filter out local workspace in footer check if needed, but we replaced it as well
    # Let's count occurrences
    forbidden = ["openclaw", "mekong-cli", "raas gateway", "water protocol"]
    for word in forbidden:
        count = html_content.lower().count(word)
        if count > 0:
            # Let's see where the occurrences are
            print(f"DEBUG: Found {count} occurrences of '{word}'")
            # find index
            idx = 0
            while True:
                idx = html_content.lower().find(word, idx)
                if idx == -1: break
                start = max(0, idx - 50)
                end = min(len(html_content), idx + 50)
                print(f"  Snippet: ... {html_content[start:end]} ...")
                idx += len(word)
            raise ValueError(f"Verification failed: guidelines.html still contains word '{word}' ({count} times)")
            
    print("HTML Verification: guidelines.html is clean of forbidden references.")
    print("All verification steps passed successfully!")

if __name__ == "__main__":
    remediate_brand_tokens()
    remediate_logo_symbol()
    remediate_guidelines()
    verify_files()

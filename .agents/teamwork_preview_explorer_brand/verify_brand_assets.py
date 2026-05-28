import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
import os
import re

BRAND_DIR = '/Users/macbook/nhipdieuxanh-agent/brand'
LOGOS_DIR = os.path.join(BRAND_DIR, 'logos')

class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.inline_svg_count = 0
        self.has_color_grid = False
        self.has_font_scale = False
        self.has_rules = False

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attrs_dict = dict(attrs)
        
        if tag == 'link':
            href = attrs_dict.get('href', '')
            rel = attrs_dict.get('rel', '')
            self.links.append((rel, href))
        elif tag == 'script':
            src = attrs_dict.get('src', '')
            if src:
                self.links.append(('script', src))
        elif tag == 'svg':
            self.inline_svg_count += 1
            
        # Check elements that could identify color grid, font scale, rules
        id_val = attrs_dict.get('id', '')
        if id_val == 'colors':
            self.has_color_grid = True
        elif id_val == 'typography':
            self.has_font_scale = True
        elif id_val == 'rules':
            self.has_rules = True

def verify_json():
    json_path = os.path.join(BRAND_DIR, 'brand_tokens.json')
    print(f"Verifying JSON: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure key token structures are present
    assert 'colors' in data, "Missing 'colors' in brand tokens"
    assert 'typography' in data, "Missing 'typography' in brand tokens"
    
    # Colors
    colors = data['colors']
    assert 'primary' in colors, "Missing primary color in tokens"
    assert colors['primary']['hex'] == '#10B981', f"Expected primary color to be #10B981, got {colors['primary']['hex']}"
    assert 'neutral' in colors, "Missing neutral color in tokens"
    assert 'accent' in colors, "Missing accent color in tokens"
    assert 'semantic' in colors, "Missing semantic color in tokens"
    
    # Check for dummies/cheats in descriptions
    for k, v in colors.items():
        desc = v.get('description', '')
        if 'test' in desc.lower() or 'placeholder' in desc.lower() or 'bypass' in desc.lower():
            print(f"WARNING: Potential dummy/placeholder text in color description for '{k}': {desc}")
            return False, data
            
    print("✓ brand_tokens.json is valid and contains genuine data.")
    return True, data

def verify_svgs():
    svg_files = ['logo-primary.svg', 'logo-monochrome.svg', 'logo-symbol.svg', 'favicon.svg']
    results = {}
    for filename in svg_files:
        path = os.path.join(LOGOS_DIR, filename)
        print(f"Verifying SVG: {path}")
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            
            # Check XML namespace and root tag
            assert root.tag.endswith('svg'), f"Root tag of {filename} is not svg"
            
            # Find paths
            namespaces = {'svg': 'http://www.w3.org/2000/svg'}
            # Since elements might or might not have namespaces in python parsing:
            paths = root.findall('.//{http://www.w3.org/2000/svg}path')
            if not paths:
                # Try without namespace
                paths = root.findall('.//path')
                
            print(f"  Found {len(paths)} path(s)")
            assert len(paths) > 0, f"No paths found in {filename}"
            
            # Verify paths contain valid path data (non-empty 'd' attribute)
            for i, p in enumerate(paths):
                d_attr = p.get('d', '')
                assert d_attr, f"Path {i} in {filename} is missing 'd' attribute"
                # Basic check on path syntax: starts with M, C, L, Z, etc.
                assert any(c in d_attr for c in ['M', 'm', 'C', 'c', 'L', 'l', 'Z', 'z']), f"Path data '{d_attr}' looks invalid"
            
            results[filename] = True
        except Exception as e:
            print(f"✕ Verification failed for {filename}: {e}")
            results[filename] = False
            
    return all(results.values())

def verify_guidelines():
    html_path = os.path.join(BRAND_DIR, 'guidelines.html')
    print(f"Verifying HTML Guidelines: {html_path}")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    parser = SimpleHTMLParser()
    parser.feed(html_content)
    
    print(f"  Inline SVGs count: {parser.inline_svg_count}")
    print(f"  Found links: {parser.links}")
    print(f"  Has color grid section: {parser.has_color_grid}")
    print(f"  Has typography section: {parser.has_font_scale}")
    print(f"  Has rules section: {parser.has_rules}")
    
    # Assertions
    assert parser.inline_svg_count >= 4, "Guidelines should render the logos inline"
    assert parser.has_color_grid, "Guidelines missing color grid"
    assert parser.has_font_scale, "Guidelines missing font scale section"
    assert parser.has_rules, "Guidelines missing rules / Dos and Don'ts section"
    
    # Verify Tailwind script is loaded
    has_tailwind = any('tailwindcss' in link[1] for link in parser.links)
    assert has_tailwind, "Tailwind CSS script not linked"
    
    # Verify Google fonts link
    has_gfonts = any('fonts.googleapis.com' in link[1] or 'fonts.gstatic.com' in link[1] for link in parser.links)
    assert has_gfonts, "Google Fonts links not found"
    
    print("✓ guidelines.html is valid, contains required sections, inline SVGs, and linked assets.")
    return True

def verify_logo_symbol_outlines():
    symbol_path = os.path.join(LOGOS_DIR, 'logo-symbol.svg')
    print(f"Verifying overlapping outline strokes in: {symbol_path}")
    with open(symbol_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # We expect:
    # 1. House path with fill=accentGrad/amber, and white stroke:
    # stroke="#FFFFFF" and stroke-width="2" or similar
    # 2. Wave path with thick white stroke, and another path with accentGrad/amber thin stroke on top
    
    # Let's inspect the parsed XML structure
    tree = ET.parse(symbol_path)
    root = tree.getroot()
    
    paths = root.findall('.//{http://www.w3.org/2000/svg}path') or root.findall('.//path')
    
    # Let's check house:
    # Look for path that is the house (starts with M 50 32 L 64 46 or similar)
    house_path = None
    wave_paths = []
    
    for p in paths:
        d = p.get('d', '')
        if 'L 64 46' in d or 'L 59 46' in d:
            house_path = p
        elif 'C 37 60' in d or 'C 58 58' in d:
            wave_paths.append(p)
            
    assert house_path is not None, "House path not found in logo-symbol.svg"
    assert len(wave_paths) >= 2, f"Expected at least 2 wave paths for stroke separation, found {len(wave_paths)}"
    
    # House stroke check
    house_stroke = house_path.get('stroke')
    house_stroke_width = house_path.get('stroke-width')
    print(f"  House stroke: {house_stroke}, width: {house_stroke_width}")
    assert house_stroke == '#FFFFFF', f"House stroke is not white (#FFFFFF), got {house_stroke}"
    assert house_stroke_width, "House is missing stroke-width"
    
    # Wave stroke checks
    white_wave = None
    colored_wave = None
    for wp in wave_paths:
        stroke = wp.get('stroke', '')
        width = float(wp.get('stroke-width', '0'))
        if stroke == '#FFFFFF':
            white_wave = (wp, width)
        elif 'accentGrad' in stroke or 'url(#accentGrad)' in stroke:
            colored_wave = (wp, width)
            
    assert white_wave is not None, "No white wave outline stroke found"
    assert colored_wave is not None, "No colored gradient wave path found"
    
    print(f"  White wave stroke width: {white_wave[1]}")
    print(f"  Colored wave stroke width: {colored_wave[1]}")
    
    # Verify white wave is thicker than colored wave
    assert white_wave[1] > colored_wave[1], f"White wave stroke ({white_wave[1]}) must be thicker than colored wave stroke ({colored_wave[1]}) to provide outline separation"
    
    print("✓ Overlapping element outlines in logo-symbol.svg verified successfully.")
    return True

def scan_forbidden_keywords():
    forbidden = ['OpenClaw', 'mekong-cli', 'RaaS', 'Water Protocol']
    regexes = [re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE) for word in forbidden]
    
    found_violations = {}
    for root_dir, _, files in os.walk(BRAND_DIR):
        for f in files:
            path = os.path.join(root_dir, f)
            # Skip binary files if any, but all these should be text
            if f.endswith(('.json', '.html', '.svg', '.txt', '.css', '.js')):
                with open(path, 'r', encoding='utf-8', errors='ignore') as file_obj:
                    content = file_obj.read()
                    for idx, word in enumerate(forbidden):
                        matches = regexes[idx].findall(content)
                        if matches:
                            if path not in found_violations:
                                found_violations[path] = []
                            found_violations[path].append((word, len(matches)))
                            
    if found_violations:
        print("✕ Forbidden keywords found:")
        for path, matches in found_violations.items():
            print(f"  {path}: {matches}")
        return False
    else:
        print("✓ No forbidden keywords found in brand files.")
        return True

def run_all_checks():
    status = []
    status.append(('JSON Tokens', verify_json()[0]))
    status.append(('SVG Parsing', verify_svgs()))
    status.append(('Guidelines HTML', verify_guidelines()))
    status.append(('Logo Symbol Outlines', verify_logo_symbol_outlines()))
    status.append(('Forbidden Keywords Scan', scan_forbidden_keywords()))
    
    overall_status = all(s[1] for s in status)
    print("\nSUMMARY OF VERIFICATION:")
    for name, ok in status:
        print(f"  {name}: {'OK' if ok else 'FAILED'}")
        
    if overall_status:
        print("\nFINAL VERDICT: CLEAN")
        return "CLEAN"
    else:
        print("\nFINAL VERDICT: VIOLATION")
        return "VIOLATION"

if __name__ == '__main__':
    run_all_checks()

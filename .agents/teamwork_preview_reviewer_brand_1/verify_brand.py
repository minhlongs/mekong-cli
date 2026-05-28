import os
import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

class SimpleHTMLValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.errors = []
        
    def handle_starttag(self, tag, attrs):
        # We don't strictly enforce closing self-closing tags in HTML5, but we track tags
        self.tags.append(tag)
        
    def handle_endtag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)

def verify_files():
    brand_dir = "/Users/macbook/nhipdieuxanh-agent/brand"
    files_to_check = [
        "brand_tokens.json",
        "guidelines.html",
        "logos/logo-primary.svg",
        "logos/logo-monochrome.svg",
        "logos/logo-symbol.svg",
        "logos/favicon.svg"
    ]
    
    print("=== VERIFYING FILE EXISTENCE AND SIZES ===")
    for f in files_to_check:
        full_path = os.path.join(brand_dir, f)
        if not os.path.exists(full_path):
            print(f"[-] FILE MISSING: {f}")
            continue
        size = os.path.getsize(full_path)
        status = "[+]" if size >= 100 else "[-]"
        print(f"{status} {f}: {size} bytes")
        
    print("\n=== VERIFYING JSON VALIDITY ===")
    json_path = os.path.join(brand_dir, "brand_tokens.json")
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            print("[+] brand_tokens.json is valid JSON.")
            # Print keys
            print(f"    Keys: {list(data.keys())}")
            if "colors" in data:
                print(f"    Colors: {list(data['colors'].keys())}")
            if "typography" in data:
                print(f"    Typography: {list(data['typography'].keys())}")
    except Exception as e:
        print(f"[-] brand_tokens.json invalid JSON: {e}")
        
    print("\n=== VERIFYING SVG XML VALIDITY ===")
    svgs = [
        "logos/logo-primary.svg",
        "logos/logo-monochrome.svg",
        "logos/logo-symbol.svg",
        "logos/favicon.svg"
    ]
    for svg in svgs:
        svg_path = os.path.join(brand_dir, svg)
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
            print(f"[+] {svg} is valid XML. Root tag: {root.tag}, attrib: {root.attrib}")
        except Exception as e:
            print(f"[-] {svg} invalid XML: {e}")
            
    print("\n=== VERIFYING HTML VALIDITY & CONTENT ===")
    html_path = os.path.join(brand_dir, "guidelines.html")
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            content = file.read()
            parser = SimpleHTMLValidator()
            parser.feed(content)
            print("[+] guidelines.html read successfully.")
            
            # Content checks
            checks = {
                "color blocks": "Color Palette" in content or "colors" in content.lower(),
                "typography scales": "Typography Scale" in content or "typography" in content.lower(),
                "logos": "Logo Variations" in content or "logos" in content.lower(),
                "Do's/Don'ts rules": "Do's & Don'ts" in content or "rules" in content.lower()
            }
            for k, v in checks.items():
                print(f"    Contains {k}: {'[+] Yes' if v else '[-] No'}")
                
            # Discrepancy checks
            print("\n=== DISCREPANCY CHECKS ===")
            claw_count = content.lower().count("openclaw")
            raas_count = content.lower().count("raas")
            ndx_count = content.lower().count("nhịp điệu xanh")
            print(f"    'OpenClaw' mentions in guidelines.html: {claw_count}")
            print(f"    'RaaS' mentions in guidelines.html: {raas_count}")
            print(f"    'Nhịp Điệu Xanh' mentions in guidelines.html: {ndx_count}")
    except Exception as e:
        print(f"[-] guidelines.html error: {e}")

if __name__ == "__main__":
    verify_files()

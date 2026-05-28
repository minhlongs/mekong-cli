import os
import json
import xml.etree.ElementTree as ET
import sys

def main():
    files_to_check = [
        "/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json",
        "/Users/macbook/nhipdieuxanh-agent/brand/guidelines.html",
        "/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-primary.svg",
        "/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-monochrome.svg",
        "/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-symbol.svg",
        "/Users/macbook/nhipdieuxanh-agent/brand/logos/favicon.svg",
    ]

    all_passed = True

    print("=== VERIFYING BRAND ASSETS ===")

    for file_path in files_to_check:
        print(f"\nChecking: {file_path}")
        # 1. Existence and size >= 100 bytes check
        if not os.path.exists(file_path):
            print("[-] ERROR: File does not exist!")
            all_passed = False
            continue
        
        size = os.path.getsize(file_path)
        print(f"[+] Found file. Size: {size} bytes")
        if size < 100:
            print("[-] ERROR: File is too small (< 100 bytes)!")
            all_passed = False
            continue
        else:
            print("[+] Size check passed (>= 100 bytes)")

        # 2. Format specific checks
        if file_path.endswith('.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                print("[+] Format check passed: Valid JSON format")
            except Exception as e:
                print(f"[-] ERROR parsing JSON: {e}")
                all_passed = False

        elif file_path.endswith('.svg'):
            try:
                # SVG is XML, try parsing with ElementTree
                tree = ET.parse(file_path)
                root = tree.getroot()
                # Simple check for svg root tag name (ignoring namespaces or including them)
                if 'svg' not in root.tag.lower():
                    print(f"[-] ERROR: Root tag is not svg, got {root.tag}")
                    all_passed = False
                else:
                    print("[+] Format check passed: Valid SVG (XML) document")
            except Exception as e:
                print(f"[-] ERROR parsing SVG (XML): {e}")
                all_passed = False
                
        elif file_path.endswith('.html'):
            # Just verify it starts with standard HTML characters or tags to ensure basic integrity
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1024)
                if '<html' in content.lower() or '<!doctype html' in content.lower():
                    print("[+] Format check passed: Valid basic HTML structure")
                else:
                    print("[-] WARNING: '<html' or '<!DOCTYPE html' not found in first 1024 bytes")
            except Exception as e:
                print(f"[-] ERROR reading HTML file: {e}")
                all_passed = False

    if all_passed:
        print("\n[SUCCESS] All files exist, size constraints met, and formats validated successfully.")
        sys.exit(0)
    else:
        print("\n[FAILURE] One or more verification checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()

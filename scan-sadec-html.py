#!/usr/bin/env python3
"""
Quét toàn bộ file HTML trong sadec-marketing-hub để tìm:
1. Broken links (href指向 không tồn tại)
2. Missing meta tags (title, description, viewport, og tags)
"""

import os
import re
from pathlib import Path
from html.parser import HTMLParser
from collections import defaultdict
import json

BASE_DIR = Path("/Users/mac/.gemini/antigravity/scratch/sadec-marketing-hub")
EXCLUDE_DIRS = {'node_modules', '.git', '.vercel', '.wrangler', '.pytest_cache', 'playwright-report'}

# Meta tags required for each HTML file
REQUIRED_META = ['charset', 'viewport', 'title']
OG_META = ['og:title', 'og:description', 'og:url', 'og:image']

class HTMLMetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta_tags = set()
        self.title = False
        self.links = []
        self.current_dir = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'meta':
            # Check charset
            if 'charset' in attrs_dict:
                self.meta_tags.add('charset')
            # Check name property
            name = attrs_dict.get('name', '')
            if name:
                self.meta_tags.add(name.lower())
            # Check property (for og: tags)
            prop = attrs_dict.get('property', '')
            if prop:
                self.meta_tags.add(prop.lower())
            # Check http-equiv
            http_equiv = attrs_dict.get('http-equiv', '')
            if http_equiv:
                self.meta_tags.add(f"http-equiv:{http_equiv.lower()}")

        elif tag == 'title':
            self.title = True

        elif tag in ('a', 'link', 'script', 'img', 'form'):
            href = attrs_dict.get('href', '') or attrs_dict.get('src', '') or attrs_dict.get('action', '')
            if href and not href.startswith(('#', 'tel:', 'mailto:', 'javascript:', 'data:')):
                self.links.append({
                    'tag': tag,
                    'href': href,
                    'line': self.getpos()[0]
                })

def parse_html_file(filepath):
    """Parse single HTML file and extract meta info + links"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        parser = HTMLMetaParser()
        parser.feed(content)

        return {
            'meta_tags': parser.meta_tags,
            'has_title': parser.title,
            'links': parser.links,
            'content': content
        }
    except Exception as e:
        return {'error': str(e), 'links': [], 'meta_tags': set(), 'has_title': False}

def check_link_exists(link_path, base_dir, all_files):
    """Check if a relative link exists"""
    if link_path.startswith(('http://', 'https://', '//')):
        return True, 'external'

    # Remove query params and hash
    clean_path = link_path.split('?')[0].split('#')[0]

    # Handle root-relative paths
    if clean_path.startswith('/'):
        clean_path = clean_path[1:]

    # Check if file exists
    target = base_dir / clean_path
    if target.exists():
        return True, 'exists'

    # Check in all_files set
    if clean_path in all_files or f"{clean_path}.html" in all_files:
        return True, 'in_registry'

    return False, 'missing'

def scan_directory():
    """Scan all HTML files in the directory"""
    results = {
        'missing_meta': [],
        'broken_links': [],
        'summary': defaultdict(int)
    }

    # Build file registry
    all_files = set()
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), BASE_DIR)
            all_files.add(rel_path)

    html_files = [f for f in all_files if f.endswith('.html')]
    results['summary']['total_html_files'] = len(html_files)

    print(f"📊 Quét {len(html_files)} file HTML...\n")

    for rel_path in html_files:
        filepath = BASE_DIR / rel_path
        parsed = parse_html_file(filepath)

        if 'error' in parsed:
            print(f"  ⚠️  Lỗi parsing {rel_path}: {parsed['error']}")
            continue

        # Check meta tags
        missing_meta = []
        if not parsed['has_title']:
            missing_meta.append('title')
        if 'charset' not in parsed['meta_tags']:
            missing_meta.append('charset')
        if 'viewport' not in parsed['meta_tags']:
            missing_meta.append('viewport')
        if 'description' not in parsed['meta_tags']:
            missing_meta.append('description')

        # Check OG tags
        missing_og = [og for og in OG_META if og not in parsed['meta_tags']]

        if missing_meta or missing_og:
            results['missing_meta'].append({
                'file': rel_path,
                'missing_required': missing_meta,
                'missing_og': missing_og
            })

        # Check internal links
        for link in parsed['links']:
            exists, status = check_link_exists(link['href'], BASE_DIR, all_files)
            if not exists:
                results['broken_links'].append({
                    'file': rel_path,
                    'line': link['line'],
                    'href': link['href'],
                    'tag': link['tag']
                })

    results['summary']['files_missing_meta'] = len(results['missing_meta'])
    results['summary']['broken_links_count'] = len(results['broken_links'])

    return results

def print_report(results):
    """Print formatted report"""
    print("=" * 80)
    print("📋 KẾT QUẢ QUÉT SADec-MARKETING-HUB")
    print("=" * 80)

    print(f"\n📊 TỔNG QUAN:")
    print(f"   • Tổng số file HTML: {results['summary']['total_html_files']}")
    print(f"   • File thiếu meta tags: {results['summary']['files_missing_meta']}")
    print(f"   • Broken links: {results['summary']['broken_links_count']}")

    if results['missing_meta']:
        print(f"\n📝 MISSING META TAGS ({len(results['missing_meta'])} files):")
        print("-" * 60)
        for item in results['missing_meta'][:20]:  # Show first 20
            missing = item['missing_required'] + item['missing_og']
            print(f"   • {item['file']}")
            print(f"      Thiếu: {', '.join(missing)}")
        if len(results['missing_meta']) > 20:
            print(f"   ... và {len(results['missing_meta']) - 20} file khác")

    if results['broken_links']:
        print(f"\n🔗 BROKEN LINKS ({len(results['broken_links'])} links):")
        print("-" * 60)
        # Group by target file
        by_target = defaultdict(list)
        for link in results['broken_links']:
            by_target[link['href']].append(link)

        for href, links in list(by_target.items())[:15]:  # Show first 15 targets
            print(f"   • {href}")
            for link in links[:3]:
                print(f"      → {link['file']}:{link['line']}")
        if len(by_target) > 15:
            print(f"   ... và {len(by_target) - 15} broken links khác")

    # Save JSON report
    report_path = BASE_DIR / ".cto-reports" / "html-scan-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert sets to lists for JSON serialization
    json_results = {
        'summary': dict(results['summary']),
        'missing_meta': results['missing_meta'],
        'broken_links': results['broken_links']
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Báo cáo chi tiết: {report_path}")
    print("=" * 80)

if __name__ == '__main__':
    results = scan_directory()
    print_report(results)

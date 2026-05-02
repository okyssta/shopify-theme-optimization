#!/usr/bin/env python3
"""Static Shopify theme performance audit.

This script inspects a Shopify theme directory or theme zip and reports common
performance issues. It does not modify files.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TEXT_EXTS = {'.liquid', '.html', '.js', '.css', '.json', '.scss', '.ts', '.mjs'}
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico', '.avif'}
JS_EXTS = {'.js', '.mjs'}
CSS_EXTS = {'.css', '.scss'}
MAX_TEXT_READ = 2_500_000

THIRD_PARTY_HINTS = (
    'klaviyo', 'judge.me', 'loox', 'yotpo', 'okendo', 'gorgias', 'recharge',
    'attentive', 'postscript', 'hotjar', 'fullstory', 'tiktok', 'facebook',
    'google-analytics', 'googletagmanager', 'gtag', 'doubleclick', 'snapchat',
    'pinterest', 'criteo', 'bing', 'zendesk', 'intercom', 'privy', 'justuno',
    'afterpay', 'klarna', 'shopifycloud', 'cdn.shopify.com/shopifycloud'
)

ABOVE_FOLD_HINTS = (
    'hero', 'slideshow', 'banner', 'image-banner', 'main-product', 'product-media',
    'header', 'featured-product', 'collection-hero', 'announcement-bar'
)


def human_bytes(num: int) -> str:
    units = ['B', 'KB', 'MB', 'GB']
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == 'B':
                return f'{int(value)} {unit}'
            return f'{value:.1f} {unit}'
        value /= 1024
    return f'{num} B'


def safe_extract_zip(zip_path: Path) -> tempfile.TemporaryDirectory[str]:
    tmp = tempfile.TemporaryDirectory(prefix='shopify_theme_audit_')
    base = Path(tmp.name).resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            target = (base / member.filename).resolve()
            if not str(target).startswith(str(base) + os.sep):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, target.open('wb') as dst:
                dst.write(src.read())
    return tmp


def detect_theme_root(path: Path) -> Path:
    if (path / 'layout' / 'theme.liquid').exists():
        return path
    candidates = []
    for child in path.rglob('layout/theme.liquid'):
        candidates.append(child.parent.parent)
    if candidates:
        candidates.sort(key=lambda p: len(p.parts))
        return candidates[0]
    return path


def iter_files(root: Path) -> Iterable[Path]:
    ignored = {'.git', 'node_modules', '.cache', 'dist', 'coverage', '.shopify'}
    for path in root.rglob('*'):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file():
            yield path


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace(os.sep, '/')


def read_text(path: Path) -> str:
    data = path.read_bytes()
    if len(data) > MAX_TEXT_READ:
        data = data[:MAX_TEXT_READ]
    return data.decode('utf-8', errors='ignore')


def line_number(text: str, pos: int) -> int:
    return text.count('\n', 0, pos) + 1


def add_finding(findings: List[Dict[str, Any]], severity: str, category: str,
                file: str, line: Optional[int], issue: str, recommendation: str,
                evidence: str = '') -> None:
    findings.append({
        'severity': severity,
        'category': category,
        'file': file,
        'line': line,
        'issue': issue,
        'recommendation': recommendation,
        'evidence': evidence.strip()[:300],
    })


def likely_above_fold_file(path_str: str) -> bool:
    lower = path_str.lower()
    return any(hint in lower for hint in ABOVE_FOLD_HINTS)


def scan_markup(path: Path, root: Path, text: str, findings: List[Dict[str, Any]]) -> None:
    r = rel(path, root)
    lower_path = r.lower()

    for match in re.finditer(r'<script\b([^>]*)>', text, re.IGNORECASE):
        attrs = match.group(1)
        attrs_lower = attrs.lower()
        line = line_number(text, match.start())
        if 'src=' in attrs_lower:
            has_nonblocking = any(token in attrs_lower for token in (' defer', ' async', 'type="module"', "type='module'"))
            is_json = 'application/ld+json' in attrs_lower or 'application/json' in attrs_lower
            if not has_nonblocking and not is_json:
                sev = 'high' if lower_path == 'layout/theme.liquid' else 'medium'
                add_finding(
                    findings, sev, 'javascript', r, line,
                    'parser-blocking script tag may delay DOM construction and LCP',
                    'Add defer/async/module when dependency order allows, or load non-critical code on interaction/idle.',
                    match.group(0)
                )
            src_match = re.search(r'src=["\']([^"\']+)', attrs, re.IGNORECASE)
            if src_match:
                src = src_match.group(1)
                if src.startswith(('http://', 'https://', '//')) and 'cdn.shopify.com' not in src:
                    sev = 'medium'
                    hint = src.lower()
                    if any(domain in hint for domain in THIRD_PARTY_HINTS):
                        sev = 'high'
                    add_finding(
                        findings, sev, 'third-party', r, line,
                        'external script found in theme code',
                        'Inventory ownership and business purpose. Defer, gate, or remove only after confirming it is non-critical.',
                        src
                    )

    for match in re.finditer(r'\|\s*script_tag\b', text):
        add_finding(
            findings, 'medium', 'javascript', r, line_number(text, match.start()),
            'Liquid script_tag filter can emit a parser-blocking script for theme assets',
            'Prefer an explicit script tag with defer for non-critical theme assets while preserving order.',
            text[max(0, match.start()-80):match.end()+80]
        )

    for match in re.finditer(r'<img\b([^>]*)>', text, re.IGNORECASE):
        tag = match.group(0)
        attrs_lower = match.group(1).lower()
        line = line_number(text, match.start())
        if 'width=' not in attrs_lower or 'height=' not in attrs_lower:
            add_finding(
                findings, 'medium', 'images/cls', r, line,
                'img tag missing explicit width and/or height',
                'Use Shopify image_tag or add dimensions/aspect-ratio to prevent CLS and lazy-loading edge cases.',
                tag
            )
        if 'loading=' not in attrs_lower:
            add_finding(
                findings, 'low', 'images', r, line,
                'img tag has no loading strategy',
                'Set loading="lazy" for below-the-fold images and eager/high priority for the single likely LCP image.',
                tag
            )
        elif 'loading="lazy"' in attrs_lower or "loading='lazy'" in attrs_lower:
            if likely_above_fold_file(lower_path):
                add_finding(
                    findings, 'high', 'lcp', r, line,
                    'likely above-the-fold image is lazy loaded',
                    'Do not lazy load the first visible hero/product image. Use eager loading and consider one preload/fetchpriority high.',
                    tag
                )

    if re.search(r'\b(lazysizes|lazyload|data-src|data-bgset|data-sizes)\b', text, re.IGNORECASE):
        add_finding(
            findings, 'medium', 'images/javascript', r, None,
            'legacy JavaScript lazy-loading pattern detected',
            'Prefer native loading attributes and Shopify image_url/image_tag responsive output unless legacy support is required.',
            'lazyload/lazysizes/data-src/data-bgset'
        )

    for match in re.finditer(r'image_tag[^\n]*loading:\s*["\']lazy["\']', text, re.IGNORECASE):
        if likely_above_fold_file(lower_path):
            add_finding(
                findings, 'high', 'lcp', r, line_number(text, match.start()),
                'Shopify image_tag in likely above-the-fold section is set to lazy',
                'Conditionally use eager loading for section.index == 1 or the known LCP media.',
                match.group(0)
            )

    for match in re.finditer(r'image_tag', text):
        snippet = text[max(0, match.start()-120):match.start()+220]
        if 'widths:' not in snippet and 'sizes:' not in snippet:
            add_finding(
                findings, 'low', 'images', r, line_number(text, match.start()),
                'image_tag may rely on default sizing without explicit sizes/widths',
                'For important/product/card images, add widths and sizes so mobile receives appropriately sized resources.',
                snippet
            )

    if re.search(r'background-image\s*:', text, re.IGNORECASE):
        add_finding(
            findings, 'low', 'images', r, None,
            'CSS background image detected',
            'For hero/LCP imagery, consider real image markup with image_tag for responsive srcset, priority, alt text, and dimensions.',
            'background-image'
        )

    preload_count = len(re.findall(r'\bpreload\b|rel=["\']preload["\']', text, re.IGNORECASE))
    if preload_count > 3:
        add_finding(
            findings, 'medium', 'network', r, None,
            f'{preload_count} preload hints detected in one file',
            'Use preloads sparingly. Too many preloads can compete with the LCP image and critical CSS.',
            f'preload count: {preload_count}'
        )

    for loop in re.finditer(r'{%\s*for\b.*?{%\s*endfor\s*%}', text, re.DOTALL):
        block = loop.group(0)
        if 'all_products[' in block:
            add_finding(
                findings, 'medium', 'liquid', r, line_number(text, loop.start()),
                'all_products lookup inside a loop can increase render cost and complexity',
                'Move lookups out of loops, limit block counts, or use direct product settings where possible.',
                block[:250]
            )
        if re.search(r'{%\s*render\b', block) and len(block) > 600:
            add_finding(
                findings, 'low', 'liquid', r, line_number(text, loop.start()),
                'large loop renders snippets repeatedly',
                'Check whether the snippet is heavy, whether output is hidden/offscreen, and whether a lighter card or pagination is safer.',
                block[:250]
            )
        if re.search(r'\|\s*(sort|where|map|uniq)\b', block):
            add_finding(
                findings, 'low', 'liquid', r, line_number(text, loop.start()),
                'collection operation inside loop',
                'Move sorting/filtering/mapping outside loops when possible.',
                block[:250]
            )

    for match in re.finditer(r'{%\s*include\b', text):
        add_finding(
            findings, 'low', 'liquid', r, line_number(text, match.start()),
            'legacy include tag detected',
            'Prefer render for snippet isolation and clearer variable passing when touching this code.',
            text[max(0, match.start()-60):match.end()+100]
        )


def scan_js(path: Path, root: Path, text: str, findings: List[Dict[str, Any]]) -> None:
    r = rel(path, root)
    if re.search(r'addEventListener\s*\(\s*["\'](?:scroll|touchmove|wheel)["\']', text):
        if 'passive' not in text:
            add_finding(
                findings, 'medium', 'inp/javascript', r, None,
                'scroll/touch/wheel listener may be non-passive',
                'Use passive listeners when the handler does not call preventDefault, and debounce expensive work.',
                'addEventListener scroll/touch/wheel'
            )
    if re.search(r'\bdocument\.write\s*\(', text):
        add_finding(
            findings, 'high', 'javascript', r, None,
            'document.write detected',
            'Remove or replace document.write because it can block parsing and cause unpredictable loading.',
            'document.write'
        )
    for match in re.finditer(r'setInterval\s*\([^,]+,\s*(\d+)\s*\)', text):
        interval = int(match.group(1))
        if interval < 250:
            add_finding(
                findings, 'medium', 'inp/javascript', r, line_number(text, match.start()),
                f'short setInterval detected ({interval}ms)',
                'Replace polling with events, observers, or a longer/debounced interval.',
                match.group(0)
            )
    if 'jquery' in text.lower() and path.name.lower() not in ('jquery.js', 'jquery.min.js'):
        add_finding(
            findings, 'low', 'javascript', r, None,
            'jQuery usage detected',
            'Check whether jQuery is still required. Avoid loading duplicate libraries or using jQuery for simple native DOM tasks.',
            'jquery'
        )


def scan_css(path: Path, root: Path, text: str, findings: List[Dict[str, Any]]) -> None:
    r = rel(path, root)
    for match in re.finditer(r'@import\s+', text):
        add_finding(
            findings, 'medium', 'css', r, line_number(text, match.start()),
            'CSS @import detected',
            'Avoid @import chains; load required CSS directly or bundle it to reduce render-blocking round trips.',
            text[max(0, match.start()-60):match.start()+160]
        )
    if re.search(r'url\(["\']?https?://', text):
        add_finding(
            findings, 'low', 'css/network', r, None,
            'external URL referenced from CSS',
            'Prefer Shopify-hosted assets or confirm the external host is required and cacheable.',
            'url(http...)'
        )


def analyze_theme(theme_root: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    files = list(iter_files(theme_root))
    asset_summary: Dict[str, Any] = {
        'js_total_bytes': 0,
        'css_total_bytes': 0,
        'image_total_bytes': 0,
        'image_count': 0,
        'js_count': 0,
        'css_count': 0,
        'liquid_count': 0,
        'top_assets': [],
    }

    for path in files:
        path_rel = rel(path, theme_root)
        ext = ''.join(Path(path.name).suffixes[-2:]).lower() if path.name.endswith('.liquid') else path.suffix.lower()
        suffix = path.suffix.lower()
        size = path.stat().st_size
        lower_name = path.name.lower()
        is_liquid_asset = lower_name.endswith(('.js.liquid', '.css.liquid', '.scss.liquid'))

        if suffix in IMAGE_EXTS:
            asset_summary['image_total_bytes'] += size
            asset_summary['image_count'] += 1
            if size > 500_000:
                add_finding(findings, 'medium', 'images', path_rel, None,
                            f'large theme image asset ({human_bytes(size)})',
                            'Compress, replace with Shopify-hosted responsive media, or ensure this asset is not loaded above the fold.', '')
        if suffix in JS_EXTS or lower_name.endswith('.js.liquid'):
            asset_summary['js_total_bytes'] += size
            asset_summary['js_count'] += 1
            if size > 150_000 and '.min.' not in lower_name:
                add_finding(findings, 'medium', 'javascript', path_rel, None,
                            f'large unminified JavaScript asset ({human_bytes(size)})',
                            'Audit usage, split route-specific code, defer loading, and minify with a project-aware build tool.', '')
            elif size > 300_000:
                add_finding(findings, 'medium', 'javascript', path_rel, None,
                            f'very large JavaScript asset ({human_bytes(size)})',
                            'Check parse/execute cost and whether this can be split, deferred, or loaded on interaction.', '')
        if suffix in CSS_EXTS or lower_name.endswith(('.css.liquid', '.scss.liquid')):
            asset_summary['css_total_bytes'] += size
            asset_summary['css_count'] += 1
            if size > 180_000 and '.min.' not in lower_name:
                add_finding(findings, 'medium', 'css', path_rel, None,
                            f'large unminified CSS asset ({human_bytes(size)})',
                            'Audit unused rules, split route-specific CSS, and minify using the theme build pipeline.', '')
        if suffix == '.liquid' or lower_name.endswith('.liquid'):
            asset_summary['liquid_count'] += 1
        if suffix in IMAGE_EXTS or suffix in JS_EXTS or suffix in CSS_EXTS or is_liquid_asset:
            asset_summary['top_assets'].append({'file': path_rel, 'bytes': size, 'size': human_bytes(size)})

        if suffix in TEXT_EXTS or lower_name.endswith(('.js.liquid', '.css.liquid', '.scss.liquid')):
            try:
                text = read_text(path)
            except OSError:
                continue
            if suffix in {'.liquid', '.html'} or lower_name.endswith('.liquid'):
                scan_markup(path, theme_root, text, findings)
            if suffix in JS_EXTS:
                scan_js(path, theme_root, text, findings)
            if suffix in CSS_EXTS or lower_name.endswith(('.css.liquid', '.scss.liquid')):
                scan_css(path, theme_root, text, findings)

    asset_summary['top_assets'].sort(key=lambda item: item['bytes'], reverse=True)
    asset_summary['top_assets'] = asset_summary['top_assets'][:25]

    if asset_summary['js_total_bytes'] > 600_000:
        add_finding(findings, 'high', 'javascript', '(theme assets)', None,
                    f'total JavaScript asset weight is high ({human_bytes(asset_summary["js_total_bytes"])})',
                    'Prioritize removing duplicates, route-splitting, defering, and loading optional features on interaction.', '')
    if asset_summary['css_total_bytes'] > 450_000:
        add_finding(findings, 'medium', 'css', '(theme assets)', None,
                    f'total CSS asset weight is high ({human_bytes(asset_summary["css_total_bytes"])})',
                    'Audit unused CSS and split route or component-specific styles if maintainable.', '')
    if asset_summary['image_total_bytes'] > 3_000_000:
        add_finding(findings, 'medium', 'images', '(theme assets)', None,
                    f'total theme image asset weight is high ({human_bytes(asset_summary["image_total_bytes"])})',
                    'Move merchant images to Shopify CDN media, compress theme images, and avoid preloading non-critical media.', '')

    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    findings.sort(key=lambda f: (severity_order.get(f['severity'], 9), f['file'], f['line'] or 0))

    return {
        'theme_root': str(theme_root),
        'file_count': len(files),
        'asset_summary': asset_summary,
        'finding_count': len(findings),
        'findings': findings,
    }


def as_markdown(report: Dict[str, Any]) -> str:
    summary = report['asset_summary']
    lines = []
    lines.append('# Shopify Theme Performance Audit')
    lines.append('')
    lines.append(f"Theme root: `{report['theme_root']}`")
    lines.append(f"Files scanned: {report['file_count']}")
    lines.append(f"Findings: {report['finding_count']}")
    lines.append('')
    lines.append('## Asset summary')
    lines.append('')
    lines.append('| Type | Count | Total raw size |')
    lines.append('|---|---:|---:|')
    lines.append(f"| JavaScript | {summary['js_count']} | {human_bytes(summary['js_total_bytes'])} |")
    lines.append(f"| CSS | {summary['css_count']} | {human_bytes(summary['css_total_bytes'])} |")
    lines.append(f"| Images | {summary['image_count']} | {human_bytes(summary['image_total_bytes'])} |")
    lines.append(f"| Liquid files | {summary['liquid_count']} | - |")
    lines.append('')
    lines.append('## Findings')
    lines.append('')
    if not report['findings']:
        lines.append('No common static issues were detected. Run Lighthouse/WebPageTest and manual QA for runtime bottlenecks.')
    else:
        lines.append('| Severity | Category | Location | Issue | Recommendation |')
        lines.append('|---|---|---|---|---|')
        for f in report['findings']:
            loc = f['file'] if f['line'] is None else f"{f['file']}:{f['line']}"
            issue = f['issue'].replace('|', '\\|')
            rec = f['recommendation'].replace('|', '\\|')
            lines.append(f"| {f['severity']} | {f['category']} | `{loc}` | {issue} | {rec} |")
    lines.append('')
    lines.append('## Largest assets')
    lines.append('')
    if summary['top_assets']:
        lines.append('| File | Size |')
        lines.append('|---|---:|')
        for item in summary['top_assets'][:15]:
            lines.append(f"| `{item['file']}` | {item['size']} |")
    else:
        lines.append('No theme assets were found.')
    lines.append('')
    lines.append('## Next steps')
    lines.append('')
    lines.append('1. Confirm high-severity findings in context before editing.')
    lines.append('2. Prioritize LCP image loading, parser-blocking scripts, missing dimensions, and duplicate/heavy third-party code.')
    lines.append('3. Preserve conversion-critical UI, apps, analytics, consent, and checkout behavior unless removal is approved.')
    lines.append('4. Measure before/after with Lighthouse or a browser trace when possible.')
    return '\n'.join(lines) + '\n'


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Static Shopify theme performance audit.')
    parser.add_argument('path', nargs='?', help='Theme directory or theme zip. Omit with --help only.')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown')
    parser.add_argument('--out', help='Write report to file instead of stdout')
    args = parser.parse_args(argv)

    if not args.path:
        parser.print_help()
        return 0

    input_path = Path(args.path).expanduser().resolve()
    if not input_path.exists():
        print(f'error: path not found: {input_path}', file=sys.stderr)
        return 2

    tmp = None
    try:
        scan_path = input_path
        if input_path.is_file() and input_path.suffix.lower() == '.zip':
            tmp = safe_extract_zip(input_path)
            scan_path = Path(tmp.name)
        theme_root = detect_theme_root(scan_path)
        report = analyze_theme(theme_root)
        output = json.dumps(report, indent=2) + '\n' if args.format == 'json' else as_markdown(report)
        if args.out:
            Path(args.out).write_text(output, encoding='utf-8')
        else:
            print(output, end='')
    finally:
        if tmp is not None:
            tmp.cleanup()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

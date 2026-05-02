#!/usr/bin/env python3
"""Conservative CSS/JS minification helper for Shopify theme assets.

Default mode is dry-run. The script intentionally skips Liquid assets and files
that contain Liquid delimiters because generic minification can break Liquid.
For production, prefer the theme's real build pipeline when one exists.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

TARGET_EXTS = {'.js', '.mjs', '.css'}
SKIP_PARTS = {'node_modules', '.git', 'dist', 'coverage', '.cache', '.shopify'}


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


def iter_assets(root: Path) -> Iterable[Path]:
    for path in root.rglob('*'):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if not path.is_file():
            continue
        lower = path.name.lower()
        if '.min.' in lower:
            continue
        if lower.endswith(('.js.liquid', '.css.liquid', '.scss.liquid')):
            continue
        if path.suffix.lower() in TARGET_EXTS:
            yield path


def contains_liquid(text: str) -> bool:
    return '{{' in text or '{%' in text or '{#' in text


def minify_css(text: str) -> str:
    text = re.sub(r'/\*![\s\S]*?\*/', lambda m: m.group(0).replace('\n', ' '), text)
    text = re.sub(r'/\*(?![!])[\s\S]*?\*/', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', text)
    text = text.replace(';}', '}')
    return text.strip() + '\n'


def strip_js_comments(text: str) -> str:
    out: List[str] = []
    i = 0
    state = 'code'
    quote = ''
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if state == 'code':
            if ch in ('"', "'", '`'):
                state = 'string'
                quote = ch
                out.append(ch)
                i += 1
            elif ch == '/' and nxt == '/':
                i += 2
                while i < len(text) and text[i] not in '\r\n':
                    i += 1
                out.append('\n')
            elif ch == '/' and nxt == '*':
                preserve = i + 2 < len(text) and text[i + 2] == '!'
                end = text.find('*/', i + 2)
                if end == -1:
                    break
                if preserve:
                    out.append(text[i:end + 2].replace('\n', ' '))
                i = end + 2
            else:
                out.append(ch)
                i += 1
        elif state == 'string':
            out.append(ch)
            if ch == '\\':
                if i + 1 < len(text):
                    out.append(text[i + 1])
                    i += 2
                else:
                    i += 1
            elif ch == quote:
                state = 'code'
                i += 1
            else:
                i += 1
    return ''.join(out)


def minify_js(text: str) -> str:
    text = strip_js_comments(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = '\n'.join(lines)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip() + '\n'


def minify(path: Path, text: str) -> str:
    suffix = path.suffix.lower()
    if suffix == '.css':
        return minify_css(text)
    return minify_js(text)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Conservatively minify pure CSS/JS theme assets. Dry-run by default.')
    parser.add_argument('theme_path', nargs='?', help='Theme directory')
    parser.add_argument('--write', action='store_true', help='Write changes. Default is dry-run.')
    parser.add_argument('--no-backup', action='store_true', help='Do not create .bak backup files when writing')
    parser.add_argument('--min-saving', type=int, default=128, help='Minimum bytes saved to report/write')
    args = parser.parse_args(argv)
    if not args.theme_path:
        parser.print_help()
        return 0
    root = Path(args.theme_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f'error: theme directory not found: {root}', file=sys.stderr)
        return 2

    changed = []
    skipped_liquid = 0
    total_before = 0
    total_after = 0
    for path in iter_assets(root):
        text = path.read_text(encoding='utf-8', errors='ignore')
        if contains_liquid(text):
            skipped_liquid += 1
            continue
        before = len(text.encode('utf-8'))
        output = minify(path, text)
        after = len(output.encode('utf-8'))
        saving = before - after
        if saving < args.min_saving:
            continue
        rel = path.relative_to(root)
        changed.append((path, str(rel), before, after, saving))
        total_before += before
        total_after += after
        if args.write:
            if not args.no_backup:
                backup = path.with_suffix(path.suffix + '.bak')
                if not backup.exists():
                    shutil.copy2(path, backup)
            path.write_text(output, encoding='utf-8')

    mode = 'write' if args.write else 'dry-run'
    print(f'Mode: {mode}')
    print(f'Assets with reportable savings: {len(changed)}')
    print(f'Skipped files containing Liquid delimiters: {skipped_liquid}')
    print(f'Potential savings: {human_bytes(total_before - total_after)}')
    if changed:
        print('')
        print('| File | Before | After | Saved |')
        print('|---|---:|---:|---:|')
        for _, rel, before, after, saving in changed:
            print(f'| `{rel}` | {human_bytes(before)} | {human_bytes(after)} | {human_bytes(saving)} |')
    if not args.write:
        print('')
        print('Dry run only. Re-run with --write to modify files. Prefer the project build pipeline for production minification when available.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

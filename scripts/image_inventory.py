#!/usr/bin/env python3
"""Inventory Shopify theme image assets and report dimensions/sizes.

Supports directories or theme zip files. Does not modify files.
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico', '.avif'}


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
    tmp = tempfile.TemporaryDirectory(prefix='shopify_image_inventory_')
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
    candidates = list(path.rglob('layout/theme.liquid'))
    if candidates:
        candidates.sort(key=lambda p: len(p.parts))
        return candidates[0].parent.parent
    return path


def iter_images(root: Path) -> Iterable[Path]:
    ignored = {'.git', 'node_modules', '.cache', 'dist', 'coverage', '.shopify'}
    for path in root.rglob('*'):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            yield path


def png_size(data: bytes) -> Optional[Tuple[int, int]]:
    if len(data) >= 24 and data.startswith(b'\x89PNG\r\n\x1a\n'):
        return struct.unpack('>II', data[16:24])
    return None


def gif_size(data: bytes) -> Optional[Tuple[int, int]]:
    if len(data) >= 10 and data[:6] in (b'GIF87a', b'GIF89a'):
        return struct.unpack('<HH', data[6:10])
    return None


def jpeg_size(data: bytes) -> Optional[Tuple[int, int]]:
    if not data.startswith(b'\xff\xd8'):
        return None
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xD8, 0xD9):
            continue
        if i + 2 > len(data):
            return None
        length = struct.unpack('>H', data[i:i + 2])[0]
        if length < 2:
            return None
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if i + 7 <= len(data):
                height = struct.unpack('>H', data[i + 3:i + 5])[0]
                width = struct.unpack('>H', data[i + 5:i + 7])[0]
                return width, height
            return None
        i += length
    return None


def webp_size(data: bytes) -> Optional[Tuple[int, int]]:
    if len(data) < 30 or data[:4] != b'RIFF' or data[8:12] != b'WEBP':
        return None
    chunk = data[12:16]
    if chunk == b'VP8X' and len(data) >= 30:
        width = 1 + int.from_bytes(data[24:27], 'little')
        height = 1 + int.from_bytes(data[27:30], 'little')
        return width, height
    if chunk == b'VP8L' and len(data) >= 25:
        b0, b1, b2, b3 = data[21], data[22], data[23], data[24]
        width = 1 + (((b1 & 0x3F) << 8) | b0)
        height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        return width, height
    if chunk == b'VP8 ' and len(data) >= 30 and data[23:26] == b'\x9d\x01\x2a':
        width = struct.unpack('<H', data[26:28])[0] & 0x3FFF
        height = struct.unpack('<H', data[28:30])[0] & 0x3FFF
        return width, height
    return None


def svg_size(text: str) -> Optional[Tuple[int, int]]:
    import re
    width = re.search(r'\bwidth=["\']([0-9.]+)', text)
    height = re.search(r'\bheight=["\']([0-9.]+)', text)
    if width and height:
        return int(float(width.group(1))), int(float(height.group(1)))
    viewbox = re.search(r'\bviewBox=["\']\s*[-0-9.]+\s+[-0-9.]+\s+([0-9.]+)\s+([0-9.]+)\s*["\']', text)
    if viewbox:
        return int(float(viewbox.group(1))), int(float(viewbox.group(2)))
    return None


def get_dimensions(path: Path) -> Optional[Tuple[int, int]]:
    data = path.read_bytes()[:512 * 1024]
    suffix = path.suffix.lower()
    if suffix == '.png':
        return png_size(data)
    if suffix in ('.jpg', '.jpeg'):
        return jpeg_size(data)
    if suffix == '.gif':
        return gif_size(data)
    if suffix == '.webp':
        return webp_size(data)
    if suffix == '.svg':
        return svg_size(data.decode('utf-8', errors='ignore'))
    return None


def analyze(root: Path) -> Dict[str, Any]:
    images = []
    total = 0
    for path in iter_images(root):
        size = path.stat().st_size
        total += size
        dims = None
        try:
            dims = get_dimensions(path)
        except OSError:
            dims = None
        rel = str(path.relative_to(root)).replace(os.sep, '/')
        width, height = (dims if dims else (None, None))
        pixels = width * height if width and height else None
        flags = []
        if size > 500_000:
            flags.append('large-file')
        if width and width > 2400:
            flags.append('very-wide')
        if height and height > 2400:
            flags.append('very-tall')
        if path.suffix.lower() in ('.jpg', '.jpeg', '.png') and size > 250_000:
            flags.append('consider-webp-avif-or-cdn-transform')
        images.append({
            'file': rel,
            'bytes': size,
            'size': human_bytes(size),
            'width': width,
            'height': height,
            'pixels': pixels,
            'flags': flags,
        })
    images.sort(key=lambda item: item['bytes'], reverse=True)
    return {'theme_root': str(root), 'image_count': len(images), 'total_bytes': total, 'total_size': human_bytes(total), 'images': images}


def as_markdown(report: Dict[str, Any], limit: int) -> str:
    lines = ['# Shopify Theme Image Inventory', '']
    lines.append(f"Theme root: `{report['theme_root']}`")
    lines.append(f"Images: {report['image_count']}")
    lines.append(f"Total raw image asset size: {report['total_size']}")
    lines.append('')
    lines.append('| File | Size | Dimensions | Flags |')
    lines.append('|---|---:|---:|---|')
    for item in report['images'][:limit]:
        dims = '-' if not item['width'] else f"{item['width']}x{item['height']}"
        flags = ', '.join(item['flags']) if item['flags'] else ''
        lines.append(f"| `{item['file']}` | {item['size']} | {dims} | {flags} |")
    lines.append('')
    lines.append('Notes: Theme asset images are not the same as Shopify product/media CDN derivatives. Use this to find oversized theme-bundled files and confirm how they are loaded in Liquid.')
    return '\n'.join(lines) + '\n'


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Inventory Shopify theme image assets.')
    parser.add_argument('path', nargs='?', help='Theme directory or theme zip')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown')
    parser.add_argument('--limit', type=int, default=30, help='Rows to show in markdown output')
    parser.add_argument('--out', help='Write report to file')
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
        root = detect_theme_root(scan_path)
        report = analyze(root)
        output = json.dumps(report, indent=2) + '\n' if args.format == 'json' else as_markdown(report, args.limit)
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

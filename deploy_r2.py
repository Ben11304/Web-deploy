#!/usr/bin/env python3
"""
Prepare and upload GeoJSON data to Cloudflare R2.

Steps:
  1. Gzip compress all GeoJSON/JSON files
  2. Upload to R2 bucket using wrangler CLI

Prerequisites:
  npm install -g wrangler
  wrangler login

Usage:
  python deploy_r2.py --prepare              # Step 1: gzip files → .r2_upload/
  python deploy_r2.py --upload BUCKET_NAME   # Step 2: upload to R2
  python deploy_r2.py --all BUCKET_NAME      # Both steps
"""

import argparse
import gzip
import os
import shutil
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).parent
GEOJSON_DIR = PROJECT_ROOT / 'app' / 'static' / 'geojson'
UPLOAD_DIR = PROJECT_ROOT / '.r2_upload'

# Directories to upload (excludes raw earthquake — use simplified version)
UPLOAD_DIRS = [
    'Exposure/earthquake_simplified',
    'Exposure/flood',
    'Exposure/wildfire',
    'states',
    'Hazard',
    'heatmap_flood_lite',
    'heatmap_wildfire_lite',
    'simple_hazard_2025_lite',
    'counties_by_state_energy',
    'drought',
    # Small files already bundled in docs/ but also upload for CDN:
    'impact',
    'social_vulnerability',
]

UPLOAD_FILES = [
    'us-states.geojson',
    'us-counties.geojson',
]


def gzip_file(src: Path, dst: Path):
    """Gzip compress a single file."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, 'rb') as f_in:
        with gzip.open(dst, 'wb', compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)
    return src.stat().st_size, dst.stat().st_size


def prepare_upload():
    """Gzip compress all data files into .r2_upload/."""
    print('Preparing data for upload...')
    print(f'Source: {GEOJSON_DIR}')
    print(f'Output: {UPLOAD_DIR}')

    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir()

    # Collect all files to process
    tasks = []

    for dir_name in UPLOAD_DIRS:
        src_dir = GEOJSON_DIR / dir_name
        if not src_dir.exists():
            print(f'  SKIP {dir_name} (not found)')
            continue
        for f in src_dir.rglob('*'):
            if f.is_file() and f.suffix in ('.geojson', '.json', '.csv'):
                rel = f.relative_to(GEOJSON_DIR)
                dst = UPLOAD_DIR / rel
                tasks.append((f, dst))

    for file_name in UPLOAD_FILES:
        src = GEOJSON_DIR / file_name
        if src.exists():
            dst = UPLOAD_DIR / file_name
            tasks.append((src, dst))

    print(f'  Found {len(tasks)} files to compress')

    total_original = 0
    total_compressed = 0
    completed = 0

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(gzip_file, src, dst): (src, dst) for src, dst in tasks}
        for future in as_completed(futures):
            src, dst = futures[future]
            try:
                orig_size, comp_size = future.result()
                total_original += orig_size
                total_compressed += comp_size
                completed += 1
                if completed % 100 == 0 or completed == len(tasks):
                    print(f'  [{completed}/{len(tasks)}] '
                          f'{total_original/1024/1024:.0f} MB → {total_compressed/1024/1024:.0f} MB '
                          f'({100-total_compressed*100/total_original:.0f}% reduction)')
            except Exception as e:
                print(f'  ERROR: {src}: {e}')

    print(f'\nCompression complete!')
    print(f'  Original:   {total_original/1024/1024/1024:.2f} GB')
    print(f'  Compressed: {total_compressed/1024/1024/1024:.2f} GB')
    print(f'  Reduction:  {100-total_compressed*100/total_original:.0f}%')
    print(f'  Files:      {completed}')

    # Write metadata for upload
    meta = {
        'files': completed,
        'original_gb': round(total_original / 1024 / 1024 / 1024, 2),
        'compressed_gb': round(total_compressed / 1024 / 1024 / 1024, 2),
    }
    import json
    (UPLOAD_DIR / '_meta.json').write_text(json.dumps(meta, indent=2))
    print(f'\nReady to upload. Run:')
    print(f'  python deploy_r2.py --upload YOUR_BUCKET_NAME')


def upload_to_r2(bucket_name: str):
    """Upload compressed files to Cloudflare R2 using wrangler."""

    # Check wrangler is installed
    try:
        subprocess.run(['wrangler', '--version'], capture_output=True, check=True)
    except FileNotFoundError:
        print('ERROR: wrangler CLI not found.')
        print('Install: npm install -g wrangler')
        print('Login:   wrangler login')
        sys.exit(1)

    if not UPLOAD_DIR.exists():
        print('ERROR: No prepared data. Run: python deploy_r2.py --prepare')
        sys.exit(1)

    files = list(UPLOAD_DIR.rglob('*'))
    files = [f for f in files if f.is_file() and f.name != '_meta.json']
    print(f'Uploading {len(files)} files to R2 bucket: {bucket_name}')

    errors = []
    for i, f in enumerate(files):
        rel_path = f.relative_to(UPLOAD_DIR)
        key = str(rel_path)

        # Determine content type
        if key.endswith('.geojson'):
            content_type = 'application/geo+json'
        elif key.endswith('.json'):
            content_type = 'application/json'
        elif key.endswith('.csv'):
            content_type = 'text/csv'
        else:
            content_type = 'application/octet-stream'

        cmd = [
            'wrangler', 'r2', 'object', 'put',
            f'{bucket_name}/{key}',
            '--file', str(f),
            '--content-type', content_type,
            '--content-encoding', 'gzip',
            '--remote',
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=120)
            if (i + 1) % 50 == 0 or (i + 1) == len(files):
                print(f'  [{i+1}/{len(files)}] uploaded')
        except subprocess.CalledProcessError as e:
            errors.append((key, e.stderr.decode() if e.stderr else str(e)))
            print(f'  ERROR: {key}')
        except subprocess.TimeoutExpired:
            errors.append((key, 'timeout'))
            print(f'  TIMEOUT: {key}')

    print(f'\nUpload complete: {len(files) - len(errors)}/{len(files)} files')
    if errors:
        print(f'Errors ({len(errors)}):')
        for key, err in errors[:10]:
            print(f'  {key}: {err[:100]}')

    print(f'\nNext steps:')
    print(f'1. Enable public access on your R2 bucket (Settings → Public access)')
    print(f'2. Note your public URL: https://<your-custom-domain> or https://pub-xxx.r2.dev')
    print(f'3. Update docs/static/js/site-config.js:')
    print(f'   window.DATA_BASE_URL = "https://YOUR_R2_PUBLIC_URL";')
    print(f'4. Rebuild: python build_static.py')
    print(f'5. Push to GitHub → auto-deploy via GitHub Pages')


def main():
    parser = argparse.ArgumentParser(description='Deploy data to Cloudflare R2')
    parser.add_argument('--prepare', action='store_true', help='Gzip compress files')
    parser.add_argument('--upload', metavar='BUCKET', help='Upload to R2 bucket')
    parser.add_argument('--all', metavar='BUCKET', help='Prepare + upload')
    args = parser.parse_args()

    if args.all:
        prepare_upload()
        upload_to_r2(args.all)
    elif args.prepare:
        prepare_upload()
    elif args.upload:
        upload_to_r2(args.upload)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

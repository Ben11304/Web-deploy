#!/usr/bin/env python3
"""
Parallel upload to Cloudflare R2 using S3 API (boto3).
Much faster than wrangler: uploads 8 files concurrently.

Prerequisites:
    pip install boto3

Setup:
    1. Go to Cloudflare Dashboard → R2 → Manage R2 API Tokens → Create API token
    2. Select "Object Read & Write" permission, apply to bucket "energy-risk-data"
    3. Save the Access Key ID and Secret Access Key
    4. Run this script — it will prompt for credentials

Usage:
    python deploy_r2_parallel.py                    # Upload all files
    python deploy_r2_parallel.py --workers 16       # More parallel workers
    python deploy_r2_parallel.py --dry-run          # Preview without uploading
"""

import argparse
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).parent
UPLOAD_DIR = PROJECT_ROOT / '.r2_upload'

# R2 config
BUCKET_NAME = 'energy-risk-data'

# Content type mapping
CONTENT_TYPES = {
    '.geojson': 'application/geo+json',
    '.json': 'application/json',
    '.csv': 'text/csv',
}


def get_s3_client(account_id, access_key, secret_key):
    """Create S3 client for Cloudflare R2."""
    import boto3
    return boto3.client(
        's3',
        endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto',
    )


def list_existing_keys(client):
    """List all existing object keys in the bucket."""
    print('Checking existing files in bucket...')
    existing = set()
    continuation_token = None

    while True:
        kwargs = {'Bucket': BUCKET_NAME, 'MaxKeys': 1000}
        if continuation_token:
            kwargs['ContinuationToken'] = continuation_token

        response = client.list_objects_v2(**kwargs)
        for obj in response.get('Contents', []):
            existing.add(obj['Key'])

        if response.get('IsTruncated'):
            continuation_token = response['NextContinuationToken']
        else:
            break

    return existing


def upload_file(client, local_path, key):
    """Upload a single gzipped file to R2."""
    suffix = Path(key).suffix
    content_type = CONTENT_TYPES.get(suffix, 'application/octet-stream')

    with open(local_path, 'rb') as f:
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=f,
            ContentType=content_type,
            ContentEncoding='gzip',
        )

    return local_path.stat().st_size


def main():
    parser = argparse.ArgumentParser(description='Parallel upload to Cloudflare R2')
    parser.add_argument('--workers', type=int, default=8, help='Parallel workers (default: 8)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without uploading')
    args = parser.parse_args()

    # Check prerequisites
    try:
        import boto3  # noqa: F401
    except ImportError:
        print('ERROR: boto3 not installed. Run: pip install boto3')
        sys.exit(1)

    if not UPLOAD_DIR.exists():
        print('ERROR: No prepared data. Run: python deploy_r2.py --prepare')
        sys.exit(1)

    # Collect files to upload
    all_files = []
    for f in UPLOAD_DIR.rglob('*'):
        if f.is_file() and f.name != '_meta.json':
            key = str(f.relative_to(UPLOAD_DIR))
            all_files.append((f, key))

    all_files.sort(key=lambda x: x[1])
    print(f'Found {len(all_files)} files to upload')

    if args.dry_run:
        total_size = sum(f.stat().st_size for f, _ in all_files)
        print(f'Total size: {total_size / 1024 / 1024:.0f} MB (compressed)')
        print('Dry run — no files uploaded')
        return

    # Get credentials
    account_id = os.environ.get('CF_ACCOUNT_ID') or input('Cloudflare Account ID: ').strip()
    access_key = os.environ.get('CF_R2_ACCESS_KEY') or input('R2 Access Key ID: ').strip()
    secret_key = os.environ.get('CF_R2_SECRET_KEY') or input('R2 Secret Access Key: ').strip()

    if not all([account_id, access_key, secret_key]):
        print('ERROR: All three credentials are required.')
        print('Find them at: Cloudflare Dashboard → R2 → Manage R2 API Tokens')
        sys.exit(1)

    client = get_s3_client(account_id, access_key, secret_key)

    # Check which files already exist (skip them)
    existing_keys = list_existing_keys(client)
    print(f'Already uploaded: {len(existing_keys)} files')

    to_upload = [(f, k) for f, k in all_files if k not in existing_keys]
    skipped = len(all_files) - len(to_upload)
    if skipped > 0:
        print(f'Skipping {skipped} already-uploaded files')

    if len(to_upload) == 0:
        print('All files already uploaded!')
        return

    print(f'Uploading {len(to_upload)} files with {args.workers} workers...')
    print()

    # Upload in parallel
    uploaded = 0
    errors = []
    total_bytes = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for local_path, key in to_upload:
            future = pool.submit(upload_file, client, local_path, key)
            futures[future] = key

        for future in as_completed(futures):
            key = futures[future]
            try:
                size = future.result()
                uploaded += 1
                total_bytes += size

                if uploaded % 50 == 0 or uploaded == len(to_upload):
                    elapsed = time.time() - start_time
                    rate = total_bytes / 1024 / 1024 / elapsed if elapsed > 0 else 0
                    eta = (len(to_upload) - uploaded) / (uploaded / elapsed) if uploaded > 0 else 0
                    print(f'  [{uploaded}/{len(to_upload)}] '
                          f'{total_bytes/1024/1024:.0f} MB uploaded, '
                          f'{rate:.1f} MB/s, '
                          f'ETA: {eta/60:.0f}m')
            except Exception as e:
                errors.append((key, str(e)))
                uploaded += 1
                if len(errors) <= 5:
                    print(f'  ERROR: {key}: {e}')

    elapsed = time.time() - start_time
    print(f'\nDone in {elapsed/60:.1f} minutes')
    print(f'  Uploaded: {uploaded - len(errors)}/{len(to_upload)}')
    print(f'  Errors: {len(errors)}')
    print(f'  Total: {total_bytes/1024/1024:.0f} MB')

    if errors:
        print(f'\nFailed files ({len(errors)}):')
        for key, err in errors[:20]:
            print(f'  {key}: {err}')
    else:
        print(f'\nAll files uploaded successfully!')
        print(f'Test: curl -I https://pub-2d678d396f414cb681a74d123b7e90b4.r2.dev/us-states.geojson')


if __name__ == '__main__':
    main()

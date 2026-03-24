#!/usr/bin/env python3
"""
Download all external images referenced in HTML files and rewrite paths to local.
Handles: cdn.sanity.io, image.mux.com, and www.rugiet.com/assets URLs.
"""

import os
import re
import hashlib
import urllib.request
import urllib.parse
import ssl
import html
from pathlib import Path
from collections import defaultdict

WEBROOT = Path("/Users/donnysmith/Desktop/rugiet-com/www.rugiet.com")
IMAGES_DIR = WEBROOT / "images"

# SSL context that doesn't verify (for downloading)
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def find_html_files():
    """Find all .html files recursively."""
    return list(WEBROOT.rglob("*.html"))


def extract_sanity_urls(content):
    """Extract all Sanity CDN URLs from HTML content."""
    # Match sanity URLs in various contexts (src, srcset, og:image, etc.)
    pattern = r'https://cdn\.sanity\.io/images/[^"\'>\s\)\\]+'
    urls = re.findall(pattern, content)
    # Also catch URLs with HTML-encoded ampersands
    pattern2 = r'https://cdn\.sanity\.io/images/[^"\'>\s\)]+'
    urls2 = re.findall(pattern2, content)
    return list(set(urls + urls2))


def extract_mux_urls(content):
    """Extract Mux thumbnail URLs."""
    pattern = r'https://image\.mux\.com/[^"\'>\s\)]+'
    return list(set(re.findall(pattern, content)))


def extract_rugiet_asset_urls(content):
    """Extract rugiet.com asset URLs."""
    pattern = r'https://www\.rugiet\.com/assets/[^"\'>\s\)]+'
    return list(set(re.findall(pattern, content)))


def parse_sanity_image_id(url):
    """
    Extract the unique image hash and extension from a Sanity URL.
    URL format: https://cdn.sanity.io/images/{projectId}/production/{hash}-{dims}.{ext}?params
    Returns (hash_with_dims, ext) e.g. ('04d1cd1048ee00f4cb502d1474ebc2a970574a68-2800x1400', 'png')
    """
    # Clean up the URL - remove trailing backslashes, HTML entities
    clean = url.split("?")[0]  # Remove query params
    clean = clean.rstrip("\\")
    # Extract the part after /production/
    match = re.search(r'/production/([^?]+)', clean)
    if match:
        filename = match.group(1)
        # filename like: hash-WxH.ext
        return filename
    return None


def get_sanity_base_url(url):
    """Get the base URL (without query params) for downloading at highest quality."""
    # Remove HTML entities, unicode escapes, trailing backslashes
    clean = url.rstrip("\\")
    # Split off query params
    base = clean.split("?")[0]
    base = base.rstrip("\\")
    return base


def get_mux_filename(url):
    """Generate a filename for a Mux thumbnail URL."""
    # Extract the video ID
    match = re.search(r'image\.mux\.com/([^/]+)/thumbnail', url)
    if match:
        video_id = match.group(1)
        return f"mux-{video_id}.webp"
    return None


def get_rugiet_asset_filename(url):
    """Generate a filename for a rugiet.com asset URL."""
    clean = url.split("?")[0]
    # Get the path after /assets/
    match = re.search(r'/assets/(.+)$', clean)
    if match:
        path = match.group(1).replace("/", "-")
        return f"asset-{path}"
    return None


def download_file(url, dest_path):
    """Download a file from URL to dest_path."""
    if dest_path.exists():
        print(f"  SKIP (exists): {dest_path.name}")
        return True

    # Clean URL for actual download
    clean_url = url.replace("&amp;", "&")
    # Remove unicode escapes
    clean_url = clean_url.replace("\\u0026", "&")
    clean_url = clean_url.rstrip("\\")

    try:
        req = urllib.request.Request(clean_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            data = resp.read()
            dest_path.write_bytes(data)
            size_kb = len(data) / 1024
            print(f"  OK ({size_kb:.0f}KB): {dest_path.name}")
            return True
    except Exception as e:
        print(f"  FAIL: {clean_url[:80]}... -> {e}")
        return False


def main():
    IMAGES_DIR.mkdir(exist_ok=True)

    # Phase 1: Scan all HTML files for URLs
    html_files = find_html_files()
    print(f"Found {len(html_files)} HTML files")

    # Collect ALL unique URLs and map them to their local filenames
    # Key: exact URL string as found in HTML -> local relative path
    url_to_local = {}

    # Track unique Sanity images (by base filename, without query params)
    sanity_base_to_filename = {}  # base_url -> local_filename

    all_sanity_urls = set()
    all_mux_urls = set()
    all_rugiet_urls = set()

    for hf in html_files:
        content = hf.read_text(errors="replace")
        all_sanity_urls.update(extract_sanity_urls(content))
        all_mux_urls.update(extract_mux_urls(content))
        all_rugiet_urls.update(extract_rugiet_asset_urls(content))

    print(f"\nFound {len(all_sanity_urls)} unique Sanity URL variants")
    print(f"Found {len(all_mux_urls)} unique Mux URLs")
    print(f"Found {len(all_rugiet_urls)} unique Rugiet asset URLs")

    # Phase 2: Determine unique images and download

    # For Sanity: group by base image (hash-dims.ext), download once at full quality
    sanity_images = {}  # filename -> base_download_url
    for url in all_sanity_urls:
        filename = parse_sanity_image_id(url)
        if filename and filename not in sanity_images:
            base = get_sanity_base_url(url)
            sanity_images[filename] = base

    print(f"\n{len(sanity_images)} unique Sanity images to download")
    print("Downloading Sanity images...")

    downloaded = 0
    failed = 0
    for filename, base_url in sorted(sanity_images.items()):
        dest = IMAGES_DIR / filename
        if download_file(base_url, dest):
            downloaded += 1
        else:
            failed += 1

    print(f"Sanity: {downloaded} downloaded, {failed} failed")

    # Download Mux thumbnails
    print("\nDownloading Mux thumbnails...")
    mux_map = {}  # original_url -> local_filename
    for url in all_mux_urls:
        fname = get_mux_filename(url)
        if fname:
            clean_url = url.replace("&amp;", "&")
            dest = IMAGES_DIR / fname
            download_file(clean_url, dest)
            mux_map[url] = fname

    # Download Rugiet assets
    print("\nDownloading Rugiet assets...")
    rugiet_map = {}  # original_url -> local_filename
    for url in all_rugiet_urls:
        fname = get_rugiet_asset_filename(url)
        if fname:
            dest = IMAGES_DIR / fname
            download_file(url, dest)
            rugiet_map[url] = fname

    # Phase 3: Build replacement map and rewrite HTML files
    print("\nRewriting HTML files...")

    # Build a mapping of all Sanity URL variants -> local path
    # We need to map each exact URL string found in HTML to the correct local image

    files_modified = 0
    total_replacements = 0

    for hf in html_files:
        content = hf.read_text(errors="replace")
        original = content

        # Replace Sanity URLs
        # Strategy: find all sanity URLs in this file and replace each one
        # We replace the full URL (including query params) with just the local path

        def replace_sanity_url(match):
            url = match.group(0)
            filename = parse_sanity_image_id(url)
            if filename:
                # Compute relative path from this HTML file to /images/
                rel = os.path.relpath(IMAGES_DIR / filename, hf.parent)
                return rel
            return url

        # Match sanity URLs - greedy enough to catch query params but stop at quotes/whitespace
        content = re.sub(
            r'https://cdn\.sanity\.io/images/[^"\'>\s\)]+',
            replace_sanity_url,
            content
        )

        # Replace Mux URLs
        for orig_url, fname in mux_map.items():
            if orig_url in content:
                rel = os.path.relpath(IMAGES_DIR / fname, hf.parent)
                content = content.replace(orig_url, rel)

        # Replace Rugiet asset URLs
        for orig_url, fname in rugiet_map.items():
            if orig_url in content:
                rel = os.path.relpath(IMAGES_DIR / fname, hf.parent)
                content = content.replace(orig_url, rel)

        if content != original:
            hf.write_text(content)
            # Count replacements
            count = original.count("cdn.sanity.io") - content.count("cdn.sanity.io")
            count += original.count("image.mux.com") - content.count("image.mux.com")
            count += original.count("www.rugiet.com/assets") - content.count("www.rugiet.com/assets")
            files_modified += 1
            total_replacements += count
            print(f"  Modified: {hf.relative_to(WEBROOT)}")

    print(f"\nDone! {files_modified} files modified, ~{total_replacements} URL references replaced")

    # Verify no remaining external image references
    remaining_sanity = 0
    remaining_mux = 0
    for hf in html_files:
        content = hf.read_text(errors="replace")
        remaining_sanity += content.count("cdn.sanity.io")
        remaining_mux += content.count("image.mux.com")

    print(f"\nRemaining cdn.sanity.io references: {remaining_sanity}")
    print(f"Remaining image.mux.com references: {remaining_mux}")


if __name__ == "__main__":
    os.chdir(WEBROOT)
    main()

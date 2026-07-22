#!/usr/bin/env python3
"""Debug TikTok page content."""

from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_tiktok_headers

TEST_TIKTOK_URL = "https://www.tiktok.com/@tiktok/video/7259788325009096966"


def main():
    client = SolenzClient()
    headers = get_tiktok_headers(referer=TEST_TIKTOK_URL)
    
    print("Fetching page...")
    resp = client.get(TEST_TIKTOK_URL, headers=headers, allow_redirects=True)
    print(f"Status code: {resp.status_code}")
    print(f"Final URL: {resp.url}")
    
    html = resp.text
    
    print("\nChecking for patterns:")
    patterns = [
        "SIGI_STATE",
        "__UNIVERSAL_DATA_FOR_REHYDRATION__",
        "window.__data",
    ]
    for p in patterns:
        if p in html:
            print(f"  [+] Found: {p}")
        else:
            print(f"  [-] Not found: {p}")
    
    # Save HTML to file for inspection
    with open("tiktok_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\nSaved HTML to tiktok_debug.html")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Debug TikTok JSON data."""

import json
import re
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_tiktok_headers

TEST_TIKTOK_URL = "https://www.tiktok.com/@tiktok/video/7259788325009096966"


def main():
    client = SolenzClient()
    headers = get_tiktok_headers(referer=TEST_TIKTOK_URL)
    
    print("Fetching page...")
    resp = client.get(TEST_TIKTOK_URL, headers=headers, allow_redirects=True)
    html = resp.text
    
    # Find __UNIVERSAL_DATA_FOR_REHYDRATION__
    pattern = r'<script\s+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>({.*?})</script>'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            data = json.loads(json_str)
            print("\nFound __UNIVERSAL_DATA_FOR_REHYDRATION__!")
            print("Keys in data:", list(data.keys()))
            
            if "__DEFAULT_SCOPE__" in data:
                print("\nKeys in __DEFAULT_SCOPE__:", list(data["__DEFAULT_SCOPE__"].keys()))
                
                # Let's print the full structure
                print("\nFull data (pretty-printed):")
                print(json.dumps(data, indent=2))
                
                # Save to file
                with open("tiktok_data.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("\nSaved to tiktok_data.json")
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print("JSON string preview:", json_str[:500])
    else:
        print("Couldn't find __UNIVERSAL_DATA_FOR_REHYDRATION__")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test Instagram extractor"""

import solenz_downloader

# Test with a sample Instagram URL
TEST_INSTAGRAM_URL = "https://www.instagram.com/p/CZs4nXqM1jY/"


def test_instagram_extract():
    print(f"[*] Testing Instagram extractor with: {TEST_INSTAGRAM_URL}")
    try:
        result = solenz_downloader.extract(TEST_INSTAGRAM_URL)
        print(f"[+] Success!")
        print(f"    Title: {result.title}")
        print(f"    Platform: {result.platform}")
        print(f"    Uploader: {result.uploader}")
        print(f"    Duration: {result.duration} seconds")
        print(f"    Streams found: {len(result.streams)}")
        for i, stream in enumerate(result.streams):
            print(f"      Stream {i+1}: {stream}")
        return result
    except Exception as e:
        print(f"[-] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_instagram_extract()

#!/usr/bin/env python3
"""Test TikTok extractor and downloader."""

import solenz_downloader

# Test with a sample TikTok URL
TEST_TIKTOK_URL = "https://vm.tiktok.com/ZM8XvQpY/"


def test_tiktok_extract():
    print(f"[*] Testing TikTok extractor with: {TEST_TIKTOK_URL}")
    try:
        result = solenz_downloader.extract(TEST_TIKTOK_URL)
        print(f"[+] Success!")
        print(f"    Title: {result.title}")
        print(f"    Platform: {result.platform}")
        print(f"    Uploader: {result.uploader}")
        print(f"    Duration: {result.duration} seconds")
        print(f"    Streams found: {len(result.streams)}")
        for i, stream in enumerate(result.streams):
            print(f"      Stream {i+1}: {stream.resolution} .{stream.ext} (has_audio={stream.has_audio}, has_video={stream.has_video})")
        return result
    except Exception as e:
        print(f"[-] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_tiktok_extract()

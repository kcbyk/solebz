#!/usr/bin/env python3
"""Test solenz_downloader library - covers all main functions"""

import solenz_downloader
import os
import sys

# Fix Windows encoding issues
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

TEST_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
TEST_MUSIC_URL = "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
OUTPUT_DIR = "./test_downloads"


def test_extract():
    """Test extract function"""
    print("\n" + "="*50)
    print("  TEST: extract()")
    print("="*50)
    try:
        result = solenz_downloader.extract(TEST_VIDEO_URL)
        print(f"[OK] Baslik: {result.title}")
        print(f"[OK] Platform: {result.platform}")
        print(f"[OK] Sure: {result.duration} saniye")
        print(f"[OK] Yukleyen: {result.uploader}")
        print(f"[OK] Akis sayisi: {len(result.streams)}")
        return result
    except Exception as e:
        print(f"[HATA] {type(e).__name__}: {e}")
        return None


def test_download():
    """Test download function (video)"""
    print("\n" + "="*50)
    print("  TEST: download()")
    print("="*50)
    try:
        path = solenz_downloader.download(
            TEST_VIDEO_URL,
            output_dir=OUTPUT_DIR,
            quality="720p"
        )
        print(f"[OK] Video indirildi: {path}")
        print(f"[OK] Dosya boyutu: {os.path.getsize(path) / 1024 / 1024:.2f} MB")
        return path
    except Exception as e:
        print(f"[HATA] {type(e).__name__}: {e}")
        return None


def test_download_audio():
    """Test download_audio function"""
    print("\n" + "="*50)
    print("  TEST: download_audio()")
    print("="*50)
    try:
        path = solenz_downloader.download_audio(
            TEST_MUSIC_URL,
            output_dir=OUTPUT_DIR,
            prefer_ext="webm"
        )
        print(f"[OK] Ses indirildi: {path}")
        print(f"[OK] Dosya boyutu: {os.path.getsize(path) / 1024 / 1024:.2f} MB")
        return path
    except Exception as e:
        print(f"[HATA] {type(e).__name__}: {e}")
        return None


def test_supported_platforms():
    """Test supported_platforms function"""
    print("\n" + "="*50)
    print("  TEST: supported_platforms()")
    print("="*50)
    platforms = solenz_downloader.supported_platforms()
    print(f"[OK] Desteklenen platformlar: {', '.join(platforms)}")
    return platforms


if __name__ == "__main__":
    print("Solenz Downloader Kutuphane Testi")
    print("="*50)

    # Test all functions
    test_supported_platforms()
    extract_result = test_extract()
    test_download_audio()
    test_download()

    print("\n" + "="*50)
    print("  TUM TESTLER TAMAMLANDI!")
    print("="*50)

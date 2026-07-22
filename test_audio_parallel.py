#!/usr/bin/env python3
"""Test parallel audio download"""

import solenz_downloader
import os
import time
import sys
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("solenz")

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TEST_URL = "https://youtu.be/4-6En3bf5TY?si=QDh0lo2UXwusOAcn"
OUTPUT_DIR = "./test_downloads"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "test_audio_parallel.webm")

# Remove old file to ensure parallel download runs
if os.path.exists(OUTPUT_FILE):
    print(f"Eski dosya siliniyor: {OUTPUT_FILE}")
    os.remove(OUTPUT_FILE)

print("Solenz Downloader Paralel Ses Indirme Testi")
print("="*50)

start_time = time.time()
try:
    path = solenz_downloader.download_audio(
        TEST_URL,
        output_dir=OUTPUT_DIR,
        filename="test_audio_parallel.webm"
    )
    end_time = time.time()
    elapsed = end_time - start_time
    file_size = os.path.getsize(path)
    speed_kb_s = (file_size / 1024) / elapsed

    print("\n" + "="*50)
    print(f"[BAŞARILI] Paralel Ses Indirme Tamamlandi!")
    print(f"[SÜRE] {elapsed:.2f} saniye")
    print(f"[DOSYA BOYUTU] {file_size / 1024 / 1024:.2f} MB")
    print(f"[ORTHALAMA HIZ] {speed_kb_s:.2f} KB/s")
    print(f"[DOSYA YOLU] {path}")
    print("="*50)

except Exception as e:
    print(f"[HATA] {type(e).__name__}: {e}")

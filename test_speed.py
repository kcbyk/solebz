#!/usr/bin/env python3
"""Download speed test."""

import time
import logging
import solenz_downloader

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

print("=" * 60)
print("SOLENZ DOWNLOADER - HIZ TESTİ")
print("=" * 60)

# Test video (Rick Astley)
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
output_dir = "test_downloads"

print(f"\nVideo URL: {url}")
print(f"Çıktı klasörü: {output_dir}")

# Extract info
print("\nVideo bilgileri alınıyor...")
start_extract = time.time()
media = solenz_downloader.extract(url)
extract_time = time.time() - start_extract

print(f"Başlık: {media.title}")
print(f"Yükleyici: {media.uploader}")
print(f"Süre: {media.duration} saniye")
print(f"Akış sayısı: {len(media.streams)}")
print(f"Bilgi alma süresi: {extract_time:.2f} saniye")

# Debug: Best stream
best_stream = media.best_stream()
print("\n--- EN İYİ AKIŞ BİLGİLERİ ---")
print(f"URL: {best_stream.url[:100]}...")
print(f"Kalite: {best_stream.quality}")
print(f"Çözünürlük: {best_stream.width}x{best_stream.height}")
print(f"Boyut: {best_stream.filesize} byte")
print(f"Codec: {best_stream.codec}")
print(f"Has video: {best_stream.has_video}")
print(f"Has audio: {best_stream.has_audio}")
print("------------------------------")

# Download
print("\nİndirme başlıyor...")
start_download = time.time()

downloaded_path = solenz_downloader.download(
    url,
    output_dir=output_dir,
)

download_time = time.time() - start_download

# Get file size
import os
file_size = os.path.getsize(downloaded_path)
size_mb = file_size / (1024 * 1024)
speed_mb_s = size_mb / download_time

print("=" * 60)
print("TEST SONUÇLARI")
print("=" * 60)
print(f"Dosya yolu: {downloaded_path}")
print(f"Dosya boyutu: {size_mb:.2f} MB")
print(f"İndirme süresi: {download_time:.2f} saniye")
print(f"Ortalama hız: {speed_mb_s:.2f} MB/s")
print("=" * 60)

#!/usr/bin/env python3
"""Debug audio download"""

from solenz_downloader.core.client import SolenzClient
from solenz_downloader.core.downloader import SolenzDownloader
from solenz_downloader.extractors import registry
import solenz_downloader
import os

TEST_URL = "https://youtu.be/4-6En3bf5TY?si=QDh0lo2UXwusOAcn"
OUTPUT_DIR = "./test_downloads"

print("Debug Audio Download")
print("="*50)

with SolenzClient() as client:
    media = registry.extract(TEST_URL, client)
    audio_stream = media.best_audio()
    
    print(f"Stream filesize: {audio_stream.filesize}")
    
    downloader = SolenzDownloader(client)
    
    print(f"downloader.max_concurrent: {downloader.max_concurrent}")
    print(f"downloader.chunk_size: {downloader.chunk_size}")
    
    # Manually check download_stream conditions
    total_size = audio_stream.filesize or downloader._get_content_length(audio_stream.url, media.url)
    print(f"total_size: {total_size}")
    
    from solenz_downloader.config import MIN_SEGMENT_SIZE
    print(f"MIN_SEGMENT_SIZE: {MIN_SEGMENT_SIZE}")
    
    supports_range = downloader._supports_range(audio_stream.url, media.url)
    print(f"supports_range: {supports_range}")
    
    print(f"Condition check: total_size={total_size} > MIN_SEGMENT_SIZE={MIN_SEGMENT_SIZE} → {total_size > MIN_SEGMENT_SIZE}")
    print(f"Condition check: max_concurrent > 1 → {downloader.max_concurrent > 1}")
    print(f"Condition check: supports_range → {supports_range}")
    print(f"All conditions met: {total_size and total_size > MIN_SEGMENT_SIZE and downloader.max_concurrent > 1 and supports_range}")
    
    print("\nStarting download...")
    path = downloader.download_stream(
        audio_stream,
        output_dir=OUTPUT_DIR,
        filename="debug_audio.webm",
        referer=media.url
    )
    print(f"\nDownloaded to: {path}")

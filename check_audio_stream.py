#!/usr/bin/env python3
"""Check audio stream details"""

import solenz_downloader
import sys

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TEST_URL = "https://youtu.be/4-6En3bf5TY?si=QDh0lo2UXwusOAcn"

print("Ses Akisi Bilgilerini Kontrol Ediyoruz")
print("="*50)

media = solenz_downloader.extract(TEST_URL)
audio_stream = media.best_audio()

print(f"Başlık: {media.title}")
print(f"\nEn iyi ses akışı:")
print(f"- Format ID: {audio_stream.format_id}")
print(f"- Codec: {audio_stream.codec}")
print(f"- Bitrate: {audio_stream.bitrate}")
print(f"- Filesize: {audio_stream.filesize} bytes")
print(f"- Has video: {audio_stream.has_video}")
print(f"- Has audio: {audio_stream.has_audio}")
print(f"- URL: {audio_stream.url[:100]}...")
print(f"- Ext: {audio_stream.ext}")
print("\n" + "="*50)

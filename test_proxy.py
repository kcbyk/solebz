#!/usr/bin/env python3
"""Test SOCKS5 proxy connection with Android TV"""

import solenz_downloader
import logging

# Enable logging to see proxy info
logging.basicConfig(level=logging.DEBUG)

TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print("Proxy ile test ediyoruz...")
print(f"Kullanılan proxy: {solenz_downloader.config.DEFAULT_PROXY}")

try:
    # Test extract with proxy
    result = solenz_downloader.extract(TEST_URL)
    print(f"\n✅ Proxy çalışıyor! Video başlığı: {result.title}")
    print(f"✅ {len(result.streams)} akış bulundu")

    # Download a small audio stream to test
    audio = result.best_audio()
    print(f"\n✅ Ses akışını indiriyoruz...")
    path = solenz_downloader.download_stream(
        audio,
        output_dir="./test_downloads",
        filename="proxy_test.webm"
    )
    print(f"\n✅ Başarılı! Dosya: {path}")

except Exception as e:
    print(f"\n❌ Hata: {type(e).__name__}: {e}")
    print("\n💡 Öneri: Android TV'de SOCKS5 proxy sunucusunu 1080 portunda çalıştırdığınızdan emin olun!")

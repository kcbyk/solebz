#!/usr/bin/env python3
"""Check if URL supports HTTP Range requests"""

from solenz_downloader.core.client import SolenzClient
import solenz_downloader

TEST_URL = "https://youtu.be/4-6En3bf5TY?si=QDh0lo2UXwusOAcn"

print("HTTP Range Desteğini Kontrol Ediyoruz")
print("="*50)

media = solenz_downloader.extract(TEST_URL)
audio_stream = media.best_audio()

print(f"Ses URL'si: {audio_stream.url[:100]}...")

# Test range support
client = SolenzClient()
try:
    headers = {"Range": "bytes=0-0"}
    resp = client.get(audio_stream.url, headers=headers, timeout=15)
    print(f"Durum Kodu: {resp.status_code}")
    
    if resp.status_code == 206:
        print("[OK] HTTP Range destekleniyor!")
        print(f"Content-Range: {resp.headers.get('Content-Range')}")
    else:
        print("[HATA] HTTP Range desteklenmiyor!")
        print(f"Headers: {dict(resp.headers)}")
        
except Exception as e:
    print(f"Hata: {type(e).__name__}: {e}")

client.close()

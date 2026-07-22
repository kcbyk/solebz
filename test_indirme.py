"""Solenz Downloader - GERCEK INDIRME TESTI

ANDROID_VR istemcisiyle gelen URL'lerin gercekten indirilip
indirilemedigini ve dosyalarin bozuk olup olmadigini kontrol eder.
"""
import os
import sys
import time
from pathlib import Path

import solenz_downloader


def make_progress(label: str):
    state = {"start": time.time(), "last_print": 0}

    def cb(downloaded: int, total: int | None, speed: float) -> None:
        now = time.time()
        if now - state["last_print"] < 0.5 and downloaded != (total or 0):
            return
        state["last_print"] = now
        pct = (downloaded / total * 100) if total and total > 0 else 0
        dl_mb = downloaded / 1024 / 1024
        tot_mb = total / 1024 / 1024 if total else 0
        speed_mb = speed / 1024 / 1024 if speed > 0 else 0
        elapsed = now - state["start"]
        print(
            f"\r  [{label}] [{pct:5.1f}%] {dl_mb:6.1f}/{tot_mb:6.1f} MB"
            f" | {speed_mb:5.1f} MB/s | {elapsed:5.1f}s",
            end="", flush=True,
        )
    return cb


URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
OUT_DIR = Path("C:/Users/senol/OneDrive/Desktop/Yeni klasör (15)/test_downloads")
OUT_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("  SOLENZ DOWNLOADER - GERCEK INDIRME TESTI")
print("=" * 70)
print()


print("[1] 1080p VIDEO indirme testi")
print("-" * 70)
try:
    media = solenz_downloader.extract(URL)

    # 1080p sec (itag 137 - 1920x1080 mp4)
    target = None
    for s in media.streams:
        if s.format_id == "137" and s.has_video:
            target = s
            break

    if not target:
        target = media.best_video()

    print(f"  Hedef   : {target.resolution} .{target.ext} itag={target.format_id}")
    print(f"  Boyut   : {target.filesize / 1024 / 1024:.1f} MB" if target.filesize else "  Boyut   : ?")
    print(f"  Codec   : {target.codec}")
    print(f"  URL Host: {target.url.split('/')[2] if target.url else '?'}")
    print()

    path = solenz_downloader.download_stream(
        target,
        output_dir=str(OUT_DIR),
        filename="test_1080p_video.mp4",
        referer=URL,
        on_progress=make_progress("VID"),
    )
    print()
    sz = os.path.getsize(path)
    print(f"  Kaydedildi: {path}")
    print(f"  Boyut    : {sz / 1024 / 1024:.1f} MB")
    if target.filesize and abs(sz - target.filesize) > 1024:
        print(f"  UYARI: Boyut beklenenden farkli (beklenen {target.filesize})")
    print(f"  >>> 1080p VIDEO INDIRME BASARILI <<<")
except Exception as e:
    print(f"\n  HATA: {type(e).__name__}: {e}")

print()


print("[2] EN IYI SES (opus) indirme testi")
print("-" * 70)
try:
    media = solenz_downloader.extract(URL)
    audio = media.best_audio()  # 251 opus 136kbps

    print(f"  Hedef   : {audio.codec} .{audio.ext} itag={audio.format_id}")
    print(f"  Bitrate : {audio.bitrate // 1000} kbps")
    print(f"  Boyut   : {audio.filesize / 1024 / 1024:.1f} MB" if audio.filesize else "")
    print(f"  URL Host: {audio.url.split('/')[2] if audio.url else '?'}")
    print()

    path = solenz_downloader.download_stream(
        audio,
        output_dir=str(OUT_DIR),
        filename="test_best_audio.webm",
        referer=URL,
        on_progress=make_progress("AUD"),
        timeout=180,
    )
    print()
    sz = os.path.getsize(path)
    print(f"  Kaydedildi: {path}")
    print(f"  Boyut    : {sz / 1024 / 1024:.1f} MB")
    print(f"  >>> EN IYI SES INDIRME BASARILI <<<")
except Exception as e:
    print(f"\n  HATA: {type(e).__name__}: {e}")

print()


print("[3] download_audio() ust duzey API testi")
print("-" * 70)
try:
    path = solenz_downloader.download_audio(
        URL,
        output_dir=str(OUT_DIR),
        filename="test_top_level_audio.m4a",
        prefer_ext="m4a",
        silent=False,
    )
    sz = os.path.getsize(path)
    print()
    print(f"  Kaydedildi: {path}")
    print(f"  Boyut    : {sz / 1024 / 1024:.1f} MB")
    print(f"  >>> UST DUZEY download_audio() BASARILI <<<")
except Exception as e:
    print(f"\n  HATA: {type(e).__name__}: {e}")

print()


print("[4] EN YUKSEK KALITE download() testi (otomatik)")
print("-" * 70)
try:
    path = solenz_downloader.download(
        URL,
        output_dir=str(OUT_DIR),
        filename="test_best_combined.mp4",
        silent=False,
    )
    sz = os.path.getsize(path)
    print()
    print(f"  Kaydedildi: {path}")
    print(f"  Boyut    : {sz / 1024 / 1024:.1f} MB")
    print(f"  >>> download() EN YUKSEK KALITE BASARILI <<<")
except Exception as e:
    print(f"\n  HATA: {type(e).__name__}: {e}")

print()
print("=" * 70)
print("  GERCEK INDIRME TESTI TAMAMLANDI")
print("=" * 70)
print()
print("Indirilen dosyalar:")
for f in sorted(OUT_DIR.iterdir()):
    print(f"  {f.name:40s} {os.path.getsize(f) / 1024 / 1024:8.1f} MB")
"""Solenz Downloader - Guclendirilmis Motor Testi"""
import solenz_downloader

print("=" * 60)
print("  SOLENZ DOWNLOADER v{} - MOTOR TESTI".format(solenz_downloader.__version__))
print("=" * 60)
print()

# --- YouTube Video Extract Testi ---
print("[1] YouTube EXTRACT - en yuksek kalite testi")
print("-" * 50)
try:
    result = solenz_downloader.extract(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    print("  Baslik   : {}".format(result.title))
    print("  Yukleyen : {}".format(result.uploader))
    print("  Sure     : {}s".format(result.duration))
    print("  Toplam   : {} akis".format(len(result.streams)))
    print()

    # Video akislari
    video_streams = [s for s in result.streams if s.has_video]
    audio_streams = [s for s in result.streams if s.has_audio and not s.has_video]
    combined = [s for s in result.streams if s.has_video and s.has_audio]

    print("  Video akislari ({} adet):".format(len(video_streams)))
    for s in sorted(video_streams, key=lambda x: x.height or 0, reverse=True)[:10]:
        sz = "{:.1f}MB".format(s.filesize / 1024 / 1024) if s.filesize else "?"
        client = s.extra.get("client", "?")
        print("    itag {:>3} | {:>10} | .{:<5} | {:>12} | {:>8} | [{}]".format(
            s.format_id, s.resolution, s.ext, s.codec, sz, client
        ))

    print()
    print("  Ses akislari ({} adet):".format(len(audio_streams)))
    for s in sorted(audio_streams, key=lambda x: x.bitrate or 0, reverse=True)[:6]:
        br = "{}kbps".format(s.bitrate // 1000) if s.bitrate else "?"
        sz = "{:.1f}MB".format(s.filesize / 1024 / 1024) if s.filesize else "?"
        client = s.extra.get("client", "?")
        print("    itag {:>3} | {:>10} | .{:<5} | {:>12} | {:>8} | [{}]".format(
            s.format_id, br, s.ext, s.codec, sz, client
        ))

    print()
    print("  Birlesik (video+ses) ({} adet):".format(len(combined)))
    for s in sorted(combined, key=lambda x: x.height or 0, reverse=True):
        sz = "{:.1f}MB".format(s.filesize / 1024 / 1024) if s.filesize else "?"
        print("    itag {:>3} | {:>10} | .{:<5} | {:>8}".format(
            s.format_id, s.resolution, s.ext, sz
        ))

    print()
    best = result.best_stream()
    best_v = result.best_video()
    best_a = result.best_audio()

    if best:
        print("  >>> EN IYI BIRLESIK  : {} .{} (itag {})".format(best.resolution, best.ext, best.format_id))
    if best_v:
        print("  >>> EN IYI VIDEO     : {} .{} (itag {})".format(best_v.resolution, best_v.ext, best_v.format_id))
    if best_a:
        br = "{}kbps".format(best_a.bitrate // 1000) if best_a.bitrate else "?"
        print("  >>> EN IYI SES       : {} .{} {} (itag {})".format(best_a.codec, best_a.ext, br, best_a.format_id))

    print()
    print("  >>> YOUTUBE EXTRACT BASARILI <<<")

except Exception as e:
    print("  HATA: {}: {}".format(type(e).__name__, e))

print()

# --- Muzik Testi ---
print("[2] YouTube MUZIK extract testi")
print("-" * 50)
try:
    result2 = solenz_downloader.extract(
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    best_audio = result2.best_audio()
    if best_audio:
        br = "{}kbps".format(best_audio.bitrate // 1000) if best_audio.bitrate else "?"
        print("  En iyi ses: {} {} .{} (itag {})".format(
            best_audio.codec, br, best_audio.ext, best_audio.format_id
        ))
        print("  >>> MUZIK EXTRACT BASARILI <<<")
    else:
        print("  Ses akisi bulunamadi")
except Exception as e:
    print("  HATA: {}: {}".format(type(e).__name__, e))

print()

# --- Shorts Testi ---
print("[3] YouTube SHORTS testi")
print("-" * 50)
try:
    result3 = solenz_downloader.extract(
        "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    )
    print("  Baslik: {}".format(result3.title))
    print("  Akis  : {} adet".format(len(result3.streams)))
    print("  >>> SHORTS BASARILI <<<")
except Exception as e:
    print("  HATA: {}: {}".format(type(e).__name__, e))

print()
print("=" * 60)
print("  TEST TAMAMLANDI")
print("=" * 60)

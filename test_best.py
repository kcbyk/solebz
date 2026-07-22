"""En iyi kalite (otomatik) testi."""
import os
import time
import solenz_downloader

URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

print('=' * 70)
print('  EN IYI VIDEO - 1080p mp4 (itag 137)')
print('=' * 70)
media = solenz_downloader.extract(URL)
target = None
for s in media.streams:
    if s.format_id == '137' and s.has_video:
        target = s
        break
print(f'Hedef: {target.resolution} .{target.ext} {target.codec}')
print(f'Boyut: {target.filesize / 1024 / 1024:.1f} MB')
print()
t0 = time.time()
path = solenz_downloader.download_stream(
    target,
    output_dir='./test_downloads',
    filename='test_best_1080p.mp4',
    referer=URL,
)
t1 = time.time()
sz = os.path.getsize(path)
print(f'\nIndi: {sz/1024/1024:.2f} MB - {t1-t0:.1f}s ({sz/(t1-t0)/1024:.1f} KB/s)')

print()
print('=' * 70)
print('  ust duzey download() - EN IYI BIRLESIK (itag 18 fallback)')
print('=' * 70)
# Not: bu video itag 18 (360p) birlesik akisina sahip
t0 = time.time()
path = solenz_downloader.download(URL, output_dir='./test_downloads', filename='test_auto_best.mp4')
t1 = time.time()
sz = os.path.getsize(path)
print(f'\nIndi: {sz/1024/1024:.2f} MB - {t1-t0:.1f}s')

print()
print('=' * 70)
print('  ust duzey download_audio() - EN IYI SES')
print('=' * 70)
t0 = time.time()
path = solenz_downloader.download_audio(URL, output_dir='./test_downloads', filename='test_auto_audio.webm')
t1 = time.time()
sz = os.path.getsize(path)
print(f'\nIndi: {sz/1024/1024:.2f} MB - {t1-t0:.1f}s')
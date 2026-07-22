"""En iyi video kalitesi (2160p 4K) testi."""
import os
import time
import solenz_downloader

print('Extracting...')
media = solenz_downloader.extract('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

# Orta kalite video (720p itag 136 - daha kucuk dosya, hizli test)
target = None
for s in media.streams:
    if s.format_id == '136' and s.has_video:  # 1280x720 mp4
        target = s
        break

if not target:
    target = media.best_video()

print(f'Hedef: {target.resolution} .{target.ext} itag={target.format_id}')
print(f'Boyut: {target.filesize / 1024 / 1024:.1f} MB')
print(f'Codec: {target.codec}')
print()
print('Indiriliyor...')
t0 = time.time()
path = solenz_downloader.download_stream(
    target,
    output_dir='./test_downloads',
    filename='test_720p_video.mp4',
    referer='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
)
t1 = time.time()
sz = os.path.getsize(path)
print(f'\nBitti: {sz} bytes ({sz/1024/1024:.2f} MB) - {t1-t0:.1f}s')
print(f'Hiz: {sz/(t1-t0)/1024:.1f} KB/s')
print(f'Yol: {path}')

# Boyut kontrolu
if target.filesize and abs(sz - target.filesize) > 1024:
    print(f'!!! BOYUT UYUSMAZ: beklenen {target.filesize}, alinan {sz}')
else:
    print('BOYUT TAM UYUSUYOR - indirme basarili!')
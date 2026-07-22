"""Hizli test - sadece ses dosyasi."""
import os
import time
import solenz_downloader

print('Extracting...')
media = solenz_downloader.extract('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
audio = media.best_audio()
print(f'Hedef: {audio.codec} {audio.bitrate//1000}kbps .{audio.ext} ({audio.filesize} bytes)')
print('URL:', audio.url[:80] + '...')
print()
print('Indiriliyor...')
t0 = time.time()
path = solenz_downloader.download_stream(
    audio,
    output_dir='./test_downloads',
    filename='quick_audio_test.webm',
    referer='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
)
t1 = time.time()
sz = os.path.getsize(path)
print(f'\nBitti: {sz} bytes ({sz/1024/1024:.2f} MB) - {t1-t0:.1f}s')
print(f'Hiz: {sz/(t1-t0)/1024:.1f} KB/s')
print(f'Yol: {path}')
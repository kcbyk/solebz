import yt_dlp
import os

def download_with_ytdlp(url: str, output_path: str, progress_callback=None, mode="video"):
    """
    yt-dlp kullanarak videoyu veya sesi Tailscale SOCKS5 uzerinden indirir.
    """
    ydl_opts = {
        'proxy': 'socks5://127.0.0.1:1055',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best' if mode == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    }

    def my_hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                progress_callback(downloaded, total)

    ydl_opts['progress_hooks'] = [my_hook]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return {
            "title": info.get("title", "Video"),
            "thumbnail": info.get("thumbnail"),
            "file_path": output_path
        }

"""Solenz Downloader - Global yapilandirma sabitleri."""

from __future__ import annotations

# --------------------------------------------------------------------------- #
#  Versiyon
# --------------------------------------------------------------------------- #
VERSION = "0.1.7"

# --------------------------------------------------------------------------- #
#  HTTP / TLS Ayarlari
# --------------------------------------------------------------------------- #
DEFAULT_TIMEOUT = 30  # saniye
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 1.5  # ustel geri cekilme carpani
REQUEST_DELAY = 0.0  # İstekler arası gecikme kaldırıldı (hız artışı için)

# curl_cffi tarayici taklidi profili
DEFAULT_IMPERSONATE = "chrome124"

# --------------------------------------------------------------------------- #
#  Varsayilan Proxy (Android TV Exit Node Tuneli)
# --------------------------------------------------------------------------- #
# Tailscale exit node uzerinden kullanmak icin:
#   1) tailscale set --exit-node=android-tv
#   2) tailscale set --socks5-server=localhost:1080
# sonra asagidaki satiri aktiflestir:
# DEFAULT_PROXY = "socks5://localhost:1080"

# Dogrudan Tailscale mesh IP uzerinden (Android TV'de SOCKS5 servisi varsa):
# DEFAULT_PROXY = "socks5://100.109.239.23:1080"  # Senin Android TV Tailscale IP'n!

import os

# Proxy yapilandirmasi devre disi birakildi (SOCKS5 hatalarini onlemek ve Cookie Pool'u kullanmak icin)
DEFAULT_PROXY = None

# --------------------------------------------------------------------------- #
#  Indirme Motoru Ayarlari (HIZ OPTİMİZASYONU)
# --------------------------------------------------------------------------- #
CHUNK_SIZE = 256 * 1024  # 256 KB - Agresif hizlandirma
# Maksimum paralel indirme limiti yukseltildi.
MAX_CONCURRENT_SEGMENTS = 16
MIN_SEGMENT_SIZE = 512 * 1024
AUDIO_SEGMENT_SIZE = 128 * 1024
VIDEO_SEGMENT_SIZE = 2 * 1024 * 1024
PROGRESS_UPDATE_INTERVAL = 0.2  # 0.2 saniye - Çok sık güncelleme performansı düşürür
# YouTube gibi yavaş akış sağlayan sunucular için stream timeout'u
STREAM_TIMEOUT = 600  # 10 dakika - Daha uzun süreli indirmeler için

# --------------------------------------------------------------------------- #
#  Desteklenen Platformlar
# --------------------------------------------------------------------------- #
SUPPORTED_PLATFORMS = [
    "youtube",
    "tiktok",
    "instagram",
]

# --------------------------------------------------------------------------- #
#  Varsayilan Basliklar (genel)
# --------------------------------------------------------------------------- #
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", '
                 '"Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# --------------------------------------------------------------------------- #
#  YouTube'a Ozel Sabitler
# --------------------------------------------------------------------------- #
YOUTUBE_CLIENT_VERSION = "2.20250115.01.00"
YOUTUBE_API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
YOUTUBE_INNERTUBE_CONTEXT = {
    "client": {
        "hl": "en",
        "gl": "US",
        "clientName": "WEB",
        "clientVersion": YOUTUBE_CLIENT_VERSION,
        "platform": "DESKTOP",
        "userAgent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }
}

"""
Solenz Downloader - Bagimsiz Python Medya Indirme Motoru
=========================================================

Harici araclara (yt-dlp, ffmpeg) bagimli olmayan, TLS parmak izi taklidi
yapan, sifirdan insa edilmis bir medya indirme kutuphanesi.

Kullanim:
    import solenz_downloader

    # Video indir (en yuksek kalite, otomatik)
    path = solenz_downloader.download("https://www.youtube.com/watch?v=VIDEO_ID")

    # Sadece ses/muzik indir
    path = solenz_downloader.download_audio("https://www.youtube.com/watch?v=VIDEO_ID")

    # Bilgi cikar (indirmeden)
    result = solenz_downloader.extract("https://www.youtube.com/watch?v=VIDEO_ID")
    print(result.title, result.streams)
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from .config import VERSION, MAX_CONCURRENT_SEGMENTS
from .core.client import SolenzClient
from .core.downloader import SolenzDownloader, ProgressCallback
from .core.models import MediaResult, StreamInfo, YouTubeSearchResult
from .exceptions import (
    SolenzError,
    ExtractionError,
    DownloadError,
    ProxyError,
    SignatureError,
    RateLimitError,
    GeoBlockError,
    AgeGateError,
)
from .extractors import registry
from .utils.proxy import ProxyConfig

logger = logging.getLogger("solenz")

__version__ = VERSION
__all__ = [
    # Ust duzey fonksiyonlar
    "extract",
    "download",
    "download_audio",
    "download_video",
    "download_stream",
    "search_youtube",
    "supported_platforms",
    # Siniflar
    "SolenzClient",
    "SolenzDownloader",
    "MediaResult",
    "StreamInfo",
    "YouTubeSearchResult",
    "ProxyConfig",
    # Hatalar
    "SolenzError",
    "ExtractionError",
    "DownloadError",
    "ProxyError",
    "SignatureError",
    "RateLimitError",
    "GeoBlockError",
    "AgeGateError",
]


# =========================================================================== #
#  Varsayilan ilerleme gosterimi
# =========================================================================== #

def _default_progress(downloaded: int, total: int | None, speed: float) -> None:
    """Konsola ilerleme yazdirir."""
    if total and total > 0:
        pct = (downloaded / total) * 100
        dl_mb = downloaded / (1024 * 1024)
        tot_mb = total / (1024 * 1024)
        speed_mb = speed / (1024 * 1024) if speed > 0 else 0
        print(
            f"\r  [{pct:5.1f}%] {dl_mb:.1f}/{tot_mb:.1f} MB"
            + (f" | {speed_mb:.1f} MB/s" if speed_mb > 0 else ""),
            end="", flush=True,
        )
    else:
        dl_mb = downloaded / (1024 * 1024)
        print(f"\r  {dl_mb:.1f} MB indiriliyor...", end="", flush=True)


# =========================================================================== #
#  UST DUZEY API
# =========================================================================== #

def extract(
    url: str,
    *,
    proxy: str | dict[str, str] | ProxyConfig | None = None,
    cookies: dict[str, str] | None = None,
    timeout: int = 30,
) -> MediaResult:
    """Verilen URL'den medya bilgilerini ve akis linklerini cikarir.

    Returns:
        MediaResult: title, streams, duration, uploader vb.
    """
    with SolenzClient(proxy=proxy, cookies=cookies, timeout=timeout) as client:
        return registry.extract(url, client)


def download(
    url: str,
    *,
    output_dir: str = ".",
    filename: str | None = None,
    quality: str | None = None,
    prefer_ext: str = "mp4",
    proxy: str | dict[str, str] | ProxyConfig | None = None,
    cookies: dict[str, str] | None = None,
    timeout: int = 30,
    on_progress: ProgressCallback | None = None,
    max_concurrent: int = MAX_CONCURRENT_SEGMENTS,
    silent: bool = False,
) -> str:
    """EN YUKSEK kalitede video indirir.

    Her zaman en yuksek cozunurluklu birlesik (video+ses) akisi secer.
    quality parametresi None ise otomatik olarak en iyi kaliteyi alir.
    """
    if on_progress is None and not silent:
        on_progress = _default_progress

    with SolenzClient(proxy=proxy, cookies=cookies, timeout=timeout) as client:
        media = registry.extract(url, client)

        logger.info("[Solenz] %s - %d akis bulundu", media.title, len(media.streams))

        downloader = SolenzDownloader(
            client,
            on_progress=on_progress,
            max_concurrent=max_concurrent,
        )

        path = downloader.download(
            media,
            output_dir=output_dir,
            filename=filename,
            quality=quality,
            prefer_ext=prefer_ext,
        )

        if not silent:
            print()  # ilerleme satirini bitir

        return path


def download_video(
    url: str,
    *,
    output_dir: str = ".",
    filename: str | None = None,
    quality: str | None = None,
    proxy: str | dict[str, str] | ProxyConfig | None = None,
    cookies: dict[str, str] | None = None,
    timeout: int = 30,
    on_progress: ProgressCallback | None = None,
    max_concurrent: int = MAX_CONCURRENT_SEGMENTS,
    silent: bool = False,
) -> str:
    """En yuksek kalitede VIDEO indirir (download ile ayni, alias)."""
    return download(
        url,
        output_dir=output_dir,
        filename=filename,
        quality=quality,
        prefer_ext="mp4",
        proxy=proxy,
        cookies=cookies,
        timeout=timeout,
        on_progress=on_progress,
        max_concurrent=max_concurrent,
        silent=silent,
    )


def download_audio(
    url: str,
    *,
    output_dir: str = ".",
    filename: str | None = None,
    prefer_ext: str = "m4a",
    proxy: str | dict[str, str] | ProxyConfig | None = None,
    cookies: dict[str, str] | None = None,
    timeout: int = 30,
    on_progress: ProgressCallback | None = None,
    max_concurrent: int = MAX_CONCURRENT_SEGMENTS,
    silent: bool = False,
) -> str:
    """En yuksek kalitede SADECE SES (muzik/sarki) indirir.

    En yuksek bitrate'li ses akisini secer ve indirir.
    Varsayilan format: m4a (AAC). Opus icin prefer_ext="webm" kullanin.
    """
    if on_progress is None and not silent:
        on_progress = _default_progress

    with SolenzClient(proxy=proxy, cookies=cookies, timeout=timeout) as client:
        media = registry.extract(url, client)

        logger.info("[Solenz] Ses: %s", media.title)

        # En iyi ses akisini sec
        audio_stream = media.best_audio(prefer_ext=prefer_ext)

        if not audio_stream:
            # Ses akisi yoksa birlesik akisin sesini al
            audio_stream = media.best_stream()
            if not audio_stream:
                raise DownloadError(
                    f"Indirilebilir ses akisi bulunamadi: {url}"
                )

        # Dosya adi
        if not filename:
            from .core.downloader import SolenzDownloader as _DL
            safe_title = _DL._sanitize_filename(media.title or media.media_id or "audio")
            ext = audio_stream.ext or prefer_ext
            filename = f"{safe_title}.{ext}"

        downloader = SolenzDownloader(
            client,
            on_progress=on_progress,
            max_concurrent=max_concurrent,
        )

        path = downloader.download_stream(
            audio_stream,
            output_dir=output_dir,
            filename=filename,
            referer=media.url,
        )

        if not silent:
            print()

        return path


def download_stream(
    stream: StreamInfo,
    *,
    output_dir: str = ".",
    filename: str | None = None,
    referer: str | None = None,
    proxy: str | dict[str, str] | ProxyConfig | None = None,
    timeout: int = 30,
    on_progress: ProgressCallback | None = None,
    max_concurrent: int = MAX_CONCURRENT_SEGMENTS,
) -> str:
    """Dogrudan bir StreamInfo nesnesini indirir."""
    with SolenzClient(proxy=proxy, timeout=timeout) as client:
        downloader = SolenzDownloader(
            client,
            on_progress=on_progress,
            max_concurrent=max_concurrent,
        )
        return downloader.download_stream(
            stream,
            output_dir=output_dir,
            filename=filename,
            referer=referer,
        )


def supported_platforms() -> list[str]:
    """Desteklenen platform adlarini dondurur."""
    return registry.supported_platforms


def search_youtube(
    query: str,
    *,
    limit: int = 10,
    proxy: str | dict[str, str] | ProxyConfig | None = None,
    cookies: dict[str, str] | None = None,
    timeout: int = 30,
) -> list[YouTubeSearchResult]:
    """YouTube'da arama yapar ve sonuçları döner.
    
    Args:
        query: Arama sorgusu
        limit: Maksimum sonuç sayısı (varsayılan: 10)
        proxy: Proxy ayarları
        cookies: Çerezler
        timeout: Zaman aşımı süresi (saniye)
    
    Returns:
        YouTubeSearchResult listesi: Her biri video_id, title, url vb. içerir
    """
    from .extractors.youtube import YouTubeExtractor
    
    with SolenzClient(proxy=proxy, cookies=cookies, timeout=timeout) as client:
        extractor = YouTubeExtractor(client)
        return extractor.search(query, limit=limit)

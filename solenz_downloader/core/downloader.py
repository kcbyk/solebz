"""Solenz Downloader - Parcali (chunked) indirme motoru.

HTTP Range basligi ile parcali indirme, ilerleme takibi,
yarida kalan indirmeleri devam ettirme ve eslamanli segment destegi.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlparse

from ..config import (
    AUDIO_SEGMENT_SIZE,
    CHUNK_SIZE,
    MAX_CONCURRENT_SEGMENTS,
    MIN_SEGMENT_SIZE,
    PROGRESS_UPDATE_INTERVAL,
    STREAM_TIMEOUT,
    VIDEO_SEGMENT_SIZE,
)
from ..core.client import SolenzClient
from ..core.models import MediaResult, StreamInfo
from ..exceptions import DownloadError

logger = logging.getLogger("solenz.downloader")

# Ilerleme callback tipi: (indirilen_byte, toplam_byte, hiz_bps)
ProgressCallback = Callable[[int, int | None, float], None]


class SolenzDownloader:
    """Parcali medya indirme motoru.

    Kullanim:
        downloader = SolenzDownloader(client)

        # Tek akis indirme
        path = downloader.download_stream(stream, output_dir="/tmp")

        # MediaResult'tan en iyi kaliteyi indir
        path = downloader.download(media_result, output_dir="/tmp")
    """

    def __init__(
        self,
        client: SolenzClient,
        *,
        chunk_size: int = CHUNK_SIZE,
        max_concurrent: int = MAX_CONCURRENT_SEGMENTS,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self.client = client
        self.chunk_size = chunk_size
        self.max_concurrent = max_concurrent
        self.on_progress = on_progress

    # -- Ust duzey indirme -------------------------------------------------- #

    def download(
        self,
        media: MediaResult,
        *,
        output_dir: str = ".",
        filename: str | None = None,
        quality: str | None = None,
        prefer_ext: str = "mp4",
    ) -> str:
        """MediaResult'tan en iyi akisi secip indirir.

        Args:
            media: Cikarilmis medya bilgisi
            output_dir: Cikis klasoru
            filename: Ozel dosya adi (None ise otomatik belirlenir)
            quality: Hedef kalite ("1080p", "720p" vb., None = en iyi)
            prefer_ext: Tercih edilen uzanti

        Returns:
            Indirilen dosyanin tam yolu
        """
        stream = self._select_stream(media, quality=quality, prefer_ext=prefer_ext)
        if not stream:
            raise DownloadError("Indirilebilir akis bulunamadi")

        if not filename:
            safe_title = self._sanitize_filename(media.title or media.media_id or "video")
            ext = stream.ext or "mp4"
            filename = f"{safe_title}.{ext}"

        return self.download_stream(
            stream,
            output_dir=output_dir,
            filename=filename,
            referer=media.url,
        )

    def download_stream(
        self,
        stream: StreamInfo,
        *,
        output_dir: str = ".",
        filename: str | None = None,
        referer: str | None = None,
        resume: bool = True,
    ) -> str:
        """Tek bir akisi indirir.

        Args:
            stream: Indirilecek akis bilgisi
            output_dir: Cikis klasoru
            filename: Dosya adi
            referer: HTTP Referer basligi
            resume: Yarida kalan indirmeyi devam ettir

        Returns:
            Indirilen dosyanin tam yolu
        """
        os.makedirs(output_dir, exist_ok=True)

        if not filename:
            filename = self._filename_from_url(stream.url, stream.ext)

        output_path = os.path.join(output_dir, filename)

        # Dosya boyutunu kontrol et (Range destegi icin)
        total_size = stream.filesize or self._get_content_length(stream.url, referer)
        logger.debug(f"Total size: {total_size} bytes")

        # Mevcut dosya boyutu (resume icin)
        existing_size = 0
        if resume and os.path.exists(output_path):
            existing_size = os.path.getsize(output_path)
            if total_size and existing_size >= total_size:
                logger.info("Dosya zaten tamamlanmis: %s", output_path)
                return output_path
            if existing_size > 0:
                logger.info(
                    "Indirme devam ettiriliyor: %d / %s byte",
                    existing_size,
                    total_size or "?",
                )

        # Buyuk dosya + Range destegi varsa parcali indir
        supports_range = self._supports_range(stream.url, referer)
        logger.debug(f"Supports Range: {supports_range}")
        
        parallel_threshold = (
            AUDIO_SEGMENT_SIZE if stream.is_audio_only else MIN_SEGMENT_SIZE
        )

        if (
            total_size
            and total_size > parallel_threshold
            and self.max_concurrent > 1
            and supports_range
            and existing_size == 0  # resume ile parcali indirme uyumsuz
        ):
            logger.info("PARALEL INDIRME kullanılıyor ({} segment)".format(self.max_concurrent))
            return self._download_parallel(
                stream.url,
                output_path,
                total_size,
                referer=referer,
                target_segment_size=(
                    AUDIO_SEGMENT_SIZE if stream.is_audio_only else VIDEO_SEGMENT_SIZE
                ),
            )

        # Tekli indirme
        logger.info("TEKLI INDIRME kullanılıyor")
        return self._download_single(
            stream.url,
            output_path,
            total_size=total_size,
            start_byte=existing_size,
            referer=referer,
        )

    # -- Tekli indirme ------------------------------------------------------ #

    def _download_single(
        self,
        url: str,
        output_path: str,
        *,
        total_size: int | None = None,
        start_byte: int = 0,
        referer: str | None = None,
    ) -> str:
        """Tek baglanti ile parcali indirme."""
        headers: dict[str, str] = {}
        if referer:
            headers["Referer"] = referer
        if start_byte > 0:
            headers["Range"] = f"bytes={start_byte}-"

        try:
            resp = self.client.get(url, headers=headers, timeout=STREAM_TIMEOUT, stream=True)
        except Exception as e:
            raise DownloadError(f"Indirme istegi basarisiz: {e}", cause=e) from e

        if start_byte > 0 and resp.status_code == 200:
            if hasattr(resp, "close"):
                resp.close()
            start_byte = 0
            downloaded = 0
            try:
                resp = self.client.get(
                    url,
                    headers={"Referer": referer} if referer else {},
                    timeout=STREAM_TIMEOUT,
                    stream=True,
                )
            except Exception as e:
                raise DownloadError(
                    f"Devam indirmesi yeniden baslatilamadi: {e}", cause=e
                ) from e

        if resp.status_code not in (200, 206):
            raise DownloadError(
                f"Beklenmeyen HTTP durumu: {resp.status_code}"
            )

        mode = "ab" if start_byte > 0 else "wb"
        downloaded = start_byte
        last_progress_time = time.time()
        downloaded_since_last = 0  # Son güncellemeden beri indirilen byte

        try:
            with open(output_path, mode) as f:
                for chunk in resp.iter_content(chunk_size=self.chunk_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    chunk_len = len(chunk)
                    downloaded += chunk_len
                    downloaded_since_last += chunk_len

                    # Ilerleme bildirimi (daha doğru hız hesaplaması)
                    now = time.time()
                    if self.on_progress and (now - last_progress_time) >= PROGRESS_UPDATE_INTERVAL:
                        elapsed = max(now - last_progress_time, 0.001)
                        speed = downloaded_since_last / elapsed
                        self.on_progress(downloaded, total_size, speed)
                        last_progress_time = now
                        downloaded_since_last = 0

        except Exception as e:
            raise DownloadError(
                f"Dosya yazma hatasi: {e}", cause=e
            ) from e

        # Son ilerleme bildirimi
        if self.on_progress:
            self.on_progress(downloaded, total_size, 0.0)

        logger.info(
            "Indirme tamamlandi: %s (%s byte)", output_path, downloaded
        )
        return output_path

    # -- Paralel (cok segmentli) indirme ------------------------------------ #

    def _download_parallel(
        self,
        url: str,
        output_path: str,
        total_size: int,
        *,
        referer: str | None = None,
        target_segment_size: int = VIDEO_SEGMENT_SIZE,
    ) -> str:
        """Buyuk dosyalari parcalara bolup eslamanli indirir."""
        segment_count = min(
            self.max_concurrent,
            max(2, (total_size + target_segment_size - 1) // target_segment_size),
        )
        segment_size = total_size // segment_count
        segments: list[tuple[int, int]] = []

        for i in range(segment_count):
            start = i * segment_size
            end = (i + 1) * segment_size - 1 if i < segment_count - 1 else total_size - 1
            segments.append((start, end))

        logger.info(
            "Paralel indirme: %d segment, her biri ~%d MB",
            len(segments),
            segment_size / (1024 * 1024),
        )

        # Gecici segment dosyalari
        segment_paths: list[str] = []
        for i in range(len(segments)):
            segment_paths.append(f"{output_path}.part{i}")

        downloaded_total = 0
        progress_lock = threading.Lock()
        last_progress_time = time.time()
        errors: list[str] = []

        def _download_segment(
            seg_idx: int, start: int, end: int, seg_path: str
        ) -> int:
            """Her segment icin yeni bir curl_cffi Session kullanir
            (Session thread-safe degil)."""
            try:
                from curl_cffi import requests as cffi_requests
                use_curl_cffi = True
            except ImportError:
                import requests as cffi_requests
                use_curl_cffi = False

            # Ana session'dan proxy/cookie ayarlarini miras al
            if use_curl_cffi:
                sess = cffi_requests.Session(
                    impersonate=self.client.impersonate,
                    timeout=self.client.timeout,
                )
            else:
                sess = cffi_requests.Session()
            sess.headers.update(dict(self.client._session.headers))
            # Cookie'leri string olarak ekle (iter uyumsuzlugu onlemek icin)
            try:
                cookie_items = []
                src_cookies = self.client._session.cookies
                # curl_cffi RequestsCookieJar veya dict olabilir
                if hasattr(src_cookies, "items"):
                    cookie_items = list(src_cookies.items())
                else:
                    for c in src_cookies:
                        if hasattr(c, "name"):
                            cookie_items.append((c.name, c.value))
                cookie_str = "; ".join(f"{k}={v}" for k, v in cookie_items)
                if cookie_str:
                    sess.headers["Cookie"] = cookie_str
            except Exception:
                pass  # cookie tasima basarisiz - devam et
            if self.client._proxy_dict:
                sess.proxies.update(self.client._proxy_dict)

            headers: dict[str, str] = {"Range": f"bytes={start}-{end}"}
            if referer:
                headers["Referer"] = referer

            try:
                request_kwargs = {
                    "headers": headers,
                    "timeout": STREAM_TIMEOUT,
                    "stream": True,
                }
                if self.client._proxy_dict:
                    request_kwargs["proxies"] = self.client._proxy_dict
                resp = sess.get(url, **request_kwargs)
                if resp.status_code != 206:
                    raise DownloadError(
                        f"Segment {seg_idx} icin Range reddedildi: HTTP {resp.status_code}"
                    )
                seg_downloaded = 0
                with open(seg_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            seg_downloaded += len(chunk)
                resp.close()
                return seg_downloaded
            finally:
                sess.close()

        try:
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                futures = {}
                for i, (start, end) in enumerate(segments):
                    future = executor.submit(
                        _download_segment, i, start, end, segment_paths[i]
                    )
                    futures[future] = i

                for future in as_completed(futures):
                    seg_idx = futures[future]
                    try:
                        seg_size = future.result()
                        with progress_lock:
                            downloaded_total += seg_size
                        
                        # İlerleme güncellemesi (zaman bazlı)
                        now = time.time()
                        if self.on_progress and (now - last_progress_time) >= PROGRESS_UPDATE_INTERVAL:
                            self.on_progress(downloaded_total, total_size, 0.0)
                            last_progress_time = now
                    except Exception as e:
                        errors.append(f"Segment {seg_idx}: {e}")

            if errors:
                raise DownloadError(
                    f"Paralel indirme hatalari: {'; '.join(errors)}"
                )

            # Segment dosyalarini birlestir (daha hızlı okuma/yazma)
            logger.info("Segment dosyalari birlestiriliyor...")
            with open(output_path, "wb") as out_f:
                for seg_path in segment_paths:
                    with open(seg_path, "rb") as seg_f:
                        # Daha büyük chunklarla oku (16 MB)
                        while True:
                            chunk = seg_f.read(16 * 1024 * 1024)  # 16 MB
                            if not chunk:
                                break
                            out_f.write(chunk)

            logger.info(
                "Paralel indirme tamamlandi: %s (%d byte)", output_path, downloaded_total
            )

        finally:
            # Gecici dosyalari temizle
            logger.info("Gecici segment dosyalari temizleniyor...")
            for seg_path in segment_paths:
                try:
                    if os.path.exists(seg_path):
                        os.remove(seg_path)
                except OSError:
                    pass

        return output_path

    # -- Yardimci metotlar -------------------------------------------------- #

    def _get_content_length(self, url: str, referer: str | None = None) -> int | None:
        """HEAD istegi ile dosya boyutunu ogrenmeye calisir."""
        try:
            headers = {}
            if referer:
                headers["Referer"] = referer
            resp = self.client.head(url, headers=headers, timeout=15)
            cl = resp.headers.get("Content-Length", "")
            return int(cl) if cl.isdigit() else None
        except Exception:
            return None

    def _supports_range(self, url: str, referer: str | None = None) -> bool:
        """Sunucunun HTTP Range destegini kontrol eder."""
        try:
            headers = {"Range": "bytes=0-0"}
            if referer:
                headers["Referer"] = referer
            resp = self.client.get(url, headers=headers, timeout=15)
            return resp.status_code == 206
        except Exception:
            return False

    def _select_stream(
        self,
        media: MediaResult,
        *,
        quality: str | None = None,
        prefer_ext: str = "mp4",
    ) -> StreamInfo | None:
        """Kalite tercihine gore en iyi akisi secer."""
        if quality:
            # Tam eslesen kalite ara
            for s in media.streams:
                if s.quality == quality and s.has_video:
                    return s
            # Yukseklik eslestir (ornegin "720p" -> height=720)
            target_h = int(re.sub(r"\D", "", quality)) if re.search(r"\d+", quality) else 0
            if target_h:
                matching = [s for s in media.streams if s.height and s.has_video]
                if matching:
                    return min(
                        matching,
                        key=lambda s: abs((s.height or 0) - target_h),
                    )

        return media.best_stream(prefer_ext=prefer_ext)

    @staticmethod
    def _sanitize_filename(name: str, max_len: int = 100) -> str:
        """Dosya adi icin guvenli hale getirir."""
        # Gecersiz karakterleri kaldir
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
        name = name.strip(". ")
        if not name:
            name = "video"
        return name[:max_len]

    @staticmethod
    def _filename_from_url(url: str, fallback_ext: str = "mp4") -> str:
        """URL'den dosya adini cikarir."""
        parsed = urlparse(url)
        path = unquote(parsed.path)
        basename = os.path.basename(path)

        if basename and "." in basename:
            return basename[:150]

        return f"download.{fallback_ext}"

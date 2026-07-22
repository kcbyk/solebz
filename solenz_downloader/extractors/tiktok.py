"""Solenz Downloader - TikTok medya URL cikarici."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .base import BaseExtractor, registry
from ..core.models import MediaResult, StreamInfo
from ..exceptions import ExtractionError
from ..utils.headers import get_tiktok_headers

logger = logging.getLogger("solenz.tiktok")


@registry.register
class TikTokExtractor(BaseExtractor):
    """TikTok video akis linklerini cikarir."""

    PLATFORM_NAME = "tiktok"

    VALID_URL_PATTERNS = [
        r"(?:https?://)?(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+",
        r"(?:https?://)?(?:vm|vt)\.tiktok\.com/\w+",
        r"(?:https?://)?(?:www\.)?tiktok\.com/t/\w+",
    ]

    def extract(self, url: str) -> MediaResult:
        headers = get_tiktok_headers(referer=url)

        # Kisa linkleri coz
        resolved_url = self._resolve_short_url(url, headers)

        html = self._get_page(resolved_url, headers=headers)

        # SIGI_STATE veya __UNIVERSAL_DATA icinden JSON cikar
        data = self._extract_video_data(html)
        if not data:
            raise ExtractionError("TikTok video verisi cikarilmadi")

        return self._parse_video_data(data, resolved_url)

    def _resolve_short_url(self, url: str, headers: dict) -> str:
        """Kisa TikTok linklerini tam URL'ye donusturur."""
        if "vm.tiktok.com" in url or "vt.tiktok.com" in url or "/t/" in url:
            resp = self.client.get(url, headers=headers, allow_redirects=True)
            return str(resp.url)
        return url

    def _extract_video_data(self, html: str) -> dict[str, Any] | None:
        """HTML içindeki video verisini JSON olarak çıkarır."""
        # Yöntem 1: SIGI_STATE
        patterns = [
            r'<script\s+id="SIGI_STATE"[^>]*>({.+?})</script>',
            r'<script\s+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>({.+?})</script>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    print("[DEBUG] Found JSON data:", json.dumps(data, indent=2)[:2000])
                    return data
                except json.JSONDecodeError:
                    continue

        # Yöntem 2: window.__data
        match = re.search(
            r"window\.__data\s*=\s*({.+?});\s*</script>", html, re.DOTALL
        )
        if match:
            try:
                data = json.loads(match.group(1))
                print("[DEBUG] Found window.__data:", json.dumps(data, indent=2)[:2000])
                return data
            except json.JSONDecodeError:
                pass

        return None

    def _parse_video_data(self, data: dict[str, Any], url: str) -> MediaResult:
        """TikTok JSON verisinden MediaResult olusturur."""
        video_info: dict[str, Any] = {}

        # __UNIVERSAL_DATA_FOR_REHYDRATION__ yapisi
        default_scope = data.get("__DEFAULT_SCOPE__", {})
        webapp_detail = default_scope.get("webapp.video-detail", {})
        if webapp_detail:
            item_info = webapp_detail.get("itemInfo", {}).get("itemStruct", {})
            if item_info:
                video_info = item_info

        # SIGI_STATE yapisi
        if not video_info:
            item_module = data.get("ItemModule", {})
            if item_module:
                video_info = next(iter(item_module.values()), {})

        if not video_info:
            raise ExtractionError("TikTok video detaylari bulunamadi")

        # Temel bilgiler
        title = video_info.get("desc", "")
        video_data = video_info.get("video", {})
        author_data = video_info.get("author", {})
        stats_data = video_info.get("stats", {})
        music_data = video_info.get("music", {})

        video_id = video_info.get("id", "")
        duration = video_data.get("duration", 0) or None

        # Kucuk resim
        thumbnail = (
            video_data.get("cover", "")
            or video_data.get("originCover", "")
            or video_data.get("dynamicCover", "")
        )

        # Akislar
        streams: list[StreamInfo] = []

        # Watermark'siz indirme URL'si
        download_url = video_data.get("downloadAddr", "")
        play_url = video_data.get("playAddr", "")
        bitrate = video_data.get("bitrate", 0)

        if play_url:
            streams.append(StreamInfo(
                url=play_url,
                mime_type="video/mp4",
                quality=f"{video_data.get('height', '')}p",
                width=video_data.get("width"),
                height=video_data.get("height"),
                bitrate=bitrate,
                has_audio=True,
                has_video=True,
                format_id="play",
                ext="mp4",
            ))

        if download_url and download_url != play_url:
            streams.append(StreamInfo(
                url=download_url,
                mime_type="video/mp4",
                quality=f"{video_data.get('height', '')}p",
                width=video_data.get("width"),
                height=video_data.get("height"),
                bitrate=bitrate,
                has_audio=True,
                has_video=True,
                format_id="download",
                ext="mp4",
            ))

        # Ses (muzik)
        music_url = music_data.get("playUrl", "")
        if music_url:
            streams.append(StreamInfo(
                url=music_url,
                mime_type="audio/mpeg",
                quality="audio_only",
                has_audio=True,
                has_video=False,
                format_id="music",
                ext="mp3",
            ))

        return MediaResult(
            url=url,
            title=title,
            thumbnail=thumbnail,
            duration=duration,
            uploader=author_data.get("uniqueId", author_data.get("nickname", "")),
            view_count=stats_data.get("playCount"),
            platform="tiktok",
            media_id=video_id,
            streams=streams,
            extra={
                "likes": stats_data.get("diggCount"),
                "comments": stats_data.get("commentCount"),
                "shares": stats_data.get("shareCount"),
            },
        )

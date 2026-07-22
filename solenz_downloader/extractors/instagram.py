"""Solenz Downloader - Instagram medya URL cikarici."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .base import BaseExtractor, registry
from ..core.models import MediaResult, StreamInfo
from ..exceptions import ExtractionError
from ..utils.headers import get_instagram_headers

logger = logging.getLogger("solenz.instagram")


@registry.register
class InstagramExtractor(BaseExtractor):
    """Instagram post/reel video ve resim akis linklerini cikarir."""

    PLATFORM_NAME = "instagram"

    VALID_URL_PATTERNS = [
        r"(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[\w-]+",
        r"(?:https?://)?(?:www\.)?instagram\.com/stories/[\w.-]+/\d+",
    ]

    # Instagram GraphQL API endpoint
    _GRAPHQL_URL = "https://www.instagram.com/graphql/query/"
    _POST_QUERY_HASH = "b3055c01b4b222b8a47dc12b090e4e64"

    def extract(self, url: str) -> MediaResult:
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            raise ExtractionError(f"Instagram shortcode cikarilmadi: {url}")

        logger.info("Instagram shortcode: %s", shortcode)

        # Yontem 1: /p/{shortcode}/?__a=1&__d=dis endpoint'i
        try:
            return self._extract_from_api(shortcode, url)
        except ExtractionError:
            logger.warning("API yontemi basarisiz, web sayfasi deneniyor...")

        # Yontem 2: Web sayfasindan cikarma
        return self._extract_from_webpage(shortcode, url)

    @staticmethod
    def _extract_shortcode(url: str) -> str:
        """URL'den Instagram shortcode'unu cikarir."""
        match = re.search(r"/(?:p|reel|reels|tv)/([\w-]+)", url)
        return match.group(1) if match else ""

    def _extract_from_api(self, shortcode: str, url: str) -> MediaResult:
        """Instagram'in JSON API'si uzerinden medya bilgilerini cikarir."""
        api_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
        headers = get_instagram_headers(referer=url)

        resp = self.client.get(api_url, headers=headers)
        if resp.status_code != 200:
            raise ExtractionError(f"Instagram API hatasi ({resp.status_code})")

        try:
            data = resp.json()
        except Exception:
            raise ExtractionError("Instagram API JSON parse hatasi")

        # API yanit yapisi
        items = data.get("items", [])
        if items:
            return self._parse_media_item(items[0], url)

        # graphql yapisi
        graphql = data.get("graphql", {}).get("shortcode_media", {})
        if graphql:
            return self._parse_graphql_media(graphql, url)

        raise ExtractionError("Instagram API yanitinda medya bulunamadi")

    def _extract_from_webpage(self, shortcode: str, url: str) -> MediaResult:
        """Web sayfasindan embed edilmis veriyi cikarir."""
        page_url = f"https://www.instagram.com/p/{shortcode}/"
        headers = get_instagram_headers(referer=page_url)

        html = self._get_page(page_url, headers=headers)

        # SharedData veya additionalData icinden JSON cikar
        data = self._find_json_in_html(html, "window._sharedData")
        if data:
            try:
                media = (
                    data["entry_data"]["PostPage"][0]
                    ["graphql"]["shortcode_media"]
                )
                return self._parse_graphql_media(media, url)
            except (KeyError, IndexError):
                pass

        # __additionalDataLoaded
        match = re.search(
            r"window\.__additionalDataLoaded\s*\(\s*['\"].*?['\"]\s*,\s*({.+?})\s*\)",
            html, re.DOTALL,
        )
        if match:
            try:
                data = json.loads(match.group(1))
                media = data.get("graphql", {}).get("shortcode_media", {})
                if media:
                    return self._parse_graphql_media(media, url)
            except (json.JSONDecodeError, KeyError):
                pass

        raise ExtractionError("Instagram web sayfasindan medya cikarilmadi")

    def _parse_media_item(self, item: dict[str, Any], url: str) -> MediaResult:
        """Instagram API items[] formatindaki veriyi parse eder."""
        media_type = item.get("media_type", 0)
        caption = item.get("caption", {})
        title = caption.get("text", "") if isinstance(caption, dict) else str(caption or "")
        user = item.get("user", {})

        streams: list[StreamInfo] = []

        # Video
        if media_type == 2:  # video
            versions = item.get("video_versions", [])
            for i, v in enumerate(versions):
                streams.append(StreamInfo(
                    url=v.get("url", ""),
                    mime_type="video/mp4",
                    quality=f"{v.get('height', '')}p",
                    width=v.get("width"),
                    height=v.get("height"),
                    has_audio=True,
                    has_video=True,
                    format_id=f"video_{i}",
                    ext="mp4",
                ))

        # Resim
        elif media_type == 1:  # photo
            candidates = item.get("image_versions2", {}).get("candidates", [])
            for i, c in enumerate(candidates):
                streams.append(StreamInfo(
                    url=c.get("url", ""),
                    mime_type="image/jpeg",
                    quality=f"{c.get('height', '')}p",
                    width=c.get("width"),
                    height=c.get("height"),
                    has_audio=False,
                    has_video=False,
                    format_id=f"image_{i}",
                    ext="jpg",
                ))

        # Carousel (coklu medya)
        elif media_type == 8:
            for ci, child in enumerate(item.get("carousel_media", [])):
                child_result = self._parse_media_item(child, url)
                for s in child_result.streams:
                    s.format_id = f"carousel_{ci}_{s.format_id}"
                    streams.append(s)

        thumbnail = ""
        img_candidates = item.get("image_versions2", {}).get("candidates", [])
        if img_candidates:
            thumbnail = img_candidates[0].get("url", "")

        return MediaResult(
            url=url,
            title=title[:200] if title else "",
            thumbnail=thumbnail,
            duration=int(item.get("video_duration", 0)) or None,
            uploader=user.get("username", ""),
            platform="instagram",
            media_id=item.get("pk", item.get("id", "")),
            streams=streams,
            extra={
                "like_count": item.get("like_count"),
                "comment_count": item.get("comment_count"),
                "media_type": media_type,
            },
        )

    def _parse_graphql_media(self, media: dict[str, Any], url: str) -> MediaResult:
        """GraphQL shortcode_media formatindaki veriyi parse eder."""
        typename = media.get("__typename", "")
        title = ""
        edges = media.get("edge_media_to_caption", {}).get("edges", [])
        if edges:
            title = edges[0].get("node", {}).get("text", "")

        owner = media.get("owner", {})
        streams: list[StreamInfo] = []

        if media.get("is_video"):
            video_url = media.get("video_url", "")
            if video_url:
                streams.append(StreamInfo(
                    url=video_url,
                    mime_type="video/mp4",
                    quality=f"{media.get('dimensions', {}).get('height', '')}p",
                    width=media.get("dimensions", {}).get("width"),
                    height=media.get("dimensions", {}).get("height"),
                    has_audio=True,
                    has_video=True,
                    format_id="video_main",
                    ext="mp4",
                ))
        else:
            display_url = media.get("display_url", "")
            if display_url:
                streams.append(StreamInfo(
                    url=display_url,
                    mime_type="image/jpeg",
                    quality=f"{media.get('dimensions', {}).get('height', '')}p",
                    width=media.get("dimensions", {}).get("width"),
                    height=media.get("dimensions", {}).get("height"),
                    has_audio=False,
                    has_video=False,
                    format_id="image_main",
                    ext="jpg",
                ))

        # Carousel (sidecar)
        if typename == "GraphSidecar":
            sidecar_edges = media.get("edge_sidecar_to_children", {}).get("edges", [])
            for i, edge in enumerate(sidecar_edges):
                node = edge.get("node", {})
                if node.get("is_video"):
                    vid_url = node.get("video_url", "")
                    if vid_url:
                        streams.append(StreamInfo(
                            url=vid_url,
                            mime_type="video/mp4",
                            quality=f"{node.get('dimensions', {}).get('height', '')}p",
                            width=node.get("dimensions", {}).get("width"),
                            height=node.get("dimensions", {}).get("height"),
                            has_audio=True,
                            has_video=True,
                            format_id=f"sidecar_video_{i}",
                            ext="mp4",
                        ))
                else:
                    img_url = node.get("display_url", "")
                    if img_url:
                        streams.append(StreamInfo(
                            url=img_url,
                            mime_type="image/jpeg",
                            quality=f"{node.get('dimensions', {}).get('height', '')}p",
                            width=node.get("dimensions", {}).get("width"),
                            height=node.get("dimensions", {}).get("height"),
                            has_audio=False,
                            has_video=False,
                            format_id=f"sidecar_image_{i}",
                            ext="jpg",
                        ))

        thumbnail = media.get("display_url", media.get("thumbnail_src", ""))

        return MediaResult(
            url=url,
            title=title[:200] if title else "",
            thumbnail=thumbnail,
            duration=int(media.get("video_duration", 0)) or None,
            uploader=owner.get("username", ""),
            view_count=media.get("video_view_count"),
            platform="instagram",
            media_id=media.get("shortcode", media.get("id", "")),
            streams=streams,
        )

"""Solenz Downloader - YouTube medya URL cikarici (v3 - ANDROID_VR).

ANDROID_VR (Oculus Quest) InnerTube istemcisi kullanarak
EN YUKSEK kalitede (4K'ya kadar) dogrudan medya URL'leri cikarir.
Imza cozme gerektirmez - dogrudan URL'ler doner.

Strateji:
  1. Web sayfasindan visitorData ve signatureTimestamp al
  2. ANDROID_VR istemcisi ile InnerTube /player API cagir
  3. Dogrudan URL'li tum formatlar (2160p/1440p/1080p/720p + ses)
  4. Yedek: WEB_KIDS -> WEB_REMIX -> web sayfasi
"""

from __future__ import annotations

import json
import logging
import os
import glob
import re
from typing import Any
from urllib.parse import unquote, parse_qs, quote


from .base import BaseExtractor, registry
from ..core.models import MediaResult, StreamInfo, YouTubeSearchResult
from ..exceptions import ExtractionError, AgeGateError
from ..utils.headers import get_youtube_headers
from ..utils.cookies import CookiePool

logger = logging.getLogger("solenz.youtube")

# Havuzdan rastgele cerez cekmek icin pool nesnesi olusturalim
cookie_pool = CookiePool(directory="cookies")



# --------------------------------------------------------------------------- #
#  InnerTube Istemci Profilleri
# --------------------------------------------------------------------------- #
_ANDROID_VR = {
    "context": {
        "client": {
            "hl": "en",
            "gl": "US",
            "clientName": "ANDROID_VR",
            "clientVersion": "1.60.19",
            "androidSdkVersion": 34,
            "userAgent": "com.google.android.apps.youtube.vr.oculus/1.60.19 (Linux; U; Android 14) gzip",
            "osName": "Android",
            "osVersion": "14",
            "deviceMake": "Oculus",
            "deviceModel": "Quest 3",
        }
    },
    "headers": {
        "User-Agent": "com.google.android.apps.youtube.vr.oculus/1.60.19 (Linux; U; Android 14) gzip",
        "X-YouTube-Client-Name": "28",
        "X-YouTube-Client-Version": "1.60.19",
    },
}

_FALLBACK_CLIENTS = [
    {
        "name": "WEB",
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "WEB",
                "clientVersion": "2.20250115.01.00",
                "platform": "DESKTOP",
            }
        },
        "headers": {
            "X-YouTube-Client-Name": "1",
            "X-YouTube-Client-Version": "2.20250115.01.00",
        },
    },
    {
        "name": "WEB_KIDS",
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "WEB_KIDS",
                "clientVersion": "2.20250113.00.00",
                "platform": "DESKTOP",
            }
        },
        "headers": {
            "X-YouTube-Client-Name": "76",
            "X-YouTube-Client-Version": "2.20250113.00.00",
        },
    },
    {
        "name": "WEB_REMIX",
        "context": {
            "client": {
                "hl": "en", "gl": "US",
                "clientName": "WEB_REMIX",
                "clientVersion": "1.20250113.01.00",
                "platform": "DESKTOP",
            }
        },
        "headers": {
            "X-YouTube-Client-Name": "67",
            "X-YouTube-Client-Version": "1.20250113.01.00",
            "Referer": "https://music.youtube.com/",
            "Origin": "https://music.youtube.com",
        },
    },
]


@registry.register
class YouTubeExtractor(BaseExtractor):
    """YouTube video/ses akis linklerini en yuksek kalitede cikarir."""

    PLATFORM_NAME = "youtube"

    VALID_URL_PATTERNS = [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(?:https?://)?youtu\.be/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+",
        r"(?:https?://)?music\.youtube\.com/watch\?v=[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/live/[\w-]+",
    ]

    # ================================================================== #
    #  ANA CIKARMA
    # ================================================================== #

    def extract(self, url: str) -> MediaResult:
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ExtractionError(f"YouTube video ID cikarilmadi: {url}")

        logger.info("YouTube video ID: %s", video_id)

        # Adim 1: Web sayfasindan visitor data + sts al
        visitor_data, sts = self._get_visitor_data(video_id)

        # Cerez havuzunda cerez varsa, WEB (Desktop) istemcisi cerezler ile %100 calisir!
        if cookie_pool.pool:
            logger.info("Cerez havuzu aktif! WEB istemcileri deneniyor...")
            for fallback in _FALLBACK_CLIENTS:
                try:
                    result = self._extract_with_client(
                        video_id, url, visitor_data, sts, fallback
                    )
                    if result.streams:
                        return result
                except Exception as e:
                    logger.warning("%s basarisiz: %s", fallback["name"], e)

        # Adim 2: ANDROID_VR ile dene
        try:
            result = self._extract_android_vr(video_id, url, visitor_data, sts)
            if result.streams:
                url_streams = [s for s in result.streams if s.url]
                logger.info(
                    "ANDROID_VR: %d akis (%d URL'li). En iyi: %s",
                    len(result.streams), len(url_streams),
                    result.streams[0].resolution if result.streams else "?"
                )
                return result
        except AgeGateError:
            raise
        except Exception as e:
            logger.warning("ANDROID_VR basarisiz: %s", e)

        # Adim 3: Yedek istemciler (cerez yoksa)
        for fallback in _FALLBACK_CLIENTS:
            try:
                result = self._extract_with_client(
                    video_id, url, visitor_data, sts, fallback
                )
                if result.streams:
                    return result
            except Exception as e:
                logger.warning("%s basarisiz: %s", fallback["name"], e)

        # Adim 4: Web sayfasindan cikarma
        try:
            result = self._extract_from_webpage(video_id, url)
            if result.streams:
                return result
        except Exception as e:
            logger.warning("Web sayfasi basarisiz: %s", e)

        # Adim 5: yt-dlp ile cikarma (Garantili Son Yontem)
        try:
            logger.info("yt-dlp ile cikarma deneniyor...")
            result = self._extract_with_ytdlp(video_id, url)
            if result and result.streams:
                logger.info("yt-dlp basariyla %d akis cikardi!", len(result.streams))
                return result
        except Exception as e:
            logger.warning("yt-dlp ile cikarma basarisiz: %s", e)

        raise ExtractionError(f"Hicbir yontemle akis cikarilmadi: {video_id}")

    # ================================================================== #
    #  VISITOR DATA VE STS
    # ================================================================== #

    def _get_visitor_data(self, video_id: str) -> tuple[str, int]:
        """visitorData ve signatureTimestamp cikarir.
        
        Render sunucusu gibi bulut IP'lerinde YouTube watch html sayfasini engelledigi icin
        visitorData bilgisi dogrudan InnerTube visitor_id API'sinden alinir.
        """
        visitor_data = ""
        sts = 20648

        # 1. InnerTube API'sinden visitorData al (Engellenmeyen %100 API)
        try:
            v_url = "https://www.youtube.com/youtubei/v1/visitor_id"
            payload = {
                "context": {
                    "client": {
                        "hl": "en",
                        "gl": "US",
                        "clientName": "ANDROID",
                        "clientVersion": "19.05.36",
                    }
                }
            }
            v_resp = self.client.post(v_url, json_data=payload, timeout=10)
            if v_resp.status_code == 200:
                v_json = v_resp.json()
                visitor_data = v_json.get("responseContext", {}).get("visitorData", "")
                if visitor_data:
                    # Eger visitor_data basariyla alindiysa web sayfasini cekmeye gerek yok (Hizli Baslangic)
                    return visitor_data, sts
        except Exception as e:
            logger.warning("visitor_id API hatasi: %s", e)

        # 2. Web sayfasindan sts al (varsa)
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = get_youtube_headers(referer=watch_url)
        headers["Cookie"] = cookie_pool.get_random_cookie_string()

        try:
            resp = self.client.get(watch_url, headers=headers, timeout=10)
            html = resp.text

            if not visitor_data:
                vd_match = re.search(r'"VISITOR_DATA"\s*:\s*"([^"]+)"', html)
                if vd_match:
                    visitor_data = vd_match.group(1)

            # Player JS URL'sinden sts cikar
            js_match = re.search(r'"(/s/player/[^"]+base\.js)"', html)
            if js_match:
                try:
                    js_resp = self.client.get(
                        f"https://www.youtube.com{js_match.group(1)}", timeout=10
                    )
                    sts_match = re.search(r'signatureTimestamp["\s:]+(\d+)', js_resp.text)
                    if sts_match:
                        sts = int(sts_match.group(1))
                except Exception:
                    pass

            if not sts or sts == 20648:
                sts_match = re.search(r'"STS"\s*:\s*(\d+)', html)
                if sts_match:
                    sts = int(sts_match.group(1))

        except Exception as e:
            logger.warning("Web sayfasindan STS cikarilamadi: %s", e)

        logger.debug("visitorData: %s..., sts: %d", visitor_data[:30], sts)
        return visitor_data, sts or 20648

    # ================================================================== #
    #  ANDROID_VR ISTEMCISI (ANA YONTEM)
    # ================================================================== #

    def _extract_android_vr(
        self, video_id: str, url: str, visitor_data: str, sts: int
    ) -> MediaResult:
        """ANDROID_VR istemcisi ile dogrudan URL'li akislari cikarir."""
        context = json.loads(json.dumps(_ANDROID_VR["context"]))
        if visitor_data:
            context["client"]["visitorData"] = visitor_data

        api_url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
        payload = {
            "videoId": video_id,
            "context": context,
            "playbackContext": {
                "contentPlaybackContext": {
                    "signatureTimestamp": sts,
                }
            },
            "contentCheckOk": True,
            "racyCheckOk": True,
        }

        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com/",
        }
        headers.update(_ANDROID_VR["headers"])
        if visitor_data:
            headers["X-Goog-Visitor-Id"] = visitor_data

        resp = self.client.post(api_url, headers=headers, json_data=payload, timeout=20)

        if resp.status_code != 200:
            raise ExtractionError(f"ANDROID_VR API hatasi ({resp.status_code})")

        data = resp.json()
        self._check_playability(data, video_id)

        streams = self._extract_streams(data, client_name="ANDROID_VR")
        vd = data.get("videoDetails", {})
        micro = data.get("microformat", {}).get("playerMicroformatRenderer", {})

        return self._build_result(vd, micro, streams, video_id, url)

    # ================================================================== #
    #  YEDEK ISTEMCI
    # ================================================================== #

    def _extract_with_client(
        self, video_id: str, url: str, visitor_data: str, sts: int,
        client_cfg: dict[str, Any],
    ) -> MediaResult:
        context = json.loads(json.dumps(client_cfg["context"]))
        if visitor_data:
            context["client"]["visitorData"] = visitor_data

        api_url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
        payload = {
            "videoId": video_id,
            "context": context,
            "playbackContext": {
                "contentPlaybackContext": {"signatureTimestamp": sts}
            },
            "contentCheckOk": True,
            "racyCheckOk": True,
        }

        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com/",
        }
        
        # Sadece WEB tabanli istemciler icin Cookie gonder
        if client_cfg["name"].startswith("WEB"):
            headers["Cookie"] = cookie_pool.get_random_cookie_string()
            
        headers.update(client_cfg.get("headers", {}))
        if visitor_data:
            headers["X-Goog-Visitor-Id"] = visitor_data

        resp = self.client.post(api_url, headers=headers, json_data=payload, timeout=20)
        if resp.status_code != 200:
            raise ExtractionError(f"{client_cfg['name']} ({resp.status_code})")

        data = resp.json()
        self._check_playability(data, video_id)

        streams = self._extract_streams(data, client_name=client_cfg["name"])
        vd = data.get("videoDetails", {})

        return self._build_result(vd, {}, streams, video_id, url)

    # ================================================================== #
    #  WEB SAYFASI (SON YEDEK)
    # ================================================================== #

    def _extract_from_webpage(self, video_id: str, url: str) -> MediaResult:
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = get_youtube_headers(referer=watch_url)
        headers["Cookie"] = cookie_pool.get_random_cookie_string()

        resp = self.client.get(watch_url, headers=headers)
        if resp.status_code != 200:
            raise ExtractionError(f"Sayfa indirilemedi ({resp.status_code})")

        m = re.search(
            r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;", resp.text, re.DOTALL
        )
        if not m:
            raise ExtractionError("ytInitialPlayerResponse bulunamadi")

        data = json.loads(m.group(1))
        self._check_playability(data, video_id)

        streams = self._extract_streams(data, client_name="WEB")
        vd = data.get("videoDetails", {})
        micro = data.get("microformat", {}).get("playerMicroformatRenderer", {})

        return self._build_result(vd, micro, streams, video_id, url)

    # ================================================================== #
    #  YT-DLP ILE CIKARMA (GARANTILI YEDEK)
    # ================================================================== #

    def _extract_with_ytdlp(self, video_id: str, url: str) -> MediaResult:
        """yt-dlp kütüphanesini kullanarak YouTube akışlarını ve metadataları çıkarır."""
        try:
            import yt_dlp
        except ImportError:
            raise ExtractionError("yt-dlp kütüphanesi yüklü değil")

        txt_files = glob.glob("cookies/*.txt")
        cookie_file = txt_files[0] if txt_files else None

        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "nocheckcertificate": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web", "tv"],
                    "player_skip": ["webpage", "configs"],
                }
            },
        }

        if cookie_file and os.path.exists(cookie_file):
            ydl_opts["cookiefile"] = cookie_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise ExtractionError("yt-dlp metadata alamadi")

                title = info.get("title", video_id)
                duration = info.get("duration")
                uploader = info.get("uploader")
                thumbnail = info.get("thumbnail")
                view_count = info.get("view_count")
                description = info.get("description")

                streams: list[StreamInfo] = []
                for fmt in info.get("formats", []):
                    fmt_url = fmt.get("url")
                    if not fmt_url:
                        continue

                    height = fmt.get("height")
                    width = fmt.get("width")
                    format_id = fmt.get("format_id", "")
                    ext = fmt.get("ext", "mp4")
                    vcodec = fmt.get("vcodec", "none")
                    acodec = fmt.get("acodec", "none")
                    filesize = fmt.get("filesize") or fmt.get("filesize_approx")
                    fps = fmt.get("fps")
                    bitrate = fmt.get("tbr") or fmt.get("vbr") or fmt.get("abr")

                    has_video = vcodec != "none"
                    has_audio = acodec != "none"

                    res = f"{height}p" if height else ("Audio" if has_audio and not has_video else None)

                    streams.append(
                        StreamInfo(
                            url=fmt_url,
                            format_id=format_id,
                            ext=ext,
                            resolution=res,
                            height=height,
                            width=width,
                            filesize=filesize,
                            fps=fps,
                            bitrate=int(bitrate) if bitrate else None,
                            has_video=has_video,
                            has_audio=has_audio,
                            vcodec=vcodec,
                            acodec=acodec,
                        )
                    )

                streams.sort(key=lambda s: (s.height or 0, s.bitrate or 0), reverse=True)

                return MediaResult(
                    media_id=video_id,
                    title=title,
                    url=url,
                    thumbnail=thumbnail,
                    uploader=uploader,
                    duration=duration,
                    view_count=view_count,
                    description=description,
                    streams=streams,
                    extractor="youtube (yt-dlp)",
                )
        except Exception as e:
            raise ExtractionError(f"yt-dlp hatasi: {e}") from e


    # ================================================================== #
    #  AKIS AYRISTIRMA
    # ================================================================== #

    def _extract_streams(self, data: dict[str, Any], *, client_name: str = "?") -> list[StreamInfo]:
        sd = data.get("streamingData", {})
        if not sd:
            return []

        streams: list[StreamInfo] = []

        for fmt in sd.get("formats", []):
            s = self._parse_format(fmt, combined=True, client_name=client_name)
            if s:
                streams.append(s)

        for fmt in sd.get("adaptiveFormats", []):
            s = self._parse_format(fmt, combined=False, client_name=client_name)
            if s:
                streams.append(s)

        # Kaliteye gore sirala
        streams.sort(key=lambda s: (s.height or 0, s.bitrate or 0), reverse=True)
        return streams

    def _parse_format(self, fmt: dict[str, Any], *, combined: bool, client_name: str = "?") -> StreamInfo | None:
        # URL belirle
        url = fmt.get("url", "")

        if not url:
            cipher = fmt.get("signatureCipher") or fmt.get("cipher", "")
            if cipher:
                url = self._try_cipher(cipher)

        if not url:
            return None

        # MIME + codec
        mime_type = fmt.get("mimeType", "")
        base_mime = mime_type.split(";")[0].strip() if mime_type else ""
        codecs = ""
        if "codecs=" in mime_type:
            cm = re.search(r'codecs="([^"]+)"', mime_type)
            codecs = cm.group(1) if cm else ""

        has_video = base_mime.startswith("video/")
        has_audio = base_mime.startswith("audio/") or (combined and has_video)

        video_codec = ""
        audio_codec = ""
        for c in [x.strip() for x in codecs.split(",")]:
            if c.startswith(("avc", "vp9", "vp09", "av01", "av1", "hev", "hvc")):
                video_codec = c
            elif c.startswith(("mp4a", "opus", "vorbis", "flac")):
                audio_codec = c

        quality = fmt.get("qualityLabel", fmt.get("quality", ""))
        ext = self._mime_to_ext(base_mime)

        filesize = None
        if "contentLength" in fmt:
            try:
                filesize = int(fmt["contentLength"])
            except (ValueError, TypeError):
                pass
        # contentLength yoksa approximate olarak hesapla (bitrate * duration) ama duration burada yok!

        return StreamInfo(
            url=url,
            mime_type=base_mime,
            quality=quality,
            width=fmt.get("width"),
            height=fmt.get("height"),
            fps=fmt.get("fps"),
            bitrate=fmt.get("bitrate"),
            filesize=filesize,
            codec=video_codec or audio_codec,
            audio_codec=audio_codec if has_video else "",
            has_audio=has_audio,
            has_video=has_video,
            format_id=str(fmt.get("itag", "")),
            ext=ext,
            extra={
                "itag": fmt.get("itag"),
                "averageBitrate": fmt.get("averageBitrate"),
                "audioSampleRate": fmt.get("audioSampleRate"),
                "audioChannels": fmt.get("audioChannels"),
                "combined": combined,
                "client": client_name,
            },
        )

    def _try_cipher(self, cipher_str: str) -> str:
        """signatureCipher'dan URL cikarma denemesi (yedek)."""
        params = parse_qs(cipher_str)
        url = params.get("url", [""])[0]
        s = params.get("s", [""])[0]
        sp = params.get("sp", ["sig"])[0]

        if not url:
            return ""

        url = unquote(url)

        if not s:
            return url

        # Imza cozme (basit deneme)
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}{sp}={quote(s, safe='')}"

    # ================================================================== #
    #  YARDIMCI
    # ================================================================== #

    def _check_playability(self, data: dict, video_id: str) -> None:
        ps = data.get("playabilityStatus", {})
        status = ps.get("status", "")

        if status == "LOGIN_REQUIRED":
            reason = ps.get("reason", "")
            if "age" in reason.lower():
                raise AgeGateError(f"Yas sinirli: {video_id}")
            raise ExtractionError(f"Giris gerekli: {reason}")

        if status == "UNPLAYABLE":
            reason = ps.get("reason", "Bilinmeyen neden")
            raise ExtractionError(f"Oynatilabilir degil: {reason}")

        if status not in ("OK", "LIVE_STREAM_OFFLINE", ""):
            reason = ps.get("reason", status)
            logger.warning("Beklenmeyen durum: %s", reason)

    def _build_result(
        self, vd: dict, micro: dict, streams: list[StreamInfo],
        video_id: str, url: str,
    ) -> MediaResult:
        thumbnail = ""
        thumbs = vd.get("thumbnail", {}).get("thumbnails", [])
        if thumbs:
            thumbnail = thumbs[-1].get("url", "")

        duration = None
        try:
            duration = int(vd.get("lengthSeconds", 0)) or None
        except (ValueError, TypeError):
            pass

        view_count = None
        vc = vd.get("viewCount", "")
        if isinstance(vc, str) and vc.isdigit():
            view_count = int(vc)

        upload_date = micro.get("uploadDate", "")
        if upload_date and "T" in upload_date:
            upload_date = upload_date.split("T")[0]

        return MediaResult(
            url=url,
            title=vd.get("title", ""),
            description=vd.get("shortDescription", ""),
            thumbnail=thumbnail,
            duration=duration,
            uploader=vd.get("author", ""),
            upload_date=upload_date,
            view_count=view_count,
            platform="youtube",
            media_id=video_id,
            streams=streams,
            extra={
                "channel_id": vd.get("channelId", ""),
                "is_live": vd.get("isLiveContent", False),
                "keywords": vd.get("keywords", []),
            },
        )

    @staticmethod
    def _extract_video_id(url: str) -> str:
        patterns = [
            r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/|/live/)([a-zA-Z0-9_-]{11})",
            r"^([a-zA-Z0-9_-]{11})$",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return ""

    # ================================================================== #
    #  ARAMA ÖZELLIĞI
    # ================================================================== #

    def search(self, query: str, limit: int = 10) -> list[YouTubeSearchResult]:
        """YouTube'da arama yapar ve sonuçları döner."""
        logger.info("YouTube arama: %s (limit=%d)", query, limit)
        
        # Basit bir web istemcisi kullanarak arama yap
        search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
        headers = get_youtube_headers(referer="https://www.youtube.com/")
        headers["Cookie"] = cookie_pool.get_random_cookie_string()
        
        resp = self.client.get(search_url, headers=headers, timeout=15)
        html = resp.text
        
        # ytInitialData'yı bul
        match = re.search(r"ytInitialData\s*=\s*(\{.+?\});\s*(?:</script>|$)", html, re.DOTALL)
        if not match:
            raise ExtractionError("Arama verisi bulunamadı (ytInitialData)")
        
        data = json.loads(match.group(1))
        results: list[YouTubeSearchResult] = []
        
        # Sonuçları ayrıştır
        contents = (
            data.get("contents", {})
            .get("twoColumnSearchResultsRenderer", {})
            .get("primaryContents", {})
            .get("sectionListRenderer", {})
            .get("contents", [])
        )
        
        for section in contents:
            if "itemSectionRenderer" in section:
                items = section["itemSectionRenderer"].get("contents", [])
                for item in items:
                    if "videoRenderer" in item:
                        vr = item["videoRenderer"]
                        
                        # Video ID
                        video_id = vr.get("videoId", "")
                        if not video_id:
                            continue
                        
                        # Başlık
                        title_runs = vr.get("title", {}).get("runs", [])
                        title = "".join([r.get("text", "") for r in title_runs])
                        
                        # Küçük resim
                        thumbs = vr.get("thumbnail", {}).get("thumbnails", [])
                        thumbnail = thumbs[-1].get("url", "") if thumbs else ""
                        
                        # Yükleyici
                        owner_runs = vr.get("ownerText", {}).get("runs", [])
                        uploader = "".join([r.get("text", "") for r in owner_runs])
                        
                        # Süre (saniye cinsinden)
                        duration_text = vr.get("lengthText", {}).get("simpleText", "")
                        duration = self._parse_duration(duration_text)
                        
                        # Görüntülenme sayısı
                        view_count_str = vr.get("viewCountText", {}).get("simpleText", "")
                        view_count = self._parse_view_count(view_count_str)
                        
                        # Açıklama (kısa)
                        desc_snippet = vr.get("detailedMetadataSnippets", [{}])[0].get("snippetText", {}).get("runs", [])
                        description = "".join([r.get("text", "") for r in desc_snippet])
                        
                        results.append(
                            YouTubeSearchResult(
                                video_id=video_id,
                                title=title,
                                url=f"https://www.youtube.com/watch?v={video_id}",
                                thumbnail=thumbnail,
                                uploader=uploader,
                                duration=duration,
                                view_count=view_count,
                                description=description,
                            )
                        )
                        
                        if len(results) >= limit:
                            break
            if len(results) >= limit:
                break
        
        logger.info("Arama sonucu: %d video bulundu", len(results))
        return results[:limit]

    def _parse_duration(self, duration_text: str) -> int | None:
        """Süre metnini saniyeye çevirir (ör: "3:45" -> 225)."""
        if not duration_text:
            return None
        try:
            parts = list(map(int, duration_text.split(":")))
            if len(parts) == 3:  # saat:dakika:saniye
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:  # dakika:saniye
                return parts[0] * 60 + parts[1]
            elif len(parts) == 1:  # sadece saniye
                return parts[0]
        except (ValueError, TypeError):
            pass
        return None

    def _parse_view_count(self, view_count_text: str) -> int | None:
        """Görüntülenme sayısını metinden sayıya çevirir (ör: "1.2M views" -> 1200000)."""
        if not view_count_text:
            return None
        try:
            # Sadece sayıları al (örn: "1.2M views" -> "1.2M")
            count_str = view_count_text.split()[0].replace(",", "").replace(".", "")
            if "M" in count_str:
                return int(float(count_str.replace("M", "")) * 1_000_000)
            elif "K" in count_str:
                return int(float(count_str.replace("K", "")) * 1_000)
            elif "B" in count_str:
                return int(float(count_str.replace("B", "")) * 1_000_000_000)
            else:
                return int(count_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _mime_to_ext(mime: str) -> str:
        return {
            "video/mp4": "mp4",
            "video/webm": "webm",
            "video/3gpp": "3gp",
            "audio/mp4": "m4a",
            "audio/webm": "webm",
            "audio/mpeg": "mp3",
        }.get(mime, "mp4")

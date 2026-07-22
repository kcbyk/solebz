"""Solenz Downloader - Veri modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StreamInfo:
    """Tek bir medya akisinin (video veya ses) bilgilerini temsil eder."""

    url: str
    mime_type: str = ""              # "video/mp4", "audio/webm" vb.
    quality: str = ""                # "1080p", "720p", "audio_only" vb.
    width: int | None = None
    height: int | None = None
    fps: int | None = None
    bitrate: int | None = None       # bps
    filesize: int | None = None      # byte
    codec: str = ""                  # "avc1.4d401f", "opus" vb.
    audio_codec: str = ""            # video+ses birlesik akim icin
    has_audio: bool = True
    has_video: bool = True
    format_id: str = ""              # platform'un kendi format tanimlayicisi
    ext: str = ""                    # "mp4", "webm", "m4a"
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def resolution(self) -> str:
        """Cozunurluk etiketini dondurur: '1920x1080' veya 'audio_only'."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        if self.quality:
            return self.quality
        return "unknown"

    @property
    def is_video(self) -> bool:
        return self.has_video

    @property
    def is_audio_only(self) -> bool:
        return self.has_audio and not self.has_video

    def __repr__(self) -> str:
        parts = [f"StreamInfo({self.resolution}"]
        if self.ext:
            parts.append(f" .{self.ext}")
        if self.codec:
            parts.append(f" codec={self.codec}")
        if self.bitrate:
            parts.append(f" {self.bitrate // 1000}kbps")
        if self.filesize:
            mb = self.filesize / (1024 * 1024)
            parts.append(f" {mb:.1f}MB")
        parts.append(")")
        return "".join(parts)


@dataclass
class YouTubeSearchResult:
    """YouTube arama sonucu."""
    video_id: str
    title: str
    url: str
    thumbnail: str
    uploader: str
    duration: int | None = None
    view_count: int | None = None
    description: str = ""


@dataclass
class MediaResult:
    """Bir medya iceriginin tum bilgilerini ve akislarini icerir."""

    url: str                                      # orijinal sayfa URL'si
    title: str = ""
    description: str = ""
    thumbnail: str = ""                            # kucuk resim URL'si
    duration: int | None = None                    # saniye
    uploader: str = ""
    upload_date: str = ""                          # "YYYY-MM-DD"
    view_count: int | None = None
    platform: str = ""                             # "youtube", "tiktok" vb.
    media_id: str = ""                             # platformun icerigi tanimlayan ID'si
    streams: list[StreamInfo] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    # -- Yardimci metotlar -------------------------------------------------- #

    def best_video(self, *, prefer_ext: str = "mp4") -> StreamInfo | None:
        """En yuksek cozunurluklu video akisini dondurur."""
        video_streams = [s for s in self.streams if s.has_video]
        if not video_streams:
            return None

        def _sort_key(s: StreamInfo) -> tuple[int, int, int]:
            height = s.height or 0
            width = s.width or 0
            ext_pref = 1 if s.ext == prefer_ext else 0
            return (height, width, ext_pref)

        return max(video_streams, key=_sort_key)

    def best_audio(self, *, prefer_ext: str = "m4a") -> StreamInfo | None:
        """En yuksek bit hizindaki saf ses akisini dondurur.

        Oncelik: saf ses akislari (audio_only) > birlesik akislar.
        """
        # Once saf ses akislari
        audio_only = [s for s in self.streams if s.is_audio_only]
        if audio_only:
            def _sort_key(s: StreamInfo) -> tuple[int, int]:
                br = s.bitrate or 0
                ext_pref = 1 if s.ext == prefer_ext else 0
                return (br, ext_pref)
            return max(audio_only, key=_sort_key)

        # Saf ses yoksa birlesik akislardan en iyisi
        audio_streams = [s for s in self.streams if s.has_audio]
        if audio_streams:
            return max(audio_streams, key=lambda s: (s.bitrate or 0, 1 if s.ext == prefer_ext else 0))

        return None

    def best_stream(self, *, prefer_ext: str = "mp4") -> StreamInfo | None:
        """En iyi akisi dondurur: video+ses birlesik > en iyi video > en iyi ses."""
        combined = [s for s in self.streams if s.has_video and s.has_audio]
        if combined:
            return max(
                combined,
                key=lambda s: (s.height or 0, s.width or 0, 1 if s.ext == prefer_ext else 0),
            )
        return self.best_video(prefer_ext=prefer_ext) or self.best_audio()

    def filter_streams(
        self,
        *,
        min_height: int | None = None,
        max_height: int | None = None,
        ext: str | None = None,
        video_only: bool = False,
        audio_only: bool = False,
    ) -> list[StreamInfo]:
        """Akislari filtreleyerek dondurur."""
        result: list[StreamInfo] = []
        for s in self.streams:
            if video_only and not s.has_video:
                continue
            if audio_only and not s.is_audio_only:
                continue
            if ext and s.ext != ext:
                continue
            if min_height and (s.height or 0) < min_height:
                continue
            if max_height and (s.height or 0) > max_height:
                continue
            result.append(s)
        return result

    def __repr__(self) -> str:
        return (
            f"MediaResult(title={self.title!r}, "
            f"platform={self.platform!r}, "
            f"streams={len(self.streams)})"
        )

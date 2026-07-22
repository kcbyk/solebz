"""Solenz Downloader - Extractors alt paketi.

Tum extractor modulleri import edildiginde otomatik olarak
global registry'ye kaydedilir.
"""

from .base import BaseExtractor, ExtractorRegistry, registry
from .youtube import YouTubeExtractor
from .tiktok import TikTokExtractor
from .instagram import InstagramExtractor

__all__ = [
    "BaseExtractor",
    "ExtractorRegistry",
    "registry",
    "YouTubeExtractor",
    "TikTokExtractor",
    "InstagramExtractor",
]

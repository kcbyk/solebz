"""Solenz Downloader - Temel Extractor altyapisi.

Tum platform-ozel extractor'lar bu sinifi miras alir.
Registry mekanizmasi ile URL'ye gore dogru extractor otomatik secilir.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, ClassVar
from urllib.parse import urlparse, parse_qs

from ..core.client import SolenzClient
from ..core.models import MediaResult, StreamInfo
from ..exceptions import ExtractionError

logger = logging.getLogger("solenz.extractor")


class BaseExtractor(ABC):
    """Tum platform extractor'larinin soyut temel sinifi."""

    # Alt siniflar bunlari override etmeli
    PLATFORM_NAME: ClassVar[str] = ""
    VALID_URL_PATTERNS: ClassVar[list[str]] = []

    def __init__(self, client: SolenzClient) -> None:
        self.client = client

    # -- Soyut metotlar ----------------------------------------------------- #

    @abstractmethod
    def extract(self, url: str) -> MediaResult:
        """Verilen URL'den medya bilgilerini ve akis linklerini cikarir."""
        ...

    # -- URL eslestirme ----------------------------------------------------- #

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Bu extractor'un verilen URL'yi isleyip isleyemeyecegini kontrol eder."""
        for pattern in cls.VALID_URL_PATTERNS:
            if re.search(pattern, url):
                return True
        return False

    # -- HTML / JSON yardimcilari ------------------------------------------- #

    @staticmethod
    def _find_json_in_html(html: str, variable_name: str) -> dict[str, Any] | None:
        """HTML icinden JavaScript degiskenine atanmis JSON nesnesini bulur.

        Ornek: ytInitialPlayerResponse = {...};
        """
        # Desen 1: var name = {...};
        pattern = rf'{variable_name}\s*=\s*(\{{.*?\}});'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        # Desen 2: var name = {...}; (noktalı virgulsuz, satirsonu ile biten)
        pattern2 = rf'{variable_name}\s*=\s*(\{{.+?\}})\s*;\s*(?:var|let|const|</script>)'
        match2 = re.search(pattern2, html, re.DOTALL)
        if match2:
            try:
                return json.loads(match2.group(1))
            except Exception:
                pass

        return None

    @staticmethod
    def _extract_between(text: str, start: str, end: str) -> str:
        """Iki isaretci arasindaki metni cikarir."""
        idx_start = text.find(start)
        if idx_start == -1:
            return ""
        idx_start += len(start)
        idx_end = text.find(end, idx_start)
        if idx_end == -1:
            return text[idx_start:]
        return text[idx_start:idx_end]

    @staticmethod
    def _parse_query_string(url: str) -> dict[str, str]:
        """URL'nin query parametrelerini sozluk olarak dondurur."""
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        return {k: v[0] for k, v in qs.items()}

    @staticmethod
    def _safe_json_loads(text: str) -> Any:
        """JSON parse hatalarini yakalar."""
        try:
            import json as _json
            return _json.loads(text)
        except (ValueError, TypeError):
            return None

    def _get_page(self, url: str, **kwargs: Any) -> str:
        """Sayfa HTML'sini indirir."""
        resp = self.client.get(url, **kwargs)
        if resp.status_code != 200:
            raise ExtractionError(
                f"Sayfa indirilemedi ({resp.status_code}): {url}"
            )
        return resp.text

    def _get_json(self, url: str, **kwargs: Any) -> Any:
        """JSON yaniti alir."""
        resp = self.client.get(url, **kwargs)
        if resp.status_code != 200:
            raise ExtractionError(
                f"JSON endpoint'i hatali ({resp.status_code}): {url}"
            )
        return resp.json()


# -- JSON modulu import (class seviyesinde kullanmak icin) ------------------- #
import json


# =========================================================================== #
#  Extractor Registry
# =========================================================================== #

class ExtractorRegistry:
    """URL'ye gore dogru extractor'i otomatik secen kayit defteri."""

    def __init__(self) -> None:
        self._extractors: list[type[BaseExtractor]] = []

    def register(self, extractor_cls: type[BaseExtractor]) -> type[BaseExtractor]:
        """Bir extractor sinifini kayit defterine ekler. Decorator olarak kullanilabilir."""
        if extractor_cls not in self._extractors:
            self._extractors.append(extractor_cls)
            logger.debug("Extractor kayit edildi: %s", extractor_cls.PLATFORM_NAME)
        return extractor_cls

    def find(self, url: str) -> type[BaseExtractor] | None:
        """Verilen URL icin uygun extractor sinifini bulur."""
        for ext_cls in self._extractors:
            if ext_cls.can_handle(url):
                return ext_cls
        return None

    def extract(self, url: str, client: SolenzClient) -> MediaResult:
        """URL'ye gore extractor'i bulur ve medya bilgilerini cikarir."""
        ext_cls = self.find(url)
        if ext_cls is None:
            raise ExtractionError(
                f"Bu URL icin desteklenen bir extractor bulunamadi: {url}"
            )
        extractor = ext_cls(client)
        logger.info("Extractor secildi: %s -> %s", url, ext_cls.PLATFORM_NAME)
        return extractor.extract(url)

    @property
    def supported_platforms(self) -> list[str]:
        return [e.PLATFORM_NAME for e in self._extractors]

    def __repr__(self) -> str:
        return f"ExtractorRegistry(platforms={self.supported_platforms})"


# Global registry
registry = ExtractorRegistry()

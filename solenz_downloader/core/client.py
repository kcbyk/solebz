"""Solenz Downloader - TLS taklitli HTTP istemci.

curl_cffi uzerine insa edilmis, tarayici parmak izi taklidi yapan,
otomatik retry ve proxy destekli HTTP istemci.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

try:
    from curl_cffi import requests as cffi_requests
    from curl_cffi.requests import Response
    HAS_CURL_CFFI = True
except ImportError:
    import requests as cffi_requests
    from requests import Response
    HAS_CURL_CFFI = False

from ..config import (
    DEFAULT_HEADERS,
    DEFAULT_IMPERSONATE,
    DEFAULT_PROXY,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    REQUEST_DELAY,
)
from ..exceptions import SolenzError, RateLimitError
from ..utils.cookies import CookieJar
from ..utils.headers import get_headers
from ..utils.proxy import format_proxy, ProxyConfig

logger = logging.getLogger("solenz.client")


class SolenzClient:
    """TLS parmak izi taklidi yapan HTTP istemci.

    Kullanim:
        client = SolenzClient()
        resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # proxy ile:
        client = SolenzClient(proxy="socks5://192.168.1.100:1080")

        # ozel basliklar ile:
        client = SolenzClient(extra_headers={"X-Custom": "value"})
    """

    def __init__(
        self,
        *,
        impersonate: str = DEFAULT_IMPERSONATE,
        proxy: str | dict[str, str] | ProxyConfig | None = DEFAULT_PROXY,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        extra_headers: dict[str, str] | None = None,
        cookies: CookieJar | dict[str, str] | None = None,
    ) -> None:
        self.impersonate = impersonate
        self.timeout = timeout
        self.max_retries = max_retries

        # proxy yapilandirmasi
        self._proxy_dict = format_proxy(proxy)

        # oturum (session) olustur
        if HAS_CURL_CFFI:
            self._session = cffi_requests.Session(
                impersonate=self.impersonate,
                timeout=self.timeout,
            )
        else:
            self._session = cffi_requests.Session()

        # varsayilan basliklar
        self._session.headers.update(DEFAULT_HEADERS)
        if not HAS_CURL_CFFI:
            self._session.headers.update(
                {
                    "User-Agent": (
                        "Mozilla/5.0 (Linux; Android 9; K) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Mobile Safari/537.36"
                    ),
                    "Accept-Encoding": "gzip, deflate",
                }
            )
        if extra_headers:
            self._session.headers.update(extra_headers)

        # cookie yonetimi
        self._cookie_jar = CookieJar()
        if isinstance(cookies, CookieJar):
            self._cookie_jar = cookies
        elif isinstance(cookies, dict):
            for k, v in cookies.items():
                self._cookie_jar.set(k, v)

    # -- Temel HTTP metotlari ----------------------------------------------- #

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        allow_redirects: bool = True,
        timeout: int | None = None,
        stream: bool = False,
    ) -> Response:
        """HTTP GET istegi gonderir."""
        return self._request(
            "GET", url,
            headers=headers,
            params=params,
            allow_redirects=allow_redirects,
            timeout=timeout,
            stream=stream,
        )

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: Any = None,
        json_data: Any = None,
        params: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> Response:
        """HTTP POST istegi gonderir."""
        return self._request(
            "POST", url,
            headers=headers,
            data=data,
            json_data=json_data,
            params=params,
            timeout=timeout,
        )

    def head(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        allow_redirects: bool = True,
        timeout: int | None = None,
    ) -> Response:
        """HTTP HEAD istegi gonderir (dosya boyutu kontrolu vb.)."""
        return self._request(
            "HEAD", url,
            headers=headers,
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> Any:
        """GET istegi atar ve yaniti JSON olarak parse eder."""
        resp = self.get(url, headers=headers, params=params, timeout=timeout)
        return resp.json()

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_data: Any = None,
        timeout: int | None = None,
    ) -> Any:
        """POST istegi atar ve yaniti JSON olarak parse eder."""
        resp = self.post(url, headers=headers, json_data=json_data, timeout=timeout)
        return resp.json()

    # -- Dahili istek motoru ------------------------------------------------ #

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: Any = None,
        json_data: Any = None,
        params: dict[str, str] | None = None,
        allow_redirects: bool = True,
        timeout: int | None = None,
        stream: bool = False,
    ) -> Response:
        """Retry mekanizmali dahili istek fonksiyonu."""
        merged_headers = dict(self._session.headers)
        if headers:
            merged_headers.update(headers)

        # cookie enjeksiyonu
        cookie_header = self._cookie_jar.to_header()
        if cookie_header:
            existing = merged_headers.get("Cookie", "")
            if existing:
                merged_headers["Cookie"] = f"{existing}; {cookie_header}"
            else:
                merged_headers["Cookie"] = cookie_header

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "[%s] %s %s (deneme %d/%d)",
                    method, url, f"proxy={self._proxy_dict}" if self._proxy_dict else "",
                    attempt, self.max_retries,
                )

                # Bot engelini onlemek için istekler arası gecikme
                if attempt == 1:
                    time.sleep(REQUEST_DELAY)

                kwargs: dict[str, Any] = {
                    "method": method,
                    "url": url,
                    "headers": merged_headers,
                    "allow_redirects": allow_redirects,
                    "timeout": timeout or self.timeout,
                }
                if HAS_CURL_CFFI:
                    kwargs["impersonate"] = self.impersonate

                if self._proxy_dict:
                    kwargs["proxies"] = self._proxy_dict
                else:
                    kwargs["proxies"] = {"http": "", "https": ""}
                if params:
                    kwargs["params"] = params
                if data is not None:
                    kwargs["data"] = data
                if json_data is not None:
                    kwargs["json"] = json_data
                if stream:
                    kwargs["stream"] = True

                resp: Response = self._session.request(**kwargs)

                # Set-Cookie basliklarini yakala
                if hasattr(resp, "headers"):
                    self._cookie_jar.parse_response_headers(
                        dict(resp.headers),
                        default_domain=self._extract_domain(url),
                    )

                # Hiz sinirlamasi kontrolu
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", "5"))
                    if attempt < self.max_retries:
                        logger.warning(
                            "429 Rate Limit - %d saniye bekleniyor...", retry_after
                        )
                        time.sleep(retry_after)
                        continue
                    raise RateLimitError(
                        f"Hiz sinirlamasi asildi: {url}", retry_after=retry_after
                    )

                # Sunucu hatasi -> yeniden dene
                if resp.status_code >= 500 and attempt < self.max_retries:
                    wait = RETRY_BACKOFF_FACTOR ** attempt
                    logger.warning(
                        "Sunucu hatasi %d - %.1f saniye sonra yeniden denenecek...",
                        resp.status_code, wait,
                    )
                    time.sleep(wait)
                    continue

                return resp

            except RateLimitError:
                raise
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = RETRY_BACKOFF_FACTOR ** attempt
                    logger.warning(
                        "Istek hatasi: %s - %.1f saniye sonra yeniden denenecek...",
                        str(e), wait,
                    )
                    time.sleep(wait)
                else:
                    raise SolenzError(
                        f"HTTP istegi basarisiz ({method} {url}): {e}", cause=e
                    ) from e

        raise SolenzError(
            f"Tum denemeler basarisiz ({method} {url})", cause=last_error
        )

    # -- Yardimci metotlar -------------------------------------------------- #

    @staticmethod
    def _extract_domain(url: str) -> str:
        """URL'den domain'i cikarir."""
        from urllib.parse import urlparse
        return urlparse(url).hostname or ""

    @property
    def cookies(self) -> CookieJar:
        return self._cookie_jar

    def set_proxy(self, proxy: str | dict[str, str] | ProxyConfig | None) -> None:
        """Proxy yapilandirmasini gunceller."""
        self._proxy_dict = format_proxy(proxy)

    def update_headers(self, headers: dict[str, str]) -> None:
        """Oturum basliklarini gunceller."""
        self._session.headers.update(headers)

    def close(self) -> None:
        """Oturumu kapatir."""
        try:
            self._session.close()
        except Exception:
            pass

    def __enter__(self) -> "SolenzClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        proxy_info = f", proxy={self._proxy_dict}" if self._proxy_dict else ""
        return f"SolenzClient(impersonate={self.impersonate!r}{proxy_info})"

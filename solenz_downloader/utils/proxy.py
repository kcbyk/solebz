"""Solenz Downloader - Proxy yapilandirma yardimcilari."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from ..exceptions import ProxyError


@dataclass
class ProxyConfig:
    """Proxy sunucu yapilandirmasi."""

    protocol: str = "http"        # "http", "https", "socks5", "socks5h"
    host: str = ""
    port: int = 0
    username: str | None = None
    password: str | None = None

    @property
    def url(self) -> str:
        """Proxy URL'sini dondurur: protocol://[user:pass@]host:port"""
        auth = ""
        if self.username:
            auth = self.username
            if self.password:
                auth += f":{self.password}"
            auth += "@"
        return f"{self.protocol}://{auth}{self.host}:{self.port}"

    @property
    def as_dict(self) -> dict[str, str]:
        """curl_cffi / requests icin proxy sozlugu."""
        u = self.url
        return {
            "http": u,
            "https": u,
        }

    def validate(self) -> None:
        """Yapilandirmayi dogrular."""
        if not self.host:
            raise ProxyError("Proxy host belirtilmedi.")
        if self.port <= 0 or self.port > 65535:
            raise ProxyError(f"Gecersiz proxy portu: {self.port}")
        valid_protocols = ("http", "https", "socks4", "socks5", "socks5h")
        if self.protocol not in valid_protocols:
            raise ProxyError(
                f"Gecersiz proxy protokolu: {self.protocol!r}. "
                f"Desteklenenler: {valid_protocols}"
            )

    @classmethod
    def from_url(cls, proxy_url: str) -> "ProxyConfig":
        """Proxy URL'sini parse eder.

        Ornekler:
            'socks5://192.168.1.100:1080'
            'http://user:pass@proxy.example.com:8080'
        """
        parsed = urlparse(proxy_url)
        protocol = parsed.scheme or "http"
        host = parsed.hostname or ""
        port = parsed.port or (1080 if "socks" in protocol else 8080)
        username = parsed.username
        password = parsed.password

        config = cls(
            protocol=protocol,
            host=host,
            port=port,
            username=username,
            password=password,
        )
        config.validate()
        return config

    def __repr__(self) -> str:
        masked = f"{self.protocol}://"
        if self.username:
            masked += f"{self.username}:****@"
        masked += f"{self.host}:{self.port}"
        return f"ProxyConfig({masked})"


def format_proxy(proxy: str | dict[str, str] | ProxyConfig | None) -> dict[str, str] | None:
    """Farkli proxy formatlarini curl_cffi'nin bekledigi sozluge donusturur."""
    if proxy is None:
        return None

    if isinstance(proxy, ProxyConfig):
        proxy.validate()
        return proxy.as_dict

    if isinstance(proxy, dict):
        return proxy

    if isinstance(proxy, str):
        config = ProxyConfig.from_url(proxy)
        return config.as_dict

    raise ProxyError(f"Desteklenmeyen proxy formati: {type(proxy)}")

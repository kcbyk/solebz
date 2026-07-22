"""Solenz Downloader - Cookie yonetim mekanizmasi."""

from __future__ import annotations

import http.cookiejar
import json
import time
from typing import Any


class CookieJar:
    """Basit cookie saklama, parse etme ve serialize islemi."""

    def __init__(self) -> None:
        self._jar: dict[str, dict[str, str]] = {}  # domain -> {name: value}

    # -- Ekleme / alma ------------------------------------------------------ #

    def set(self, name: str, value: str, domain: str = "") -> None:
        self._jar.setdefault(domain, {})[name] = value

    def get(self, name: str, domain: str = "") -> str | None:
        return self._jar.get(domain, {}).get(name)

    def get_all(self, domain: str = "") -> dict[str, str]:
        """Belirli bir domain icin tum cookie'leri dondurur."""
        if domain:
            return self._jar.get(domain, {}).copy()
        merged: dict[str, str] = {}
        for cookies in self._jar.values():
            merged.update(cookies)
        return merged

    def remove(self, name: str, domain: str = "") -> None:
        if domain in self._jar:
            self._jar[domain].pop(name, None)

    def clear(self, domain: str | None = None) -> None:
        if domain:
            self._jar.pop(domain, None)
        else:
            self._jar.clear()

    # -- Set-Cookie basligini parse etme ------------------------------------ #

    def parse_set_cookie(self, header_value: str, default_domain: str = "") -> None:
        """Bir 'Set-Cookie' baslik degerini parse eder ve saklar."""
        if not header_value:
            return

        parts = header_value.split(";")
        if not parts:
            return

        # ilk parca: name=value
        name_value = parts[0].strip()
        if "=" not in name_value:
            return
        name, _, value = name_value.partition("=")
        name = name.strip()
        value = value.strip()

        # domain attribute'unu ara
        domain = default_domain
        for part in parts[1:]:
            part = part.strip().lower()
            if part.startswith("domain="):
                domain = part[7:].strip().lstrip(".")
                break

        self.set(name, value, domain)

    def parse_response_headers(
        self, headers: dict[str, Any], default_domain: str = ""
    ) -> None:
        """Yanit basliklarindaki tum Set-Cookie satirlarini parse eder."""
        for key, value in headers.items():
            if key.lower() == "set-cookie":
                if isinstance(value, list):
                    for v in value:
                        self.parse_set_cookie(v, default_domain)
                else:
                    self.parse_set_cookie(str(value), default_domain)

    # -- Serialize / Deserialize -------------------------------------------- #

    def to_header(self, domain: str = "") -> str:
        """Cookie: baslik degeri olarak dondurur."""
        cookies = self.get_all(domain)
        return "; ".join(f"{k}={v}" for k, v in cookies.items())

    def to_dict(self, domain: str = "") -> dict[str, str]:
        return self.get_all(domain)

    def to_json(self) -> str:
        return json.dumps(self._jar, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "CookieJar":
        jar = cls()
        jar._jar = json.loads(data)
        return jar

    @classmethod
    def from_browser_cookie_string(cls, cookie_str: str, domain: str = "") -> "CookieJar":
        """Tarayicidan kopyalanan 'name=val; name2=val2' cookie string'ini parse eder."""
        jar = cls()
        for pair in cookie_str.split(";"):
            pair = pair.strip()
            if "=" in pair:
                name, _, value = pair.partition("=")
                jar.set(name.strip(), value.strip(), domain)
        return jar

    def __len__(self) -> int:
        return sum(len(v) for v in self._jar.values())

    def __repr__(self) -> str:
        return f"CookieJar(domains={list(self._jar.keys())}, total={len(self)})"

"""Solenz Downloader - Tarayici baslik profilleri."""

from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------------- #
#  Chrome 124 (Windows)
# --------------------------------------------------------------------------- #
CHROME_124_WINDOWS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", '
                 '"Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

# --------------------------------------------------------------------------- #
#  Chrome 124 (Android)
# --------------------------------------------------------------------------- #
CHROME_124_ANDROID: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.6367.82 Mobile Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", '
                 '"Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# --------------------------------------------------------------------------- #
#  Firefox 125 (Windows)
# --------------------------------------------------------------------------- #
FIREFOX_125_WINDOWS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}

# --------------------------------------------------------------------------- #
#  Safari 17 (macOS)
# --------------------------------------------------------------------------- #
SAFARI_17_MACOS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.4.1 Safari/605.1.15"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# --------------------------------------------------------------------------- #
#  XHR / API istekleri icin basliklar (AJAX cagrilari)
# --------------------------------------------------------------------------- #
XHR_HEADERS: dict[str, str] = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest",
}

# --------------------------------------------------------------------------- #
#  Profil secici
# --------------------------------------------------------------------------- #
PROFILES: dict[str, dict[str, str]] = {
    "chrome_windows": CHROME_124_WINDOWS,
    "chrome_android": CHROME_124_ANDROID,
    "firefox_windows": FIREFOX_125_WINDOWS,
    "safari_macos": SAFARI_17_MACOS,
    "xhr": XHR_HEADERS,
}


def get_headers(
    profile: str = "chrome_windows",
    *,
    referer: str | None = None,
    origin: str | None = None,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    """Belirtilen profildeki basliklari dondurur, opsiyonel ek basliklar ekler."""
    headers = PROFILES.get(profile, CHROME_124_WINDOWS).copy()
    if referer:
        headers["Referer"] = referer
    if origin:
        headers["Origin"] = origin
    if extra:
        headers.update(extra)
    return headers


def get_youtube_headers(*, referer: str | None = None) -> dict[str, str]:
    """YouTube'a ozel baslik seti."""
    h = get_headers("chrome_windows", referer=referer or "https://www.youtube.com/")
    h["Origin"] = "https://www.youtube.com"
    return h


def get_tiktok_headers(*, referer: str | None = None) -> dict[str, str]:
    """TikTok'a ozel baslik seti (mobil profil kullanarak WAF'i atlat)."""
    h = get_headers("chrome_android", referer=referer or "https://www.tiktok.com/")
    h["Origin"] = "https://www.tiktok.com"
    return h


def get_instagram_headers(*, referer: str | None = None) -> dict[str, str]:
    """Instagram'a ozel baslik seti."""
    h = get_headers("chrome_windows", referer=referer or "https://www.instagram.com/")
    h["Origin"] = "https://www.instagram.com"
    h["X-IG-App-ID"] = "936619743392459"
    h["X-Requested-With"] = "XMLHttpRequest"
    return h

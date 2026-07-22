"""Solenz Downloader - YouTube Player JS imza cozucu.

YouTube'un player JavaScript dosyasindan imza cozme (decipher)
fonksiyonunu dinamik olarak cikarir ve Python'a cevirir.
Ayrica 'n' parametresi (throttle token) donusumunu yapar.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

logger = logging.getLogger("solenz.decipher")


class SignatureDecipher:
    """YouTube player.js'ten imza cozme fonksiyonunu cikarir ve uygular."""

    def __init__(self, player_js: str) -> None:
        self._js = player_js
        self._decipher_func: list[tuple[str, int]] | None = None
        self._nsig_func_code: str | None = None

        self._parse_decipher()
        self._parse_nsig()

    # ================================================================== #
    #  IMZA COZME (sig / s parametresi)
    # ================================================================== #

    def decipher(self, signature: str) -> str:
        """Sifreli imzayi cozer."""
        if not self._decipher_func:
            logger.warning("Decipher fonksiyonu cikarilmadi, ham imza donuyor")
            return signature

        sig = list(signature)
        for op, arg in self._decipher_func:
            if op == "reverse":
                sig.reverse()
            elif op == "splice":
                sig = sig[arg:]
            elif op == "swap":
                sig[0], sig[arg % len(sig)] = sig[arg % len(sig)], sig[0]

        return "".join(sig)

    def _parse_decipher(self) -> None:
        """Player JS'ten decipher fonksiyonunu parse eder."""
        # Adim 1: Ana decipher fonksiyonunu bul
        # Desen: var XX=function(a){a=a.split("");YY.ZZ(a,N);...;return a.join("")};
        # veya: function XX(a){a=a.split("");YY.ZZ(a,N);...;return a.join("")}
        func_patterns = [
            # \b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\(([a-zA-Z0-9$]+)\(
            r'\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\(([a-zA-Z0-9$]+)\(',
            # \b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\(([a-zA-Z0-9$]+)\(
            r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\(([a-zA-Z0-9$]+)\(',
            # \bm=([a-zA-Z0-9$]{2,})\(decodeURIComponent\(h\.s\)\)
            r'\bm=([a-zA-Z0-9$]{2,})\(decodeURIComponent\(h\.s\)\)',
            # \bc\s*&&\s*d\.set\([^,]+\s*,\s*(?:encodeURIComponent\s*\()([a-zA-Z0-9$]+)\(
            r'\bc\s*&&\s*d\.set\([^,]+\s*,\s*(?:encodeURIComponent\s*\()([a-zA-Z0-9$]+)\(',
            # \bc\s*&&\s*[a-z]\.set\([^,]+\s*,\s*([a-zA-Z0-9$]+)\(
            r'\bc\s*&&\s*[a-z]\.set\([^,]+\s*,\s*([a-zA-Z0-9$]+)\(',
            # generic: XX=function(a){a=a.split("")
            r'([a-zA-Z0-9$]+)\s*=\s*function\(\s*a\s*\)\s*\{\s*a\s*=\s*a\.split\(\s*""\s*\)',
        ]

        func_name = None
        for pattern in func_patterns:
            m = re.search(pattern, self._js)
            if m:
                func_name = m.group(1)
                break

        if not func_name:
            logger.warning("Decipher fonksiyon adi bulunamadi")
            return

        logger.debug("Decipher fonksiyon adi: %s", func_name)

        # Adim 2: Fonksiyon govdesini bul
        escaped = re.escape(func_name)
        body_pattern = (
            r'(?:function\s+' + escaped + r'|' + escaped + r'\s*=\s*function)'
            r'\s*\(\s*a\s*\)\s*\{([^}]+)\}'
        )
        m = re.search(body_pattern, self._js)
        if not m:
            logger.warning("Decipher fonksiyon govdesi bulunamadi: %s", func_name)
            return

        body = m.group(1)
        logger.debug("Decipher fonksiyon govdesi: %s", body[:200])

        # Adim 3: Yardimci nesne adini bul (ornegin: YY.ZZ(a,N))
        helper_match = re.search(r'([a-zA-Z0-9$]+)\.[a-zA-Z0-9$]+\(', body)
        if not helper_match:
            logger.warning("Yardimci nesne adi bulunamadi")
            return

        helper_name = helper_match.group(1)

        # Adim 4: Yardimci nesnenin metotlarini bul
        helper_escaped = re.escape(helper_name)
        helper_pattern = (
            r'var\s+' + helper_escaped + r'\s*=\s*\{([\s\S]+?)\};'
        )
        hm = re.search(helper_pattern, self._js)
        if not hm:
            logger.warning("Yardimci nesne bulunamadi: %s", helper_name)
            return

        helper_body = hm.group(1)

        # Adim 5: Metot islevlerini tanimla
        method_map: dict[str, str] = {}
        # reverse: function(a){a.reverse()}
        # splice:  function(a,b){a.splice(0,b)}
        # swap:    function(a,b){var c=a[0];a[0]=a[b%a.length];a[b%a.length]=c}
        for method_match in re.finditer(
            r'([a-zA-Z0-9$]+)\s*:\s*function\s*\([^)]*\)\s*\{([^}]+)\}',
            helper_body,
        ):
            method_name = method_match.group(1)
            method_body = method_match.group(2)

            if "reverse" in method_body:
                method_map[method_name] = "reverse"
            elif "splice" in method_body:
                method_map[method_name] = "splice"
            else:
                method_map[method_name] = "swap"

        # Adim 6: Islemleri siraya diz
        operations: list[tuple[str, int]] = []
        for call_match in re.finditer(
            helper_escaped + r'\.([a-zA-Z0-9$]+)\s*\(\s*a\s*,\s*(\d+)\s*\)',
            body,
        ):
            method = call_match.group(1)
            arg = int(call_match.group(2))
            op = method_map.get(method, "")
            if op:
                operations.append((op, arg))

        # reverse cagrisi argumansiz da olabilir
        for call_match in re.finditer(
            helper_escaped + r'\.([a-zA-Z0-9$]+)\s*\(\s*a\s*\)',
            body,
        ):
            method = call_match.group(1)
            op = method_map.get(method, "")
            if op == "reverse":
                operations.append(("reverse", 0))

        if operations:
            self._decipher_func = operations
            logger.info(
                "Decipher fonksiyonu basariyla cikarildi: %d islem", len(operations)
            )
        else:
            logger.warning("Decipher islemleri cikarilmadi")

    # ================================================================== #
    #  N-SIG (THROTTLE TOKEN) DONUSUMU
    # ================================================================== #

    def transform_nsig(self, n_value: str) -> str:
        """n parametresini donusturur (throttle engelleme).

        Not: Tam nsig cozumu icin JS interpreter gerekir.
        Burada basit bypass denemesi yapilir.
        """
        # nsig donusumu cok karmasik (tam JS yorumlayici gerektirir)
        # Simdilik n parametresini oldugu gibi birakiyoruz
        # Bu durumda YouTube hiz sinirlamasi uygulayabilir
        return n_value

    def _parse_nsig(self) -> None:
        """n-sig fonksiyon kodunu cikarir (gelecekte kullanim icin)."""
        patterns = [
            r'\.get\("n"\)\)&&\(b=([a-zA-Z0-9$]+)(?:\[(\d+)\])?\(b\)',
            r'b=([a-zA-Z0-9$]+)(?:\[(\d+)\])?\(b\),b\.set\("n",b\)',
        ]
        for pattern in patterns:
            m = re.search(pattern, self._js)
            if m:
                self._nsig_func_code = m.group(0)
                logger.debug("nsig referansi bulundu: %s", self._nsig_func_code[:80])
                break

    # ================================================================== #
    #  SIGNATURE TIMESTAMP
    # ================================================================== #

    def get_sts(self) -> int | None:
        """Player JS'ten signatureTimestamp degerini cikarir."""
        m = re.search(r'signatureTimestamp["\s:]+(\d+)', self._js)
        if m:
            return int(m.group(1))
        return None

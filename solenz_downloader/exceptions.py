"""Solenz Downloader - Ozel istisna siniflari."""


class SolenzError(Exception):
    """Tum Solenz hatalarinin temel sinifi."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


class ExtractionError(SolenzError):
    """Platform'dan medya URL'si cikarilirken olusan hata."""
    pass


class DownloadError(SolenzError):
    """Dosya indirilirken olusan hata."""
    pass


class ProxyError(SolenzError):
    """Proxy baglantisi veya yapilandirma hatasi."""
    pass


class SignatureError(ExtractionError):
    """Sifrelenmis imza cozulemediginde firlatilir (ornegin YouTube nsig/sig)."""
    pass


class RateLimitError(SolenzError):
    """Platform tarafindan hiz sinirlamasi uygulandiginda firlatilir."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class GeoBlockError(SolenzError):
    """Icerik cografi kisitlama nedeniyle erisilemediginde firlatilir."""
    pass


class AgeGateError(SolenzError):
    """Icerik yas sinirlamasi nedeniyle erisilemediginde firlatilir."""
    pass

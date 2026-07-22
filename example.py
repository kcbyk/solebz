"""
Solenz Downloader - Kullanim Ornekleri
======================================

Bu dosya kutuphanenin temel kullanimini gosterir.
Calistirmadan once 'pip install curl_cffi' yuklu olmalidir.
"""

import solenz_downloader


def ornek_extract():
    """Bir YouTube videosunun medya bilgilerini cikarir."""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    print(f"[*] Medya bilgileri cikariliyor: {url}")
    result = solenz_downloader.extract(url)

    print(f"    Baslik  : {result.title}")
    print(f"    Platform: {result.platform}")
    print(f"    Sure    : {result.duration} saniye")
    print(f"    Yukleyen: {result.uploader}")
    print(f"    Akis Sayisi: {len(result.streams)}")
    print()

    # Akislari listele
    for s in result.streams:
        size_str = f"{s.filesize / 1024 / 1024:.1f}MB" if s.filesize else "?"
        print(f"    [{s.format_id:>4}] {s.resolution:>10} | {s.ext:>5} | {s.codec:>15} | {size_str}")

    # En iyi akis
    best = result.best_stream()
    if best:
        print(f"\n    En iyi akis: {best.resolution} {best.ext}")

    return result


def ornek_download():
    """Bir YouTube videosunu indirir."""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def ilerleme(indirilen, toplam, hiz):
        if toplam:
            yuzde = (indirilen / toplam) * 100
            print(f"\r    Ilerleme: {yuzde:.1f}% ({indirilen}/{toplam} byte)", end="", flush=True)
        else:
            print(f"\r    Indirilen: {indirilen} byte", end="", flush=True)

    print(f"[*] Indiriliyor: {url}")
    dosya_yolu = solenz_downloader.download(
        url,
        output_dir="./downloads",
        quality="720p",
        on_progress=ilerleme,
    )
    print(f"\n    Tamamlandi: {dosya_yolu}")


def ornek_proxy_ile():
    """SOCKS5 proxy uzerinden indirme."""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    result = solenz_downloader.extract(
        url,
        proxy="socks5://192.168.1.100:1080",
    )
    print(f"[*] Proxy ile cikarildi: {result.title}")


def ornek_sadece_ses():
    """Sadece ses akisini indirir."""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    result = solenz_downloader.extract(url)
    ses_akisi = result.best_audio()

    if ses_akisi:
        print(f"[*] En iyi ses: {ses_akisi.codec} {ses_akisi.bitrate}bps")
        dosya = solenz_downloader.download_stream(
            ses_akisi,
            output_dir="./downloads",
            filename="muzik.m4a",
            referer=url,
        )
        print(f"    Ses indirildi: {dosya}")


def ornek_desteklenen_platformlar():
    """Desteklenen platformlari listeler."""
    platformlar = solenz_downloader.supported_platforms()
    print(f"[*] Desteklenen platformlar: {', '.join(platformlar)}")


if __name__ == "__main__":
    ornek_desteklenen_platformlar()
    print()

    try:
        ornek_extract()
    except solenz_downloader.SolenzError as e:
        print(f"    Hata: {e}")
    except Exception as e:
        print(f"    Beklenmeyen hata: {e}")

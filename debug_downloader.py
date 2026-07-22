
import logging
import solenz_downloader
from solenz_downloader.core.downloader import SolenzDownloader
from solenz_downloader.core.client import SolenzClient

logging.basicConfig(level=logging.DEBUG)

TEST_URL = "https://youtu.be/4-6En3bf5TY?si=QDh0lo2UXwusOAcn"

media = solenz_downloader.extract(TEST_URL)
audio_stream = media.best_audio()

client = SolenzClient()
downloader = SolenzDownloader(
    client,
    max_concurrent=32,  # Use max possible
    chunk_size=16*1024*1024,
)

print("\n--- İndirme Başlıyor ---")
result = downloader.download_stream(
    audio_stream,
    output_dir="test_downloads",
    referer=media.url,
    resume=False,
)

print("İndirme tamamlandı:", result)

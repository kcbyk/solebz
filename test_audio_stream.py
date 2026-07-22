
import solenz_downloader

TEST_URL = "https://youtu.be/4-6En3bf5TY?si=QDh0lo2UXwusOAcn"

print("Test ediliyor:", TEST_URL)
media = solenz_downloader.extract(TEST_URL)
audio_stream = media.best_audio()

print("\n--- Ses Akışı Detayları ---")
print("URL:", audio_stream.url[:100] + "...")
print("Filesize:", audio_stream.filesize)
print("Quality:", audio_stream.quality)
print("Ext:", audio_stream.ext)
print("Has Audio:", audio_stream.has_audio)
print("Has Video:", audio_stream.has_video)

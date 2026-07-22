#!/usr/bin/env python3
"""YouTube arama testi."""

import solenz_downloader

print("=" * 60)
print("YouTube Arama Testi")
print("=" * 60)

query = "Rick Astley Never Gonna Give You Up"
print(f"\nArama: {query}\n")

results = solenz_downloader.search_youtube(query, limit=5)

print(f"Toplam {len(results)} sonuç bulundu:\n")

for i, result in enumerate(results, 1):
    print(f"{i}. {result.title}")
    print(f"   URL: {result.url}")
    print(f"   Yükleyici: {result.uploader}")
    if result.duration:
        print(f"   Süre: {result.duration} saniye")
    if result.view_count:
        print(f"   Görüntülenme: {result.view_count}")
    if result.description:
        print(f"   Açıklama: {result.description[:80]}...")
    print()

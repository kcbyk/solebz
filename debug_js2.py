"""Debug: Adaptive format yapisi analizi"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
import re, json

client = SolenzClient(proxy=None)
headers = get_youtube_headers()
resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
html = resp.text

pr_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;", html, re.DOTALL)
pr = json.loads(pr_match.group(1))
sd = pr.get("streamingData", {})

# Format 0 (birlesik) - tum anahtarlar
print("=== FORMAT (birlesik) ===")
for f in sd.get("formats", []):
    print(f"  Anahtarlar: {list(f.keys())}")
    if "signatureCipher" in f:
        print(f"  signatureCipher: {f['signatureCipher'][:120]}...")
    if "cipher" in f:
        print(f"  cipher: {f['cipher'][:120]}...")
    if "url" in f:
        print(f"  url: {f['url'][:120]}...")
    print()

# Adaptive - ilk 5
print("=== ADAPTIVE FORMATS ===")
for f in sd.get("adaptiveFormats", [])[:8]:
    itag = f.get("itag")
    quality = f.get("qualityLabel", f.get("quality", ""))
    mime = f.get("mimeType", "")[:40]
    keys = list(f.keys())
    print(f"  itag={itag} {quality} {mime}")
    print(f"    Anahtarlar: {keys}")
    if "url" in f:
        print(f"    url: {f['url'][:150]}...")
    if "signatureCipher" in f:
        print(f"    signatureCipher: {f['signatureCipher'][:150]}...")
    if "cipher" in f:
        print(f"    cipher: {f['cipher'][:150]}...")
    # Baska URL benzeri alanlar var mi?
    for k, v in f.items():
        if isinstance(v, str) and ("http" in v or "googlevideo" in v):
            print(f"    {k}: {v[:150]}...")
    print()

# Player JS'te decipher fonksiyonu ES6 arama
print("=== PLAYER JS ES6 DECIPHER ARAMA ===")
resp2 = client.get("https://www.youtube.com" + re.search(r'"(/s/player/[^"]+base\.js)"', html).group(1), timeout=30)
js = resp2.text

# Arrow function ile split
arrow_splits = re.findall(r'(\w+)\s*=\s*(?:function\s*\(a\)|a\s*=>)\s*\{[^}]*a\.split\s*\(\s*""\s*\)', js[:500000])
print(f"  Arrow/function split: {arrow_splits}")

# a=a.split("") herhangi bir formda
all_splits = [(m.start(), js[max(0,m.start()-50):m.start()+80]) for m in re.finditer(r'a=a\.split\(""\)', js)]
print(f"  a=a.split('') bulunma sayisi: {len(all_splits)}")
for pos, ctx in all_splits[:3]:
    print(f"    @{pos}: ...{ctx.strip()}...")

# encodeURIComponent cagrilari
enc_contexts = [(m.start(), js[max(0,m.start()-80):m.start()+40]) for m in re.finditer(r'encodeURIComponent\(\w+\(', js[:200000])]
print(f"\n  encodeURIComponent baglam ({len(enc_contexts)}):")
for pos, ctx in enc_contexts[:5]:
    print(f"    @{pos}: ...{ctx.strip()[:120]}...")

client.close()

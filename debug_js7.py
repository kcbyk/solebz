"""Debug: Player JS imza isleyici bulma - URL yapim zinciri"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
import re

client = SolenzClient(proxy=None)
headers = get_youtube_headers()
headers["Cookie"] = "CONSENT=YES+cb.20210328-17-p0.en+FX+435"

resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
html = resp.text
js_match = re.search(r'"(/s/player/[^"]+base\.js)"', html)
js_url = "https://www.youtube.com" + js_match.group(1)
resp2 = client.get(js_url, timeout=30)
js = resp2.text

# signatureCipher konumu 654779 civari - o bolgedeki kodu incele
print("=== signatureCipher civarindaki kod (654700-655200) ===")
print(js[654600:655400])

print("\n\n=== URL yapi arama ===")
# &sig= veya ?sig= yazar kodda
for pat_name, pat in [
    ("&sig=", r'["\']&sig=["\']'),
    ("sig=", r'["\']sig=["\']'),
    ('+"sig"', r'\+\s*"sig"'),
    ('set("sig', r'set\(\s*"sig"'),
    ('"sp"', r'"sp"\s*,'),
    ('url.set', r'\.set\(\s*["\']url["\']'),
    ('signatureCipher read', r'signatureCipher["\']?\s*\]'),
    ('&&b.set', r'&&\s*\w+\.set\('),
]:
    matches = [(m.start(), js[max(0,m.start()-60):m.end()+60].strip()) for m in re.finditer(pat, js)]
    if matches:
        print(f"\n  {pat_name}: {len(matches)} bulundu")
        for pos, ctx in matches[:5]:
            print(f"    @{pos}: {ctx[:150]}")

# "url" ve "signatureCipher" birlikte gecen bolgeleri ara
print("\n=== 'url' + 'signatureCipher' birlikte ===")
for m in re.finditer(r'signatureCipher', js):
    pos = m.start()
    block = js[max(0,pos-200):pos+500]
    if 'url' in block.lower():
        print(f"  @{pos}:")
        print(f"    {block[:400]}")
        print()

# get("url") veya get("s") patternleri
print("\n=== get('s') / get('url') / get('sp') ===")
for pat_name, pat in [
    ('get("s")', r'\.get\(\s*"s"\s*\)'),
    ('get("url")', r'\.get\(\s*"url"\s*\)'),
    ('get("sp")', r'\.get\(\s*"sp"\s*\)'),
    ('get("sig")', r'\.get\(\s*"sig"\s*\)'),
    ('get("n")', r'\.get\(\s*"n"\s*\)'),
]:
    matches = [(m.start(), js[max(0,m.start()-80):m.end()+80].strip()) for m in re.finditer(pat, js)]
    if matches:
        print(f"\n  {pat_name}: {len(matches)} bulundu")
        for pos, ctx in matches[:5]:
            print(f"    @{pos}: {ctx[:180]}")

client.close()

"""Debug: Player JS imza cozme fonksiyonu detayli arama"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
import re

client = SolenzClient(proxy=None)
headers = get_youtube_headers()
headers["Cookie"] = "CONSENT=YES+cb.20210328-17-p0.en+FX+435"

# Watch sayfasindan player JS URL al
resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
html = resp.text
js_match = re.search(r'"(/s/player/[^"]+base\.js)"', html)
js_url = "https://www.youtube.com" + js_match.group(1)

# Player JS indir
resp2 = client.get(js_url, timeout=30)
js = resp2.text
print(f"Player JS boyutu: {len(js)} karakter")

# 1) split iceren fonksiyonlar - her turlu varyasyon
print("\n=== SPLIT ARAMA ===")
split_patterns = [
    (r'\.split\(\s*""\s*\)', "split('')"),
    (r'\.split\(\s*\'\'\s*\)', "split('')  tek tirnak"),
    (r'\.split\(""\)', "split exact"),
]
for pat, desc in split_patterns:
    matches = [(m.start(), js[max(0,m.start()-80):m.start()+30].strip()) for m in re.finditer(pat, js)]
    print(f"  {desc}: {len(matches)} bulundu")
    for pos, ctx in matches[:3]:
        print(f"    @{pos}: ...{ctx[-100:]}...")

# 2) join iceren fonksiyonlar
print("\n=== JOIN ARAMA ===")
join_matches = [(m.start(), js[max(0,m.start()-80):m.start()+30].strip()) for m in re.finditer(r'\.join\(\s*""\s*\)', js)]
print(f"  join(''): {len(join_matches)} bulundu")
for pos, ctx in join_matches[:5]:
    print(f"    @{pos}: ...{ctx[-100:]}...")

# 3) reverse + splice + swap islemleri
print("\n=== REVERSE/SPLICE ARAMA ===")
for op, pat in [
    ("reverse", r'\.reverse\(\s*\)'),
    ("splice", r'\.splice\(\s*0\s*,'),
    ("swap", r'var\s+\w+=\w+\[0\];\w+\[0\]='),
]:
    matches = list(re.finditer(pat, js))
    print(f"  {op}: {len(matches)} bulundu")

# 4) signatureCipher ile ilgili kodlar
print("\n=== SIGNATURECIPHER REFERANSLARI ===")
for pat_name, pat in [
    ("signatureCipher", r'signatureCipher'),
    ("decipher", r'decipher'),
    ("sig &&", r'"sig"\s*&&'),
    ("set sig", r'\.set\(\s*"sig"'),
    ("sp&&", r'"sp"\s*&&'),
]:
    matches = [(m.start(), js[max(0,m.start()-40):m.start()+60].strip()) for m in re.finditer(pat, js)]
    print(f"  {pat_name}: {len(matches)}")
    for pos, ctx in matches[:3]:
        print(f"    @{pos}: ...{ctx[:120]}...")

# 5) URL islemcisi - set("url", ...) veya benzeri
print("\n=== URL SET ISLEMLERI ===")
url_set_matches = [(m.start(), js[max(0,m.start()-60):m.start()+80].strip()) for m in re.finditer(r'["\']url["\']\s*\)', js[:200000])]
for pos, ctx in url_set_matches[:5]:
    print(f"  @{pos}: ...{ctx[:140]}...")

# 6) Fonksiyon zincirleri: x(y) gibi tek arguman alan, split-join arasinda
print("\n=== POTANSIYEL DECIPHER FONKSIYONLARI ===")
# split ve join arasinda nesne metot cagrisi yapan fonksiyonlar
# Pattern: function(a){a=a.split("");...;return a.join("")}
# ES6 varyasyon: (a)=>{a=a.split("");...;return a.join("")}
decipher_patterns = [
    r'(\w+)\s*=\s*function\s*\(\s*\w+\s*\)\s*\{[^}]*split[^}]*join[^}]*\}',
    r'function\s+(\w+)\s*\(\s*\w+\s*\)\s*\{[^}]*split[^}]*join[^}]*\}',
    r'(\w+)\s*=\s*\(\s*\w+\s*\)\s*=>\s*\{[^}]*split[^}]*join[^}]*\}',
]
for pat in decipher_patterns:
    for m in re.finditer(pat, js):
        func_name = m.group(1)
        func_body = m.group(0)[:300]
        print(f"  Fonksiyon: {func_name}")
        print(f"    {func_body[:200]}...")

# 7) Player icinde ara: a=a.split("") - literal string search
print("\n=== LITERAL ARAMA ===")
literal = 'a=a.split("")'
idx = js.find(literal)
if idx >= 0:
    print(f"  BULUNDU @{idx}: {js[max(0,idx-100):idx+150]}")
else:
    print(f"  '{literal}' BULUNAMADI")
    # Alternatif: herhangi bir degisken.split("")
    for m in re.finditer(r'(\w)=\1\.split\(""\)', js):
        pos = m.start()
        print(f"  Alternatif @{pos}: {js[max(0,pos-80):pos+100]}")
        break

client.close()

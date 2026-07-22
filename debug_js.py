"""Debug: Player JS analizi"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
import re, json

client = SolenzClient(proxy=None)

# 1) Watch sayfasini indir
print("[1] Watch sayfasi indiriliyor...")
headers = get_youtube_headers()
resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
html = resp.text
print(f"    HTML boyutu: {len(html)} karakter")

# 2) Player JS URL bul
patterns = [
    r'"jsUrl"\s*:\s*"(/s/player/[^"]+base\.js)"',
    r'"PLAYER_JS_URL"\s*:\s*"([^"]+)"',
    r'src="(/s/player/[^"]+base\.js)"',
    r'"(/s/player/[^"]+base\.js)"',
]
player_url = ""
for p in patterns:
    m = re.search(p, html)
    if m:
        player_url = "https://www.youtube.com" + m.group(1)
        print(f"    Player JS: {player_url}")
        break

if not player_url:
    print("    Player JS URL BULUNAMADI!")
    # HTML icinde player ile ilgili satirlari goster
    for line in html.split("\n"):
        if "base.js" in line or "player_ias" in line or "jsUrl" in line:
            print(f"    > {line.strip()[:150]}")
    client.close()
    exit()

# 3) Player JS indir
print("[2] Player JS indiriliyor...")
resp2 = client.get(player_url, timeout=30)
js = resp2.text
print(f"    JS boyutu: {len(js)} karakter")

# 4) ytInitialPlayerResponse kontrol
print("[3] ytInitialPlayerResponse analizi...")
pr_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;", html, re.DOTALL)
if pr_match:
    try:
        pr = json.loads(pr_match.group(1))
        sd = pr.get("streamingData", {})
        formats = sd.get("formats", [])
        adaptive = sd.get("adaptiveFormats", [])
        print(f"    formats: {len(formats)}, adaptiveFormats: {len(adaptive)}")

        for f in formats[:2]:
            has_url = "url" in f
            has_cipher = "signatureCipher" in f or "cipher" in f
            print(f"    format itag={f.get('itag')} url={'VAR' if has_url else 'YOK'} cipher={'VAR' if has_cipher else 'YOK'}")

        for f in adaptive[:5]:
            has_url = "url" in f
            has_cipher = "signatureCipher" in f or "cipher" in f
            itag = f.get("itag")
            quality = f.get("qualityLabel", f.get("quality", ""))
            mime = f.get("mimeType", "")[:30]
            print(f"    adaptive itag={itag} {quality} {mime} url={'VAR' if has_url else 'YOK'} cipher={'VAR' if has_cipher else 'YOK'}")
    except Exception as e:
        print(f"    JSON parse hatasi: {e}")
else:
    print("    ytInitialPlayerResponse BULUNAMADI")

# 5) Decipher fonksiyon adi arama
print("[4] Decipher fonksiyon arama...")

# a.split("") iceren fonksiyonlari ara
split_funcs = re.findall(r'([a-zA-Z0-9$]{2,})\s*=\s*function\s*\(\s*a\s*\)\s*\{\s*a\s*=\s*a\.split\(\s*""\s*\)', js)
print(f"    a.split('') fonksiyonlari: {split_funcs}")

# encodeURIComponent ile iliskili
enc_matches = re.findall(r'encodeURIComponent\(([a-zA-Z0-9$]+)\(', js[:100000])
print(f"    encodeURIComponent(...( fonksiyonlari: {enc_matches[:10]}")

# set fonksiyonlari
set_matches = re.findall(r'\.set\([^,]+,\s*(?:encodeURIComponent\s*\()?([a-zA-Z0-9$]+)\(', js[:100000])
print(f"    .set(...) fonksiyonlari: {set_matches[:10]}")

# signatureTimestamp
sts_match = re.search(r'signatureTimestamp["\s:]+(\d+)', js)
if sts_match:
    print(f"    signatureTimestamp: {sts_match.group(1)}")

client.close()

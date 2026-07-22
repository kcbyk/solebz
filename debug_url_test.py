"""Debug: Pratik URL insa ve indirme testi"""
from solenz_downloader.core.client import SolenzClient
from solenz_downloader.utils.headers import get_youtube_headers
from urllib.parse import urlparse, parse_qs, urlencode, unquote, quote
import re, json

client = SolenzClient(proxy=None)
headers = get_youtube_headers()
headers["Cookie"] = "CONSENT=YES+cb.20210328-17-p0.en+FX+435"

resp = client.get("https://www.youtube.com/watch?v=dQw4w9WgXcQ", headers=headers)
html = resp.text

pr_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;", html, re.DOTALL)
pr = json.loads(pr_match.group(1))
sd = pr.get("streamingData", {})

# itag 18 signatureCipher
fmt18 = sd["formats"][0]
cipher = fmt18["signatureCipher"]
cp = parse_qs(cipher)
raw_url = unquote(cp["url"][0])
sig = cp["s"][0]
sp = cp["sp"][0]

print(f"=== ITAG 18 URL ANALIZI ===")
print(f"  sig uzunluk: {len(sig)}")
print(f"  sp: {sp}")

# sparams icerigi kontrol
parsed = urlparse(raw_url)
params = parse_qs(parsed.query)
sparams = params.get("sparams", [""])[0]
print(f"  sparams: {sparams}")
print(f"  'itag' sparams icinde mi: {'itag' in sparams}")

# Test 1: Raw URL, sig olmadan
print(f"\n=== TEST 1: URL sig olmadan ===")
try:
    r = client.head(raw_url, headers={"Referer": "https://www.youtube.com/"}, timeout=10)
    print(f"  Status: {r.status_code} CT: {r.headers.get('Content-Type','?')}")
except Exception as e:
    print(f"  HATA: {e}")

# Test 2: Raw URL + raw sig
print(f"\n=== TEST 2: URL + raw sig ===")
url_with_raw_sig = f"{raw_url}&{sp}={quote(sig, safe='')}"
try:
    r = client.head(url_with_raw_sig, headers={"Referer": "https://www.youtube.com/"}, timeout=10)
    print(f"  Status: {r.status_code} CT: {r.headers.get('Content-Type','?')} CL: {r.headers.get('Content-Length','?')}")
except Exception as e:
    print(f"  HATA: {e}")

# Test 3: itag degistirme denemesi (sparams'ta itag yoksa isleyebilir)
if "itag" not in sparams:
    print(f"\n=== TEST 3: ITAG DEGISTIRME (itag sparams'ta degil!) ===")
    for test_itag in [137, 248, 140, 251]:
        modified_url = re.sub(r'itag=\d+', f'itag={test_itag}', raw_url)
        test_url_sig = f"{modified_url}&{sp}={quote(sig, safe='')}"
        try:
            r = client.head(test_url_sig, headers={"Referer": "https://www.youtube.com/"}, timeout=10)
            ct = r.headers.get("Content-Type", "?")
            cl = r.headers.get("Content-Length", "?")
            print(f"  itag={test_itag}: {r.status_code} | CT={ct} | CL={cl}")
        except Exception as e:
            print(f"  itag={test_itag}: HATA - {e}")

# Test 4: URL'yi GET ile dene (belki HEAD reddediliyordur)
print(f"\n=== TEST 4: GET ile deneme (itag 18) ===")
try:
    r = client.get(raw_url, headers={"Referer": "https://www.youtube.com/", "Range": "bytes=0-1024"}, timeout=15)
    print(f"  Status: {r.status_code} CT: {r.headers.get('Content-Type','?')} Body: {len(r.content)} bytes")
except Exception as e:
    print(f"  HATA: {e}")

# Test 5: URL + sig GET
print(f"\n=== TEST 5: GET + raw sig (itag 18) ===")
try:
    r = client.get(url_with_raw_sig, headers={"Referer": "https://www.youtube.com/", "Range": "bytes=0-1024"}, timeout=15)
    print(f"  Status: {r.status_code} CT: {r.headers.get('Content-Type','?')} Body: {len(r.content)} bytes")
    if r.status_code == 200 or r.status_code == 206:
        print(f"  >>> CALISIYOR! <<<")
except Exception as e:
    print(f"  HATA: {e}")

client.close()
